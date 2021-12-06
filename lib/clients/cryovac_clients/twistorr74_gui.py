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
        self.setFixedSize(225, 225)
        #twistorr 74
        self.twistorr_label = QLabel('Twistorr 74 Pump')
        self.twistorr_label.setFont(QFont(shell_font, pointSize= 18))
        self.twistorr_label.setAlignment(Qt.AlignCenter)
            #readout
        self.twistorr_display_label = QLabel('Pressure (mbar)')
        self.twistorr_display = QLabel('Pressure')
        self.twistorr_display.setFont(QFont(shell_font, pointSize=20))
        self.twistorr_display.setAlignment(Qt.AlignCenter)
        self.twistorr_display.setStyleSheet('color: blue')
            #record button
        self.twistorr_record = TextChangingButton(('Stop Recording', 'Start Recording'))
            #power
        self.twistorr_lockswitch = TextChangingButton(('Unlocked', 'Locked'))
        self.twistorr_lockswitch.setChecked(True)
        self.twistorr_power = TextChangingButton(('On', 'Off'))

    def makeLayout(self):
        layout = QGridLayout()
        shell_font = 'MS Shell Dlg 2'

        pump1_col = 0
        #pump2_col = 9

        layout.addWidget(self.twistorr_label, 0, pump1_col)
        layout.addWidget(self.twistorr_display_label, 1, pump1_col)
        layout.addWidget(self.twistorr_display, 2, pump1_col)
        layout.addWidget(self.twistorr_power, 3, pump1_col)
        layout.addWidget(self.twistorr_lockswitch, 4, pump1_col)
        layout.addWidget(self.twistorr_record, 5, pump1_col)

        #layout.minimumSize()
        self.setLayout(layout)

if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runGUI
    runGUI(twistorr74_gui)



