import os
import time
import datetime as datetime

from twisted.internet.task import LoopingCall
from twisted.internet.defer import inlineCallbacks

from EGGS_labrad.lib.clients.cryovac_clients.twistorr74_gui import twistorr74_gui

class twistorr74_client(twistorr74_gui):

    name = 'Twistorr74 Client'

    PRESSUREID = 694321
    ENERGYID = 694322
    RPMID = 694323
    POWERID = 694324

    def __init__(self, reactor, cxn=None, parent=None):
        super().__init__()
        self.cxn = cxn
        self.gui = self
        self.reactor = reactor
        self.servers = ['TwisTorr74 Server', 'Data Vault']
        # initialization sequence
        d = self.connect()
        d.addCallback(self.initData)
        d.addCallback(self.initializeGUI)

    @inlineCallbacks
    def connect(self):
        """
        Creates an asynchronous connection to pump servers
        and relevant labrad servers
        """
        # create labrad connection
        if not self.cxn:
            import os
            LABRADHOST = os.environ['LABRADHOST']
            from labrad.wrappers import connectAsync
            self.cxn = yield connectAsync(LABRADHOST, name=self.name)

        # try to get servers
        try:
            self.reg = self.cxn.registry
            self.dv = self.cxn.data_vault
            self.tt = self.cxn.twistorr74_server
        except Exception as e:
            print('Required servers not connected, disabling widget.')
            self.setEnabled(False)

        # set recording stuff
        self.c_record = self.cxn.context()
        self.recording = False

        # connect to signals
            # device parameters
        yield self.tt.signal__pressure_update(self.PRESSUREID)
        yield self.tt.addListener(listener=self.updatePressure, source=None, ID=self.PRESSUREID)
        yield self.tt.signal__energy_update(self.ENERGYID)
        yield self.tt.addListener(listener=self.updateEnergy, source=None, ID=self.ENERGYID)
        yield self.tt.signal__rpm_update(self.RPMID)
        yield self.tt.addListener(listener=self.updateRPM, source=None, ID=self.RPMID)
        yield self.tt.signal__power_update(self.POWERID)
        yield self.tt.addListener(listener=self.updatePower, source=None, ID=self.POWERID)
            # server connections
        yield self.cxn.manager.subscribe_to_named_message('Server Connect', 9898989, True)
        yield self.cxn.manager.addListener(listener=self.on_connect, source=None, ID=9898989)
        yield self.cxn.manager.subscribe_to_named_message('Server Disconnect', 9898989 + 1, True)
        yield self.cxn.manager.addListener(listener=self.on_disconnect, source=None, ID=9898989 + 1)

        # start device polling
        poll_params = yield self.tt.polling()
        # only start polling if not started
        if not poll_params[0]:
            yield self.tt.polling(True, 5.0)

        return self.cxn

    @inlineCallbacks
    def initData(self, cxn):
        """
        Get startup data from servers and show on GUI.
        """
        power_tmp = yield self.tt.toggle()
        self.gui.twistorr_power.setChecked(power_tmp)

    @inlineCallbacks
    def initializeGUI(self, cxn):
        """
        Connect signals to slots and other initializations.
        """
        self.gui.twistorr_lockswitch.toggled.connect(lambda status: self.lock_twistorr(status))
        self.gui.twistorr_power.clicked.connect(lambda status: self.toggle_twistorr(status))
        self.gui.twistorr_record.toggled.connect(lambda status: self.record_pressure(status))


    # SIGNALS
    @inlineCallbacks
    def on_connect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' reconnected, enabling widget.')
            yield self.initData(self.cxn)
            self.setEnabled(True)

    def on_disconnect(self, c, message):
        server_name = message[1]
        if server_name in self.servers:
            print(server_name + ' disconnected, disabling widget.')
            self.setEnabled(False)

    @inlineCallbacks
    def updatePressure(self, c, pressure):
        """
        Updates GUI when values are received from server.
        """
        self.gui.pressure_display.setText(str(pressure))
        if self.recording:
            elapsedtime = time.time() - self.starttime
            yield self.dv.add(elapsedtime, pressure, context=self.c_record)

    def updateEnergy(self, c, energy):
        """
        Updates GUI when values are received from server.
        """
        self.gui.power_display.setText(str(energy))

    def updateRPM(self, c, rpm):
        """
        Updates GUI when values are received from server.
        """
        self.gui.rpm_display.setText(str(rpm))

    def updatePower(self, c, power):
        """
        Updates GUI when other clients have made changes to the device.
        """
        self.gui.twistorr_power.setChecked(power)


    # SLOTS
    @inlineCallbacks
    def record_pressure(self, status):
        """
        Creates a new dataset to record pressure and
        tells polling loop to add data to data vault.
        """
        # set up datavault
        self.recording = status
        if self.recording == True:
            self.starttime = time.time()
            date = datetime.now()
            year = str(date.year)
            month = '{:02d}'.format(date.month)

            trunk1 = '{0:s}_{1:s}_{2:02d}'.format(year, month, date.day)
            trunk2 = '{0:s}_{1:02d}:{2:02d}'.format(self.name, date.hour, date.minute)
            yield self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_record)
            yield self.dv.new('Twistorr 74 Pump Controller', [('Elapsed time', 't')],
                              [('Pump Pressure', 'Pressure', 'mbar')], context=self.c_record)

    #@inlineCallbacks
    def toggle_twistorr(self, status):
        """
        Sets pump power on or off.
        """
        print('set power: ' + str(status))
        #yield self.tt.toggle(status)

    def lock_twistorr(self, status):
        """
        Locks user interface to device.
        """
        self.gui.twistorr_power.setEnabled(status)

    def closeEvent(self, event):
        self.cxn.disconnect()
        if self.reactor.running:
            self.reactor.stop()


if __name__ == "__main__":
    from EGGS_labrad.lib.clients import runClient
    runClient(twistorr74_client)
