import sys
from threading import Thread

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QScrollArea, QVBoxLayout, QLabel, \
    QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt, QRect

from app_qt import MacroSquare
from app_qt import MacroEditor
from macro import Macro


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.macros = []
        self.editors = {}
        self.base_central_widget = None
        self.grid = None
        self.edit_mode = False
        self.editLayoutButton = None
        self.cancelLayoutButton = None
        self.macros_to_delete = []
        self.max_pos = 0
        self.scroll = None
        self.initUI()

    def initUI(self):
        central_widget = QWidget(self)

        self.setCentralWidget(central_widget)

        self.setWindowTitle("Macro manager")

        size = (800, 600)
        self.setGeometry(
            (self.screen().size().width() - size[0]) // 2,
            (self.screen().size().height() - size[1]) // 2,
            *size
        )

        self.setMinimumSize(400, 200)

        vbox = QVBoxLayout(central_widget)
        vbox.setContentsMargins(0, 0, 0, 0)

        hbox_bar = QHBoxLayout()
        hbox_bar_left = QHBoxLayout()
        hbox_bar_right = QHBoxLayout()

        spacer_left = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        hbox_bar_right.addItem(spacer_right)

        hbox_bar_left.setContentsMargins(20, 20, 20, 20)
        hbox_bar_right.setContentsMargins(20, 20, 20, 20)

        vbox.addLayout(hbox_bar, 0)

        title = QLabel("Macro manager")
        title.setMargin(10)
        font = title.font()
        font.setPointSize(font.pointSize() * 2)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hbox_bar.addLayout(hbox_bar_left, 0)
        hbox_bar.addWidget(title, 0)
        hbox_bar.addLayout(hbox_bar_right, 0)

        start_server_button = QPushButton("Reload macros")
        start_server_button.setObjectName("startServerBtn")
        start_server_button.setCursor(Qt.CursorShape.PointingHandCursor)
        start_server_button.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        start_server_button.clicked.connect(self.refresh_layout)
        hbox_bar_right.addWidget(start_server_button)

        self.editLayoutButton = QPushButton("Edit layout")
        self.editLayoutButton.setObjectName("editLayoutBtn")
        self.editLayoutButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.editLayoutButton.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.editLayoutButton.clicked.connect(self.set_edit_mode)
        hbox_bar_left.addWidget(self.editLayoutButton)

        self.cancelLayoutButton = QPushButton("Cancel")
        self.cancelLayoutButton.setObjectName("cancelLayoutBtn")
        self.cancelLayoutButton.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancelLayoutButton.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.cancelLayoutButton.clicked.connect(self.end_edit_mode)
        hbox_bar_left.addWidget(self.cancelLayoutButton)

        new_macro_btn = QPushButton("New macro")
        new_macro_btn.setObjectName("newMacroBtn")
        new_macro_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_macro_btn.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        new_macro_btn.clicked.connect(self.new_macro)
        hbox_bar_left.addWidget(new_macro_btn)

        hbox_bar_left.addItem(spacer_left)

        self.cancelLayoutButton.hide()

        self.grid = QGridLayout()

        self.load_macros()

        grid_widget = QWidget()
        grid_widget.setLayout(self.grid)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(grid_widget)

        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        vbox.addWidget(self.scroll, 1)

    def load_macros(self):
        self.macros = []
        loaded_macros = Macro.get_all_macros_info_objects()
        loaded_macros.sort(key=lambda x: x.get_position())
        self.max_pos = len(loaded_macros)
        for macro in loaded_macros:
            ms = MacroSquare(macro.get_name(), macro.get_description(), macro)
            ms.set_fn_on_edit(self.open_editor)
            ms.set_fn_on_execute(self.run_macro)
            ms.set_fn_on_delete(self.delete_macro)
            self.macros.append(ms)
            self.grid.addWidget(self.macros[-1])

    def delete_macro(self, macro: MacroSquare):
        print(f"Deleting macro {macro}")
        self.macros_to_delete.append(macro.macro)
        self.macros.remove(macro)
        self.grid.removeWidget(macro)
        macro.deleteLater()
        self.resizeEvent(None)

    def run_macro(self, macro: MacroSquare):
        if macro.macro:
            def stop():
                macro.macro.stop()
                thread.join()
                macro.macro_running = False
                if self.edit_mode:
                    macro.set_edit_mode()
                else:
                    macro.set_normal_mode()
            def run(ms):
                ms.macro.execute()
                ms.set_play_btn()

            macro.on_stop = stop
            macro.set_stop_btn()
            thread = Thread(target=lambda: run(macro), daemon=True)
            thread.start()

            return True
        print("Error, running macro - is None")
        return False

    def resizeEvent(self, event):
        macro_width = int(MacroSquare.WIDTH * 1.1)
        grid_width = self.width() // macro_width
        self.grid.layout().setColumnStretch(0, grid_width)
        for i, macro in enumerate(self.macros):
            row = i // grid_width
            col = i % grid_width
            self.grid.layout().addWidget(macro, row, col)

    def set_edit_mode(self):
        if self.edit_mode:
            self.end_edit_mode(True)
            self.editLayoutButton.setText("Edit layout")
            self.cancelLayoutButton.hide()
            return
        self.editLayoutButton.setText("Save")
        self.cancelLayoutButton.show()
        self.edit_mode = True
        for macro in self.macros:
            macro.set_edit_mode()

    def end_edit_mode(self, save: bool = False):
        self.editLayoutButton.setText("Edit layout")
        self.cancelLayoutButton.hide()
        self.edit_mode = False
        for macro in self.macros:
            macro.set_normal_mode()

        if save:
            for macro in self.macros_to_delete:
                macro.delete()
            for i, ms in enumerate(self.macros):
                ms.macro.position = i
                ms.macro.save("macros", overwrite=True, only_info=True)
        else:
            self.macros.sort(key=lambda x: x.macro.position)
            self.load_macros()
            self.refill_grid()

    def new_macro(self):
        macro = Macro("New macro", "New macro description", [], 1, self.max_pos, True)
        ms = MacroSquare(macro.get_name(), macro.get_description(), macro)
        ms.set_fn_on_edit(self.open_editor)
        ms.set_fn_on_execute(self.run_macro)
        ms.set_fn_on_delete(self.delete_macro)
        if self.edit_mode:
            ms.set_edit_mode()
        self.macros.append(ms)
        self.grid.addWidget(ms)
        self.max_pos += 1

        self.open_editor(ms)
        self.update()
        self.resizeEvent(None)

    def open_editor(self, macro: MacroSquare):
        if macro in self.editors:
            editor = self.editors[macro]
            editor.show()
            return

        macro.macro.load_commands()
        editor = MacroEditor(macro.macro, self.close_editor)
        editor.setPalette(self.palette())
        self.editors[macro] = editor
        editor.show()

    def __update_layout(self):
        self.load_macros()
        self.refill_grid()

    def close_editor(self, editor: MacroEditor, save):
        if save == MacroEditor.SAVE:

            ms_macro = None
            for ms in self.macros:
                if ms.macro == editor.orig_macro:
                    ms_macro = ms.macro
                    ms.macro = editor.macro
                    ms.reload_data()
                    break

            if editor.orig_macro.get_name() != editor.macro.get_name():  # New != old
                is_unique = False
                while not is_unique:
                    for macro in Macro.get_all_macros_info_objects():
                        if macro.get_name() == editor.macro.get_name():  # Matches a different existing macro
                            editor.macro.set_name(editor.macro.get_name() + "_1")
                            break
                    else:
                        is_unique = True

            editor.orig_macro.delete()
            editor.macro.save(overwrite=True)

            self.load_macros()
            self.refill_grid()
        elif save == MacroEditor.SAVE_AS_NEW:
            is_unique = False
            while not is_unique:
                for macro in Macro.get_all_macros_info_objects():  # Make sure
                    if macro.get_name() == editor.macro.get_name():
                        editor.macro.set_name(editor.macro.get_name() + "_1")
                        break
                else:
                    is_unique = True

            editor.macro.position = self.max_pos
            self.max_pos += 1
            ms = MacroSquare(editor.macro.get_name(), editor.macro.get_description(), editor.macro)
            ms.set_fn_on_edit(self.open_editor)
            ms.set_fn_on_execute(self.run_macro)
            ms.set_fn_on_delete(self.delete_macro)
            ms.reload_data()
            self.macros.append(ms)
            self.grid.addWidget(ms)

            editor.macro.save(overwrite=True)
            self.load_macros()
            self.refill_grid()
        else:
            pass

        for macro, ed in self.editors.items():
            if ed == editor:
                self.editors.pop(macro)
                break
        editor.close()

    def dragEnterEvent(self, event):
        event.accept()

    def dropEvent(self, event):
        pos = event.position()
        pos = pos.toPoint()
        pos = self.scroll.mapFromGlobal(self.mapToGlobal(pos))
        pos.setY(pos.y() + self.scroll.verticalScrollBar().value())
        for ms in self.macros:
            rect = ms.geometry()

            if rect.contains(pos):
                idx1 = self.macros.index(ms)
                idx2 = self.macros.index(event.source())
                self.macros[idx1], self.macros[idx2] = self.macros[idx2], self.macros[idx1]
                break
        self.refill_grid()
        event.accept()

    def refill_grid(self):
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)
        for ms in self.macros:
            self.grid.addWidget(ms)
            if self.edit_mode:
                ms.set_edit_mode()
        self.update()
        self.resizeEvent(None)

    def closeEvent(self, event):
        for macro, editor in self.editors.items():
            editor.close()
        event.accept()

    def refresh_layout(self):  # btn click
        self.__update_layout()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    with open("app_qt/css/style.css", "r") as f:
        app.setStyleSheet(f.read())

    palette = app.palette()

    palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor("black"))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.ColorRole.BrightText, QColor("red"))
    palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("black"))

    app.setPalette(palette)
    window = MainWindow()
    window.setPalette(palette)
    window.show()
    app_exec_val = app.exec()
    sys.exit(app_exec_val)
