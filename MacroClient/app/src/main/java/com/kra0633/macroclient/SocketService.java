package com.kra0633.macroclient;

import android.app.Service;
import android.content.Intent;
import android.os.Binder;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.util.Log;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.function.Consumer;

public class SocketService extends Service {

    private final IBinder mBinder = new LocalBinder();

    public class LocalBinder extends Binder {
        SocketService getService() {
            return SocketService.this;
        }
    }

    private Socket socket;
    private Thread socketThread;
    private Thread recvThread;
    private Thread heartbeatThread;
    private ArrayList<Consumer<JSONObject>> callbacks = new ArrayList<>();
    private final ArrayList<Runnable> disconnectCallbacks = new ArrayList<>();
    private Handler handler;
    private boolean isConnected = false;
    private boolean heartbeatReceived = false;

    public SocketService() {
    }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        this.handler = new Handler(Looper.getMainLooper());
        return START_STICKY;
    }

    @Override
    public IBinder onBind(Intent intent) {
        return mBinder;
    }

    public void setCallback(Consumer<JSONObject> callback) {
        if (this.callbacks == null) {
            this.callbacks = new ArrayList<>();
        }
        if (callback != null && !this.callbacks.contains(callback)) {
            this.callbacks.add(callback);
        }
    }

    public void removeCallback(Consumer<JSONObject> callback) {
        if (this.callbacks != null) {
            this.callbacks.remove(callback);
        }
    }

    public void setOnDisconnectCallback(Runnable callback) {
        if (callback != null && !this.disconnectCallbacks.contains(callback)) {
            this.disconnectCallbacks.add(callback);
        }
    }

    public void removeOnDisconnectCallback(Runnable callback) {
        this.disconnectCallbacks.remove(callback);
    }

    private void makeHeartbeatThread() {
        if (this.heartbeatThread != null) {
            if (this.heartbeatThread.isAlive()) {
                this.heartbeatThread.interrupt();
            }
        }
        this.heartbeatThread = new Thread(() -> {
            boolean firstHeartbeat = true;
            while (true) {
                try {
                    Thread.sleep(5000);
                    if (!this.heartbeatReceived && !firstHeartbeat) {
                        Log.e("Socket service error", "Heartbeat not received, disconnecting");
                        this.disconnect();
                        break;
                    }
                    firstHeartbeat = false;
                    this.sendMessage("heartbeat", "ping", false);
                    this.heartbeatReceived = false;
                } catch (Exception e) {
                    if (!this.isConnected) {
                        Log.e("Socket service error", "Heartbeat not received, disconnecting");
                        this.disconnect();
                        break;
                    }
                }
            }
        });
    }

    public void connect(String ip, int port, int retries, Consumer<Boolean> callback) {
        try {
            if (this.handler == null) {
                this.handler = new Handler(Looper.getMainLooper());
            }
            boolean connected = false;
            for (int i=0; i < retries; i++){
                connected = this.connect(ip, port + i);
                if (connected) {
                    break;
                }
            }
            boolean finalConnected = connected;
            handler.post(() -> {
                callback.accept(finalConnected);
            });
        } catch (Exception e) {
            Log.e("Socket service error", e.getMessage());
        }
    }

    public boolean connect(String ip, int port) {

        if (this.socketThread != null) {
            if (this.socketThread.isAlive()) {
                this.socketThread.interrupt();
            }
        }

        if (this.socket != null) {
            try {
                this.socket.close();
                this.socket = null;
            } catch (Exception e) {
                Log.e("Socket service error", e.getMessage());
            }
        }

        this.socketThread = new Thread(() -> {
            try {
                this.socket = new Socket(ip, port);
            } catch (Exception e) {
                Log.e("Socket service error", e.getMessage());
            }
        });

        this.makeHeartbeatThread();

        this.socketThread.start();
        try {
            this.socketThread.join(500);
        } catch (InterruptedException e) {
            throw new RuntimeException(e);
        }
        if (this.socket == null || this.socket.isClosed()) {
            Log.e("Socket service error", "Failed to connect to server at " + ip + ":" + port);
            return false;
        }
        this.isConnected = true;
        this.recvMessages();
        return true;
    }

    public void startHeartbeats() {
        if (this.heartbeatThread != null) {
            if (this.heartbeatThread.isAlive()) {
                this.heartbeatThread.interrupt();
            }
        }
        this.makeHeartbeatThread();
        this.heartbeatThread.start();
    }

    private void interruptThreadsAndCallCallbacks() {
        this.heartbeatThread.interrupt();
        for (Runnable callback : this.disconnectCallbacks) {
            callback.run();
        }
    }

    public void disconnect() {
        try {
            this.socket.close();
            this.isConnected = false;
            this.interruptThreadsAndCallCallbacks();
            this.recvThread.interrupt();
        } catch (Exception e) {
            Log.e("Socket service error", e.getMessage());
        }
    }

    public boolean sendMessage(String msgType, String msgData, boolean join) {
        if (this.socket == null || this.socket.isClosed()) {
            Log.e("Socket service error", "Not connected to server");
            return false;
        }

        JSONObject msg = new JSONObject();
        try {
            msg.put("type", msgType);
            msg.put("data", msgData);
        } catch (Exception e) {
            Log.e("Socket service error", e.getMessage());
            return false;
        }

        byte[] message = msg.toString().getBytes(StandardCharsets.UTF_8);
        byte[] newline = "\n".getBytes(StandardCharsets.UTF_8);
        byte[] buffer = new byte[message.length + newline.length];
        System.arraycopy(message, 0, buffer, 0, message.length);
        System.arraycopy(newline, 0, buffer, message.length, newline.length);


        Thread sendThread = new Thread(() -> {
            try {
                this.socket.getOutputStream().write(buffer);
            } catch (Exception e) {
                Log.e("Socket service error", e.getMessage());
            }
        });

        sendThread.start();

        if (join) {
            try {
                sendThread.join(500);
            } catch (Exception e) {
                Log.e("Socket service error", e.getMessage());
                return false;
            }
        }
        return true;
    }

    private void recvMessages() {
        if (this.recvThread != null && this.recvThread.isAlive()) {
            return;
        }
        if (this.recvThread != null) {
            this.recvThread.interrupt();
        }
        this.recvThread = new Thread(() -> {
            try {
                Thread.sleep(50);
                if (this.socket == null || this.socket.isClosed()) {
                    Thread.sleep(1000); // Try waiting for the socket to actually connect
                }
                if (this.socket == null || this.socket.isClosed()) {
                    Log.e("Socket service error", "Socket is null");

                    this.interruptThreadsAndCallCallbacks();
                    return;
                }
                InputStream is = this.socket.getInputStream();
                BufferedReader br = new BufferedReader(new java.io.InputStreamReader(is));
                StringBuilder sb = new StringBuilder();
                int character;
                while ((character = br.read()) != -1) {
                    if (character == '\n') {
                        String message = sb.toString();

                        String msgType;
                        String msgData;
                        JSONObject msg;
                        try {
                            msg = new JSONObject(message);
                            msgType = msg.getString("type");
                            msgData = msg.getString("data");
                        } catch (Exception e) {
                            Log.e("Socket service error", e.getMessage());
                            continue;
                        }
                        Log.d("Message received", message);

                        if (msgType.equals("error")) {
                            Log.e("Socket service error", msgData);
                        }
                        if (msgType.equals("heartbeat")) {
                            heartbeatReceived = true;
                        }
                        if (msgType.equals("hello") && msgData.equals("accept")) {
                            this.startHeartbeats();
                        }
                        if (this.callbacks != null && !this.callbacks.isEmpty()) {
                            try {
                                if (this.handler == null) {
                                    this.handler = new Handler(Looper.getMainLooper());
                                }
                                handler.post(() -> {
                                    for (Consumer<JSONObject> callback : this.callbacks) {
                                        callback.accept(msg);
                                    }
                                });
                            } catch (Exception e) {
                                Log.e("Socket service error", e.getMessage());
                            }
                        }

                        sb.setLength(0);
                    } else {
                        sb.append((char) character);
                    }
                }
                this.socket.close();
                Log.e("Error", "Connection closed");

                this.interruptThreadsAndCallCallbacks();

            } catch (Exception e) {
                Log.e("Error", e.getMessage());
            }

            isConnected = false;
        });
        this.recvThread.start();
    }

    @Override
    public void onDestroy() {
        super.onDestroy();
        if (this.socket != null) {
            try {
                this.socket.close();
            } catch (Exception e) {
                Log.e("Socket service error", e.getMessage());
            }
        }
        if (this.socketThread != null) {
            this.socketThread.interrupt();
        }
    }
}

