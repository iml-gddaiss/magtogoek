import pytest
from magtogoek.configfile import (ConfigFileError, load_configfile)



def test_load():
    load_configfile("data/config_test_files/valid_config.ini")


@pytest.mark.parametrize(
    "filename, error",
    [
        ("data/config_test_files/choice_error.ini", "choice"),
        ("data/config_test_files/range_error.ini", "range"),
        ("data/config_test_files/nargs_error.ini", "nargs"),
        ("data/config_test_files/dtype_error.ini", "dtype"),
        ("data/config_test_files/sensor_type_error.ini", "sensor_type"),
    ],
)
def test_ConfigFileError(filename, error):
    with pytest.raises(ConfigFileError) as exc_info:
        load_configfile(filename)
    assert str(exc_info.value.error) == error
