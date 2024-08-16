import threading

from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
import pynput

from macro import Macro, InputRecorder, InputRecorderOptions
from macro.commands import *


class MacroEditor(QWidget):
    KEY_PRESS_TEXT = "Key press"
    KEY_RELEASE_TEXT = "Key release"
    MOUSE_PRESS_TEXT = "Mouse press"
    MOUSE_RELEASE_TEXT = "Mouse release"
    MOUSE_MOVE_TEXT = "Mouse move"
    MOUSE_SCROLL_TEXT = "Mouse scroll"
    DELAY_TEXT = "Delay"
    TEXT_INPUT_TEXT = "Text input"
    CANCEL = 0
    SAVE = 1
    SAVE_AS_NEW = 2

    def __init__(self, macro, exit_fn=None):
        super().__init__()
        self.orig_macro = macro
        self.macro = Macro(macro.name, macro.description, macro.commands, macro.repeat, macro.position, macro.timing)
        self.exit_fn = exit_fn
        self.sequence_list = None
        self.name_input = None
        self.desc_input = None
        self.repeat_input = None
        self.command_options_vbox = None
        self.recorder = None
        self.time_input = None
        self.time_label = None
        self.record_keyboard = None
        self.record_mouse_clicks = None
        self.record_mouse_moves = None
        self.record_mouse_scroll = None
        self.mouse_freq_label = None
        self.mouse_freq_input = None
        self.key_input = None
        self.btn_input = None
        self.recorder_running = False
        self.macro_running = False
        self.record_btn = None
        self.run_stop_btn = None
        self.save_state = self.CANCEL
        self.initRecorder()
        self.initUI()

    def initUI(self):
        self.setWindowTitle(f"Macro Editor - {self.macro.name}")
        size = (800, 600)
        self.setGeometry(
            (self.screen().size().width() - size[0]) // 2,
            (self.screen().size().height() - size[1]) // 2,
            *size
        )
        vbox = QVBoxLayout()
        self.setLayout(vbox)

        bar = QHBoxLayout()
        left_bar = QHBoxLayout()
        right_bar = QHBoxLayout()

        spacer_left = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        spacer_right = QSpacerItem(0, 0, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("saveBtn")
        save_btn.clicked.connect(self.save)
        left_bar.addWidget(save_btn)

        save_as_btn = QPushButton("Save as new macro")
        save_as_btn.setObjectName("saveAsBtn")
        save_as_btn.clicked.connect(self.save_as)
        left_bar.addWidget(save_as_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("exitBtn")
        cancel_btn.clicked.connect(self.cancel)
        left_bar.addWidget(cancel_btn)

        left_bar.addItem(spacer_left)
        right_bar.addItem(spacer_right)

        self.run_stop_btn = QPushButton("Run macro")
        self.run_stop_btn.setObjectName("playBtn")
        self.run_stop_btn.clicked.connect(self.exec_macro)
        right_bar.addWidget(self.run_stop_btn)

        vbox.addLayout(bar, 0)

        title = QLabel(f"Macro Editor - {self.macro.name}")
        title.setObjectName("titleLabel")
        font = title.font()
        font.setPointSize(font.pointSize() * 2)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        bar.addLayout(left_bar, 1)
        bar.addWidget(title, 0)
        bar.addLayout(right_bar, 1)

        hbox_main = QHBoxLayout()
        vbox.addLayout(hbox_main, 1)

        vbox1 = QVBoxLayout()
        vbox2 = QVBoxLayout()
        vbox3 = QVBoxLayout()
        vbox4 = QVBoxLayout()
        hbox_main.addLayout(vbox1, 1)
        hbox_main.addLayout(vbox2, 2)
        hbox_main.addLayout(vbox3, 1)
        hbox_main.addLayout(vbox4, 2)

        self.init_vbox1(vbox1)
        self.init_vbox2(vbox2)
        self.init_vbox3(vbox3)
        self.init_vbox4(vbox4)

        hbox_bottom_bar = QHBoxLayout()
        vbox.addLayout(hbox_bottom_bar, 0)

        hbox_bottom_bar.setAlignment(Qt.AlignmentFlag.AlignRight)
        hbox_bottom_bar.setSpacing(10)

    def init_vbox1(self, vbox):
        commands_label = QLabel("Commands")
        commands_label.setObjectName("commandsLabel")
        commands_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        commands_label.setStyleSheet("margin-bottom: 10px;")
        vbox.addWidget(commands_label, 0)

        commands_list = QListWidget()
        commands_list.setObjectName("commandsList")
        commands_list.itemClicked.connect(self.on_command_click)

        vbox.addWidget(commands_list, 1)

        key_command = QListWidgetItem(self.KEY_PRESS_TEXT)
        commands_list.addItem(key_command)

        key_release = QListWidgetItem(self.KEY_RELEASE_TEXT)
        commands_list.addItem(key_release)

        mouse_click = QListWidgetItem(self.MOUSE_PRESS_TEXT)
        commands_list.addItem(mouse_click)

        mouse_release = QListWidgetItem(self.MOUSE_RELEASE_TEXT)
        commands_list.addItem(mouse_release)

        mouse_move = QListWidgetItem(self.MOUSE_MOVE_TEXT)
        commands_list.addItem(mouse_move)

        mouse_scroll = QListWidgetItem(self.MOUSE_SCROLL_TEXT)
        commands_list.addItem(mouse_scroll)

        delay = QListWidgetItem(self.DELAY_TEXT)
        commands_list.addItem(delay)

        text_input = QListWidgetItem(self.TEXT_INPUT_TEXT)
        commands_list.addItem(text_input)

    def init_vbox2(self, vbox):
        sequence_label = QLabel("Program sequence")
        sequence_label.setObjectName("sequenceLabel")
        sequence_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sequence_label.setStyleSheet("margin-bottom: 10px;")
        vbox.addWidget(sequence_label, 0)

        self.sequence_list = QListWidget()
        self.sequence_list.setObjectName("sequenceList")
        self.sequence_list.itemClicked.connect(self.on_seq_command_click)
        self.sequence_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        for command in self.macro.commands:
            list_item = QListWidgetItem()
            list_item.setData(100, command)
            list_item.setText(command.name)
            self.sequence_list.addItem(list_item)

        vbox.addWidget(self.sequence_list, 1)

    def init_vbox3(self, vbox):
        self.init_recorder_box(vbox)

        options_label = QLabel("Command Options")
        options_label.setObjectName("optionsLabel")
        options_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        options_label.setStyleSheet("margin-bottom: 20px;")
        vbox.addWidget(options_label, 0)

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        vbox.addItem(spacer)

        self.command_options_vbox = QVBoxLayout()
        vbox.addLayout(self.command_options_vbox, 1)

    def init_vbox4(self, vbox):
        macro_options_label = QLabel("Macro Options")
        macro_options_label.setObjectName("macroOptionsLabel")
        macro_options_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        macro_options_label.setStyleSheet("margin-bottom: 20px;")
        vbox.addWidget(macro_options_label, 0)

        # name
        name_label = QLabel("Name")
        name_label.setObjectName("nameLabel")
        vbox.addWidget(name_label, 0)

        self.name_input = QLineEdit()
        self.name_input.setObjectName("nameInput")
        self.name_input.setText(self.macro.name)
        self.name_input.textChanged.connect(lambda text: self.macro.set_name(text))

        palette = self.name_input.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))
        # palette text color
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))

        self.name_input.setPalette(palette)
        self.name_input.setStyleSheet("border: 1px solid gray;")
        vbox.addWidget(self.name_input, 1)

        # description
        desc_label = QLabel("Description")
        desc_label.setObjectName("descLabel")
        vbox.addWidget(desc_label, 0)

        self.desc_input = QTextEdit()
        self.desc_input.setObjectName("descInput")
        self.desc_input.setText(self.macro.description)
        self.desc_input.textChanged.connect(
            lambda: self.macro.set_description(description=self.desc_input.toPlainText()))
        vbox.addWidget(self.desc_input, 1)

        # repeat
        repeat_label = QLabel("Repeat")
        repeat_label.setObjectName("repeatLabel")
        vbox.addWidget(repeat_label, 0)

        self.repeat_input = QSpinBox()
        self.repeat_input.setObjectName("repeatInput")
        self.repeat_input.setMinimum(1)
        self.repeat_input.setMaximum(999)
        self.repeat_input.setSingleStep(1)
        self.repeat_input.setSuffix(" times")
        self.repeat_input.valueChanged.connect(lambda value: self.macro.set_repeat(value))
        self.repeat_input.setValue(self.macro.repeat)

        self.repeat_input.setPalette(palette)
        vbox.addWidget(self.repeat_input, 1)

        # commands timed
        time_label = QLabel("Commands timing")
        time_label.setObjectName("timeLabel")
        vbox.addWidget(time_label, 0)

        # some toggle
        time_toggle = QCheckBox()
        time_toggle.setObjectName("timeToggle")
        time_toggle.setText("Use timing")
        if self.macro.timing:
            time_toggle.setChecked(True)
        time_toggle.stateChanged.connect(lambda state: self.set_timing(state == 2))
        vbox.addWidget(time_toggle, 1)



    def init_recorder_box(self, vbox):
        recorder_label = QLabel("Recorder")
        recorder_label.setObjectName("recorderLabel")
        recorder_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        recorder_label.setStyleSheet("margin-bottom: 20px;")
        vbox.addWidget(recorder_label, 0)

        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()
        vbox.addLayout(hbox1, 1)
        vbox.addLayout(hbox2, 1)

        # options for recording
        self.record_keyboard = QCheckBox()
        self.record_keyboard.setObjectName("recordKeyboard")
        self.record_keyboard.setText("Keyboard")
        self.record_keyboard.setChecked(True)
        self.record_keyboard.stateChanged.connect(lambda state: self.update_recording_options(keyboard=(state == 2)))
        hbox1.addWidget(self.record_keyboard, 1)

        self.record_mouse_clicks = QCheckBox()
        self.record_mouse_clicks.setObjectName("recordMouse")
        self.record_mouse_clicks.setText("Mouse clicks")
        self.record_mouse_clicks.setChecked(True)
        self.record_mouse_clicks.stateChanged.connect(lambda state: self.update_recording_options(click=(state == 2)))
        hbox1.addWidget(self.record_mouse_clicks, 1)

        self.record_mouse_moves = QCheckBox()
        self.record_mouse_moves.setObjectName("recordMouseMoves")
        self.record_mouse_moves.setText("Mouse moves")
        self.record_mouse_moves.setChecked(True)
        self.record_mouse_moves.stateChanged.connect(lambda state: self.update_recording_options(move=(state == 2)))
        hbox2.addWidget(self.record_mouse_moves, 1)

        self.record_mouse_scroll = QCheckBox()
        self.record_mouse_scroll.setObjectName("recordMouseScroll")
        self.record_mouse_scroll.setText("Mouse scroll")
        self.record_mouse_scroll.setChecked(True)
        self.record_mouse_scroll.stateChanged.connect(lambda state: self.update_recording_options(scroll=(state == 2)))
        hbox2.addWidget(self.record_mouse_scroll, 1)

        # input for mouse freq
        self.mouse_freq_label = QLabel("Mouse capture rate (once every x seconds): ")
        self.mouse_freq_label.setObjectName("mouseFreqLabel")
        vbox.addWidget(self.mouse_freq_label, 0)

        self.mouse_freq_input = QDoubleSpinBox()
        self.mouse_freq_input.setObjectName("mouseFreqInput")
        self.mouse_freq_input.setMinimum(0.001)
        self.mouse_freq_input.setMaximum(100)
        self.mouse_freq_input.setSingleStep(0.01)
        self.mouse_freq_input.setDecimals(3)
        self.mouse_freq_input.valueChanged.connect(lambda value: self.update_recording_options(mouse_freq=value))
        self.mouse_freq_input.setValue(0.05)
        palette = self.mouse_freq_input.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))

        self.mouse_freq_input.setPalette(palette)
        vbox.addWidget(self.mouse_freq_input, 1)

        self.record_btn = QPushButton("Record")
        self.record_btn.setObjectName("recordBtn")
        self.record_btn.setStyleSheet("margin-bottom: 30px;")
        self.record_btn.clicked.connect(self.toggle_recording)
        vbox.addWidget(self.record_btn, 1)

    def initRecorder(self):
        options = InputRecorderOptions()
        self.recorder = InputRecorder(options)
        self.recorder.add_callback(self.recorder_callback)

    def get_key_from_recorder(self):

        def get_key(event):
            if isinstance(event.key, pynput.keyboard.KeyCode):
                key_name = event.key.char if event.key.char else event.key.vk
                key_name = str(key_name)
                self.key_input.setText(key_name)
            elif isinstance(event.key, pynput.keyboard.Key):
                self.key_input.setText(event.key.name)
            else:
                return
            recorder.stop(True)

            selected = self.sequence_list.selectedItems()[0]
            command = selected.data(100)
            command.update(key=event.key)
            selected.setText(command.name)

        recorder = InputRecorder(InputRecorderOptions(record_keyboard=True, record_time=False, record_mouse_click=False,
                                                      record_mouse_move=False, record_mouse_scroll=False, keyboard_callbacks=[get_key]))
        recorder.start()

    def get_button_from_recorder(self):
        def get_btn(event):
            self.btn_input.setText(event.button.name)
            recorder.stop(True)

            selected = self.sequence_list.selectedItems()[0]
            command = selected.data(100)
            command.update(button=event.button)
            selected.setText(command.name)

        recorder = InputRecorder(InputRecorderOptions(record_keyboard=False, record_time=False, record_mouse_click=True,
                                                      record_mouse_move=False, record_mouse_scroll=False, mouse_callbacks=[get_btn]))
        recorder.start()

    def update_recording_options(self, keyboard=None, click=None, move=None, scroll=None, mouse_freq=None):
        if keyboard is not None:
            self.recorder.options.record_keyboard = keyboard
        if click is not None:
            self.recorder.options.record_mouse_click = click
        if move is not None:
            self.recorder.options.record_mouse_move = move
        if scroll is not None:
            self.recorder.options.record_mouse_scroll = scroll
        if mouse_freq is not None:
            self.recorder.options.move_timeout = mouse_freq

    def enable_disable_recording_checkboxes(self):
        if self.recorder_running:
            self.record_keyboard.setEnabled(False)
            self.record_mouse_clicks.setEnabled(False)
            self.record_mouse_moves.setEnabled(False)
            self.record_mouse_scroll.setEnabled(False)
            self.mouse_freq_input.setEnabled(False)
        else:
            self.record_keyboard.setEnabled(True)
            self.record_mouse_clicks.setEnabled(True)
            self.record_mouse_moves.setEnabled(True)
            self.record_mouse_scroll.setEnabled(True)
            self.mouse_freq_input.setEnabled(True)

    def toggle_recording(self):
        if self.recorder_running:
            self.stop_recording(True)
        else:
            self.start_recording()

    def start_recording(self):
        self.setFocus()
        self.recorder_running = True
        self.record_btn.setText(f"Stop ({self.recorder.key_to_stop.name})")
        self.recorder.on_stop_callback = self.stop_recording
        self.enable_disable_recording_checkboxes()
        if self.macro.timing:
            if self.sequence_list.selectedItems():
                selected_item = self.sequence_list.selectedItems()[0]
                self.recorder.options.time_offset = selected_item.data(100).time

        self.recorder.start()

    def stop_recording(self, do_stop=False):
        self.recorder_running = False
        self.record_btn.setText("Record")
        self.enable_disable_recording_checkboxes()
        if do_stop:
            self.recorder.stop()
        else:
            self.recorder.stop(no_join=True)

    def recorder_callback(self, command):
        try:
            list_item = QListWidgetItem()
            list_item.setData(100, command)
            list_item.setText(command.name)

            self.sequence_list.scrollToBottom()
            if self.sequence_list.selectedItems():
                selected_item = self.sequence_list.selectedItems()[0]
                self.sequence_list.insertItem(self.sequence_list.row(selected_item) + 1, list_item)
                self.sequence_list.scrollToItem(list_item)
                inserted_item = self.sequence_list.item(self.sequence_list.row(selected_item) + 1)
            else:
                self.sequence_list.addItem(list_item)
                self.sequence_list.scrollToBottom()
                inserted_item = self.sequence_list.item(self.sequence_list.count() - 1)
            inserted_item.setSelected(True)
        except Exception as e:
            print(f"Error in recorder callback: {e}")

    def remove_widgets(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            sublayout = item.layout()
            if sublayout:
                self.remove_widgets(sublayout)
            if widget:
                widget.deleteLater()

    def on_seq_command_click(self, item):
        command = item.data(100)
        self.remove_widgets(self.command_options_vbox)
        palette = self.name_input.palette()
        palette.setColor(QPalette.ColorRole.Base, QColor(25, 25, 25))

        # add new options
        if isinstance(command, KeyCommand):
            key_label = QLabel("Key (click and press to select)")
            key_label.setObjectName("keyLabel")
            self.command_options_vbox.addWidget(key_label, 0)

            # Button to select key
            self.key_input = QPushButton("Select key")
            self.key_input.setObjectName("keyInput")
            self.key_input.setPalette(palette)
            self.key_input.setStyleSheet("border: 1px solid gray;")
            self.key_input.clicked.connect(self.get_key_from_recorder)
            self.command_options_vbox.addWidget(self.key_input, 1)

            press_toggle = QCheckBox()
            press_toggle.setObjectName("pressToggle")
            press_toggle.setText("Press")
            press_toggle.setChecked(command.press)
            press_toggle.stateChanged.connect(lambda state: self.update_key_command_toggle(state, item))
            self.command_options_vbox.addWidget(press_toggle, 1)

        elif isinstance(command, MouseClick):
            button_label = QLabel("Button (click and press to select)")
            button_label.setObjectName("buttonLabel")
            self.command_options_vbox.addWidget(button_label, 0)

            self.btn_input = QPushButton("Select button")
            self.btn_input.setObjectName("buttonInput")
            self.btn_input.setPalette(palette)
            self.btn_input.setStyleSheet("border: 1px solid gray;")
            self.btn_input.clicked.connect(self.get_button_from_recorder)

            self.command_options_vbox.addWidget(self.btn_input, 1)

            xbox = QHBoxLayout()

            x_label = QLabel("X: ")
            x_label.setObjectName("xLabel")
            xbox.addWidget(x_label, 0)

            x_input = QSpinBox()
            x_input.setObjectName("xInput")
            x_input.setMinimum(-999999)
            x_input.setMaximum(999999)
            x_input.setValue(command.x)
            x_input.setSingleStep(1)
            x_input.setPalette(palette)
            x_input.valueChanged.connect(lambda value: self.update_click_position(value, y_input.value(), item))

            xbox.addWidget(x_input, 1)

            self.command_options_vbox.addLayout(xbox)

            ybox = QHBoxLayout()
            y_label = QLabel("Y: ")
            y_label.setObjectName("yLabel")
            ybox.addWidget(y_label, 0)

            y_input = QSpinBox()
            y_input.setObjectName("yInput")
            y_input.setMinimum(-999999)
            y_input.setMaximum(999999)
            y_input.setValue(command.y)
            y_input.setSingleStep(1)
            y_input.setPalette(palette)
            y_input.valueChanged.connect(lambda value: self.update_click_position(x_input.value(), value, item))

            ybox.addWidget(y_input, 1)

            self.command_options_vbox.addLayout(ybox)

            radiobox = QHBoxLayout()

            abs_radio = QRadioButton("Absolute")
            abs_radio.setObjectName("absRadio")
            abs_radio.setChecked(command.absolute)
            radiobox.addWidget(abs_radio, 0)

            rel_radio = QRadioButton("Relative")
            rel_radio.setObjectName("relRadio")
            rel_radio.setChecked(not command.absolute)
            radiobox.addWidget(rel_radio, 1)


            abs_radio.toggled.connect(
                lambda state: self.update_click_absolute(state, item))

            self.command_options_vbox.addLayout(radiobox)

            press_toggle = QCheckBox()
            press_toggle.setObjectName("pressToggle")
            press_toggle.setText("Press")
            press_toggle.setChecked(command.press)
            press_toggle.stateChanged.connect(lambda state: self.update_key_command_toggle(state, item))

            self.command_options_vbox.addWidget(press_toggle, 1)

        elif isinstance(command, MouseMove):
            xbox = QHBoxLayout()

            x_label = QLabel("X: ")
            x_label.setObjectName("xLabel")
            xbox.addWidget(x_label, 0)

            x_input = QSpinBox()
            x_input.setObjectName("xInput")
            x_input.setMinimum(-999999)
            x_input.setMaximum(999999)
            x_input.setValue(command.x)
            x_input.setSingleStep(1)
            x_input.setPalette(palette)
            x_input.valueChanged.connect(lambda value: self.update_move_position(value, y_input.value(), item))

            xbox.addWidget(x_input, 1)

            self.command_options_vbox.addLayout(xbox)

            ybox = QHBoxLayout()
            y_label = QLabel("Y: ")
            y_label.setObjectName("yLabel")
            ybox.addWidget(y_label, 0)

            y_input = QSpinBox()
            y_input.setObjectName("yInput")
            y_input.setMinimum(-999999)
            y_input.setMaximum(999999)
            y_input.setValue(command.y)
            y_input.setSingleStep(1)
            y_input.setPalette(palette)
            y_input.valueChanged.connect(lambda value: self.update_move_position(x_input.value(), value, item))

            ybox.addWidget(y_input, 1)

            self.command_options_vbox.addLayout(ybox)

            radiobox = QHBoxLayout()

            abs_radio = QRadioButton("Absolute")
            abs_radio.setObjectName("absRadio")
            abs_radio.setChecked(command.absolute)
            radiobox.addWidget(abs_radio, 0)

            rel_radio = QRadioButton("Relative")
            rel_radio.setObjectName("relRadio")
            rel_radio.setChecked(not command.absolute)
            radiobox.addWidget(rel_radio, 1)

            abs_radio.toggled.connect(
                lambda state: self.update_move_toggle(state, item))

            self.command_options_vbox.addLayout(radiobox)

        elif isinstance(command, MouseScroll):
            dx_label = QLabel("Horizontal (negative to scroll left)")
            dx_label.setObjectName("dxLabel")
            self.command_options_vbox.addWidget(dx_label, 0)

            dx_input = QSpinBox()
            dx_input.setObjectName("dxInput")
            dx_input.setMinimum(-999999)
            dx_input.setMaximum(999999)
            dx_input.setValue(command.x)
            dx_input.setSingleStep(1)
            dx_input.setPalette(palette)
            dx_input.valueChanged.connect(lambda value: self.update_scroll(value, dy_input.value(), item))

            self.command_options_vbox.addWidget(dx_input, 1)

            dy_label = QLabel("Vertical (negative to scroll down)")
            dy_label.setObjectName("dyLabel")
            self.command_options_vbox.addWidget(dy_label, 0)

            dy_input = QSpinBox()
            dy_input.setObjectName("dyInput")
            dy_input.setMinimum(-999999)
            dy_input.setMaximum(999999)
            dy_input.setValue(command.y)
            dy_input.setSingleStep(1)
            dy_input.setPalette(palette)
            dy_input.valueChanged.connect(lambda value: self.update_scroll(dx_input.value(), value, item))

            self.command_options_vbox.addWidget(dy_input, 1)

        elif isinstance(command, Delay):
            delay_label = QLabel("Delay (seconds)")
            delay_label.setObjectName("delayLabel")
            self.command_options_vbox.addWidget(delay_label, 0)

            delay_input = QDoubleSpinBox()
            delay_input.setObjectName("delayInput")
            delay_input.setMinimum(0)
            delay_input.setMaximum(999999)
            delay_input.setValue(command.delay)
            delay_input.setSingleStep(0.01)
            delay_input.setPalette(palette)
            delay_input.setDecimals(3)
            delay_input.valueChanged.connect(lambda value: self.update_delay(value, item))

            self.command_options_vbox.addWidget(delay_input, 1)
        elif isinstance(command, TextInput):
            text_label = QLabel("Text")
            text_label.setObjectName("textLabel")
            self.command_options_vbox.addWidget(text_label, 0)

            text_input = QLineEdit()
            text_input.setObjectName("textInput")
            text_input.setPalette(palette)
            text_input.setStyleSheet("border: 1px solid gray;")
            text_input.setText(command.text)
            text_input.textChanged.connect(lambda text: self.update_text(text, item))

            self.command_options_vbox.addWidget(text_input, 1)

        self.time_label = QLabel("Time (seconds)")
        self.time_label.setObjectName("timeLabel")
        self.command_options_vbox.addWidget(self.time_label, 0)

        self.time_input = QDoubleSpinBox()
        self.time_input.setObjectName("timeInput")
        self.time_input.setMinimum(0)
        self.time_input.setMaximum(999999)
        self.time_input.setValue(command.time)
        self.time_input.setSingleStep(0.01)
        self.time_input.setPalette(palette)
        self.time_input.setDecimals(3)
        self.time_input.valueChanged.connect(lambda value: self.command_time_update(time=value, item=item))
        self.command_options_vbox.addWidget(self.time_input, 1)

        spacer = QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.command_options_vbox.addItem(spacer)

        hbox = QHBoxLayout()
        self.command_options_vbox.addLayout(hbox)

        move_up_btn = QPushButton("Move up")
        move_up_btn.setObjectName("moveUpBtn")
        move_up_btn.clicked.connect(lambda: self.move_command(item, -1))
        hbox.addWidget(move_up_btn, 0)

        move_down_btn = QPushButton("Move down")
        move_down_btn.setObjectName("moveDownBtn")
        move_down_btn.clicked.connect(lambda: self.move_command(item, 1))
        hbox.addWidget(move_down_btn, 0)

        del_btn = QPushButton("Delete")
        del_btn.setObjectName("delBtn")
        del_btn.clicked.connect(lambda: self.delete_command(item))
        self.command_options_vbox.addWidget(del_btn, 0)

        if self.macro.timing:
            self.show_timing()
        else:
            self.hide_timing()

    def move_command(self, item, amount):
        idx = self.sequence_list.row(item)
        if idx + amount < 0 or idx + amount >= self.sequence_list.count():
            return
        self.sequence_list.takeItem(idx)
        self.sequence_list.insertItem(idx + amount, item)

    def delete_command(self, item):
        idx = self.sequence_list.row(item)
        self.sequence_list.takeItem(self.sequence_list.row(item))
        if self.sequence_list.count() > 0:
            if idx > 0:
                self.sequence_list.item(idx - 1).setSelected(True)
                self.on_seq_command_click(self.sequence_list.item(idx - 1))
            else:
                self.sequence_list.item(0).setSelected(True)
                self.on_seq_command_click(self.sequence_list.item(0))
        else:
            self.remove_widgets(self.command_options_vbox)

    def on_command_click(self, item):
        itext = item.text()
        if itext == self.KEY_PRESS_TEXT:
            command = KeyCommand()
        elif itext == self.KEY_RELEASE_TEXT:
            command = KeyCommand(press=False)
        elif itext == self.MOUSE_PRESS_TEXT:
            command = MouseClick()
        elif itext == self.MOUSE_RELEASE_TEXT:
            command = MouseClick(press=False)
        elif itext == self.MOUSE_MOVE_TEXT:
            command = MouseMove()
        elif itext == self.MOUSE_SCROLL_TEXT:
            command = MouseScroll()
        elif itext == self.DELAY_TEXT:
            command = Delay()
        elif itext == self.TEXT_INPUT_TEXT:
            command = TextInput()
        else:
            command = None
            print(f"Unknown command {itext}")
            return

        list_item = QListWidgetItem()
        list_item.setData(100, command)
        list_item.setText(command.name)

        if self.sequence_list.selectedItems():
            selected_item = self.sequence_list.selectedItems()[0]
            self.sequence_list.insertItem(self.sequence_list.row(selected_item) + 1, list_item)
            self.sequence_list.scrollToItem(list_item)
            inserted_item = self.sequence_list.item(self.sequence_list.row(selected_item) + 1)
        else:
            self.sequence_list.addItem(list_item)
            self.sequence_list.scrollToBottom()
            inserted_item = self.sequence_list.item(self.sequence_list.count() - 1)
        inserted_item.setSelected(True)
        self.on_seq_command_click(inserted_item)

    def set_timing(self, state):
        self.macro.timing = state
        if state:
            self.show_timing()
        else:
            self.hide_timing()

    def show_timing(self):
        try:
            if self.time_input:
                self.time_input.show()
            if self.time_label:
                self.time_label.show()
        except Exception as e:
            print(f"Error showing timing: {e}")

    def hide_timing(self):
        try:
            if self.time_input:
                self.time_input.hide()
            if self.time_label:
                self.time_label.hide()
        except Exception as e:
            print(f"Error hiding timing: {e}")

    def exec_macro(self):
        self.update_macro_commands()
        self.set_macro_running(True)
        self.setFocus()
        threading.Thread(target=self.exec_macro_and_set_state).start()

    def stop_macro(self):
        self.macro.stop()
        self.set_macro_running(False)

    def exec_macro_and_set_state(self):
        self.macro.execute()
        self.set_macro_running(False)

    def set_macro_running(self, running):
        if running:
            self.run_stop_btn.setText("Stop macro")
            self.run_stop_btn.setObjectName("stopBtn")
            self.run_stop_btn.clicked.connect(self.stop_macro)
        else:
            self.run_stop_btn.setText("Run macro")
            self.run_stop_btn.setObjectName("playBtn")
            self.run_stop_btn.clicked.connect(self.exec_macro)

    def update_key_command_toggle(self, state, item):
        item.data(100).update(press=True if state == 2 else False)
        item.setText(item.data(100).name)

    def command_time_update(self, time, item):
        item.data(100).update(time=time)
        item.setText(item.data(100).name)

    def update_click_position(self, x, y, item):
        item.data(100).update(x=x, y=y)
        item.setText(item.data(100).name)

    def update_click_toggle(self, state, item):
        item.data(100).update(press=True if state == 2 else False)
        item.setText(item.data(100).name)

    def update_click_absolute(self, state, item):
        item.data(100).update(absolute=state)
        item.setText(item.data(100).name)

    def update_move_position(self, x, y, item):
        item.data(100).update(x=x, y=y)
        item.setText(item.data(100).name)

    def update_move_toggle(self, state, item):
        item.data(100).update(absolute=state)
        item.setText(item.data(100).name)

    def update_scroll(self, dx, dy, item):
        item.data(100).update(x=dx, y=dy)
        item.setText(item.data(100).name)

    def update_delay(self, time, item):
        item.data(100).update(delay=time)
        item.setText(item.data(100).name)

    def update_text(self, text, item):
        item.data(100).update(text=text)
        item.setText(item.data(100).name)

    def save_as(self):
        self.save(True)

    def update_macro_commands(self):
        commands = []
        for i in range(self.sequence_list.count()):
            item = self.sequence_list.item(i)
            command = item.data(100)
            if command:
                commands.append(command)
        self.macro.commands = commands

    def save(self, save_as=False):
        if save_as:
            self.save_state = self.SAVE_AS_NEW
        else:
            self.save_state = self.SAVE

        self.macro.description = self.desc_input.toPlainText()
        self.macro.repeat = self.repeat_input.value()

        self.update_macro_commands()
        self.exit()

    def cancel(self):
        self.save_state = self.CANCEL
        self.exit()

    def exit(self):
        self.stop_macro()
        self.stop_recording()
        if self.exit_fn:
            self.exit_fn(self, self.save_state)

    def closeEvent(self, event):
        self.cancel()
        event.accept()
