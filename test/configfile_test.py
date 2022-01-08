import pytest
from magtogoek.configfile import load_configfile
from magtogoek.taskparser import TaskParserError



def test_load():
    load_configfile("data/config_test_files/valid_config.ini")


@pytest.mark.parametrize(
    "filename, error",
    [
        ("data/config_test_files/choice_error.ini", "choice"),
        ("data/config_test_files/range_error.ini", "range"),
        ("data/config_test_files/nargs_error.ini", "nargs"),
        ("data/config_test_files/dtype_error.ini", "dtypes"),
        ("data/config_test_files/required_error.ini", "required"),
    ],
)
def test_ConfigFileError(filename, error):
    with pytest.raises(TaskParserError) as exc_info:
        load_configfile(filename)
    assert str(exc_info.value.error) == error
