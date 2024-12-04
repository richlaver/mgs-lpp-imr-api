# Class definition for file dialog widget accessed from a layout object
# =====================================================================
import os
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QHBoxLayout, QFileDialog, QLineEdit, QPushButton, QSizePolicy)


class FileDialogLyt(QHBoxLayout):
    """
    FileDialogLyt
    =============
    ``class`` for file dialog widget accessed from a QPushButton within a QHBoxLayout. The selected file or directory is
    displayed in a QLineEdit.

    ----

    **Attributes**

    **output_value** *str*
        File or directory path selected by the file dialog. The ``getOutputValue()`` method accesses the selected path
        after the file dialog box is closed.
    **ldt_name** *QLineEdit*
        Line edit widget for displaying the name of the selected file or directory
    **pbn_select** *QPushButton*
        Push button widget for opening the file dialog.
    **dir** *str*
        Directory for the last selected file or parent directory for the last selected directory, i.e. the parent of the
        last selected path. This is used to initialise the location where the file dialog accesses when first opened.
    """
    def __init__(
            self,
            object_type='File',
            mode='Save',
            initial_file=None,
            name_filter='Excel files (*.xls *.xlsx *.xslm)'
    ) -> None:
        """
        **__init__** Class constructor.

        :param object_type: Type of object that the file dialog accesses. To access a file, object_type = 'File'. To access a directory, object_type = 'Folder' or 'Directory'.
        :type object_type: str
        :param mode: Mode of the file dialog. To open a file, mode = 'Open'. To save a file, mode = 'Save'.
        :type mode: str
        :param initial_file: File or directory path used to render the initial object that the file dialog opens to. This path determines the file or directory name for initial display.
        :type initial_file: str or None
        :param name_filter: File types filtered by the file dialog.
        :type name_filter: str
        """
        super(FileDialogLyt, self).__init__()
        # Initialise the output for the selected file as the initial_file argument.
        self.output_value = initial_file
        self.ldt_name = QLineEdit()
        self.ldt_name.setAlignment(Qt.AlignLeft)
        self.ldt_name.setMinimumWidth(200)
        self.addWidget(self.ldt_name)
        self.pbn_select = QPushButton('Select')
        self.pbn_select.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.addWidget(self.pbn_select)
        if initial_file is None:
            # If the initial_file argument is None, set the directory to which the file dialog opens to the directory
            # containing this app.
            self.dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        else:
            self.dir = os.path.dirname(initial_file)
            self.ldt_name.setText(os.path.basename(initial_file))
            self.ldt_name.setCursorPosition(0)
        self.pbn_select.clicked.connect(lambda: showDialog())

        def showDialog() -> None:
            """
            **showDialog** Show file dialog.
            """
            file_dialog = QFileDialog()
            file_dialog.setDirectory(self.dir)
            if object_type in ['Folder', 'Directory']:
                file_dialog.setFileMode(QFileDialog.Directory)
            if object_type == 'File':
                if mode == 'Open':
                    file_dialog.setFileMode(QFileDialog.ExistingFile)
                if mode == 'Save':
                    file_dialog.setFileMode(QFileDialog.AnyFile)
            file_dialog.setNameFilter(name_filter)
            file_dialog.exec()
            if len(file_dialog.selectedFiles()) > 0:
                self.output_value = file_dialog.selectedFiles()[0]
                self.ldt_name.setText(os.path.basename(self.output_value))
                self.ldt_name.setCursorPosition(0)
                self.dir = os.path.dirname(self.output_value)

    def getOutputValue(self):
        """
        **getOutputValue** Get selected file or directory path.

        :return: String. Selected file or directory path.
        """
        return self.output_value