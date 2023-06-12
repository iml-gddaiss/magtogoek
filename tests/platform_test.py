from magtogoek.platforms import load_platform_metadata

FILENAME = "files/iml_platforms.json"


def test_load_platform_metadata():
    platform_metadata = load_platform_metadata(platform_file=FILENAME, platform_id="IML6_2017")
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