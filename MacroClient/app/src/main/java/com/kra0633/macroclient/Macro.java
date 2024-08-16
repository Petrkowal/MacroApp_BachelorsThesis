package com.kra0633.macroclient;

import java.util.function.Consumer;

public class Macro {
    private final String name;
    private final String description;
    private final String id;
    private boolean running;

    public int getPosition() {
        return position;
    }

    public void setPosition(int position) {
        this.position = position;
    }

    private int position;

    private Consumer<Macro> executeCallback = null;
    private Runnable stopCallback = null;
    private Runnable onStateChange = null;


    public Macro(String name, String description, String id, int position) {
        this.name = name;
        this.description = description;
        this.id = id;
        this.position = position;
        this.running = false;
    }

    public String getName() {
        return name;
    }

    public String getId() {
        return id;
    }

    public String getDescription() {
        return description;
    }

    private void start() {
        if (executeCallback != null) {
            executeCallback.accept(this);
        }
    }

    private void stop() {
        if (stopCallback != null) {
            stopCallback.run();
        }
    }

    public boolean isRunning () {
        return running;
    }

    public void setExecuteCallback(Consumer<Macro> callback) {
        this.executeCallback = callback;
    }

    public void setStopCallback(Runnable callback) {
        this.stopCallback = callback;
    }

    public void setRunning(boolean running) {
        this.running = running;
        if (this.onStateChange != null)
            this.onStateChange.run();
    }

    public void setOnStateChange(Runnable onStateChange) {
        this.onStateChange = onStateChange;
    }

    public void onClick() {
        if (running) {
            stop();
        } else {
            start();
        }
    }
    
    
}
