package com.kra0633.macroclient;

import android.app.Service;
import android.content.Intent;
import android.content.ServiceConnection;
import android.content.SharedPreferences;
import android.util.Log;
import android.view.Menu;
import android.view.MenuItem;
import android.widget.Toast;
import androidx.appcompat.app.AppCompatActivity;
import android.os.Bundle;
import androidx.recyclerview.widget.ItemTouchHelper;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.function.Consumer;

public class MacrosActivity extends AppCompatActivity {

    private SocketService socketService;
    private ServiceConnection serviceConnection;
    private boolean isBound = false;
    private boolean anyMacroRunning = false;
    private final List<Macro> macroList = new ArrayList<>();
    private RecyclerView recyclerView;
    private boolean editMode = false;
    private MenuItem reorderMenuItem;
    private MenuItem saveMenuItem;
    private MenuItem refreshMenuitem;
    private MenuItem discardMenuItem;
    private RecyclerRowMoveCallback callback = null;
    private CustomMacroAdapter adapter = null;
    private SharedPreferences sharedPref;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        sharedPref = getSharedPreferences(getString(R.string.shared_preferences), MODE_PRIVATE);
        if (sharedPref.getBoolean("black_and_white", false)) {
            setTheme(R.style.Theme_MacroClient_Grayscale);
        } else {
            setTheme(R.style.Theme_MacroClient);
        }
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_macros);

        this.bindService();
        JSONObject macros;
        try {
            macros = new JSONObject(getIntent().getStringExtra("macros"));
            JSONArray macrosArray = macros.getJSONArray("macro_list");
            this.makeMacroList(macrosArray);
        } catch (Exception e) {
            Log.e("MacrosActivity", "Error: " + e.getMessage());
            Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
        }
    }

    private void makeMacroList(JSONArray macros) {
        for (int i = 0; i < macros.length(); i++) {
            try {
                JSONObject macro = macros.getJSONObject(i);
                String name = macro.getString("name");
                String description = macro.getString("description");
                String id = macro.getString("macro_id");
                int position = macro.getInt("position");
                Macro newMacro = new Macro(name, description, id, position);
                newMacro.setExecuteCallback(this.executeMacro);
                newMacro.setStopCallback(this.stopMacro);
                this.macroList.add(newMacro);
            } catch (Exception e) {
                Log.e("MacrosActivity", "Error: " + e.getMessage());
                Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
            }
        }
        this.macroList.sort(Comparator.comparingInt(Macro::getPosition));

        this.setupRecyclerView();
        this.tryResetingMenu();

    }

    private void tryResetingMenu() {
        if (this.reorderMenuItem != null) {
            this.reorderMenuItem.setVisible(true);
            this.saveMenuItem.setVisible(false);
            this.discardMenuItem.setVisible(false);
            callback.setLongPressEnabled(false);
        }
    }

    private void setupRecyclerView() {
        recyclerView = findViewById(R.id.recyclerViewMacros);
        adapter = new CustomMacroAdapter(getApplicationContext(), this.macroList);

        callback = new RecyclerRowMoveCallback(adapter);
        ItemTouchHelper touchHelper = new ItemTouchHelper(callback);
        touchHelper.attachToRecyclerView(recyclerView);

        recyclerView.setAdapter(adapter);
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
    }

    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.macro_menu, menu);
        this.reorderMenuItem = menu.findItem(R.id.menuItemReorder);
        this.saveMenuItem = menu.findItem(R.id.menuItemSave);
        this.discardMenuItem = menu.findItem(R.id.menuItemDiscard);
        this.refreshMenuitem = menu.findItem(R.id.menuitemRefresh);
        this.saveMenuItem.setVisible(false);
        this.discardMenuItem.setVisible(false);
        this.editMode = false;
        return true;
    }

    public boolean onOptionsItemSelected(MenuItem item) {
        int id = item.getItemId();
        if (id == R.id.menuitemRefresh) {
            if (this.editMode) {
                this.editMode = false;
                this.reorderMenuItem.setVisible(true);
                this.saveMenuItem.setVisible(false);
                this.discardMenuItem.setVisible(false);
            }
            this.socketService.sendMessage("request-macros-update", "", false);
        }
        else if (id == R.id.menuItemReorder) {
            this.editMode = true;
            this.reorderMenuItem.setVisible(false);
            this.saveMenuItem.setVisible(true);
            this.discardMenuItem.setVisible(true);
            callback.setLongPressEnabled(true);
        }
        else if (id == R.id.menuItemSave) {
            this.editMode = false;
            this.reorderMenuItem.setVisible(true);
            this.saveMenuItem.setVisible(false);
            this.discardMenuItem.setVisible(false);
            callback.setLongPressEnabled(false);
            adapter.save();
            String messageData = getLayoutData();
            Log.e("MacrosActivity", messageData);
            if (!this.socketService.sendMessage("set-layout", messageData, true)){
                finish();
            }
        }
        else if (id == R.id.menuItemDiscard) {
            this.editMode = false;
            this.reorderMenuItem.setVisible(true);
            this.saveMenuItem.setVisible(false);
            this.discardMenuItem.setVisible(false);
            callback.setLongPressEnabled(false);
            adapter.revert();
        }

        return super.onOptionsItemSelected(item);
    }

    private String getLayoutData() {
        JSONArray layoutData = new JSONArray();
        List<Macro> macros = adapter.getItemList();
        for (int i = 0; i < macros.size(); i++) {
            JSONObject macroData = new JSONObject();
            try {
                macroData.put("macro_id", macros.get(i).getId());
                macroData.put("position", i);
                layoutData.put(macroData);
            } catch (Exception e) {
                Log.e("MacrosActivity", "Error: " + e.getMessage());
            }
        }
        return layoutData.toString();
    }

    private final Runnable stopMacro = () -> {
        if (this.isBound) {
            if (this.anyMacroRunning) {
                if (!this.socketService.sendMessage("stop-macro", "", true))
                    finish();
            }
        }
    };

    private final Consumer<Macro> executeMacro = (Macro macro) -> {
        if (this.isBound) {
            if (!this.socketService.sendMessage("execute-macro", macro.getId(), true))
                finish();
        }
    };

    private Macro getMacroById(String macroId) {
        for (Macro macro : this.macroList) {
            if (macro.getId().equals(macroId)) {
                return macro;
            }
        }
        return null;
    }

    private final Consumer<JSONObject> receiveMessage = (JSONObject message) -> {
        Log.d("SocketService", message.toString());

        String type = message.optString("type");
        String data = message.optString("data");

        if (type.equals("error")) {
            Log.e("SocketService", data);
            Toast.makeText(this, "Error: " + data, Toast.LENGTH_LONG).show();
        } else if (type.equals("macro-started")) {
            this.anyMacroRunning = true;
            Macro macro = this.getMacroById(data);
            if (macro != null)
                macro.setRunning(true);
        } else if (type.equals("macro-stopped") || type.equals("macro-ended")) {
            this.anyMacroRunning = false;
            Macro macro = this.getMacroById(data);
            if (macro != null)
                macro.setRunning(false);
        } else if (type.equals("macro-already-running")) {
            this.anyMacroRunning = true;
            Macro macro = this.getMacroById(data);
            if (macro != null)
                macro.setRunning(true);
        } else if (type.equals("update-macro-list")) {
            this.macroList.clear();
            try {
                JSONObject macros = new JSONObject(data);
                JSONArray macrosArray = macros.getJSONArray("macro_list");
                this.makeMacroList(macrosArray);
            } catch (Exception e) {
                Log.e("MacrosActivity", "Error: " + e.getMessage());
                Toast.makeText(this, "Error: " + e.getMessage(), Toast.LENGTH_LONG).show();
            }
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
            }
        };
        bindService(new Intent(this, SocketService.class), this.serviceConnection, Service.BIND_AUTO_CREATE);
    }

    private final Runnable onDisconnect = () -> {
        this.socketService.removeOnDisconnectCallback(this.onDisconnect);
        this.unbindService();
        this.closeSocket();
        finish();
    };

    private void closeSocket() {
        if (this.isBound) {
            try {
                this.socketService.disconnect();
            } catch (Exception e) {
                Log.e("Socket service error", e.getMessage());
            }
        }
    }

    private void unbindService() {
        if (this.isBound) {
            socketService.removeCallback(receiveMessage);
            unbindService(this.serviceConnection);
            this.isBound = false;
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        this.socketService.removeOnDisconnectCallback(onDisconnect);
        this.closeSocket();
        this.unbindService();
    }
}