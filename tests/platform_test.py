import pytest
from magtogoek.platforms import load_platform_metadata

LOAD_FILE = "files/platform_test/test_platforms.json"
LON_LAT_PARSING_FILE = "files/platform_test/test_lon_lat_parsing.json"


def test_load_platform_metadata():
    platform_metadata = load_platform_metadata(platform_file=LOAD_FILE, platform_id="IML6_2017")

    assert platform_metadata.platform.platform_name == "IML-6"
    assert platform_metadata.platform.platform_type == "buoy"
    assert platform_metadata.platform.sounding == 100
    assert platform_metadata.platform.longitude == -60
    assert platform_metadata.platform.latitude == 50
    assert platform_metadata.platform.description == "This is a description of the platform."

    assert platform_metadata.buoy_specs.type == "MTE"
    assert platform_metadata.buoy_specs.model == "Viking"
    assert platform_metadata.buoy_specs.height == "4.5 m"
    assert platform_metadata.buoy_specs.diameter == "2.1 m"
    assert platform_metadata.buoy_specs.weight == "1000 kg"
    assert platform_metadata.buoy_specs.description == "bouée noire (partie immergée) avec jaune."

    assert "CTD_01" in platform_metadata.instruments

    assert platform_metadata.instruments["ADCP_01"].sensor_type == "adcp"
    assert platform_metadata.instruments["ADCP_01"].sensor_depth == 5
    assert platform_metadata.instruments["ADCP_01"].sensor_height is None
    assert platform_metadata.instruments["ADCP_01"].serial_number == "Serial_test_platform"
    assert platform_metadata.instruments["ADCP_01"].manufacturer == "Teledyne RD Instruments Inc."
    assert platform_metadata.instruments["ADCP_01"].model == "WorkHorse"
    assert platform_metadata.instruments["ADCP_01"].firmware_version == "sensor_firmware_test"
    assert platform_metadata.instruments["ADCP_01"].chief_scientist == "Peter Galbraith"
    assert platform_metadata.instruments["ADCP_01"].comments == "The model and serial number are the same for the temperature and pressure sensors as the ADCP."

    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].description == "temperature_description"
    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].comments == "temperature_comments"

    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].calibration.date == "calibration_date"
    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].calibration.number_of_coefficients == "calibration_noc"
    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].calibration.coefficients == "calibration_coeff"
    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].calibration.calibration_equation == "calibration_eq"
    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].calibration.calibration_units == "calibration_units"
    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].calibration.archiving_units == "calibration_arch_units"
    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].calibration.conversion_factor == "calibration_conv_facto"
    assert platform_metadata.instruments["ADCP_01"].sensors["temperature"].calibration.comments == "calibration_comments"

@pytest.mark.parametrize(
    "platform_id, longitude, latitude",
    [
        ("p1", 60.5555, -50.555555),
        ("p2", 60.555555, 50.555555),
        ("p3", -60.555555, -50.555555),
        ("p4", None , None)
    ]
)
def test_platform_lon_lat_parsing(platform_id, longitude, latitude):

    platform_metadata = load_platform_metadata(platform_file=LON_LAT_PARSING_FILE, platform_id=platform_id)

    assert platform_metadata.platform.longitude == longitude
    assert platform_metadata.platform.latitude == latitude