# Class definition for progress dialog widget
# ===========================================
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QLabel, QProgressDialog


class ProgressDialog(QProgressDialog):
    """
    ProgressDialog
    ==============

    ``class`` for progress dialog widget.

    **Attributes**

    **label :** *QLabel*
        *QLabel* displaying message in progress dialog.
    """
    def __init__(self) -> None:
        super(ProgressDialog, self).__init__()
        self.setWindowIcon(QIcon(r'.\gui\gear.png'))
        self.setWindowTitle('Process I&M data')
        self.setCancelButtonText('Abort')
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignLeft)
        self.setLabel(self.label)
        self.setWindowModality(Qt.WindowModal)
        # Display progress dialog.
        QApplication.processEvents()

    def executeFunction(self, function) -> None:
        """
        **executeFunction** Execute function and display its progress through the progress dialog.

        :param function: Function to execute. The function should be a generator yielding a tuple with the first element as the message text for the dialog, the second element as the minimum scale for the progress bar, the third element as the maximum scale for the progress bar and the fourth element as the current progress for defining the completion length within the progress bar.
        """
        self.show()
        # Iterate through generated tuples. The elements of the tuple should be as follows:
        #     1    Message text to display in the progress dialog
        #     2    Minimum scale for the progress bar, corresponding to zero progress
        #     3    Maximum scale for the progress bar, corresponding to complete progress
        #     4    Value defining the completed progress to display in the progress bar. The value must be in the range
        #               bounded by the minimum scale and the maximum scale
        for (label_text, min, max, value) in function:
            if self.wasCanceled():
                exit()
            self.setLabelText(label_text)
            self.setMinimum(min)
            self.setMaximum(max)
            self.setValue(value)
            # Update progress bar.
            QApplication.processEvents()
