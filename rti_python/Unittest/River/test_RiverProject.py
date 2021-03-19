import os
import h5py
from rti_python.River.RiverProject import RiverProject
from rti_python.River.RiverProjectMeta import RiverProjectMeta
from rti_python.Utilities.config import RtiConfig

rti_config = RtiConfig()
rti_config.init_river_project_config()


def test_constructor():
    project = RiverProject(rti_config, "Project111", os.path.join(rti_config.config['RIVER']['output_dir'], "Project111.hdf5"))

    assert "Project111" == project.name
    assert os.path.join(rti_config.config['RIVER']['output_dir'], "Project111.hdf5") == project.file_path


def test_set_values():
    project = RiverProject(rti_config, "Project112", os.path.join(rti_config.config['RIVER']['output_dir'], "Project112.hdf5"))
    project.adcp_serial_num = "0001"
    project.firmware_ver = "0.0.1.2"
    project.draft_transducer = 11.11
    project.magnetic_declination = 1.234
    project.software_ver = "1.2.3.4"
    project.ident_of_crew = "Jon and Bob"
    project.station_name = "River1"
    project.station_id = "111R1"
    project.water_temp = 1.34
    project.percentage_discharged_measured = 23.4
    project.channel_width = 1234
    project.cross_section_area = 34
    project.comments = "everything is good"

    assert "0001" == project.adcp_serial_num
    assert "0.0.1.2" == project.firmware_ver
    assert 11.11 == project.draft_transducer
    assert 1.234 == project.magnetic_declination
    assert "1.2.3.4" == project.software_ver
    assert "Jon and Bob" == project.ident_of_crew
    assert "River1" == project.station_name
    assert "111R1" == project.station_id
    assert 1.34 == project.water_temp
    assert 23.4 == project.percentage_discharged_measured
    assert 1234 == project.channel_width
    assert 34 == project.cross_section_area
    assert "everything is good" == project.comments


def test_to_dict():
    project = RiverProject(rti_config, "Project113", os.path.join(rti_config.config['RIVER']['output_dir'], "Project113.hdf5"))
    project.adcp_serial_num = "0001"
    project.firmware_ver = "0.0.1.2"
    project.draft_transducer = 11.11
    project.magnetic_declination = 1.234
    project.software_ver = "1.2.3.4"
    project.ident_of_crew = "Jon and Bob"
    project.station_name = "River1"
    project.station_id = "111R1"
    project.water_temp = 1.34
    project.percentage_discharged_measured = 23.4
    project.channel_width = 1234
    project.cross_section_area = 34
    project.comments = "everything is good"

    project_dict = project.to_dict()

    assert "Project113" == project_dict[RiverProjectMeta.PROJECT_NAME]
    assert "0001" == project_dict[RiverProjectMeta.PROJECT_SERIAL_NUM]
    assert "0.0.1.2" == project_dict[RiverProjectMeta.PROJECT_FIRMWARE_VER]
    assert 11.11 == project_dict[RiverProjectMeta.PROJECT_DRAFT_XDCR]
    assert 1.234 == project_dict[RiverProjectMeta.PROJECT_MAG_DECL]
    assert "1.2.3.4" == project_dict[RiverProjectMeta.PROJECT_SOFT_VER]
    assert "Jon and Bob" == project_dict[RiverProjectMeta.PROJECT_IDENT_CREW]
    assert "River1" == project_dict[RiverProjectMeta.PROJECT_STATION_NAME]
    assert "111R1" == project_dict[RiverProjectMeta.PROJECT_STATION_ID]
    assert 1.34 == project_dict[RiverProjectMeta.PROJECT_WATER_TEMP]
    assert 23.4 == project_dict[RiverProjectMeta.PROJECT_PCT_DISCHARGED_MEASURED]
    assert 1234 == project_dict[RiverProjectMeta.PROJECT_CHANNEL_WIDTH]
    assert 34 == project_dict[RiverProjectMeta.PROJECT_CROSS_SEC_AREA]
    assert "everything is good" == project_dict[RiverProjectMeta.PROJECT_COMMENTS]


def test_save_project_meta():
    project = RiverProject(rti_config, "Project114", os.path.join(rti_config.config['RIVER']['output_dir'], "Project114.hdf5"))
    project.adcp_serial_num = "0001"
    project.firmware_ver = "0.0.1.2"
    project.draft_transducer = 11.11
    project.magnetic_declination = 1.234
    project.software_ver = "1.2.3.4"
    project.ident_of_crew = "Jon and Bob"
    project.station_name = "River1"
    project.station_id = "111R1"
    project.water_temp = 1.34
    project.percentage_discharged_measured = 23.4
    project.channel_width = 1234
    project.cross_section_area = 34
    project.comments = "everything is good"

    project.save_project_meta()

    with h5py.File(project.file_path, "a") as prj_file:
        assert "Project114" == prj_file.attrs[RiverProjectMeta.PROJECT_NAME]
        assert "0001" == prj_file.attrs[RiverProjectMeta.PROJECT_SERIAL_NUM]
        assert "0.0.1.2" == prj_file.attrs[RiverProjectMeta.PROJECT_FIRMWARE_VER]
        assert 11.11 == prj_file.attrs[RiverProjectMeta.PROJECT_DRAFT_XDCR]
        assert 1.234 == prj_file.attrs[RiverProjectMeta.PROJECT_MAG_DECL]
        assert "1.2.3.4" == prj_file.attrs[RiverProjectMeta.PROJECT_SOFT_VER]
        assert "Jon and Bob" == prj_file.attrs[RiverProjectMeta.PROJECT_IDENT_CREW]
        assert "River1" == prj_file.attrs[RiverProjectMeta.PROJECT_STATION_NAME]
        assert "111R1" == prj_file.attrs[RiverProjectMeta.PROJECT_STATION_ID]
        assert 1.34 == prj_file.attrs[RiverProjectMeta.PROJECT_WATER_TEMP]
        assert 23.4 == prj_file.attrs[RiverProjectMeta.PROJECT_PCT_DISCHARGED_MEASURED]
        assert 1234 == prj_file.attrs[RiverProjectMeta.PROJECT_CHANNEL_WIDTH]
        assert 34 == prj_file.attrs[RiverProjectMeta.PROJECT_CROSS_SEC_AREA]
        assert "everything is good" == prj_file.attrs[RiverProjectMeta.PROJECT_COMMENTS]
