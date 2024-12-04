# Class definition for calendar widget
# ====================================
from PySide6.QtCore import QDate
from PySide6.QtWidgets import QCalendarWidget, QMainWindow, QLineEdit


class Calendar(QCalendarWidget):
    """
    Calendar
    ========
    ``class`` for calendar widget.

    ----

    **Attributes**

    **line_edit :** *QLineEdit*
        Stores instance for parent line edit.
    **mainwindow :** *QMainWindow*
        Stores instance for parent main window.
    """
    def __init__(self, parent: QMainWindow or None = None, line_edit: QLineEdit or None = None) -> None:
        """
        **__init__** Class constructor.

        :param parent: Instance for parent main window.
        :type parent: QMainWindow
        :param line_edit: Instance for parent line edit.
        :type line_edit: QLineEdit
        """
        super().__init__()
        self.line_edit = line_edit
        self.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.setGridVisible(True)
        self.setMaximumDate(QDate.currentDate())
        self.mainwindow = parent
        self.setSelectedDate(self.line_edit.displaydate)
        self.setSelectionMode(QCalendarWidget.SingleSelection)
        self.clicked.connect(lambda date: self.onClick(date))

    def onClick(self, date) -> None:
        self.line_edit.displaydate = date
        self.line_edit.setText(date.toString('dd-MM-yyyy'))
        self.close()