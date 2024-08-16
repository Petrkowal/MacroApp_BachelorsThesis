package com.kra0633.macroclient;

import androidx.annotation.NonNull;
import androidx.annotation.Nullable;
import androidx.recyclerview.widget.ItemTouchHelper;
import androidx.recyclerview.widget.RecyclerView;
import org.jetbrains.annotations.NotNull;

public class RecyclerRowMoveCallback extends ItemTouchHelper.Callback {


    private final RecyclerViewRowTouchHelperContract contract;
    private boolean longPressEnabled = false;

    public boolean getLongPressEnabled() {
        return longPressEnabled;
    }

    public void setLongPressEnabled(boolean longPressEnabled) {
        this.longPressEnabled = longPressEnabled;
    }

    public RecyclerRowMoveCallback(RecyclerViewRowTouchHelperContract contract) {
        this.contract = contract;
    }

    @Override
    public boolean isLongPressDragEnabled() {
        return longPressEnabled;
    }

    @Override
    public boolean isItemViewSwipeEnabled() {
        return false;
    }

    @Override
    public int getMovementFlags(@NonNull @NotNull RecyclerView recyclerView, @NonNull @NotNull RecyclerView.ViewHolder viewHolder) {
        int dragFlag = ItemTouchHelper.UP | ItemTouchHelper.DOWN;
        return makeMovementFlags(dragFlag, 0);
    }

    @Override
    public boolean onMove(@NonNull @NotNull RecyclerView recyclerView, @NonNull @NotNull RecyclerView.ViewHolder viewHolder, @NonNull @NotNull RecyclerView.ViewHolder target) {
        contract.onRowMoved(viewHolder.getAdapterPosition(), target.getAdapterPosition());
        return true;
    }

    @Override
    public void onSelectedChanged(@Nullable @org.jetbrains.annotations.Nullable RecyclerView.ViewHolder viewHolder, int actionState) {
        if (actionState != ItemTouchHelper.ACTION_STATE_IDLE) {
            if (viewHolder instanceof CustomMacroViewHolder){
                CustomMacroViewHolder macroViewHolder = (CustomMacroViewHolder) viewHolder;
                contract.onRowSelected(macroViewHolder);
            }
        }
        super.onSelectedChanged(viewHolder, actionState);
    }

    @Override
    public void clearView(@NonNull @NotNull RecyclerView recyclerView, @NonNull @NotNull RecyclerView.ViewHolder viewHolder) {
        super.clearView(recyclerView, viewHolder);
        if (viewHolder instanceof CustomMacroViewHolder){
            CustomMacroViewHolder macroViewHolder = (CustomMacroViewHolder) viewHolder;
            contract.onRowClear(macroViewHolder);
        }
    }

    @Override
    public void onSwiped(@NonNull @NotNull RecyclerView.ViewHolder viewHolder, int direction) {

    }

    public interface RecyclerViewRowTouchHelperContract {
        void onRowMoved(int fromPosition, int toPosition);
        void onRowSelected(RecyclerView.ViewHolder viewHolder);
        void onRowClear(RecyclerView.ViewHolder viewHolder);
    }
}
