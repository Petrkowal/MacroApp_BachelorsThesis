package com.kra0633.macroclient;

import android.util.Log;
import android.view.View;
import android.widget.ImageButton;
import android.widget.TextView;
import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;
import org.jetbrains.annotations.NotNull;

public class CustomMacroViewHolder extends RecyclerView.ViewHolder {

    private final TextView nameTextView;
    private final TextView descTextView;
    private ImageButton playButton;
    private Macro macro;

    public CustomMacroViewHolder(@NonNull @NotNull View itemView) {
        super(itemView);
        nameTextView = itemView.findViewById(R.id.textViewMacroName);
        descTextView = itemView.findViewById(R.id.textViewMacroDescription);
        playButton = itemView.findViewById(R.id.imageBtnMacroPlay);

    }

    public void setData(@NonNull @NotNull Macro macro){
        this.macro = macro;
        this.macro.setOnStateChange(onMacroStateChange);
        nameTextView.setText(macro.getName());
        descTextView.setText(macro.getDescription());
        descTextView.setMaxLines(5);
        playButton.setOnClickListener(v -> {
            Log.d("CustomMacroViewHolder", "Play button clicked");
            macro.onClick();
        });
    }

    public Runnable onMacroStateChange = () -> {
        if (macro.isRunning()) {
            setPauseButton();
        } else {
            setPlayButton();
        }
    };

    private void setPlayButton() {
        playButton.setImageResource(android.R.drawable.ic_media_play);
    }

    private void setPauseButton() {
        playButton.setImageResource(android.R.drawable.ic_media_pause);
    }

}