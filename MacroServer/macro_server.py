import ctypes
import socket
import selectors
import subprocess
import threading
import time
import json
import click
import sys

from typing import Dict

from macro import Macro


class SocketClient:
    def __init__(self, sock, addr, port):
        self.sock = sock
        self.addr = addr
        self.port = port
        self.authorized = False
        self.buffer = b''
        self.last_heartbeat = time.time()


class Server:
    def __init__(self):
        self.sel = None
        self.refs = []
        self.accept_sock = None
        self.clients: Dict[SocketClient] = {}
        self.forbidden_clients: [str] = []
        self.heartbeat_thread = None
        self.auth_mode = False
        self.macro_running = None

    def run(self, server_addr, port, max_attempts, auth_mode):

        self.auth_mode = auth_mode
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_monitor, daemon=True)
        self.heartbeat_thread.start()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as self.accept_sock:
            for i in range(max_attempts):
                try_port = port + i
                try:
                    self.accept_sock.bind((server_addr, try_port))
                    break
                except OSError as e:
                    print(f'Cannot listen on {server_addr}:{try_port}.')
            else:
                # print(f'Could not after {max_attempts} attempts.')
                print(f'Could not bind to any port after {max_attempts} attempts. Exiting.')
                sys.exit(1)

            self.sel = selectors.DefaultSelector()
            self.accept_sock.listen()
            self.accept_sock.setblocking(False)
            self.sel.register(self.accept_sock, selectors.EVENT_READ, data=(self.accept, None))

            print(f'Server listening on {server_addr}:{try_port}.')
            try:
                while True:
                    events = self.sel.select(timeout=1)
                    for key, mask in events:
                        callback = key.data[0]
                        callback(key.fileobj, mask, key.data[1])
            except Exception as e:
                print(f"Error: {e}")
            finally:
                self.end()

    def heartbeat_monitor(self):
        while True:
            now = time.time()
            to_remove = []
            for addr, client in self.clients.items():
                if now - client.last_heartbeat > 15:
                    print(f"Client {addr} timed out.")
                    self.disconnect_client(client)
                    to_remove.append(addr)
            for addr in to_remove:
                self.clients.pop(addr)
            time.sleep(1)

    def disconnect_client(self, client):
        try:
            if client is None:
                pass
                # print(f"Trying to disconnect non-existing client")
            if client.sock and client.sock.fileno() != -1:
                self.sel.unregister(client.sock)
                client.sock.close()
            self.clients.pop(client.addr)
        except Exception as e:
            print(f"Error closing client socket: {e}")

    def accept(self, sock, mask, *args, **kwargs):
        conn, addr = sock.accept()
        print(f'Client connected: {addr[0]}:{addr[1]}')
        if addr[0] in self.forbidden_clients:
            print(f'Forbidden client {addr} tried to connect, disconnecting them.')
            self.send_message(conn, 'hello', 'reject')
            conn.close()
            return

        if self.auth_mode:
            approve = input(
                f"Approve connection from {addr[0]}:{addr[1]}? Yes / No / Ban (y/n/b): ")
            if approve.lower() == 'y' or approve.lower() == 'yes':
                pass
            elif approve.lower() == 'b' or approve.lower() == 'ban':
                self.forbidden_clients.append(addr[0])
                self.send_message(conn, 'hello', 'reject')
                conn.close()
                return
            else:
                self.send_message(conn, 'hello', 'reject')
                conn.close()
                return

        self.clients[addr] = SocketClient(conn, addr[0], addr[1])
        self.clients[addr].authorized = True

        conn.setblocking(False)
        self.send_message(conn, 'hello', 'accept')
        self.sel.register(conn, selectors.EVENT_READ, data=(self.handle_socket_message, addr))

    def handle_socket_message(self, sock, mask, addr):
        client = self.clients[addr]
        if addr[0] in self.forbidden_clients:
            print(f'Attempt to send message from forbidden client {addr}.')
            self.disconnect_client(client)
            return

        if client is None:
            print(f'Client {addr} not found.')
            return

        if not client.authorized:
            print(f"Unauthorized client {addr}.")
            return

        try:
            if mask & selectors.EVENT_READ:
                data = sock.recv(4096)
                if not data:
                    raise OSError
                client.buffer += data
                while b'\n' in client.buffer:
                    message, client.buffer = client.buffer.split(b'\n', 1)
                    msg_dict = json.loads(message)
                    self.handle_message(msg_dict, client)
            else:
                print(f'Unexpected mask: {mask}')

            return

        except OSError:
            print(f"Client {addr[0]}, {addr[1]} disconnected.")

        except Exception as e:
            print(f"Error retrieving message: {e}")

        if addr in self.clients:
            self.sel.unregister(sock)
            sock.close()
            self.clients[addr].sock = None
            self.clients.pop(addr)

    def send_message(self, sock, msg_type, msg_data):
        message = {'type': msg_type, 'data': msg_data}
        enc_message = json.dumps(message).encode() + b'\n'
        sock.sendall(enc_message)

    def send_message_to_all(self, msg_type, msg_data, not_to=None):
        for addr, client in self.clients.items():
            if not_to is not None and client == not_to:
                continue
            if client.sock:
                self.send_message(client.sock, msg_type, msg_data)

    def handle_message(self, message_dict, client):
        if client is None:
            raise ValueError('Client is None in handle message')
        message_type = message_dict.get('type')
        message_data = message_dict.get('data')
        if message_type == 'heartbeat':
            self.send_message(client.sock, 'heartbeat', 'pong')
            client.last_heartbeat = time.time()
        if message_type == 'request-macros':
            self.send_message(client.sock, 'macro-list', self.get_macros())
        if message_type == 'request-macros-update':
            self.send_message(client.sock, 'update-macro-list', self.get_macros())
        if message_type == 'execute-macro':
            if self.macro_running is not None:
                self.send_message(client.sock, 'macro-already-running', self.macro_running.macro_id)
                return
            macro = self.get_macro(message_data)
            if macro is None:
                self.send_message(client.sock, 'error', f'Macro {message_data} not found')
                return
            self.macro_running = macro

            t = threading.Thread(target=self.execute_macro, daemon=False)
            t.start()
            self.send_message_to_all('macro-started', message_data)

        if message_type == 'stop-macro':
            if self.macro_running is not None:
                self.macro_running.stop()
                self.send_message_to_all('macro-stopped', self.macro_running.macro_id)
                self.macro_running = None
                return
            self.send_message(client.sock, 'error', 'No macro running')
        if message_type == 'set-layout':
            macro_list = []
            try:
                layout = json.loads(message_data)
                for macro in layout:
                    macro_id = macro.get('macro_id')
                    position = macro.get('position')
                    if macro_id is not None and position is not None:
                        m = Macro.load(f'macros/{macro_id}.json')
                        if not m:
                            self.send_message(client.sock, 'error', f'Macro {macro_id} not found')
                            continue
                        m.position = position
                        macro_list.append(m)
                    else:
                        self.send_message(client.sock, 'error', 'Invalid layout data')
                        return
                for m in macro_list:
                    m.save(overwrite=True, only_info=True)
                self.send_message_to_all('update-macro-list', self.get_macros(), not_to=client)
                print("Layout has been set.")
            except Exception as e:
                print(f"Error setting layout: {e}")
                self.send_message(client.sock, 'error', 'Invalid layout data')

    def execute_macro(self):
        exec_ret_val = ''
        try:
            exec_ret_val = self.macro_running.execute()
        except Exception as e:
            print(f"Error executing macro: {e}")
            self.send_message_to_all('macro-ended', 'Unexpected error')

        if exec_ret_val == 'success':
            self.send_message_to_all('macro-ended', self.macro_running.macro_id)
        elif exec_ret_val == 'stopped':
            pass  # Client already notified
        else:
            self.send_message_to_all('macro-ended', self.macro_running.macro_id)
            print(f'Unexpected return value from macro.execute(): {exec_ret_val}')
        self.macro_running = None

    def get_macro(self, macro_id):
        return Macro.load(f'macros/{macro_id}.json')

    def get_macros(self):
        return Macro.get_all_macros_info()

    def end(self):
        for _, client in self.clients.items():
            self.disconnect_client(client)

        if self.macro_running:
            self.macro_running.stop()
        try:
            self.accept_sock.close()
        except Exception as e:
            print(f"Error closing server accept socket: {e}")

        self.sel.close()

        print("Server closed.")


def check_firewall_rule(port, count=1):
    command = f"netsh advfirewall firewall show rule name=\"MacroServer\""

    try:
        output = subprocess.check_output(command, shell=True, text=True)
        output = output.replace(" ", "")
        str_ports = output.split("LocalPort:")[1].split("\n")[0].split("-")
        if count == 1:
            if f"{str_ports[0]}" in output:
                return True
            else:
                return False
        else:
            ports = [int(p) for p in str_ports]
            if ports[0] <= port and ports[1] >= port + count - 1:
                return True
            return False

    except subprocess.CalledProcessError as e:
        # print(f"Error checking firewall rule: {e}")
        return False
    except Exception as e:
#         print(f"Error checking firewall rule: {e}")
        return False


def add_firewall_rule(port, count=1):
    # Try removing any old firewall rule
    command = f"netsh advfirewall firewall delete rule name=\"MacroServer\""
    try:
        subprocess.check_output(command, shell=True)
    except subprocess.CalledProcessError as e:
        # print(f"Error deleting firewall rule: {e}")
        pass

    # Add a new rule
    if count == 1:
        command = f"netsh advfirewall firewall add rule name=\"MacroServer\" dir=in action=allow protocol=TCP localport={port} enable=yes"
    else:
        command = f"netsh advfirewall firewall add rule name=\"MacroServer\" dir=in action=allow protocol=TCP localport={port}-{port + count - 1} enable=yes"
    try:
        subprocess.check_output(command, shell=True)
        return True
    except subprocess.CalledProcessError as e:
        return False


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def run_as_admin():
    if is_admin():
        return
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)


@click.command()
@click.option('--server', '-s', default="", help="Server address to bind to, default is all interfaces.")
@click.option('--port', '-p', type=int, default=5908, help="Port to bind to.")
@click.option('--max-attempts', type=int, default=3,
              help="Number of attempts to find a next free port (right after --port) if selected port is not available. When used with manage_firewall, this is the number of ports to open.")
@click.option('--manage_firewall', '-fw', is_flag=True,
              help="Check and configure firewall rule for the port or port range, see --max_attemts")
@click.option('--auth', '-a', is_flag=True,
              help="Require manual authorization of clients, by default all clients are automatically accepted.")
def main(server, port, max_attempts, manage_firewall, auth):
    if manage_firewall:
        if not is_admin():
            print(
                "Not running as admin, can't check or add firewall rules, please grant admin privileges.")
            run_as_admin()
            sys.exit(0)
        if not check_firewall_rule(port, max_attempts):
            print(f"Firewall rule doesn't exist or match port range, creating a new rule.")
            if not add_firewall_rule(port, max_attempts):
                print(f"Error adding firewall rule.")
                sys.exit(1)
            print(f"Firewall rule added.")
        else:
            print(f"Firewall was already configured.")
        input("Press Enter to continue...")
        sys.exit(0)
    if not manage_firewall:
        if is_admin():
            print(f"Running as admin is not recommended, are you sure?")
            input("Press Enter to continue...")
    srv = Server()
    srv.run(server, port, max_attempts, auth)


if __name__ == "__main__":
    main()
