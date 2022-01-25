"""
### BEGIN NODE INFO
[info]
name = PMT Server
version = 1.0.0
description = Controls the Hamamatsu H10892 PMT via ARTIQ
instancename = PMT Server

[startup]
cmdline = %PYTHON% %FILE%
timeout = 20

[shutdown]
message = 987654321
timeout = 20
### END NODE INFO
"""

from labrad.units import WithUnit
from labrad.server import setting, Signal
from twisted.internet.defer import inlineCallbacks, returnValue

from EGGS_labrad.lib.servers.server_classes import ARTIQServer
_TTL_MAX_TIME_US = 10000
_TTL_MIN_TIME_US = 1


class PMTServer(LabradServer, ARTIQServer):
    """
    Controls the Hamamatsu H10892 PMT via ARTIQ.
    """

    name = 'PMT Server'
    regKey = 'PMTServer'

    ddb_path = 'C:\\Users\\EGGS1\\Documents\\ARTIQ\\artiq-master\\device_db.py'
    dma_name = 'PMT_exp'
    dma_exp_file = "%LABRAD_ROOT%\\lib\\servers\\pmt\\pmt_server.py"
    dataset_name = ''

    # SIGNALS
    pressure_update = Signal(999999, 'signal: pressure update', '(ii)')

    def initServer(self):
        # declare PMT variables
        self.ttl_number = 0
        self.trigger_status = False
        self.trigger_ttl_number = -1
        self.bin_time_us = 10
        self.reset_time_us = 10
        self.length_us = 1000
        self.edge_type = 'rising'
        # get all input TTLs
        artiq_devices = self.get_devices(self.ddb_path)
        self.available_ttls = []
        for name, params in artiq_devices.items():
            # only get devices with named class
            if ('class' not in params) and (params['class'] == 'TTLInOut'):
                self.available_ttls.append(name)


    # HARDWARE
    @setting(211, 'Select PMT', chan_num='i', returns='s')
    def PMTselect(self, c, chan_num=None):
        """
        Select the PMT TTL channel.
        Arguments:
            chan_num    (bool)  : the TTL channel number for PMT input
        Returns:
                        (str)   : the input TTL device name
        """
        if chan_num in self.available_ttls:
            self.ttl_number = chan_num
        else:
            raise Exception('Error: invalid TTL channel.')
        return 'ttl' + str(self.ttl_number)

    @setting(221, 'Select Trigger', status='b', chan_num='i', returns='(bs)')
    def triggerSelect(self, c, status=None, chan_num=None):
        """
        Select the trigger TTL channel.
        Arguments:
            status      (bool)  : whether triggering should be active
            chan_num    (int)   : the TTL channel number for PMT input
        Returns:
                        (bs)    : (triggering status, trigger device name)
        """
        if chan_num is None:
            if self.status is not None:
                self.trigger_active = status
        elif chan_num in self.available_ttls():
            self.trigger_ttl_number = chan_num
        else:
            raise Exception('Error: invalid TTL channel.')
        return (self.trigger_status, 'ttl'+self.trigger_ttl_number)


    # GATING
    @setting(311, 'Gating Time', time_us='i', returns='i')
    def gateTime(self, c, time_us=None):
        """
        Set the gate time.
        Arguments:
            time_us (int)   : the gate time in us
        Returns:
                    (int)   : the gate time in us
        """
        if (time_us > _TTL_MIN_TIME_US) and (time_us < _TTL_MAX_TIME_US):
            self.bin_time_us = time_us
        else:
            raise Exception('Error: invalid delay time. Must be in [1us, 10ms].')
        return self.bin_time_us

    @setting(312, 'Gating Delay', time_us='i', returns='i')
    def gateDelay(self, c, time_us=None):
        """
        Set the delay time between bins.
        Arguments:
            time_us (int)   : the delay time between bins in us
        Returns:
                    (int)   : the delay time between bins in us
        """
        if (time_us > _TTL_MIN_TIME_US) and (time_us < _TTL_MAX_TIME_US):
            self.reset_time_us = time_us
        else:
            raise Exception('Error: invalid delay time. Must be in [1us, 10ms].')
        return self.reset_time_us

    @setting(313, 'Gating Edge', edge_type='s', returns='s')
    def gateEdge(self, c, edge_type=None):
        """
        Set the edge detection for each count.
        Arguments:
            edge_type   (str)   : the edge detection type. Must be one of ('rising', 'falling', 'both').
        Returns:
                        (str)   : the edge detection type
        """
        if edge_type.lower() in ('rising', 'falling', 'both'):
            self.edge_type = edge_type
        else:
            raise Exception('Error: invalid edge type. Must be one of (rising, falling, both).')
        return self.edge_type


    # RECORDING
    @setting(411, 'Length', time_us='i', returns='i')
    def length(self, c, time_us):
        """
        Set the record time (in us).
        Arguments:
            time_us (int)   : the length of time to record for
        Returns:
                    (int)   : the length of time to record for
        """
        self.length_us = time_us


    # RUN
    @setting(511, 'Program', returns='')
    def program(self, c):
        """
        Program the PMT sequence onto core DMA.
        """
        yield self.runExperiment(self.dma_exp_file)

    @setting(521, 'Start', returns='(*v, *i)')
    def start(self, c):
        """
        Start acquisition by running the core DMA experiment.
        Returns:
                    (*v, *i)    : (time array, count array)
        """
        yield self.DMArun(self.dma_name)
        res = yield self.getDataset(self.dataset_name)
        returnValue(res)


if __name__ == '__main__':
    from labrad import util
    util.runServer(PMTServer())