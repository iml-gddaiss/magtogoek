import pytest
from magtogoek.process_configurations import load_configfile
from magtogoek.taskparser import TaskParserError



def test_load():
    load_configfile("files/config_test/valid_config.ini")


@pytest.mark.parametrize(
    "filename, error",
    [
        ("files/config_test/choice_error.ini", "choice"),
        ("files/config_test/range_error.ini", "range"),
        ("files/config_test/nargs_error.ini", "nargs"),
        ("files/config_test/dtype_error.ini", "dtypes"),
        ("files/config_test/required_error.ini", "required"),
    ],
)
def test_ConfigFileError(filename, error):
    with pytest.raises(TaskParserError) as exc_info:
        load_configfile(filename)
    assert str(exc_info.value.error) == error
