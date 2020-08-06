from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QDesktopWidget
from PyQt5.QtCore import Qt

from . import load_config
import pathlib


# import yaml
import oyaml as yaml  # This preserves dictionary order in dumping

from PyQt5 import QtCore
from PyQt5.QtCore import QMimeData, QSize, Qt, pyqtSlot, pyqtSignal, Signal
from PyQt5.QtGui import QBrush, QColor, QDrag, QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class KanbanWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        base_path = pathlib.Path(__file__).parent.parent
        file_config = base_path.joinpath("config.yml")

        self.config_dict = load_config.load_config(file_config)

        screenGeom = QDesktopWidget().availableGeometry()
        sh = screenGeom.height()
        sw = screenGeom.width()
        dx = 800
        dy = 150
        y_offset = 700
        self.setGeometry(sw - dx + 100, sh - dy - y_offset, dx, dy)

        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        #        self.setWindowFlag(Qt.FramelessWindowHint)
        #        self.setGeometry(300, 350, 800, 500)

        self.columns = ["backlog", "todo", "doing", "done"]
        n_columns = len(self.columns)
        grid = QGridLayout()
        grid.setSpacing(n_columns)

        self.column_dict = {}
        for i, column in enumerate(self.columns):
            self.column_dict[column] = ColumnWidget(self)

            grid.addWidget(QLabel(column), 0, i)
            grid.addWidget(self.column_dict[column], 1, i)

        self.setLayout(grid)

    def update_kanban(self):
        self.todo_filename = self.config_dict["dropbox"].joinpath(
            "Notebook", "miscellaneous", "todo.yml"
        )
        with open(self.todo_filename) as file_config:
            self.full_yaml = yaml.safe_load(file_config)

        # need to clear column dict
        for key, column in self.column_dict.items():
            column.clear()
        kanban_columndicts = self.full_yaml["kanban_state"]
        for key in kanban_columndicts.keys():
            item_list = kanban_columndicts[key]

            if item_list:
                for i, item_name in enumerate(item_list):
                    if item_name:
                        item = QListWidgetItem()
                        # item.setBackground(QBrush(QColor("#FEF4E0")))
                        item.setText(item_name)
                        item.setFont(QFont("DejaVu Sans", 10))
                        item.setSizeHint(QSize(60, 17))
                        # item.setSizeHint(QSize(60, 35))
                        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                        item.setToolTip(item_name)

                        self.column_dict[key].insertItem(i, item)

            item = QListWidgetItem()
            item.setText("")
            item.setFont(QFont("DejaVu Sans", 10))
            item.setSizeHint(QSize(60, 15))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            self.column_dict[key].insertItem(len(item_list), item)

    @pyqtSlot()
    def save_state(self):

        kanban_dict = {}
        for column_name, column in self.column_dict.items():
            kanban_dict[column_name] = []
            for row in range(column.count()):
                column_item = column.item(row).text()
                kanban_dict[column_name].append(column_item)
            if len(kanban_dict[column_name]) == 0:
                kanban_dict[column_name] = None

        output_dict = self.full_yaml
        output_dict["kanban_state"] = kanban_dict

        with open(self.todo_filename, "w") as file_dump:
            yaml.safe_dump(
                output_dict, file_dump, default_flow_style=False, line_break="\r"
            )
        print("Saved kanban state")

    def closeEvent(self, event):
        print("closing kanban")
        self.save_state()


class ColumnWidget(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.AllEditTriggers = True

    def dropEvent(self, event):
        super().dropEvent(event)
        event.setDropAction(QtCore.Qt.MoveAction)
