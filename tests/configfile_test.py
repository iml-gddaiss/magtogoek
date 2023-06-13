import pytest
from magtogoek.config_handler import load_configfile
from magtogoek.taskparser import TaskParserError



def test_load():
    load_configfile("tests/files/config_test/valid_config.ini")


@pytest.mark.parametrize(
    "filename, error",
    [
        ("data/config_test/choice_error.ini", "choice"),
        ("data/config_test/range_error.ini", "range"),
        ("data/config_test/nargs_error.ini", "nargs"),
        ("data/config_test/dtype_error.ini", "dtypes"),
        ("data/config_test/required_error.ini", "required"),
    ],
)
def test_ConfigFileError(filename, error):
    with pytest.raises(TaskParserError) as exc_info:
        load_configfile(filename)
    assert str(exc_info.value.error) == error
