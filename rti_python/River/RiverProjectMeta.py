class RiverProjectMeta:
    """
    Groups are named using CamelCase, datasets are all lower case with underscores
    """
    # Subgroups
    SUBGROUP_TRANSECT = 'Transects'                     # Transect folder to hold all transects
    SUBGROUP_MBT = 'MovingBedTest'                      # Moving Bed Test Subgroup

    MANAGER_VERSION = "manager_version"                 # River Project Manager Version

    # All META data entries for a project dictonary
    PROJECT_VERSION = "project_version"                 # Project version to keep track of changes to format
    PROJECT_FILE_PATH = 'project_path'                  # Local File path to HDF5
    PROJECT_NAME = 'project_name'                       # Project Name
    PROJECT_DATETIME = 'datetime'                       # Project Date Time
    PROJECT_SERIAL_NUM = 'serial_num'                   # ADCP Serial Number
    PROJECT_FIRMWARE_VER = 'firmware_ver'               # Firmware Version
    PROJECT_DRAFT_XDCR = 'draft_xdcr'                   # Draft of Transducer
    PROJECT_MAG_DECL = 'mag_declination'                # Magnetic Declination
    PROJECT_SOFT_VER = 'software_ver'                   # Software Version
    PROJECT_IDENT_CREW = 'ident_crew'                   # Identification of Crew
    PROJECT_STATION_NAME = 'station_name'               # Station Name
    PROJECT_STATION_ID = 'station_id'                   # Station ID
    PROJECT_WATER_TEMP = 'water_temp'                   # Water Temperature
    PROJECT_PCT_DISCHARGED_MEASURED = 'pct_discharge_measured'  # Percent Discharge Measured
    PROJECT_CHANNEL_WIDTH = 'channel_width'             # Channel Width
    PROJECT_CROSS_SEC_AREA = 'cross_section_area'       # Cross Section Area
    PROJECT_COMMENTS = 'comments'                       # Project comments

    TRANSECT_VERSION = 'transect_version'               # Transect Version
    TRANSECT_STATION_NAME = 'station_name'              # Transect Station name
    TRANSECT_STATION_INFO = 'station_info'              # Transect Station Info
    TRANSECT_STATION_COMMENTS = 'station_comments'      # Transection Station comments