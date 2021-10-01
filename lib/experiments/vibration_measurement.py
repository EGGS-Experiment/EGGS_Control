from common.lib.servers.script_scanner.scan_methods import experiment

import labrad
import numpy as np
import time
import datetime as datetime

class vibration_measurement(experiment):

    '''
    Records scope trace and its FFT, pressure, and temperature
    '''

    name = 'Vibration Measurement'

    exp_parameters = [
                    ('VibrationMeasurement', 'dt'),
                    ]

    @classmethod
    def all_required_parameters(cls):
        return cls.exp_parameters

    def initialize(self, cxn, context, ident):
        #properties
        self.ident = ident
        self.cxn = labrad.connect(name = 'Vibration Measurement')

        #base servers
        self.dv = self.cxn.data_vault
        self.p = self.parameters
        #self.grapher = self.cxn.real_simple_grapher

        #device servers
        #self.oscope = self.cxn.oscilloscope_server
        #self.tempcontroller = self.cxn.lakeshore336server
        #self.pump = self.cxn.twistorr74server

        #set scannable parameters
        self.time_interval = self.p.VibrationMeasurement.dt
        self.time_interval = 1.0

        #convert parameter to labrad type
        #welp, todo

        #dataset context
        self.c_temp = self.cxn.context()
        self.c_press = self.cxn.context()

        #set up data vault
        self.set_up_datavault()

    def run(self, cxn, context, replacement_parameters={}):
        prevtime = time.time()
        starttime = time.time()

        while (True):
            if (self.pause_or_stop() == True):
                break
            if (time.time() - prevtime) <= self.time_interval:
                continue

            #tempK = self.tempcontroller.read_temperature('0')
            #pressure = self.pump.read_pressure()
            pressure = 3
            tempK = np.array([0.1,0.2,0.3,0.4],dtype=float)
            # trace = self.oscope.get_trace('1')
            elapsedtime = time.time() - starttime
            try:
                self.dv.add(elapsedtime, tempK[0], tempK[1], tempK[2], tempK[3], context = self.c_temp)
                self.dv.add(elapsedtime, pressure, context = self.c_press)
            except:
                pass

            crt_time = time.time()

    def finalize(self, cxn, context):
        self.cxn.disconnect()

    def set_up_datavault(self):
        #set up folder
        date = datetime.datetime.now()
        year  = str(date.year)
        month = '%02d' % date.month     # Padded with a zero if one digit
        day   = '%02d' % date.day       # Padded with a zero if one digit
        hour  = '%02d' % date.hour      # Padded with a zero if one digit
        minute = '%02d' % date.minute   # Padded with a zero if one digit

        trunk1 = year + '_' + month + '_' + day
        trunk2 = self.name + '_' + hour + ':' + minute

        #create datasets
        self.dv.cd(['', year, month, trunk1, trunk2], True, context = self.c_temp)
        dataset_temp = self.dv.new('Lakeshore 336 Temperature Controller',[('time', 't')], [('Diode 1', 'Temperature', 'K'), ('Diode 2', 'Temperature', 'K'), \
                                                                                             ('Diode 3', 'Temperature', 'K'), ('Diode 4', 'Temperature', 'K')] , context = self.c_temp)

        self.dv.cd(['', year, month, trunk1, trunk2], True, context=self.c_press)
        dataset_pressure = self.dv.new('TwisTorr 74 Pressure Controller',[('time', 't')], [('Pump Pressure', 'Pressure', 'mTorr')], context = self.c_press)
        #dataset_oscope = self.dv.new('Rigol DS1104z Oscilloscope',[('time', 't')], [('Scope Trace', 'Scope Trace', '1')], context = self.c_result)

        #add parameters to data vault
        for parameter in self.p:
            self.dv.add_parameter(parameter, self.p[parameter], context = self.c_temp)
            self.dv.add_parameter(parameter, self.p[parameter], context = self.c_press)

        #set live plotting
        #self.grapher.plot(dataset, 'bright/dark', False)


if __name__ == '__main__':
    cxn = labrad.connect()
    scanner = cxn.scriptscanner
    exprt = vibration_measurement(cxn = cxn)
    ident = scanner.register_external_launch(exprt.name)
    exprt.execute(ident)