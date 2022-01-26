import os
from twisted.internet.defer import inlineCallbacks

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTabWidget, QGridLayout


class EGGS_GUI(QMainWindow):

    name = 'EGGS GUI'
    LABRADPASSWORD = os.environ['LABRADPASSWORD']

    def __init__(self, reactor, clipboard=None, parent=None):
        super(EGGS_gui, self).__init__(parent)
        self.clipboard = clipboard
        self.reactor = reactor
        self.setWindowIcon(QIcon('/eggs.png'))
        self.setWindowTitle('EGGS GUI')
        # connect devices synchronously
        d = self.connect()
        d.addCallback(self.makeLayout)

    @inlineCallbacks
    def connect(self):
        from EGGS_labrad.clients.connect import connection
        self.cxn = connection(name=self.name)
        yield self.cxn.connect()
        return self.cxn

    def makeLayout(self, cxn):
        # central layout
        centralWidget = QWidget()
        layout = QHBoxLayout()
        self.tabWidget = QTabWidget()

        # create subwidgets
        script_scanner = self.makeScriptScannerWidget(self.reactor, cxn)
        cryovac = self.makeCryovacWidget(self.reactor, cxn)
        trap = self.makeTrapWidget(self.reactor, cxn)
        lasers = self.makeLaserWidget(self.reactor, cxn)
        #imaging = self.makeImagingWidget(self.reactor, cxn)

        # create tabs for each subwidget
        self.tabWidget.addTab(script_scanner, '&Script Scanner')
        self.tabWidget.addTab(cryovac, '&Cryovac')
        self.tabWidget.addTab(trap, '&Trap')
        self.tabWidget.addTab(lasers, '&Lasers')
        #self.tabWidget.addTab(imaging, '&Imaging')

        # put it all together
        layout.addWidget(self.tabWidget)
        centralWidget.setLayout(layout)
        self.setCentralWidget(centralWidget)
        self.setWindowTitle(self.name)

    def makeScriptScannerWidget(self, reactor, cxn):
        from EGGS_labrad.clients.script_scanner_gui import script_scanner_gui
        scriptscanner = script_scanner_gui(reactor, cxn=cxn)
        return scriptscanner

    def makeCryovacWidget(self, reactor, cxn):
        # import constituent widgets
        from EGGS_labrad.clients.cryovac_clients.lakeshore336_client import lakeshore336_client
        from EGGS_labrad.clients.cryovac_clients.niops03_client import niops03_client
        from EGGS_labrad.clients.cryovac_clients.twistorr74_client import twistorr74_client
        from EGGS_labrad.clients.cryovac_clients.RGA_client import RGA_client
        from EGGS_labrad.clients.cryovac_clients.fma1700a_client import fma1700a_client
        #from EGGS_labrad.clients.cryovac_clients.f70_client import f70_client

        # instantiate constituent widgets
        lakeshore = lakeshore336_client(reactor, cxn=cxn.cxn)
        niops = niops03_client(reactor, cxn=cxn.cxn)
        twistorr = twistorr74_client(reactor, cxn=cxn.cxn)
        rga = RGA_client(reactor, cxn=cxn.cxn)
        fma = fma1700a_client(reactor, cxn=cxn.cxn)
        #f70 = f70_client(reactor, cxn=cxn.cxn)

        # tab layout
        holder_widget = QWidget()
        holder_layout = QGridLayout()
        holder_widget.setLayout(holder_layout)
        holder_layout.addWidget(lakeshore, 0, 0)
        holder_layout.addWidget(rga, 0, 1)
        holder_layout.addWidget(twistorr, 0, 2)
        holder_layout.addWidget(niops, 1, 1)
        holder_layout.addWidget(fma, 1, 2)
        #holder_layout.addWidget(f70, 2, 0)
        return holder_widget

    def makeTrapWidget(self, reactor, cxn):
        # import constituent widgets
        from EGGS_labrad.clients.trap_clients.rf_client import rf_client
        from EGGS_labrad.clients.trap_clients.DC_client import DC_client

        # instantiate constituent widgets
        rf = rf_client(reactor, cxn.cxn)
        dc = DC_client(reactor, cxn.cxn)

        # tab layout
        holder_widget = QWidget()
        holder_layout = QGridLayout()
        holder_widget.setLayout(holder_layout)
        holder_layout.addWidget(rf, 0, 0)
        holder_layout.addWidget(dc, 0, 1)
        return holder_widget

    def makeLaserWidget(self, reactor, cxn):
        from EGGS_labrad.clients.SLS_client.SLS_client import SLS_client
        sls_widget = SLS_client(reactor, cxn=cxn.cxn)
        return sls_widget

    def makeImagingWidget(self, reactor, cxn):
        from EGGS_labrad.clients.PMT_client.PMT_client import PMT_client
        PMT_widget = pmt_client(reactor, cxn=cxn.cxn)
        return PMT_widget

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.clients import runClient
    runClient(EGGS_GUI)
