package com.kra0633.macroclient;

import android.app.Service;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.SharedPreferences;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.PopupMenu;
import android.widget.TextView;
import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import org.json.JSONObject;

import java.util.function.Consumer;


public class MainActivity extends AppCompatActivity {


    private Button btnConnect;
    private EditText editText;
    private SocketService socketService;
    private ServiceConnection serviceConnection;
    private boolean isBound = false;
    private TextView statusTextView;
    private final int retries = 10;
    private final int defaultPort = 5908;
    private SharedPreferences sharedPref;
    private SharedPreferences.Editor editor;
    private MenuItem grayToggle;


    @Override
    protected void onCreate(Bundle savedInstanceState) {
        if (this.sharedPref == null || this.editor == null){
            this.sharedPref = getSharedPreferences(getString(R.string.shared_preferences), MODE_PRIVATE);
            this.editor = sharedPref.edit();
        }
        if (sharedPref.getBoolean("black_and_white", false)){
            setTheme(R.style.Theme_MacroClient_Grayscale);
        }
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        this.btnConnect = findViewById(R.id.btnConnect);
        this.editText = findViewById(R.id.editTextIp);
        this.statusTextView = findViewById(R.id.textViewStatus);

        this.statusTextView.setMaxWidth((int) (getResources().getDisplayMetrics().widthPixels * 0.9));

        this.bindService();

        this.btnConnect.setOnClickListener(v -> {

            setStatus("Connecting...");

            String ip = this.editText.getText().toString();
            ip = ip.replaceAll("\\s", "");
            String[] parts = ip.split(":");
            if (parts.length == 1)
                this.connect(parts[0], defaultPort, retries);
            else if (parts.length == 2)
                this.connect(parts[0], Integer.parseInt(parts[1]), 1);
            else
                setStatus("Invalid IP address");
        });
    }

    private void connect(String ip, int port, int retries) {

        if (this.isBound && this.serviceConnection != null) {
            new Thread(() -> this.socketService.connect(ip, port, retries, connectedCallback)).start();
        } else {
            setStatus("Not connected - Service not bound");
        }
    }

    private final Consumer<Boolean> connectedCallback = (Boolean connected) -> {
        if (connected) {
            setStatus("Connected, waiting for data");
        } else {
            setStatus("Failed to connect");
        }
    };

    private void setStatus(String status) {
        this.statusTextView.setText(String.format("Status: %s", status));
    }

    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.main_menu_btn, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        int id = item.getItemId();
        if (id == R.id.showPopup) {
            showPopupMenu(findViewById(R.id.showPopup));
            return true;
        }
        return true;
    }

    private void showPopupMenu(View view) {
        PopupMenu popupMenu = new PopupMenu(this, view);
        popupMenu.getMenuInflater().inflate(R.menu.main_menu, popupMenu.getMenu());
        grayToggle = popupMenu.getMenu().findItem(R.id.grayScaleToggle);
        grayToggle.setChecked(sharedPref.getBoolean("black_and_white", false));
        popupMenu.setOnMenuItemClickListener(item -> {
            if (item.getItemId() == R.id.grayScaleToggle) {
                boolean state = !item.isChecked();
                editor.putBoolean("black_and_white", state);
                editor.apply();
                item.setChecked(state);
                if (state){
                    setTheme(R.style.Theme_MacroClient_Grayscale);
                }
                else {
                    setTheme(R.style.Theme_MacroClient);
                }
                recreate();
            }

            item.setShowAsAction(MenuItem.SHOW_AS_ACTION_COLLAPSE_ACTION_VIEW);
            item.setActionView(new View(MainActivity.this));
            item.setOnActionExpandListener(new MenuItem.OnActionExpandListener() {
                @Override
                public boolean onMenuItemActionExpand(MenuItem item) {
                    return true;
                }

                @Override
                public boolean onMenuItemActionCollapse(MenuItem item) {
                    return true;
                }
            });

            return false;
        });

        popupMenu.show();
        grayToggle = popupMenu.getMenu().findItem(R.id.grayScaleToggle);
        grayToggle.setChecked(sharedPref.getBoolean("black_and_white", false));
    }
    private final Consumer<JSONObject> receiveMessage = (JSONObject message) -> {
        Log.d("SocketService", message.toString());

        String type = message.optString("type");
        String data = message.optString("data");

        if (type.equals("error")) {
            Log.e("SocketService", data);
        } else if (type.equals("hello") && data.equals("reject")) {
            Log.e("SocketService", "Access denied");
            setStatus("Access denied");
        } else if (type.equals("hello") && data.equals("accept")) {
            this.socketService.sendMessage("request-macros", "", false);
        } else if (type.equals("macro-list")) {
            Log.d("MainActivity", "macros: " + data);
            Intent intent = new Intent(this, MacrosActivity.class);
            intent.putExtra("macros", data);
            startActivity(intent);
        }
    };

    private void bindService() {
        this.serviceConnection = new ServiceConnection() {
            public void onServiceConnected(android.content.ComponentName name, android.os.IBinder service) {
                SocketService.LocalBinder binder = (SocketService.LocalBinder) service;
                socketService = binder.getService();
                isBound = true;
                socketService.setCallback(receiveMessage);
                socketService.setOnDisconnectCallback(onDisconnect);
            }

            public void onServiceDisconnected(android.content.ComponentName name) {
                isBound = false;
                onDisconnect.run();
            }
        };
        bindService(new Intent(this, SocketService.class), this.serviceConnection, Service.BIND_AUTO_CREATE);
    }

    private void closeSocket() {
        if (this.isBound) {
            try {
                this.socketService.disconnect();
            } catch (Exception e) {
                Log.e("Socket service disconnect error", e.getMessage());
            }
        }
    }

    private final Runnable onDisconnect = () -> {
        setStatus("Disconnected");
    };

    private void unbindService() {
        if (this.isBound) {
            unbindService(this.serviceConnection);
            this.isBound = false;
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        this.closeSocket();
        this.unbindService();
    }


}