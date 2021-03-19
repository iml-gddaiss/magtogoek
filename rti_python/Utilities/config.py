import configparser
import os
import logging
import socket
import rti_python.Comm.adcp_serial_port as adcp_serial


class RtiConfig:
    """
    Read and Write a configuration.
    """

    def __init__(self, file_path='config.ini'):
        # File path to configuration
        self.config_file_path = file_path

        # Create a default config if no config exist
        if not os.path.exists('config.ini'):
            self.create_default_config()

        # Current configuration
        self.config = self.read()

    def write(self):
        """
        Write the configuration.
        :return:
        """
        # Load the configuration file
        try:
            with open(self.config_file_path, 'w') as f:
                self.config.write(f)
        except Exception as e:
            logging.error("Error writing configuration. " + str(e))

    def read(self):
        """
        Read latest configuration in the file.
        :return: Configuration
        """
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file_path)
        return self.config

    def create_default_config(self):
        self.config = configparser.ConfigParser()

        # Write the default config
        self.write()

    def init_terminal_config(self):
        """
        Default configuration for the terminal.
        Call this to add the terminal sections to the config.
        You can later add more to this section here or in your own code.
        :return:
        """
        ports = adcp_serial.get_serial_ports()

        # Verify the section exist
        if 'Comm' not in self.config:
            self.config['Comm'] = {}
            if ports:
                self.config['Comm']['Port'] = ports[0]
            else:
                self.config['Comm']['Port'] = ''
            self.config['Comm']['Baud'] = '115200'
            self.config['Comm']['output_dir'] = os.path.expanduser('~')

            self.write()

        # Verify each value exist
        if not self.config.has_option('Comm', 'Port'):
            if ports:
                self.config['Comm']['Port'] = ports[0]
            else:
                self.config['Comm']['Port'] = ''
            self.write()

        if not self.config.has_option('Comm', 'Baud'):
            self.config['Comm']['Baud'] = '115200'
            self.write()

        if not self.config.has_option('Comm', 'output_dir'):
            self.config['Comm']['output_dir'] = os.path.expanduser('~')
            self.write()

    def init_waves_config(self):
        """
        Default configuration for a waves setup.
        Call this to add the waves sections to the config.
        You can later add more to this section here or in your own code.
        :return:
        """

        # Verify the section exist
        if 'Waves' not in self.config:
            self.config['Waves'] = {}
            self.config['Waves']['output_dir'] = os.path.expanduser('~')
            self.config['Waves']['4b_vert_pair'] = 'True'
            self.config['Waves']['ens_in_burst'] = '1024'
            self.config['Waves']['selected_bin_1'] = '8'
            self.config['Waves']['selected_bin_2'] = '9'
            self.config['Waves']['selected_bin_3'] = '10'
            self.config['Waves']['corr_thresh'] = '0.25'
            self.config['Waves']['height_source'] = 'vertical'
            self.config['Waves']['pressure_sensor_height'] = '30.0'
            self.config['Waves']['pressure_sensor_offset'] = '0.0'
            self.config['Waves']['latitude'] = '0.0'
            self.config['Waves']['longitude'] = '0.0'
            self.config['Waves']['replace_pressure_with_vertical'] = 'False'
            self.config['Waves']['data_timeout'] = '30'
            self.write()

        # Verify each value exist
        if not self.config.has_option('Waves', 'output_dir'):
            self.config['Waves']['output_dir'] = os.path.expanduser('~')
            self.write()

        if not self.config.has_option('Waves', 'ens_in_burst'):
            self.config['Waves']['ens_in_burst'] = '1024'
            self.write()

        if not self.config.has_option('Waves', 'selected_bin_1'):
            self.config['Waves']['selected_bin_1'] = '8'
            self.write()

        if not self.config.has_option('Waves', 'selected_bin_2'):
            self.config['Waves']['selected_bin_2'] = '9'
            self.write()

        if not self.config.has_option('Waves', 'selected_bin_3'):
            self.config['Waves']['selected_bin_3'] = '10'
            self.write()

        if not self.config.has_option('Waves', 'corr_thresh'):
            self.config['Waves']['corr_thresh'] = '0.25'
            self.write()

        if not self.config.has_option('Waves', 'height_source'):
            self.config['Waves']['height_source'] = 'vertical'
            self.write()

        if not self.config.has_option('Waves', 'pressure_sensor_height'):
            self.config['Waves']['pressure_sensor_height'] = '30.0'
            self.write()

        if not self.config.has_option('Waves', 'pressure_sensor_offset'):
            self.config['Waves']['pressure_sensor_offset'] = '0.0'
            self.write()

        if not self.config.has_option('Waves', 'latitude'):
            self.config['Waves']['latitude'] = '0.0'
            self.write()

        if not self.config.has_option('Waves', 'longitude'):
            self.config['Waves']['longitude'] = '0.0'
            self.write()

        if not self.config.has_option('Waves', '4b_vert_pair'):
            self.config['Waves']['4b_vert_pair'] = 'True'
            self.write()

        if not self.config.has_option('Waves', 'replace_pressure_with_vertical'):
            self.config['Waves']['replace_pressure_with_vertical'] = 'False'
            self.write()

        if not self.config.has_option('Waves', 'data_timeout'):
            self.config['Waves']['data_timeout'] = '30'
            self.write()

    def init_average_waves_config(self):
        """
        Default configuration for the Average Waves Column.
        Call this to add the Average Waves Column (AWC) sections to the config.
        You can later add more to this section here or in your own code.
        :return:
        """

        # Verify the section exist
        if 'AWC' not in self.config:
            self.config['AWC'] = {}
            self.config['AWC']['num_ensembles'] = '600'
            self.config['AWC']['output_dir'] = os.path.expanduser('~')
            self.config['AWC']['max_file_size'] = '16'
            self.config['AWC']['csv_max_hours'] = '24'
            self.write()

        # Verify each value exist
        if not self.config.has_option('AWC', 'num_ensembles'):
            self.config['AWC']['num_ensembles'] = '600'
            self.write()

        if not self.config.has_option('AWC', 'output_dir'):
            self.config['AWC']['output_dir'] = os.path.expanduser('~')
            self.write()

        if not self.config.has_option('AWC', 'max_file_size'):
            self.config['AWC']['max_file_size'] = '16'
            self.write()

        if not self.config.has_option('AWC', 'csv_max_hours'):
            self.config['AWC']['csv_max_hours'] = '24'
            self.write()

    def init_plot_server_config(self):
        """
        Default configuration for the Bokeh Plot server.
        Call this to add the Bokeh Plot Server (PLOT) sections to the config.
        You can later add more to this section here or in your own code.
        :return:
        """

        # Verify the section exist
        if 'PLOT' not in self.config:
            self.config['PLOT'] = {}
            self.config['PLOT']['IP'] = RtiConfig.get_ip()
            self.config['PLOT']['PORT'] = '5001'
            self.config['PLOT']['LIVE'] = 'True'
            self.config['PLOT']['RATE'] = '2500'
            self.config['PLOT']["BUFF_SIZE"] = '1000'
            self.config['PLOT']["MAX_POINTS"] = '4096'
            self.write()

        # Verify each value exist
        if not self.config.has_option('PLOT', 'IP'):
            self.config['PLOT']['IP'] = RtiConfig.get_ip()
            self.write()

        if not self.config.has_option('PLOT', 'PORT'):
            self.config['PLOT']['PORT'] = '5001'
            self.write()

        if not self.config.has_option('PLOT', 'LIVE'):
            self.config['PLOT']['LIVE'] = 'True'
            self.write()

        if not self.config.has_option('PLOT', 'RATE'):
            self.config['PLOT']['RATE'] = '2500'
            self.write()

        if not self.config.has_option('PLOT', 'BUFF_SIZE'):
            self.config['PLOT']['BUFF_SIZE'] = '1000'
            self.write()

        if not self.config.has_option('PLOT', 'MAX_POINTS'):
            self.config['PLOT']['MAX_POINTS'] = '4096'
            self.write()

    def init_timeseries_plot_config(self):
        """
        Default configuration for the Time Series Plot.
        Call this to add the Time Series (TIMESERIES) sections to the config.
        You can later add more to this section here or in your own code.
        :return:
        """

        # Verify the section exist
        if 'TIMESERIES' not in self.config:
            self.config['TIMESERIES'] = {}
            self.config['TIMESERIES']['IP'] = RtiConfig.get_ip()
            self.config['TIMESERIES']['PORT'] = '4241'
            self.config['TIMESERIES']['IS_BOAT_SPEED'] = 'True'
            self.config['TIMESERIES']['IS_BOAT_DIR'] = 'False'
            self.config['TIMESERIES']['IS_HEADING'] = 'False'
            self.config['TIMESERIES']['IS_PITCH'] = 'False'
            self.config['TIMESERIES']['IS_ROLL'] = 'False'
            self.config['TIMESERIES']['IS_TEMPERATURE'] = 'False'
            self.config['TIMESERIES']["IS_GNSS_QUAL"] = 'False'
            self.config['TIMESERIES']["IS_GNSS_HDOP"] = 'False'
            self.config['TIMESERIES']['IS_NUM_SATS'] = 'False'
            self.config['TIMESERIES']['IS_WATER_SPEED'] = 'False'
            self.config['TIMESERIES']["IS_WATER_DIR"] = 'False'
            self.config['TIMESERIES']["IS_VTG_SPEED"] = 'False'
            self.config['TIMESERIES']["MAX_ENS"] = '1024'
            self.write()

        # Verify each value exist
        if not self.config.has_option('TIMESERIES', 'IP'):
            self.config['TIMESERIES']['IP'] = RtiConfig.get_ip()
            self.write()

        if not self.config.has_option('TIMESERIES', 'PORT'):
            self.config['TIMESERIES']['PORT'] = '4241'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_BOAT_SPEED'):
            self.config['TIMESERIES']['PORT'] = 'True'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_BOAT_DIR'):
            self.config['TIMESERIES']['IS_BOAT_DIR'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_HEADING'):
            self.config['TIMESERIES']['IS_HEADING'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_PITCH'):
            self.config['TIMESERIES']['IS_PITCH'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_ROLL'):
            self.config['TIMESERIES']['IS_ROLL'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_TEMPERATURE'):
            self.config['TIMESERIES']['IS_TEMPERATURE'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_GNSS_QUAL'):
            self.config['TIMESERIES']['IS_GNSS_QUAL'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_GNSS_HDOP'):
            self.config['TIMESERIES']['IS_GNSS_HDOP'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_NUM_SATS'):
            self.config['TIMESERIES']['IS_NUM_SATS'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_WATER_SPEED'):
            self.config['TIMESERIES']['IS_WATER_SPEED'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_WATER_DIR'):
            self.config['TIMESERIES']['IS_WATER_DIR'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'IS_VTG_SPEED'):
            self.config['TIMESERIES']['IS_VTG_SPEED'] = 'False'
            self.write()

        if not self.config.has_option('TIMESERIES', 'MAX_ENS'):
            self.config['TIMESERIES']['MAX_ENS'] = '1024'
            self.write()

    def init_river_project_config(self):
        """
        Default configuration for the terminal.
        Call this to add the terminal sections to the config.
        You can later add more to this section here or in your own code.
        :return:
        """
        # Verify the section exist
        if 'RIVER' not in self.config:
            self.config['RIVER'] = {}
            self.config['RIVER']['output_dir'] = os.path.expanduser('~')
            self.config['RIVER']['auto_save_raw'] = 'True'
            self.write()

        # Verify each value exist
        if not self.config.has_option('RIVER', 'output_dir'):
            self.config['RIVER']['output_dir'] = os.path.expanduser('~')
            self.write()

        # Verify each value exist
        if not self.config.has_option('RIVER', 'auto_save_raw'):
            self.config['RIVER']['auto_save_raw'] = 'True'
            self.write()

    @staticmethod
    def get_ip():
        """
        Get the computers IP address.
        :return:
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    @staticmethod
    def bool_to_str(bool_val: bool):
        if bool_val:
            return "True"

        return "False"
