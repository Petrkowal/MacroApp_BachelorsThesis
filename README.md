# Macro App - Bachelor's Thesis

My bachelor's thesis - App for running macros on a PC from an Android device\
The application allows you to create macros on a computer and run them on the computer using an Android device.
1. Server on a PC (Python) - MacroServer
   - Macro editor - PyQT6 application for creating, editing, and managing macros
   - Server - socket server that listens for commands from the client and runs macros on the computer
2. Client as an Android application (Java) - MacroClient

The thesis is written in Czech, you can find it in the `Thesis` folder along with the reviews.\
Link to the thesis - DSpace VŠB-TUO: https://dspace.vsb.cz/handle/10084/153637



## Macro
A sequence of commands that can be executed on a computer.\
Macro can be created, tested and saved in the editor application.\
Each macro is saved as a JSON file.

List of elementary commands:
- Keyboard input (key press / release)
- Mouse input (press / release, move, scroll)
- Text input (text to be typed)
- Delay (pause between commands)
  - Macro can also use command timing - instead of fixed delays, each command has a timestamp relative to the start of the macro, so the delay is calculated dynamically during the execution of the macro.

## MacroServer

### Requirements
- Tested on Python 3.10, but should probably work on any version of Python 3
- Developed for Windows, works on Linux too, but the library for simulating user input works slightly differently which can cause some issues, especially with special keys.

### Installation
1. Create a virtual environment
   ```bash
   python -m venv venv
   ```   
2. Activate the virtual environment
   ```bash
    venv\Scripts\activate
    ```
3. Install the required packages
    ```bash
    python -m pip install -r requirements.txt
    ```

### Usage
#### Macro manager
Just run the `macro_manager.py`, nothing difficult here.
#### Macro Server
Run the `macro_server.py` to start the server.\
Here you can set the IP, port and some additional settings.
```
--server, -s <IP>       Server IP address
--port, -p <port>       Server port, default: 5908
--auth, -a              Enable authentication (default: False) - requires manual approval of each client connection
--max-attempts          If the selected port is already in use, the server will try to find a free port in the range from the selected port to the selected port + max-attempts (default: 3)
--manage_firewall, -fw  Add a rule to the firewall (Windows only) to allow incoming connections on the specified port (default: False)
```

## MacroClient

### Installation
Install the APK file on your Android device.\
Should work on any non-ancient Android version.\
If you want to build the application yourself, you can use some Android IDE (e.g. Android Studio) and build the project from the source code, which uses `Gradle` to build the project.
