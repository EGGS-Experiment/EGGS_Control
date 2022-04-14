:: LabRAD Master
:: Starts the LabRAD Master.

@ECHO OFF
SETLOCAL EnableDelayedExpansion

REM: Prepare LabRAD CMD
CALL %EGGS_LABRAD_ROOT%\bin\prepare_labrad.bat

REM: Parse arguments for server activation
SET /A server_flag=0
SET /A raw_flag=0
FOR %%x IN (%*) DO (
    IF "%%x"=="-s" (SET /a server_flag=1)
    IF "%%x"=="-r" (SET /a raw_flag=1)
    IF "%%x"=="-h" (GOTO HELP)
    IF "%%x"=="--help" (GOTO HELP)
)

REM: Set up syslog daemon
START "Labrad SysLog" /min CMD "/k activate labart && python %EGGS_LABRAD_ROOT%\bin\labrad_syslog.py

REM: Core Servers
START "Labrad Manager" /min %HOME%\Code\scalabrad-0.8.3\bin\labrad.bat --tls-required false
START "Labrad Web GUI" /min %HOME%\Code\scalabrad-web-server-2.0.6\bin\labrad-web.bat
START "Labrad Node" /min CMD "/k activate labart && python %HOME%\Code\pylabrad\labrad\node\__init__.py -s -x %LABRADHOST%:%EGGS_LABRAD_SYSLOG_PORT%"
START "" "%ProgramFiles(x86)%\chrome-win\chrome.exe" http://localhost:7667

REM: Temporary solution: need to have device

REM: Don't open any servers if raw flag is active
IF %raw_flag%==1 (GOTO SHELL)

REM: ARTIQ
START /min CMD /c %EGGS_LABRAD_ROOT%\bin\artiq_start.bat

:SHELL

REM: Run all device servers as specified, then open a python shell to begin
IF %server_flag%==1 (
    TIMEOUT 8 > NUL && START /min CMD /c %EGGS_LABRAD_ROOT%\bin\utils\start_labrad_servers.bat
    TIMEOUT 8 > NUL && CALL %EGGS_LABRAD_ROOT%\bin\server_cxn.bat
) ELSE ( CALL %EGGS_LABRAD_ROOT%\bin\labrad_cxn.bat )

REM: Clients
START /min CMD /c %EGGS_LABRAD_ROOT%\bin\utils\start_labrad_clients.bat

GOTO EOF

:HELP
@ECHO usage: labrad_master [-h] [-s] [-r]
@ECHO:
@ECHO LabRAD Master
@ECHO Optional Arguments:
@ECHO    -h, --help          show this message and exit
@ECHO    -s                  start all day-to-day device servers (specific to EGGS Experiment)
@ECHO    -r                  start only the labrad core (i.e. the manager, a node, and the Chromium GUI)
@ECHO:

:EOF

REM: Unset variables
SET "server_flag="
SET "raw_flag="
