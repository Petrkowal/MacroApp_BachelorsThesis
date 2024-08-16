package com.kra0633.macroclient;

import android.content.Context;
import android.content.SharedPreferences;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import androidx.annotation.NonNull;
import androidx.core.content.ContextCompat;
import androidx.recyclerview.widget.RecyclerView;
import org.jetbrains.annotations.NotNull;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;


public class CustomMacroAdapter extends RecyclerView.Adapter<CustomMacroViewHolder> implements RecyclerRowMoveCallback.RecyclerViewRowTouchHelperContract {

    private List<Macro> itemList;
    private List<Macro> origItemList;
    private Context context;
    private SharedPreferences sharedPref;

    public CustomMacroAdapter(Context context, List<Macro> list) {
        this.context = context;
        this.itemList = list;
        this.origItemList = new ArrayList<>(list);
        this.sharedPref = context.getSharedPreferences(context.getString(R.string.shared_preferences), Context.MODE_PRIVATE);
    }

    public List<Macro> getItemList() {
        return itemList;
    }

    public void revert() {
        itemList.clear();
        itemList.addAll(origItemList);
        notifyDataSetChanged();
    }

    public void save() {
        origItemList.clear();
        origItemList.addAll(itemList);
        for (int i = 0; i < itemList.size(); i++) {
            itemList.get(i).setPosition(i);
        }
    }

    @NonNull
    @NotNull
    @Override
    public CustomMacroViewHolder onCreateViewHolder(@NonNull @NotNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.macro_item, parent, false);
        return new CustomMacroViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull @NotNull CustomMacroViewHolder holder, int position) {
        Macro macro = itemList.get(position);
        holder.setData(macro);
    }

    @Override
    public int getItemCount() {
        return itemList.size();
    }

    @Override
    public void onRowMoved(int fromPosition, int toPosition) {
        if (fromPosition < toPosition) {
            for (int i = fromPosition; i < toPosition; i++) {
                Collections.swap(itemList, i, i + 1);
            }
        } else {
            for (int i = fromPosition; i > toPosition; i--) {
                Collections.swap(itemList, i, i - 1);
            }
        }
        notifyItemMoved(fromPosition, toPosition);
    }

    @Override
    public void onRowSelected(RecyclerView.ViewHolder viewHolder) {
        int nightModeFlags = context.getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_NIGHT_MASK;
        if (sharedPref.getBoolean("black_and_white", false)) {

            if (nightModeFlags == android.content.res.Configuration.UI_MODE_NIGHT_YES) {
                int color = ContextCompat.getColor(context, R.color.white);
                viewHolder.itemView.setBackgroundColor(color);
            } else {
                int color = ContextCompat.getColor(context, R.color.black);
                viewHolder.itemView.setBackgroundColor(color);
            }

        }
        else{
            int color;
            if (nightModeFlags == android.content.res.Configuration.UI_MODE_NIGHT_YES) {
                color = ContextCompat.getColor(context, R.color.drag_dark);
            }
            else{
                color = ContextCompat.getColor(context, R.color.drag);

            }
            viewHolder.itemView.setBackgroundColor(color);

        }
    }

    @Override
    public void onRowClear(RecyclerView.ViewHolder viewHolder) {
        viewHolder.itemView.setBackgroundColor(0);
    }
}
