# Class definition for line edit object for date entry
# ====================================================
from PySide6.QtCore import QDate, QRegularExpression
from PySide6.QtGui import QIcon, QPixmap, QRegularExpressionValidator
from PySide6.QtWidgets import QLineEdit, QMainWindow
from pathlib import Path
from .calendar import Calendar


class DateLineEdit(QLineEdit):
    """
    DateLineEdit
    ============
    ``class`` for line edit object for date entry.

    ----

    **Attributes**

    **calendariconpath :** *str*
        File path to the calendar icon that will be moused over to open the calendar widget.
    **iconwidth :** *int*
        Width of the calendar icon in pixels after conversion to a pixel map.
    **validateregex :** *QRegularExpression*
        Regex object applied to validate an entry as a valid date.
    **mainwindow :** *QMainWindow*
        Stores instance for parent main window.
    **displaydate :** *QDate*
        Date to display in the line edit.
    """
    def __init__(self, parent: QMainWindow or None = None, display_date: QDate or None = None) -> None:
        """
        **__init__** Class constructor.

        :param parent: Instance for parent main window.
        :type parent: QMainWindow or None
        :param display_date: Date to display in the line edit.
        :type display_date: QDate or None
        """
        super().__init__()
        self.calendariconpath = str(Path(__file__).parents[2].joinpath('resources', 'icon', 'calendar-select.png'))
        # Locate the calendar icon at the far right of the line edit.
        self.addAction(
            QIcon(self.calendariconpath), QLineEdit.TrailingPosition)
        self.setPlaceholderText('DD-MM-YYYY')
        self.iconwidth = QPixmap(self.calendariconpath).width()
        self.setMouseTracking(True)
        self.validateregex = QRegularExpression('(0[1-9]|[12]\d|3[01])\W'
                                                '(0[1-9]|1[0-2])\W'
                                                '(19[0-9][0-9]|2[01][0-9][0-9])')
        self.setValidator(QRegularExpressionValidator(self.validateregex))
        self.mainwindow = parent
        self.displaydate = display_date
        self.setText(QDate.toString(display_date, 'dd-MM-yyyy'))

    def mouseMoveEvent(self, event) -> None:
        # Do nothing if a calendar widget already exists which is not hidden by a previous opening and closing of the
        # widget.
        if hasattr(self, 'cld_calendarwindow'):
            if not self.cld_calendarwindow.isHidden():
                return
        # Show the calendar widget if the mouse moved over the calendar icon
        if event.x() > self.width() - self.iconwidth - self.textMargins().right():
            self.cld_calendarwindow = Calendar(self.mainwindow, line_edit=self)
            self.cld_calendarwindow.show()