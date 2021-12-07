from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QFrame, QWidget, QLabel, QGridLayout

from EGGS_labrad.lib.clients.Widgets import TextChangingButton as _TextChangingButton


class TextChangingButton(_TextChangingButton):
    def __init__(self, button_text=None, parent=None):
        super(TextChangingButton, self).__init__(button_text, parent)
        self.setMaximumHeight(30)


class twistorr74_gui(QFrame):
    def __init__(self, parent=None):
        window = QWidget.__init__(self, parent)
        self.setFrameStyle(0x0001 | 0x0030)
        self.makeWidgets()
        self.makeLayout()
        self.setWindowTitle("Twistorr74 Client")

    def makeWidgets(self):
        shell_font = 'MS Shell Dlg 2'
        self.setFixedSize(225, 325)
        #twistorr 74
        self.twistorr_label = QLabel('Twistorr 74 Pump')
        self.twistorr_label.setFont(QFont(shell_font, pointSize= 18))
        self.twistorr_label.setAlignment(Qt.AlignCenter)
            # pressure readout
        self.pressure_display_label = QLabel('Pressure (mbar)')
        self.pressure_display = QLabel('Pressure')
        self.pressure_display.setFont(QFont(shell_font, pointSize=20))
        self.pressure_display.setAlignment(Qt.AlignCenter)
        self.pressure_display.setStyleSheet('color: blue')
            # power readout
        self.power_display_label = QLabel('Pressure (mbar)')
        self.power_display = QLabel('Power')
        self.power_display.setFont(QFont(shell_font, pointSize=20))
        self.power_display.setAlignment(Qt.AlignCenter)
        self.power_display.setStyleSheet('color: blue')
            # speed readout
        self.rpm_display_label = QLabel('Speed (rpm)')
        self.rpm_display = QLabel('Speed')
        self.rpm_display.setFont(QFont(shell_font, pointSize=20))
        self.rpm_display.setAlignment(Qt.AlignCenter)
        self.rpm_display.setStyleSheet('color: blue')
            #record button
        self.twistorr_record = TextChangingButton(('Stop Recording', 'Start Recording'))
            #power
        self.twistorr_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.twistorr_lockswitch.setChecked(True)
        self.twistorr_power = TextChangingButton(('On', 'Off'))

    def makeLayout(self):
        layout = QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        col1 = 0
        col2 = 1

        layout.addWidget(self.twistorr_label, 0, col1, 1, 1)

        layout.addWidget(self.pressure_display_label, 1, col1)
        layout.addWidget(self.pressure_display, 2, col1)
        layout.addWidget(self.power_display_label, 3, col1)
        layout.addWidget(self.power_display, 4, col1)
        layout.addWidget(self.rpm_display_label, 5, col1)
        layout.addWidget(self.rpm_display, 6, col1)

        layout.addWidget(self.twistorr_power, 7, col1)
        layout.addWidget(self.twistorr_lockswitch, 8, col1)
        layout.addWidget(self.twistorr_record, 9, col1)

        #layout.minimumSize()
        self.setLayout(layout)

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(twistorr74_gui)



