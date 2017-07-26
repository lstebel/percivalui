"""
Created on 20 May 2016

@author: Alan Greer
"""
from __future__ import print_function
import os
import logging
from percival.log import get_exclusive_file_logger
from datetime import datetime, timedelta
import getpass

from percival.carrier import const
from percival.carrier.buffer import SensorBufferCommand
from percival.carrier.channels import ControlChannel, MonitoringChannel
from percival.carrier.devices import DeviceFactory
from percival.carrier.database import InfluxDB
from percival.carrier.registers import generate_register_maps, BoardValueRegisters
from percival.carrier.sensor import Sensor
from percival.carrier.settings import BoardSettings
from percival.carrier.system import SystemCommand, SystemSettings, ClockSettings
from percival.carrier.chip import ChipReadoutSettings
from percival.carrier.txrx import TxRx
from percival.carrier.values import BoardValues
from percival.carrier.configuration import SystemSettingsParameters, \
    ChipReadoutSettingsParameters, \
    ClockSettingsParameters, \
    ChannelParameters,\
    SensorConfigurationParameters, \
    BoardParameters, \
    ControlParameters,\
    ChannelGroupParameters,\
    SetpointGroupParameters,\
    BufferParameters,\
    env_carrier_ip
from percival.detector.errors import PercivalDetectorError
from percival.detector.groups import Group
from percival.detector.command import PercivalCommandNames
from percival.detector.set_point import SetPointControl


class PercivalParameters(object):
    """
    High level representation of Parameters loaded from ini files.

    Currently the files are all hardcoded here which is not very elegant.

    A better approach would be to be able to specify the files within the main ini file, and for the files to be
    searched in standard locations or through environment variables.  This is partially implemented for the
    ChannelParameters class.

    ini files are parsed for overall control parameters, for each of the boards and finally for the channels.

    All ini settings are stored and can be accessed through this class.
    """
    def __init__(self, ini_file=None):
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        # Check for master ini file
        if ini_file:
            self._control_params = ControlParameters(ini_file)
        else:
            # Try to load a default file
            try:
                self._control_params = ControlParameters("config/percival.ini")
            except:
                raise PercivalDetectorError("Could not process the Percival initialisation file")

        self._board_params = None

        #self._board_params = {
        #    const.BoardTypes.left: BoardParameters("config/Board LEFT.ini"),
        #    const.BoardTypes.bottom: BoardParameters("config/Board BOTTOM.ini"),
        #    const.BoardTypes.carrier: BoardParameters("config/Board CARRIER.ini"),
        #    const.BoardTypes.plugin: BoardParameters("config/Board PLUGIN.ini")
        #}


        self._channel_params = None
        self._buffer_params = None

        #self._channel_params = ChannelParameters("config/Channel parameters.ini")
        #self._buffer_params = BufferParameters("config/SensorDAC.ini")
        #self._control_group_params = ChannelGroupParameters("config/ControlGroups.ini")
        #self._monitor_group_params = ChannelGroupParameters("config/MonitorGroups.ini")
        #print(self._control_params.setpoint_ini_file)
        #self._setpoint_group_params = SetpointGroupParameters("config/SetpointGroups.ini")
        self._system_settings_params = None
        self._chip_readout_settings_params = None
        self._clock_settings_params = None
        self._sensor_configuration_params = None
        self._sensor_calibration_params = None
        self._sensor_debug_params = None
        self._control_group_params = None
        self._monitor_group_params = None
        self._setpoint_group_params = None

    def load_ini(self):
        """
        Load the initialisation files for the control, four board types and for the channels
        """
        self._control_params.load_ini()

        try:
            self._board_params = {
                const.BoardTypes.left: BoardParameters(self._control_params.board_left_settings_file),
                const.BoardTypes.bottom: BoardParameters(self._control_params.board_bottom_settings_file),
                const.BoardTypes.carrier: BoardParameters(self._control_params.board_carrier_settings_file),
                const.BoardTypes.plugin: BoardParameters(self._control_params.board_plugin_settings_file)
            }
            self._board_params[const.BoardTypes.left].load_ini()
            self._board_params[const.BoardTypes.bottom].load_ini()
            self._board_params[const.BoardTypes.carrier].load_ini()
            self._board_params[const.BoardTypes.plugin].load_ini()
        except:
            self._log.error("Could not initialise board configuration from ini files")
            raise PercivalDetectorError("Could not initialise board configuration from ini files")

        try:
            self._channel_params = ChannelParameters(self._control_params.channel_settings_file)
            self._channel_params.load_ini()
        except:
            self._log.error("Could not initialise channel parameters from ini file")
            raise PercivalDetectorError("Could not initialise channel parameters from ini file")

        try:
            self._buffer_params = BufferParameters(self._control_params.sensor_dac_file)
            self._buffer_params.load_ini()
        except:
            self._log.error("Could not initialise buffer parameters from ini file")
            raise PercivalDetectorError("Could not initialise buffer parameters from ini file")

        #self._control_group_params.load_ini()
        #self._monitor_group_params.load_ini()
        #self._setpoint_group_params.load_ini()
        try:
            self.load_system_settings_ini(self._control_params.system_settings_file)
        except:
            self._log.debug("No default system settings ini file to load")

        try:
            self.load_chip_readout_settings_ini(self._control_params.chip_readout_settings_file)
        except:
            self._log.debug("No default chip readout settings ini file to load")

        try:
            self.load_clock_settings_ini(self._control_params.clock_settings_file)
        except:
            self._log.debug("No default clock settings ini file to load")

        try:
            self.load_sensor_configuration_params(self._control_params.sensor_configuration_file)
        except:
            self._log.debug("No default sensor configuration ini file to load")

        try:
            self.load_control_group_ini(self._control_params.control_group_ini_file)
        except:
            self._log.debug("No default control groups ini file to load")

        try:
            self.load_monitor_group_ini(self._control_params.monitor_group_ini_file)
        except:
            self._log.debug("No default monitor groups ini file to load")

        try:
            self.load_setpoint_group_ini(self._control_params.setpoint_ini_file)
        except:
            self._log.debug("No default setpoints ini file to load")

    def load_system_settings_ini(self, filename):
        # Create the ini object from either filename or raw file
        self._system_settings_params = SystemSettingsParameters(filename)
        self._system_settings_params.load_ini()

    def load_chip_readout_settings_ini(self, filename):
        # Create the ini object from either filename or raw file
        self._chip_readout_settings_params = ChipReadoutSettingsParameters(filename)
        self._chip_readout_settings_params.load_ini()

    def load_clock_settings_ini(self, filename):
        # Create the ini object from either filename or raw file
        self._clock_settings_params = ClockSettingsParameters(filename)
        self._clock_settings_params.load_ini()

    def load_sensor_configuration_params(self, filename):
        # Create the ini object from either filename or raw file
        self._sensor_configuration_params = SensorConfigurationParameters(filename)
        self._sensor_configuration_params.load_ini()

    def load_control_group_ini(self, filename):
        # Create the ini object from either filename or raw file
        self._control_group_params = ChannelGroupParameters(filename)
        self._control_group_params.load_ini()

    def load_monitor_group_ini(self, filename):
        # Create the ini object from either filename or raw file
        self._monitor_group_params = ChannelGroupParameters(filename)
        self._monitor_group_params.load_ini()

    def load_setpoint_group_ini(self, filename):
        # Create the ini object from either filename or raw file
        self._setpoint_group_params = SetpointGroupParameters(filename)
        self._setpoint_group_params.load_ini()

    @property
    def carrier_ip(self):
        """
        Return the IP address of the carrier board.

        The IP address configuration will be loaded from the percival.ini config file or overwritten by the user with
        the environment variable PERCIVAL_CARRIER_IP. If no configurations can be found it will default to 192.168.0.2.

        :returns: IP address of the carrier board
        :rtype: str
        """
        try:
            default_carrier_ip = self._control_params.carrier_ip
        except RuntimeError:
            default_carrier_ip = "192.168.0.2"
            self._log.warning("No carrier IP address found in configuration file")
        return os.getenv(env_carrier_ip, default_carrier_ip)

    @property
    def database(self):
        """
        Return the IP address, port number and name of the database.

        The IP address configuration will be loaded from the percival.ini config file.

        :returns: Database configuration object
        :rtype: Dict
        """
        db = {}
        try:
            db["address"] = self._control_params.database_ip
        except RuntimeError:
            db["address"] = "127.0.0.1"

        try:
            db["port"] = int(self._control_params.database_port)
        except RuntimeError:
            db["port"] = 8086

        try:
            db["name"] = self._control_params.database_name
        except RuntimeError:
            db["name"] = "percival"

        return db

    @property
    def download_system_settings(self):
        download = False
        try:
            download = self._control_params.system_settings_download
        except:
            self._log.info("Could not parse download_system_settings value from config file")
        return download

    @property
    def download_chip_readout_settings(self):
        download = False
        try:
            download = self._control_params.chip_readout_settings_download
        except:
            self._log.info("Could not parse download_chip_readout_settings value from config file")
        return download

    @property
    def download_clock_settings(self):
        download = False
        try:
            download = self._control_params.clock_settings_download
        except:
            self._log.info("Could not parse download_clock_settings value from config file")
        return download

    @property
    def download_sensor_configuration(self):
        download = False
        try:
            download = self._control_params.sensor_configuration_download
        except:
            self._log.info("Could not parse download_sensor_configuration value from config file")
        return download

    def board_name(self, board):
        """
        Return the name of the specified board type

        :param board: Which board to return the name
        :type board: const.BoardTypes
        :returns: Name of the specified board
        :rtype: str
        """
        return self._board_params[board].board_name

    def board_type(self, board):
        """
        Return the type of the specified board

        :param board: Which board to return the type
        :type board: const.BoardTypes
        :returns: Type of the specified board
        :rtype: str
        """
        return self._board_params[board].board_type

    def control_channels_count(self, board):
        """
        Return the number of control channels of the specified board

        :param board: Which board to return the number of control channels
        :type board: const.BoardTypes
        :returns: Number of control channels
        :rtype: int
        """
        return self._board_params[board].control_channels_count

    def monitoring_channels_count(self, board):
        """
        Return the number of monitor channels of the specified board

        :param board: Which board to return the number of monitor channels
        :type board: const.BoardTypes
        :returns: Number of monitor channels
        :rtype: int
        """
        return self._board_params[board].monitoring_channels_count

    def control_channel_by_address(self, uart_address):
        """
        Search for the control channel by its UART address

        :param uart_address: Address of the control channel
        :type uart_address: int
        :returns: Control channel ini parameters
        :rtype: configuration.ControlChannelIniParameters
        """
        return self._channel_params.control_channel_by_address(uart_address)

    def monitoring_channel_by_address(self, uart_address):
        """
        Search for the monitor channel by its UART address

        :param uart_address: Address of the monitor channel
        :type uart_address: int
        :returns: Monitor channel ini parameters
        :rtype: configuration.MonitorChannelIniParameters
        """
        return self._channel_params.monitoring_channel_by_address(uart_address)

    def monitoring_channel_name_by_index_and_board_type(self, index, board):
        """
        Search for the monitor channel name by its ini file index and the board type

        :param index: Index of the channel
        :type index: int
        :param board: Which board to search
        :type board: const.BoardTypes
        :returns: Monitor channel name
        :rtype: str
        """
        return self._channel_params.monitoring_channel_name_by_id_and_board_type(index, board)

    def monitoring_channel_by_name(self, channel_name):
        """
        Search for the monitor channel by its name

        :param channel_name: Name of the monitor channel
        :type channel_name: str
        :returns: Monitor channel ini parameters
        :rtype: configuration.MonitorChannelIniParameters
        """
        self._log.debug(self._channel_params)
        return self._channel_params.monitoring_channels_by_name(channel_name)

    def control_channel_by_name(self, channel_name):
        """
        Search for the control channel by its name

        :param channel_name: Name of the control channel
        :type channel_name: str
        :returns: Control channel ini parameters
        :rtype: configuration.ControlChannelIniParameters
        """
        self._log.debug(self._channel_params)
        return self._channel_params.control_channels_by_name(channel_name)

    @property
    def monitoring_channels(self):
        """
        Return a list of `MonitoringChannelIniParameters`

        :returns: List of monitor channel ini parameters
        :rtype: list
        """
        return self._channel_params.monitoring_channels

    @property
    def control_channels(self):
        """
        Return a list of `ControlChannelIniParameters`

        :returns: List of control channel ini parameters
        :rtype: list
        """
        return self._channel_params.control_channels

    @property
    def sensor_dac_channels(self):
        """
        Return a list of `BufferDACIniParameters`

        :returns: List of control channel ini parameters for sensor DACs
        :rtype: list
        """
        return self._buffer_params.dac_channels

    @property
    def system_settings_params(self):
        return self._system_settings_params

    @property
    def chip_readout_settings_params(self):
        return self._chip_readout_settings_params

    @property
    def clock_settings_params(self):
        return self._clock_settings_params

    @property
    def sensor_configuration_params(self):
        return self._sensor_configuration_params

    @property
    def control_group_params(self):
        return self._control_group_params

    @property
    def monitor_group_params(self):
        return self._monitor_group_params

    @property
    def setpoint_params(self):
        return self._setpoint_group_params


class PercivalDetector(object):
    """
    High level representation of Detector hardware.
    This class manages the connection to the hardware, as well as the configuration and specific setup.

    Low level hardware complexity is handled internally and a simple interface is presented as a public API
    for control and status monitoring.

    This class has no threading internally but should be considered thread safe (needs checking)
    """
    def __init__(self, ini_file=None, download_config=True, initialise_hardware=True):
        self._log = logging.getLogger(".".join([__name__, self.__class__.__name__]))
        self._trace_log = logging.getLogger("percival_trace")
        self._trace_log = get_exclusive_file_logger('./logs/percival_trace_{}.log'.format(datetime.now()
                                                                                          .isoformat()
                                                                                          .replace(':', '_')
                                                                                          .replace('-', '_')))
        self._trace_log.info("Percival execution trace logging")
        self._start_time = datetime.now()
        self._username = getpass.getuser()
        self._txrx = None
        self._db = None
        self._global_monitoring = False
        self._percival_params = PercivalParameters(ini_file)
        self._board_settings = {}
        self._board_values ={}
        self._monitors = {}
        self._controls = {}
        self._sys_cmd = None
        self._sensor_buffer_cmd = None
        self._sensor = None
        self._control_groups = None
        self._monitor_groups = None
        self._system_settings = SystemSettings()
        self._chip_readout_settings = ChipReadoutSettings()
        self._clock_settings = ClockSettings()
        self._setpoint_control = SetPointControl(self)
        self._setpoint_control.start_scan_loop()
        self.load_ini()
        self.setup_db()
        self.setup_control()
        self.auto_download()
        if download_config:
            self.load_configuration()
        self.load_channels()
        if initialise_hardware:
            self.initialize_channels()

    def cleanup(self):
        self._setpoint_control.stop_scan_loop()

    def load_ini(self):
        """
        Load the initialisation files for the detector
        """
        self._log.info("Loading detector ini files...")
        self._percival_params.load_ini()
        self._system_settings.load_ini(self._percival_params.system_settings_params)
        self._chip_readout_settings.load_ini(self._percival_params.chip_readout_settings_params)
        self._clock_settings.load_ini(self._percival_params.clock_settings_params)
        self._setpoint_control.load_ini(self._percival_params.setpoint_params)

    def setup_control(self):
        """
        Setup the control interface for the detector.
        This currently:
        Creates the TxRx connection class and connects to the hardware
        Creates the BoardSettings classes to describe the hardware.  These can be used to either download hardware
        configurations from ini files or to read settings from the hardware.
        Creates a SystemCommand instance which can be used to send system commands to the hardware.
        """
        self._log.info("Carrier IP set as: %s", self._percival_params.carrier_ip)
        self._txrx = TxRx(self._percival_params.carrier_ip)
        self._board_settings[const.BoardTypes.left] = BoardSettings(self._txrx, const.BoardTypes.left)
        self._board_settings[const.BoardTypes.bottom] = BoardSettings(self._txrx, const.BoardTypes.bottom)
        self._board_settings[const.BoardTypes.carrier] = BoardSettings(self._txrx, const.BoardTypes.carrier)
        self._board_settings[const.BoardTypes.plugin] = BoardSettings(self._txrx, const.BoardTypes.plugin)
        self._board_values[const.BoardTypes.carrier] = BoardValues(self._txrx, const.BoardTypes.carrier)
        self._system_settings.set_txrx(self._txrx)
        self._chip_readout_settings.set_txrx(self._txrx)
        self._clock_settings.set_txrx(self._txrx)
        self._sys_cmd = SystemCommand(self._txrx)
        self._sensor_buffer_cmd = SensorBufferCommand(self._txrx)
        self._sensor = Sensor(self._sensor_buffer_cmd)

    def auto_download(self):
        # Check if we are asked to auto download the system settings to hardware
        if self._percival_params.download_system_settings:
            self._log.info("Auto-downloading system settings from default ini file")
            self.download_system_settings()

        # Check if we are asked to auto download the chip readout settings to hardware
        if self._percival_params.download_chip_readout_settings:
            self._log.info("Auto-downloading chip readout settings from default ini file")
            self.download_chip_readout_settings()

        # Check if we are asked to auto download the clock settings to hardware
        if self._percival_params.download_clock_settings:
            self._log.info("Auto-downloading clock settings from default ini file")
            self.download_clock_settings()

        # Check if we are asked to auto download the sensor configuration to hardware
        if self._percival_params.download_sensor_configuration:
            self._log.info("Auto-downloading sensor configuration from default ini file")
            self._sensor.apply_configuration(self._percival_params.sensor_configuration_params.value_map)

    def setup_db(self):
        """
        Provide a DB interface for logging data from the detector.
        This will store the DB object for use when reading status.
        The DB object must support the following interface:
        ...
        ...
        ...

        :param db:
        :return:
        """
        self._db = InfluxDB(self._percival_params.database["address"],
                            self._percival_params.database["port"],
                            self._percival_params.database["name"]
                            )
        self._connect_db()

    def _connect_db(self):
        # Attempt connection to the database
        self._db.connect()

    def load_configuration(self):
        """
        Download the configuration from ini files to the hardware.
        """
        self._log.info("Downloading configuration to hardware")

        cmd_msgs = self._board_settings[const.BoardTypes.left].initialise_board(self._percival_params)
        cmd_msgs += self._board_settings[const.BoardTypes.bottom].initialise_board(self._percival_params)
        cmd_msgs += self._board_settings[const.BoardTypes.carrier].initialise_board(self._percival_params)
        cmd_msgs += self._board_settings[const.BoardTypes.plugin].initialise_board(self._percival_params)
        for cmd_msg in cmd_msgs:
            try:
                resp = self._txrx.send_recv_message(cmd_msg)
            except RuntimeError:
                self._log.exception("no response (message: %s)", cmd_msg)
            # TODO: check response resp

    def download_system_settings(self):
        self._log.info("Downloading system settings to hardware")
        self._system_settings.download_settings()

    def download_chip_readout_settings(self):
        self._log.info("Downloading chip readout settings to hardware")
        self._chip_readout_settings.download_settings()

    def download_clock_settings(self):
        self._log.info("Downloading clock settings to hardware")
        self._clock_settings.download_settings()

    def load_channels(self):
        """
        Readout the settings from the hardware and create all control and monitoring devices according to the current
        settings coupled with the ini file descriptions.
        Monitor type devices are stored in the _monitors dictionary.
        Control type devices are stored in the _controls dictionary.
        """
        # Readback the monitoring settings
        self._board_settings[const.BoardTypes.left].readback_monitoring_settings()
        self._board_settings[const.BoardTypes.bottom].readback_monitoring_settings()
        self._board_settings[const.BoardTypes.carrier].readback_monitoring_settings()
        self._board_settings[const.BoardTypes.plugin].readback_monitoring_settings()
        # Get the list of monitor names
        monitors = self._percival_params.monitoring_channels
        for monitor in monitors:
            # Check for the board type
            bt = const.BoardTypes(monitor.Board_type)
            if bt != const.BoardTypes.prototype:
                settings = self._board_settings[bt].device_monitoring_settings(monitor.UART_address)
                mc = MonitoringChannel(self._txrx, monitor, settings)
                if mc._channel_ini.Channel_name is None or len(mc._channel_ini.Channel_name) == 0:
                    self._log.debug("Dropping %s as it has no channel name defined",
                                    (const.DeviceFamily(mc._channel_ini.Component_family_ID)).name)
                else:
                    self._log.debug("Adding %s [%s] to monitor set",
                                       (const.DeviceFamily(mc._channel_ini.Component_family_ID)).name,
                                       mc._channel_ini.Channel_name)
                    description, device = DeviceFactory[const.DeviceFamily(mc._channel_ini.Component_family_ID)]
                    self._monitors[mc._channel_ini.Channel_name] = device(mc._channel_ini.Channel_name, mc)

        # Readback the control settings
        self._board_settings[const.BoardTypes.left].readback_control_settings()
        self._board_settings[const.BoardTypes.bottom].readback_control_settings()
        self._board_settings[const.BoardTypes.carrier].readback_control_settings()
        self._board_settings[const.BoardTypes.plugin].readback_control_settings()
        # Get the list of control names
        controls = self._percival_params.control_channels
        for control in controls:
            # Check for the board type
            bt = const.BoardTypes(control.Board_type)
            if bt != const.BoardTypes.prototype:
                settings = self._board_settings[bt].device_control_settings(control.UART_address)
                cc = ControlChannel(self._txrx, control, settings)
                if cc._channel_ini.Channel_name is None or len(cc._channel_ini.Channel_name) == 0:
                    self._log.debug("Dropping %s as it has no channel name defined",
                                    (const.DeviceFamily(cc._channel_ini.Component_family_ID)).name)
                else:
                    self._log.debug("Adding %s [%s] to control set",
                                       (const.DeviceFamily(cc._channel_ini.Component_family_ID)).name,
                                       cc._channel_ini.Channel_name)
                    description, device = DeviceFactory[const.DeviceFamily(cc._channel_ini.Component_family_ID)]
                    self._controls[cc._channel_ini.Channel_name] = device(cc._channel_ini.Channel_name, cc)

        # Load the sensor DACs from the ini file
        sensor_dacs = self._percival_params.sensor_dac_channels
        for dac in sensor_dacs:
            self._sensor.add_dac(dac)

        # Load in control groups from the ini file
        self._control_groups = Group(self._percival_params.control_group_params)

        # Load in control groups from the ini file
        self._monitor_groups = Group(self._percival_params.monitor_group_params)

    def load_system_settings(self, system_settings_ini):
        self._log.debug("Loading system settings with config: %s", system_settings_ini)
        self._percival_params.load_system_settings_ini(system_settings_ini)
        self._system_settings.load_ini(self._percival_params.system_settings_params)

    def load_chip_readout_settings(self, chip_readout_settings_ini):
        self._log.debug("Loading chip readout settings with config: %s", chip_readout_settings_ini)
        self._percival_params.load_chip_readout_settings_ini(chip_readout_settings_ini)
        self._chip_readout_settings.load_ini(self._percival_params.chip_readout_settings_params)

    def load_clock_settings(self, clock_settings_ini):
        self._log.debug("Loading clock settings with config: %s", clock_settings_ini)
        self._percival_params.load_clock_settings_ini(clock_settings_ini)
        self._clock_settings.load_ini(self._percival_params.clock_settings_params)

    def load_sensor_configuration(self, sensor_config_ini):
        self._log.debug("Loading sensor configuration with config: %s", sensor_config_ini)
        self._percival_params.load_sensor_configuration_params(sensor_config_ini)

    def load_control_groups(self, control_groups_ini):
        self._log.debug("Loading control groups with config: %s", control_groups_ini)
        self._percival_params.load_control_group_ini(control_groups_ini)
        self._control_groups = Group(self._percival_params.control_group_params)

    def load_monitor_groups(self, monitor_groups_ini):
        self._log.debug("Loading monitor groups with config: %s", monitor_groups_ini)
        self._percival_params.load_monitor_group_ini(monitor_groups_ini)
        self._monitor_groups = Group(self._percival_params.monitor_group_params)

    def load_setpoints(self, setpoint_ini):
        self._log.debug("Loading set-points with config: %s", setpoint_ini)
        self._percival_params.load_setpoint_group_ini(setpoint_ini)
        self._setpoint_control.load_ini(self._percival_params.setpoint_params)

    def execute_command(self, command):
        """
        Log the execution of the command (use command trace)
        Apply the command trace to the detector
        Check for the specific command type and call the correct method
        :param command:
        :return:
        """
        response = {}
        # Check if the command is a PUT command
        if 'PUT' in command.command_type:
            # Log the trace information from the command object
            self._trace_log.info("Command {} [{}] executed".format(command.command_type, command.command_name))
            self._trace_log.info(command.format_trace)
            # Check if the command is a connection request to the DB
            if command.command_name in str(PercivalCommandNames.cmd_connect_db):
                # No parameters required for this command
                self.setup_db()
            elif command.command_name in str(PercivalCommandNames.cmd_load_config):
                # Parameter [config_type] one of setpoint, ctrl_group, mon_group, channels
                # Parameter [config] path to config file or the configuration contents
                if command.has_param('config_type'):
                    if command.has_param('config'):
                        config_type = command.get_param('config_type')
                        config_desc = command.get_param('config').replace('::', '=')
                        if 'setpoints' in config_type:
                            self.load_setpoints(config_desc)
                        elif 'control_groups' in config_type:
                            self.load_control_groups(config_desc)
                        elif 'monitor_groups' in config_type:
                            self.load_monitor_groups(config_desc)
                        elif 'system_settings' in config_type:
                            self.load_system_settings(config_desc)
                            self.download_system_settings()
                        elif 'chip_readout_settings' in config_type:
                            self.load_chip_readout_settings(config_desc)
                            self.download_chip_readout_settings()
                        elif 'clock_settings' in config_type:
                            self.load_clock_settings(config_desc)
                            self.download_clock_settings()
                    else:
                        raise PercivalDetectorError("No config provided (file or object)")
                else:
                    raise PercivalDetectorError("No config_type specified")
            elif command.command_name in str(PercivalCommandNames.cmd_set_channel):
                # Parameter [channel] is the name of the channel to apply to
                # Parameter [value] is the value to apply
                if command.has_param('channel'):
                    channel = command.get_param('channel')
                    if command.has_param('value'):
                        value = int(float(command.get_param('value')))
                        self.set_value(channel, value)
                    else:
                        raise PercivalDetectorError("No value supplied to set channel command")
                else:
                    raise PercivalDetectorError("No channel supplied for set channel command")
            elif command.command_name in str(PercivalCommandNames.cmd_apply_setpoint):
                # Parameter [setpoint] is the name of the setpoint to apply
                if command.has_param('setpoint'):
                    self._setpoint_control.apply_set_point(command.get_param('setpoint'))
            elif command.command_name in str(PercivalCommandNames.cmd_scan_setpoints):
                # Parameter [setpoints] is a list of setpoints to scan
                # Parameter [dwell] is the dwell time in ms at each point
                # Parameter [steps] is the number of steps between the points
                if command.has_param('setpoints'):
                    # Check there are at least two setpoints
                    setpoints = command.get_param('setpoints')
                    if len(setpoints) < 2:
                        raise PercivalDetectorError("Scanning requires two setpoints")
                    if command.has_param('dwell'):
                        dwell = int(command.get_param('dwell'))
                        if command.has_param('steps'):
                            steps = int(command.get_param('steps'))
                            self._setpoint_control.scan_set_points(setpoints, steps, dwell)
                        else:
                            raise PercivalDetectorError("Number of scan steps required to scan")
                    else:
                        raise PercivalDetectorError("Dwell time (ms) required to scan")
                else:
                    raise PercivalDetectorError("No setpoints defined to scan between")
            elif command.command_name in str(PercivalCommandNames.cmd_update_monitors):
                # Force a read of the monitors.  This will result in values being written to db
                self.update_status()
            elif command.command_name in str(PercivalCommandNames.cmd_initialise_channels):
                # Initialise the channels on the Percival hardware
                self.initialize_channels()
            elif command.command_name in str(PercivalCommandNames.cmd_apply_sensor_dacs):
                # Apply the current set of sensor DAC values
                self.apply_sensor_dac_values()
            # Check if the command is a system_command
            elif command.command_name in str(PercivalCommandNames.cmd_system_command):
                # We expect a single parameter which is the command
                if command.has_param('name'):
                    # Execute the system command
                    self.system_command(command.get_param('name'))

        # Check if the command is a GET command
        elif 'GET' in command.command_type:
            # Request for reading information
            response = self.read(command.command_name)

        return response

    def download_configuration(self):
        self.load_configuration()
        self.load_channels()

    def initialize_channels(self):
        """
        Initialize all control devices that support the command.
        """
        for control in self._controls:
            self._controls[control].initialize()

    def set_global_monitoring(self, state=True):
        """
        Turn on or off global monitoring.  This sends two system commands; enable_global_monitoring and
        enable_device_level_safety_controls.
        It also sets the internal monitoring flag to either True or False.

        :param state: Turn global monitoring on (True) or off (False)
        :type state: bool
        """
        if state:
            self._sys_cmd.send_command(const.SystemCmd.enable_global_monitoring)
            self._sys_cmd.send_command(const.SystemCmd.enable_device_level_safety_controls)
            self._global_monitoring = True
        else:
            self._global_monitoring = False
            self._sys_cmd.send_command(const.SystemCmd.disable_global_monitoring)
            self._sys_cmd.send_command(const.SystemCmd.disable_device_level_safety_controls)

    def system_command(self, cmd):
        """
        Send a system command.

        :param cmd: System command to send
        :type cmd: str
        """
        self._sys_cmd.send_command(const.SystemCmd[cmd])

    def initialize(self, device):
        """
        Initialize a control device.

        :param device: Name of device to set the value of
        :type device: str
        """
        if device in self._controls:
            self._controls[device].initialize()

    def set_value(self, device, value, timeout=0.1):
        """
        Set the value of a control device.

        :param device: Name of device to set the value of
        :type device: str
        :param value: Value to set
        :type value: int
        :param timeout: Timeout for the set operation
        :type timeout: double
        """
        self._log.info("Setting %s to %d", device, value)
        if device in self._controls:
            self._controls[device].set_value(value, timeout)

        elif device in self._sensor.dacs:
            self._sensor.set_dac(device, value)

        elif device in self._control_groups.group_names:
            # A group name has been specified for the set value
            # Get the list of channels and apply the value for each one
            for channel in self._control_groups.get_channels(device):
                self._controls[channel].set_value(value, timeout)

        else:
            self._log.info("Device  %s not found", device)
            raise PercivalDetectorError("Cannot set value, device {} does not exist".format(device))

    def apply_sensor_dac_values(self):
        self._sensor.apply_dac_values()

    def read(self, parameter):
        """
        Read a parameter from the detector.
        The parameters currently include:
        - list of control devices
        - list of monitor devices
        - hardware description
        - status of all monitors
        - status of a specific monitor

        :param parameter: Name of parameter to read status of
        :type parameter: str
        :returns: Status report of the requested parameter
        :rtype: dict
        """
        self._log.debug("Reading data %s", parameter)

        # First check to see if parameter is a keyword
        if parameter == "driver":
            reply = {"username": self._username,
                     "start_time": self._start_time.strftime("%B %d, %Y %H:%M:%S"),
                     "up_time": str(datetime.now() - self._start_time),
                     "influx_db": self._db.get_status(),
                     "hardware": self._txrx.get_status()
                     }

        elif parameter == "groups":
            # Construct dictionaries of control and monitor groups
            reply = {"control_groups": {"group_names": []},
                     "monitor_groups": {"group_names": []}
                     }
            ctrl_group_names = self._control_groups.group_names
            for ctrl_group in ctrl_group_names:
                reply["control_groups"]["group_names"].append(ctrl_group)
                reply["control_groups"][ctrl_group] = {
                    "description": self._control_groups.get_description(ctrl_group),
                    "channels": self._control_groups.get_channels(ctrl_group)
                }
            monitor_group_names = self._monitor_groups.group_names
            for monitor_group in monitor_group_names:
                reply["monitor_groups"]["group_names"].append(monitor_group)
                reply["monitor_groups"][monitor_group] = {
                    "description": self._monitor_groups.get_description(monitor_group),
                    "channels": self._monitor_groups.get_channels(monitor_group)
                }

        elif parameter == "commands":
            reply = {}
            reply["commands"] = []
            for name, tmp in const.SystemCmd.__members__.items():
                reply["commands"].append(name)

        elif parameter == "setpoints":
            reply = {}
            reply["setpoints"] = []
            for name in self._setpoint_control.set_points:
                reply["setpoints"].append(name)

        elif parameter == "controls":
            reply = {}
            reply["controls"] = []
            for control in self._controls:
                reply["controls"].append(control)
                reply[control] = self._controls[control].device

        elif parameter == "monitors":
            reply = {}
            reply["monitors"] = []
            for monitor in self._monitors:
                reply["monitors"].append(monitor)
                reply[monitor] = self._monitors[monitor].device

        elif parameter == "boards":
            reply = {
                "boards": [const.BoardTypes.carrier.name,
                           const.BoardTypes.left.name,
                           const.BoardTypes.bottom.name,
                           const.BoardTypes.plugin.name
                          ],
                const.BoardTypes.carrier.name: {
                    "name":           self._percival_params.board_name(const.BoardTypes.carrier),
                    "type":           self._percival_params.board_type(const.BoardTypes.carrier).name,
                    "controls_count": self._percival_params.control_channels_count(const.BoardTypes.carrier),
                    "monitors_count": self._percival_params.monitoring_channels_count(const.BoardTypes.carrier)
                },
                const.BoardTypes.left.name: {
                    "name": self._percival_params.board_name(const.BoardTypes.left),
                    "type": self._percival_params.board_type(const.BoardTypes.left).name,
                    "controls_count": self._percival_params.control_channels_count(const.BoardTypes.left),
                    "monitors_count": self._percival_params.monitoring_channels_count(const.BoardTypes.left)
                },
                const.BoardTypes.bottom.name: {
                    "name": self._percival_params.board_name(const.BoardTypes.bottom),
                    "type": self._percival_params.board_type(const.BoardTypes.bottom).name,
                    "controls_count": self._percival_params.control_channels_count(const.BoardTypes.bottom),
                    "monitors_count": self._percival_params.monitoring_channels_count(const.BoardTypes.bottom)
                },
                const.BoardTypes.plugin.name: {
                    "name": self._percival_params.board_name(const.BoardTypes.plugin),
                    "type": self._percival_params.board_type(const.BoardTypes.plugin).name,
                    "controls_count": self._percival_params.control_channels_count(const.BoardTypes.plugin),
                    "monitors_count": self._percival_params.monitoring_channels_count(const.BoardTypes.plugin)
                },
            }

        elif parameter == "status":
            reply = {}
            for monitor in self._monitors:
                reply[monitor] = self._monitors[monitor].status

        # Check to see if the parameter is a monitoring device that we own
        elif parameter in self._monitors:
            reply = { parameter: self._monitors[parameter].status }

        else:
            reply = { "error": "Parameter not found" }

        return reply

    def update_status(self):
        """
        Update the status of the monitor devices.
        The values shortcut is read out from the hardware and the status of all
        monitors is updated appropriately.
        """
        self._log.debug("Update status callback called")
        status_msg = {}
        if self._global_monitoring:
            response = self._board_values[const.BoardTypes.carrier].read_values()
            #time_now = datetime.today() - timedelta(hours=1)
            time_now = datetime.utcnow()
            self._log.debug(response)
            read_maps = generate_register_maps(response)
            self._log.debug(read_maps)

            readback_block = BoardValueRegisters[const.BoardTypes.carrier]
            for addr, value in response:  # pylint: disable=W0612
                offset = addr - readback_block.start_address
                name = self._percival_params.monitoring_channel_name_by_index_and_board_type(offset, const.BoardTypes.carrier)
                if name in self._monitors:
                    self._monitors[name].update(read_maps[offset])
                    status_msg[name] = self._monitors[name].status
                    if self._db:
                        self._db.log_point(time_now, name, self._monitors[name].status)

            self._log.debug("Status: %s", status_msg)
        return status_msg
