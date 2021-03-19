import h5py
import datetime
from rti_python.Utilities.config import RtiConfig
from rti_python.River.RiverProjectMeta import RiverProjectMeta


class RiverProject:

    VERSION = 1.0

    def __init__(self, rti_config: RtiConfig, project_name: str, file_path: str):
        self.rti_config = rti_config
        self.file_path = file_path
        self.datetime = datetime.datetime.now()
        self.adcp_serial_num = ""
        self.firmware_ver = ""
        self.draft_transducer = 0.0
        self.software_ver = ""
        self.ident_of_crew = ""
        self.station_name = ""
        self.station_id = ""
        self.water_temp = ""
        self.channel_width = 0.0
        self.cross_section_area = 0.0
        self.comments = ""
        self.percentage_discharged_measured = 0.0
        self.magnetic_declination = 0.0
        self.transect = []
        self.moving_bed_test = []

    def to_dict(self) -> {}:
        project = {
            RiverProjectMeta.PROJECT_VERSION: self.version,
            RiverProjectMeta.PROJECT_NAME: self.name,
            RiverProjectMeta.PROJECT_FILE_PATH: self.file_path,
            RiverProjectMeta.PROJECT_DATETIME: self.datetime.isoformat(),
            RiverProjectMeta.PROJECT_SERIAL_NUM: self.adcp_serial_num,
            RiverProjectMeta.PROJECT_FIRMWARE_VER: self.firmware_ver,
            RiverProjectMeta.PROJECT_DRAFT_XDCR: self.draft_transducer,
            RiverProjectMeta.PROJECT_MAG_DECL: self.magnetic_declination,
            RiverProjectMeta.PROJECT_SOFT_VER: self.software_ver,
            RiverProjectMeta.PROJECT_IDENT_CREW: self.ident_of_crew,
            RiverProjectMeta.PROJECT_STATION_NAME: self.station_name,
            RiverProjectMeta.PROJECT_STATION_ID: self.station_id,
            RiverProjectMeta.PROJECT_WATER_TEMP: self.water_temp,
            RiverProjectMeta.PROJECT_PCT_DISCHARGED_MEASURED: self.percentage_discharged_measured,
            RiverProjectMeta.PROJECT_CHANNEL_WIDTH: self.channel_width,
            RiverProjectMeta.PROJECT_CROSS_SEC_AREA: self.cross_section_area,
            RiverProjectMeta.PROJECT_COMMENTS: self.comments
        }

        return project

    def save_project_meta(self):
        # Create the H5DF file object to verify subgroups exist
        with h5py.File(self.file_path, "a") as prj_file:
            prj_file.attrs[RiverProjectMeta.PROJECT_NAME] = self.name
            prj_file.attrs[RiverProjectMeta.PROJECT_FILE_PATH] = self.file_path
            prj_file.attrs[RiverProjectMeta.PROJECT_VERSION] = self.version
            prj_file.attrs[RiverProjectMeta.PROJECT_DATETIME] = self.datetime.isoformat()
            prj_file.attrs[RiverProjectMeta.PROJECT_SERIAL_NUM] = self.adcp_serial_num
            prj_file.attrs[RiverProjectMeta.PROJECT_FIRMWARE_VER] = self.firmware_ver
            prj_file.attrs[RiverProjectMeta.PROJECT_DRAFT_XDCR] = self.draft_transducer
            prj_file.attrs[RiverProjectMeta.PROJECT_MAG_DECL] = self.magnetic_declination
            prj_file.attrs[RiverProjectMeta.PROJECT_SOFT_VER] = self.software_ver
            prj_file.attrs[RiverProjectMeta.PROJECT_IDENT_CREW] = self.ident_of_crew
            prj_file.attrs[RiverProjectMeta.PROJECT_STATION_NAME] = self.station_name
            prj_file.attrs[RiverProjectMeta.PROJECT_STATION_ID] = self.station_id
            prj_file.attrs[RiverProjectMeta.PROJECT_WATER_TEMP] = self.water_temp
            prj_file.attrs[RiverProjectMeta.PROJECT_PCT_DISCHARGED_MEASURED] = self.percentage_discharged_measured
            prj_file.attrs[RiverProjectMeta.PROJECT_CHANNEL_WIDTH] = self.channel_width
            prj_file.attrs[RiverProjectMeta.PROJECT_CROSS_SEC_AREA] = self.cross_section_area
            prj_file.attrs[RiverProjectMeta.PROJECT_COMMENTS] = self.comments





