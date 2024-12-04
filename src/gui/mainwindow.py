# Class definition for main window of graphical user interface
# ============================================================
from PySide6.QtWidgets import QComboBox, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QSizePolicy, QStatusBar, QVBoxLayout, QWidget
from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QCloseEvent, QIcon
from pathlib import Path
from datetime import datetime, timedelta
from .datelineedit import DateLineEdit
from .filedialoggbx import FileDialogGbx
from src.jsontools.jsontools import readJSON, writeJSON
from src.ftp.downloaddata import checkLastQuery


class MainWindow(QMainWindow):
    """
    MainWindow
    ==========
    ``class`` for main window of graphical user interface.
    """
    def __init__(self, guidata_path: Path, lastquery: dict) -> None:
        """
        **__init__** Class constructor.

        :param guidata_path: File path to the dictionary storing data from the graphical user interface.
        :type guidata_path: Path
        :param lastquery:  Dictionary storing date range for most recent downloaded data.
        :type lastquery: dict
        """
        super(MainWindow, self).__init__()
        self.setWindowIcon(QIcon(str(Path(__file__).parents[2].joinpath('resources', 'icon', 'report.png'))))
        self.setWindowTitle('I&M weekly report')
        self.guidata_path = guidata_path
        self.guidata_dict = readJSON(filepath=str(self.guidata_path))
        # Initialise 'proceed' field indicating whether to continue execution or to quit after the main window is
        # closed. 'proceed ' = True to continue, or False to quit.
        self.guidata_dict['proceed'] = False
        self.lastquery = lastquery
        # One of the following two icons is rendered on the status bar of the main window.
        self.pth_ftpdownloadicon = Path(__file__).parents[2].joinpath('resources', 'icon', 'download-cloud.png')
        self.pth_localdataicon = Path(__file__).parents[2].joinpath('resources', 'icon', 'drive-upload.png')

        # Define the contents of a groupbox for inputting fields for referencing the report.
        self.lbl_reportprefix = QLabel('Prefix:')
        self.ldt_reportprefix = QLineEdit()
        self.ldt_reportprefix.setText(self.guidata_dict['reportprefix'])
        self.lbl_reportnumber = QLabel('Number:')
        self.ldt_reportnumber = QLineEdit()
        # Specify a minimum of one digit and a maximum of three for data entry.
        self.ldt_reportnumber.setInputMask('900')
        self.ldt_reportnumber.setText(str(self.guidata_dict['reportnumber']))
        self.lbl_reportrevision = QLabel('Revision:')
        self.ldt_reportrevision = QLineEdit()
        # Specify a minimum of one digit for data entry.
        self.ldt_reportrevision.setInputMask('9')
        self.ldt_reportrevision.setText(str(self.guidata_dict['reportrevision']))
        self.lyt_reportref = QVBoxLayout()
        self.lyt_reportref.addWidget(self.lbl_reportprefix)
        self.lyt_reportref.addWidget(self.ldt_reportprefix)
        self.lyt_reportref.addSpacing(7)
        self.lyt_reportref.addWidget(self.lbl_reportnumber)
        self.lyt_reportref.addWidget(self.ldt_reportnumber)
        self.lyt_reportref.addSpacing(7)
        self.lyt_reportref.addWidget(self.lbl_reportrevision)
        self.lyt_reportref.addWidget(self.ldt_reportrevision)
        self.gbx_reportref = QGroupBox('Report reference')
        self.gbx_reportref.setLayout(self.lyt_reportref)

        # Define a groupbox for entering the issue date of the report.
        self.ldt_issuedate = DateLineEdit(self, display_date=QDate().currentDate())
        self.lyt_issuedate = QHBoxLayout()
        self.lyt_issuedate.addWidget(self.ldt_issuedate)
        self.lyt_issuedate.addStretch(1)
        self.gbx_issuedate = QGroupBox('Issue date')
        self.gbx_issuedate.setLayout(self.lyt_issuedate)

        # Define a groupbox for defining the date range of the monitoring data presented in the report.
        self.lbl_startdate = QLabel('Start date')
        # The dates method returns the start or end date depending upon the date_type argument.
        self.ldt_startdate = DateLineEdit(self, display_date=self.dates(date_type='start'))
        # Test to see if the requested date range falls within the date range of already-downloaded data when the start
        # date field is edited.
        self.ldt_startdate.textChanged.connect(lambda: self.ftpDownloadStatus())
        self.lyt_startdate = QHBoxLayout()
        self.lyt_startdate.addWidget(self.ldt_startdate)
        self.lyt_startdate.addStretch(1)
        self.lbl_enddate = QLabel('End date')
        # The dates method returns the start or end date depending upon the date_type argument.
        self.ldt_enddate = DateLineEdit(self, display_date=self.dates(date_type='end'))
        # Test to see if the requested date range falls within the date range of already-downloaded data when the end
        # date field is edited.
        self.ldt_enddate.textChanged.connect(lambda: self.ftpDownloadStatus())
        self.lyt_enddate = QHBoxLayout()
        self.lyt_enddate.addWidget(self.ldt_enddate)
        self.lyt_enddate.addStretch(1)
        self.lbl_ignoreperiod00 = QLabel('Ignore data ')
        self.cmb_ignoreperiod = QComboBox()
        for number in range(0, 51):
            self.cmb_ignoreperiod.addItem('{0:.0f}'.format(number))
        self.cmb_ignoreperiod.setCurrentText('{0:.0f}'.format(self.guidata_dict['ignoreperiod']))
        # Test to see if the requested date range falls within the date range of already-downloaded data when the ignore
        # period field is edited.
        self.cmb_ignoreperiod.currentTextChanged.connect(lambda: self.ftpDownloadStatus())
        self.lbl_ignoreperiod01 = QLabel(' days before')
        self.lyt_ignoreperiod = QHBoxLayout()
        self.lyt_ignoreperiod.addWidget(self.lbl_ignoreperiod00)
        self.lyt_ignoreperiod.addWidget(self.cmb_ignoreperiod)
        self.lyt_ignoreperiod.addWidget(self.lbl_ignoreperiod01)
        self.lyt_ignoreperiod.addStretch(1)
        self.lyt_period = QVBoxLayout()
        self.lyt_period.addWidget(self.lbl_startdate)
        self.lyt_period.addLayout(self.lyt_startdate)
        self.lyt_period.addSpacing(7)
        self.lyt_period.addWidget(self.lbl_enddate)
        self.lyt_period.addLayout(self.lyt_enddate)
        self.lyt_period.addSpacing(7)
        self.lyt_period.addLayout(self.lyt_ignoreperiod)
        self.gbx_period = QGroupBox('Period')
        self.gbx_period.setLayout(self.lyt_period)

        # A Level 1 layout (level01) is the second level down from the parent layout. h00 refers to the first layout box
        # in a horizontal arrangement, i.e. the left one.
        self.lyt_level01h00 = QVBoxLayout()
        self.lyt_level01h00.addWidget(self.gbx_reportref)
        self.lyt_level01h00.addWidget(self.gbx_issuedate)
        self.lyt_level01h00.addWidget(self.gbx_period)
        self.lyt_level01h00.addStretch(1)

        # Define a groupbox for specifying thresholds that define whether output from an instrument is classified as an
        # observation for reporting purposes.
        self.lbl_smxthresholdname = QLabel('Settlement marker:')
        self.lbl_smxthresholdname.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cmb_smxthresholdvalue = QComboBox()
        self.cmb_smxthresholdvalue.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_smxthresholdunit = QLabel('mm/week')
        self.lbl_smxthresholdunit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_mpxthresholdname = QLabel('Extensometer:')
        self.lbl_mpxthresholdname.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cmb_mpxthresholdvalue = QComboBox()
        self.cmb_mpxthresholdvalue.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_mpxthresholdunit = QLabel('mm/week')
        self.lbl_mpxthresholdunit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_incthresholdname = QLabel('Inclinometer:')
        self.lbl_incthresholdname.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cmb_incthresholdvalue = QComboBox()
        self.cmb_incthresholdvalue.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_incthresholdunit = QLabel('mm/week')
        self.lbl_incthresholdunit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_vwpthresholdname = QLabel('Vibrating wire piezometer:')
        self.lbl_vwpthresholdname.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.cmb_vwpthresholdvalue = QComboBox()
        self.cmb_vwpthresholdvalue.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.lbl_vwpthresholdunit = QLabel('m/week')
        self.lbl_vwpthresholdunit.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        # Populate the comboboxes using progressively increasing intervals with increasing value.
        for number in range(0, 12, 2):
            self.cmb_smxthresholdvalue.addItem('{0:.0f}'.format(number))
            self.cmb_mpxthresholdvalue.addItem('{0:.0f}'.format(number))
            self.cmb_incthresholdvalue.addItem('{0:.0f}'.format(number))
        for number in range(15, 55, 5):
            self.cmb_smxthresholdvalue.addItem('{0:.0f}'.format(number))
            self.cmb_mpxthresholdvalue.addItem('{0:.0f}'.format(number))
            self.cmb_incthresholdvalue.addItem('{0:.0f}'.format(number))
        for number in range(60, 110, 10):
            self.cmb_smxthresholdvalue.addItem('{0:.0f}'.format(number))
            self.cmb_mpxthresholdvalue.addItem('{0:.0f}'.format(number))
            self.cmb_incthresholdvalue.addItem('{0:.0f}'.format(number))
        for number in range(120, 220, 20):
            self.cmb_smxthresholdvalue.addItem('{0:.0f}'.format(number))
            self.cmb_mpxthresholdvalue.addItem('{0:.0f}'.format(number))
            self.cmb_incthresholdvalue.addItem('{0:.0f}'.format(number))
        for number in range(0, 11, 1):
            self.cmb_vwpthresholdvalue.addItem('{0:.1f}'.format(0.1 * number))
        for number in range(12, 22, 2):
            self.cmb_vwpthresholdvalue.addItem('{0:.1f}'.format(0.1 * number))
        for number in range(25, 55, 5):
            self.cmb_vwpthresholdvalue.addItem('{0:.1f}'.format(0.1 * number))
        for number in range(6, 11, 1):
            self.cmb_vwpthresholdvalue.addItem('{0:.1f}'.format(number))
        for number in range(12, 22, 2):
            self.cmb_vwpthresholdvalue.addItem('{0:.1f}'.format(number))
        for number in range(25, 55, 5):
            self.cmb_vwpthresholdvalue.addItem('{0:.1f}'.format(number))
        self.cmb_smxthresholdvalue.setCurrentText('{0:.0f}'.format(self.guidata_dict['smxthreshold']))
        self.cmb_mpxthresholdvalue.setCurrentText('{0:.0f}'.format(self.guidata_dict['mpxthreshold']))
        self.cmb_incthresholdvalue.setCurrentText('{0:.0f}'.format(self.guidata_dict['incthreshold']))
        self.cmb_vwpthresholdvalue.setCurrentText('{0:.1f}'.format(self.guidata_dict['vwpthreshold']))
        self.lyt_thresholds = QGridLayout()
        self.lyt_thresholds.addWidget(self.lbl_smxthresholdname, 0, 0, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.cmb_smxthresholdvalue, 0, 1, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.lbl_smxthresholdunit, 0, 2, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.lbl_mpxthresholdname, 1, 0, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.cmb_mpxthresholdvalue, 1, 1, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.lbl_mpxthresholdunit, 1, 2, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.lbl_incthresholdname, 2, 0, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.cmb_incthresholdvalue, 2, 1, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.lbl_incthresholdunit, 2, 2, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.lbl_vwpthresholdname, 3, 0, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.cmb_vwpthresholdvalue, 3, 1, Qt.AlignLeft)
        self.lyt_thresholds.addWidget(self.lbl_vwpthresholdunit, 3, 2, Qt.AlignLeft)
        self.lyt_thresholds.setColumnStretch(2, 1)
        self.gbx_thresholds = QGroupBox('Observation thresholds')
        self.gbx_thresholds.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.gbx_thresholds.setLayout(self.lyt_thresholds)

        # Define a groupbox for selecting the directory within which to write the generated report.
        self.gbx_outputdir = FileDialogGbx(
            object_type='Directory',
            mode='Save',
            initial_file=self.guidata_dict['outputfolder'],
            title='Output folder'
        )

        # A Level 1 layout (level01) is the second level down from the parent layout. h01 refers to the second layout
        # box in a horizontal arrangement, i.e. the second-to-left one, or the right one in the case of only two.
        self.lyt_level01h01 = QVBoxLayout()
        self.lyt_level01h01.addWidget(self.gbx_thresholds)
        self.lyt_level01h01.addWidget(self.gbx_outputdir)
        self.lyt_level01h01.addStretch(1)

        # A Level 0 layout (level00) is the first level down from the parent layout. v00 refers to the first layout box
        # in a vertical arrangement, i.e. the top one.
        self.lyt_level00v00 = QHBoxLayout()
        self.lyt_level00v00.addLayout(self.lyt_level01h00)
        self.lyt_level00v00.addLayout(self.lyt_level01h01)

        # A Level 0 layout (level00) is the first level down from the parent layout. v01 refers to the first layout box
        # in a vertical arrangement, i.e. the second-from-top one, or the bottom one in the case of only two.
        self.lyt_level00v01 = QHBoxLayout()
        self.pbn_ok = QPushButton('OK')
        self.pbn_ok.setDefault(True)
        self.pbn_ok.clicked.connect(lambda: self.okEvent())
        self.pbn_cancel = QPushButton('Cancel')
        self.pbn_cancel.clicked.connect(lambda: self.cancelEvent())
        self.lyt_level00v01 = QHBoxLayout()
        self.lyt_level00v01.addStretch(1)
        self.lyt_level00v01.addWidget(self.pbn_ok)
        self.lyt_level00v01.addWidget(self.pbn_cancel)

        self.lyt_parent = QVBoxLayout()
        self.lyt_parent.addLayout(self.lyt_level00v00)
        self.lyt_parent.addStretch(1)
        self.lyt_parent.addLayout(self.lyt_level00v01)

        self.wdg_central = QWidget()
        self.wdg_central.setLayout(self.lyt_parent)
        self.setCentralWidget(self.wdg_central)

        # Define a status bar, which indicates whether the requested date range falls within the date range of
        # already-downloaded data, and therefore whether data needs to be downloaded from the FTP server. The status bar
        # displays an icon followed by text.
        self.lbl_ftpdownloadtext = QLabel()
        self.ftpDownloadStatus()
        self.statusbar = QStatusBar()
        self.statusbar.addPermanentWidget(self.lbl_ftpdownloadtext, 1)
        self.setStatusBar(self.statusbar)

    def dates(self, date_type: str) -> QDate or None:
        """
        **dates** Return a *QDate* for initialising either the start date or end date fields. The end date is defined as
        the last Friday at least three days before the current date. The start date is defined one week before the end
        date.

        :param date_type: Date type to return, as one of two values: 'start' or 'end'.
        :type date_type: str
        :return: QDate or None
        """
        # Define the end date as the last Friday at least three days before the current date.
        enddate = QDate.currentDate().addDays(-3 -((QDate.currentDate().addDays(-3).dayOfWeek() - 5) % 7))
        if date_type == 'end':
            return enddate
        elif date_type == 'start':
            # Define the start date as one week before the end date.
            return enddate.addDays(-7)
        else:
            return None

    def ftpDownloadStatus(self) -> None:
        """
        **ftpDownloadStatus** Populate the *QLabel* displayed in the status bar, indicating whether data needs to be
        downloaded from the FTP server.
        """
        # Consider start and end dates as the time 23:59:59 on the selected date, so as to consider readings taken
        # during the 24 hours of the date itself.
        self.guidata_dict['startdate'] = (datetime.strptime(self.ldt_startdate.text(), '%d-%m-%Y') + timedelta(days=1) - timedelta(seconds=1)).strftime('%d-%m-%Y %H:%M:%S')
        self.guidata_dict['enddate'] = (datetime.strptime(self.ldt_enddate.text(), '%d-%m-%Y') + timedelta(days=1) - timedelta(seconds=1)).strftime('%d-%m-%Y %H:%M:%S')
        self.guidata_dict['ignoreperiod'] = float(self.cmb_ignoreperiod.currentText())
        # Check whether the requested date range falls within the date range of already-downloaded data. The boolean
        # flag downloadFlag is False if it does, and True if it does not.
        downloadFlag = checkLastQuery(
            guidata=self.guidata_dict,
            lastquery=self.lastquery
        )
        if downloadFlag:
            self.lbl_ftpdownloadtext.setText(f'<html><img src="{str(self.pth_ftpdownloadicon)}"></html> FTP download required')
        else:
            self.lbl_ftpdownloadtext.setText(f'<html><img src="{str(self.pth_localdataicon)}"></html> Local data sufficient')

    def cancelEvent(self) -> None:
        """
        **cancelEvent** Method called when the Cancel *QPushButton* is clicked.
        """
        self.closeEvent(event=QCloseEvent())

    def closeEvent(self, event):
        # Close any open child windows
        if hasattr(self.ldt_issuedate, 'cld_calendarwindow'):
            self.ldt_issuedate.cld_calendarwindow.close()
        if hasattr(self.ldt_startdate, 'cld_calendarwindow'):
            self.ldt_startdate.cld_calendarwindow.close()
        if hasattr(self.ldt_enddate, 'cld_calendarwindow'):
            self.ldt_enddate.cld_calendarwindow.close()
        # Record data from the graphical user interface in a JSON file.
        writeJSON(filepath=str(self.guidata_path), data=self.guidata_dict)
        self.close()

    def okEvent(self):
        # Indicate that execution should proceed after the main window is closed.
        self.guidata_dict['proceed'] = True
        self.guidata_dict['reportprefix'] = self.ldt_reportprefix.text()
        self.guidata_dict['reportnumber'] = int(self.ldt_reportnumber.text())
        self.guidata_dict['reportrevision'] = int(self.ldt_reportrevision.text())
        self.guidata_dict['issuedate'] = datetime.strptime(self.ldt_issuedate.text(), '%d-%m-%Y').strftime('%d-%m-%Y %H:%M:%S')
        # Consider start and end dates as the time 23:59:59 on the selected date, so as to consider readings taken
        # during the 24 hours of the date itself.
        self.guidata_dict['startdate'] = (datetime.strptime(self.ldt_startdate.text(), '%d-%m-%Y') + timedelta(days=1) - timedelta(seconds=1)).strftime('%d-%m-%Y %H:%M:%S')
        self.guidata_dict['enddate'] = (datetime.strptime(self.ldt_enddate.text(), '%d-%m-%Y') + timedelta(days=1) - timedelta(seconds=1)).strftime('%d-%m-%Y %H:%M:%S')
        self.guidata_dict['ignoreperiod'] = float(self.cmb_ignoreperiod.currentText())
        self.guidata_dict['smxthreshold'] = float(self.cmb_smxthresholdvalue.currentText())
        self.guidata_dict['mpxthreshold'] = float(self.cmb_mpxthresholdvalue.currentText())
        self.guidata_dict['incthreshold'] = float(self.cmb_incthresholdvalue.currentText())
        self.guidata_dict['vwpthreshold'] = float(self.cmb_vwpthresholdvalue.currentText())
        self.guidata_dict['outputfolder'] = self.gbx_outputdir.getOutputValue()
        self.closeEvent(event=QCloseEvent())