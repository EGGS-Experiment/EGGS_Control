@echo off && conda activate labart && python -ix "%~f0" %* & goto :eof
import labrad
cxn = labrad.connect()
tt=cxn.twistorr74_server
tt.device_select('causewaybay','COM10')