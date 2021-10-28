#labrad and artiq imports
from labrad.server import LabradServer, setting, Signal

#async imports
from twisted.internet import reactor, task
from twisted.internet.defer import DeferredLock, inlineCallbacks, returnValue, Deferred

#wrapper imports
from sequence import Sequence

#function imports
import numpy as np

class Pulser_legacy(LabradServer):

    """Contains legacy functionality for Pulser"""

    onSwitch = Signal(611051, 'signal: switch toggled', '(ss)')
    on_dds_param = Signal(142006, 'signal: new dds parameter', '(ssv)')
    on_line_trigger_param = Signal(142007, 'signal: new line trigger parameter', '(bv)')

    def initServer(self):
        #todo: appropriate these variables
            #device storage
        self.channelDict = hardwareConfiguration.channelDict
        self.ddsDict = hardwareConfiguration.ddsDict
        self.remoteChannels = hardwareConfiguration.remoteChannels
            #pmt
        self.collectionTime = hardwareConfiguration.collectionTime
        self.collectionMode = hardwareConfiguration.collectionMode
        self.collectionTimeRange = hardwareConfiguration.collectionTimeRange
            #ttl
        self.timeResolution = float(hardwareConfiguration.timeResolution)
        self.sequenceTimeRange = hardwareConfiguration.sequenceTimeRange
        yield self.initializeRemote()
        self.listeners = set()

        #TTLs
        for channel in self.channelDict.values():
            channelnumber = channel.channelnumber
            if channel.ismanual:
                state = channel.manualin ^ channel.manualstate
                self.api.setManual(channelnumber, state)
            else:
                self.api.setAuto(channelnumber, channel.autoinv)

        #DDS
        self._ddsSeq = list()
        self.api.initializeDDS()

        for name, channel in self.ddsDict.items():
            channel.name = name
            freq, ampl, phase = (channel.frequency, channel.amplitude, channel.phase)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
            yield self.inCommunication.run(self._setDDSParam, channel, freq, ampl, phase)

        #Linetrigger
        self.linetrigger_limits = [WithUnit(v, 'us') for v in hardwareConfiguration.lineTriggerLimits]

    @inlineCallbacks
    def initializeRemote(self):
        self.remoteConnections = {}
        if len(self.remoteChannels):
            from labrad.wrappers import connectAsync
            for name, rc in self.remoteChannels.items():
                try:
                    self.remoteConnections[name] = yield connectAsync(rc.ip)
                    print('Connected to {}'.format(name))
                except:
                    print('Not Able to connect to {}'.format(name))
                    self.remoteConnections[name] = None

    @setting(111, 'Add TTL Pulse', channel = 's', start = 'v[s]', duration = 'v[s]')
    def addTTLPulse(self, c, channel, start, duration):
        """
        Add a TTL Pulse to the sequence, times are in seconds
        """
        if channel not in self.channelDict.keys():
            raise Exception("Unknown Channel {}".format(channel))
        hardwareAddr = self.channelDict.get(channel).channelnumber
        sequence = c.get('sequence')
        start = start['s']
        duration = duration['s']
        #simple error checking
        if not ((self.sequenceTimeRange[0] <= start <= self.sequenceTimeRange[1]) and
                 (self.sequenceTimeRange[0] <= start + duration <= self.sequenceTimeRange[1])):
            raise Exception("Time boundaries are out of range")
        if not duration >= self.timeResolution:
            raise Exception("Incorrect duration")
        if not sequence:
            raise Exception("Please create new sequence first")
        sequence.addPulse(hardwareAddr, start, duration)

    @setting(112, 'Add TTL Pulses', pulses = '*(sv[s]v[s])')
    def addTTLPulses(self, c, pulses):
        """
        Add multiple TTL Pulses to the sequence, times are in seconds. The pulses are a list in the same format as 'add ttl pulse'.
        """
        for pulse in pulses:
            channel = pulse[0]
            start = pulse[1]
            duration = pulse[2]
            yield self.addTTLPulse(c, channel, start, duration)

    @setting(113, "Extend Sequence Length", timeLength = 'v[s]')
    def extendSequenceLength(self, c, timeLength):
        """
        Allows to optionally extend the total length of the sequence beyond the last TTL pulse.
        """
        sequence = c.get('sequence')
        if not (self.sequenceTimeRange[0] <= timeLength['s'] <= self.sequenceTimeRange[1]):
            raise Exception("Time boundaries are out of range")
        if not sequence:
            raise Exception("Please create new sequence first")
        sequence.extendSequenceLength(timeLength['s'])

    @setting(114, "Human Readable TTL", getProgrammed = 'b', returns = '*2s')
    def humanReadableTTL(self, c, getProgrammed = None):
        """
        Args:
            getProgrammed (bool): False/None(default) to get the sequence added by current context,
                              True to get the last programmed sequence
        Returns:
            a readable form of TTL sequence
        """
        sequence = c.get('sequence')
        if getProgrammed:
            sequence = self.programmed_sequence
        if not sequence:
            raise Exception ("Please create new sequence first")
        ttl, dds = sequence.humanRepresentation()
        return ttl.tolist()

    @setting(115, "Human Readable DDS", getProgrammed = 'b', returns = '*(svv)')
    def humanReadableDDS(self, c, getProgrammed = None):
        """
        Args:
            getProgrammed (bool): False/None(default) to get the sequence added by current context,
                              True to get the last programmed sequence
        Returns:
            a readable form of DDS sequence
        """
        sequence = c.get('sequence')
        if getProgrammed:
            sequence = self.programmed_sequence
        if not sequence:
            raise Exception("Please create new sequence first")
        ttl, dds = sequence.humanRepresentation()
        return dds

    @setting(116, 'Get Channels', returns = '*(sw)')
    def getChannels(self, c):
        """
        Returns all available channels, and the corresponding hardware numbers
        """
        d = self.channelDict
        keys = d.keys()
        numbers = [d[key].channelnumber for key in keys]
        return zip(keys, numbers)

    @setting(117, 'Get State', channelName = 's', returns = '(bbbb)')
    def getState(self, c, channelName):
        """
        Returns the current state of the switch: in the form (Manual/Auto, ManualOn/Off, ManualInversionOn/Off, AutoInversionOn/Off)
        """
        if channelName not in self.channelDict.keys():
            raise Exception("Incorrect Channel")
        channel = self.channelDict[channelName]
        answer = (channel.ismanual, channel.manualstate, channel.manualinv, channel.autoinv)
        return answer

    #DDS functions
    @setting(121, "Get DDS Channels", returns = '*s')
    def getDDSChannels(self, c):
        """get the list of available channels"""
        return self.ddsDict.keys()

    @setting(122, 'Add DDS Pulses',  values = ['*(sv[s]v[s]v[MHz]v[dBm]v[deg]v[MHz]v[dB])'])
    def addDDSPulses(self, c, values):
        '''
        input in the form of a list [(name, start, duration, frequency, amplitude, phase, ramp_rate, amp_ramp_rate)]
        '''
        sequence = c.get('sequence')
        if not sequence:
            raise Exception("Please create new sequence first")
        for value in values:
            try:
                name, start, dur, freq, ampl = value
                phase = 0.0
                ramp_rate = 0.0
            except ValueError:
                name, start, dur, freq, ampl, phase, ramp_rate, amp_ramp_rate = value
            try:
                channel = self.ddsDict[name]
            except KeyError:
                raise Exception("Unknown DDS channel {}".format(name))
            start = start['s']
            dur = dur['s']
            freq = freq['MHz']
            ampl = ampl['dBm']
            phase = phase['deg']
            ramp_rate = ramp_rate['MHz']
            amp_ramp_rate = amp_ramp_rate['dB']
            freq_off, ampl_off = channel.off_parameters
            #only check range if dds won't be off
            if (freq == 0) or (ampl == 0):
                freq, ampl = freq_off, ampl_off
            else:
                self._checkRange('frequency', channel, freq)
                self._checkRange('amplitude', channel, ampl)
            #convert DDS settings to RAM data
            num = self.settings_to_num(channel, freq, ampl, phase, ramp_rate, amp_ramp_rate)
            num_off = self.settings_to_num(channel, freq, ampl_off, phase, ramp_rate, amp_ramp_rate)
            #todo: convert
            num_ARTIQ = (asf, ftw, pow)
            num_off_ARTIQ = (asf, ftw, pow)
            #note < sign, because start can not be 0.
            #this would overwrite the 0 position of the ram, and cause the dds to change before pulse sequence is launched
            if not self.sequenceTimeRange[0] < start <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start))
            if not self.sequenceTimeRange[0] < start + dur <= self.sequenceTimeRange[1]:
                raise Exception("DDS start time out of acceptable input range for channel {0} at time {1}".format(name, start + dur))
            if not dur == 0:    #0 length pulses are ignored
                sequence.addDDS(name, start, num_ARTIQ, 'start')
                sequence.addDDS(name, start + dur, num_off_ARTIQ, 'stop')

    @setting(123, 'Get DDS Amplitude Range', name = 's', returns = '(vv)')
    def getDDSAmplRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedamplrange

    @setting(124, 'Get DDS Frequency Range', name = 's', returns = '(vv)')
    def getDDSFreqRange(self, c, name = None):
        channel = self._getChannel(c, name)
        return channel.allowedfreqrange

    @setting(131, "Get Line Trigger Limits", returns='*v[us]')
    def getLineTriggerLimits(self, c):
        """get limits for duration of line triggering"""
        return self.linetrigger_limits

    #Signal/Context functions
    def notifyOtherListeners(self, context, message, f):
        """
        Notifies all listeners except the one in the given context, executing function f
        """
        notified = self.listeners.copy()
        notified.remove(context.ID)
        f(message, notified)

    def initContext(self, c):
        """Initialize a new context object."""
        self.listeners.add(c.ID)

    def expireContext(self, c):
        self.listeners.remove(c.ID)

    #Backwards compatibility
    @inlineCallbacks
    def _setDDSRemote(self, channel, addr, buf):
        cxn = self.remoteConnections[channel.remote]
        remote_info = self.remoteChannels[channel.remote]
        server, reset, program = remote_info.server, remote_info.reset, remote_info.program
        try:
            yield cxn.servers[server][reset]()
            yield cxn.servers[server][program]([(channel.channelnumber, buf)])
        except (KeyError, AttributeError):
            print('Not programming remote channel {}'.format(channel.remote))

    def _channel_to_num(self, channel):
        '''returns the current state of the channel in the num represenation'''
        if channel.state:
            #if on, use current values. else, use off values
            freq, ampl = (channel.frequency, channel.amplitude)
            self._checkRange('amplitude', channel, ampl)
            self._checkRange('frequency', channel, freq)
        else:
            freq,ampl = channel.off_parameters
        num = self.settings_to_num(channel, freq, ampl)
        return num

    def _checkRange(self, t, channel, val):
        if t == 'amplitude':
            r = channel.allowedamplrange
        elif t == 'frequency':
            r = channel.allowedfreqrange
        if not r[0] <= val <= r[1]:
            raise Exception("channel {0} : {1} of {2} is outside the allowed range".format(channel.name, t, val))

    def _getChannel(self, c, name):
        try:
            channel = self.ddsDict[name]
        except KeyError:
            raise Exception("Channel {0} not found".format(name))
        return channel
