from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class MacroSquare(QWidget):
    WIDTH = 150
    HEIGHT = 150

    def __init__(self, title, description, macro=None):
        super().__init__()
        self.title = title
        self.description = description
        self.macro = macro
        self.on_edit = None
        self.on_execute = None
        self.on_delete = None
        self.on_stop = None
        self.w = None
        self.grid = None
        self.right_btn = None
        self.mode_edit = False
        self.macro_running = False
        self.start_pos = None
        self.initUI()

    def initUI(self):
        self.setObjectName("macroSquare")

        self.grid = QGridLayout()
        self.setLayout(self.grid)

        title = QLabel(self.title)
        description = QLabel(self.description)
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setAlignment(Qt.AlignmentFlag.AlignTop)

        edit_btn = QToolButton()
        edit_btn.setIcon(QIcon("app_qt/icons/edit.svg"))
        edit_btn.setIconSize(QSize(30, 30))
        edit_btn.setObjectName("editBtn")
        edit_btn.clicked.connect(self.edit)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.setStyleSheet("* { background-color: #003dc5;} *:hover { background-color: #0000ff;}")

        self.right_btn = QToolButton()
        self.right_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.right_btn.setIconSize(QSize(30, 30))
        self.set_normal_mode()

        self.grid.addWidget(title, 0, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        self.grid.addWidget(description, 1, 0, 1, 3, alignment=Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)
        self.grid.addWidget(edit_btn, 2, 0)
        self.grid.addWidget(self.right_btn, 2, 2)

        self.setFixedSize(self.WIDTH, self.HEIGHT)

    def set_data(self, title=None, description=None, macro=None):
        if title:
            self.title = title
        if description:
            self.description = description
        if macro:
            self.macro = macro
        self.grid.itemAt(0).widget().setText(self.title)
        self.grid.itemAt(1).widget().setText(self.description)

    def reload_data(self):
        self.title = self.macro.name
        self.description = self.macro.description
        self.grid.itemAt(0).widget().setText(self.title)
        self.grid.itemAt(1).widget().setText(self.description)

    def set_del_btn(self):
        self.right_btn.setIcon(QIcon("app_qt/icons/trash.svg"))
        self.right_btn.setObjectName("delBtn")
        self.right_btn.setStyleSheet("* { background-color: #b60000;} *:hover { background-color: #ff0000;}")
        self.right_btn.disconnect()
        self.right_btn.clicked.connect(self.on_del_click)

    def set_play_btn(self):
        self.right_btn.setIcon(QIcon("app_qt/icons/play.svg"))
        self.right_btn.setObjectName("playBtn")
        self.right_btn.setStyleSheet("* { background-color: #00b600;} *:hover { background-color: #00ff00;}")
        self.right_btn.disconnect()
        self.right_btn.clicked.connect(self.on_execute_click)

    def set_stop_btn(self):
        self.right_btn.setIcon(QIcon("app_qt/icons/stop.svg"))
        self.right_btn.setStyleSheet("* { background-color: #b60000;} *:hover { background-color: #ff0000;}")
        self.right_btn.disconnect()
        self.right_btn.clicked.connect(self.on_stop_click)
        self.update()

    def set_edit_mode(self):
        if self.macro_running:
            return
        self.mode_edit = True
        self.set_del_btn()
        self.update()

    def set_normal_mode(self):
        if self.macro_running:
            return
        self.mode_edit = False
        self.set_play_btn()
        self.update()

    def on_stop_click(self):
        self.on_stop()

    def on_execute_click(self, *args):
        self.on_execute(self)

    def set_fn_on_edit(self, func):
        self.on_edit = func

    def set_fn_on_execute(self, func):
        self.on_execute = func

    def set_fn_on_delete(self, func):
        self.on_delete = func

    def edit(self):
        self.on_edit(self)

    def on_del_click(self, *args):
        self.on_delete(self)

    def mouseMoveEvent(self, event, *args):
        if self.mode_edit:
            if event.buttons() & Qt.MouseButton.LeftButton:
                drag = QDrag(self)
                mime_data = QMimeData()
                mime_data.setText("macro")
                drag.setMimeData(mime_data)
                drag.setPixmap(self.grab())
                drag.setHotSpot(event.pos())
                drag.exec(Qt.DropAction.MoveAction)

    def paintEvent(self, event, *args):
        pixmap = QPixmap(self.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        qp = QPainter(pixmap)
        qp.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(0, 0, -1, -1)
        qp.setPen(QPen(QColor(0, 0, 0), 1))
        qp.setBrush(QBrush(QColor(80, 80, 80)))
        qp.drawRoundedRect(rect, 15, 15)

        if self.mode_edit:
            pixmap2 = QPixmap("app_qt/icons/move.svg")
            rect2 = QRect(5, 5, 30, 30)
            qp.drawPixmap(rect2, pixmap2)
            self.setCursor(Qt.CursorShape.OpenHandCursor)
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

        qp.end()

        qp = QPainter(self)
        qp.drawPixmap(0, 0, pixmap)
        qp.end()
