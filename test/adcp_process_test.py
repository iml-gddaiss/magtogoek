import pytest
from pathlib import Path
from magtogoek.adcp.process import ProcessConfig

INPUT_FILES = str(Path('input_file').absolute())
CONFIG_PATH = Path().cwd()


@pytest.mark.parametrize(
    "config_dict, netcdf_output, odf_output, netcdf_path, odf_path, log_path",
    [
        ({'netcdf_output': True, 'odf_output': True}, True, True, INPUT_FILES, str(CONFIG_PATH), INPUT_FILES),
        ({'netcdf_output': True, 'odf_output': False}, True, False, INPUT_FILES, None, INPUT_FILES),
        ({'netcdf_output': False, 'odf_output': False}, True, False, INPUT_FILES, None, INPUT_FILES),
        (
                {'netcdf_output': 'filename', 'odf_output': True},
                True, True, str(CONFIG_PATH) + '/filename', str(CONFIG_PATH), INPUT_FILES
        ),
        (
                {'netcdf_output': '../magtogoek/filename_nc', 'odf_output': '../magtogoek/filename_odf'}, True, True,
                str(CONFIG_PATH.joinpath('../magtogoek/filename_nc').resolve()),
                str(CONFIG_PATH.joinpath('../magtogoek/filename_odf').resolve()),
                str(CONFIG_PATH.joinpath('../magtogoek/filename_nc').resolve())
        ),
        (
                {'netcdf_output': False, 'odf_output': 'filename'}, False, True,
                None,
                str(CONFIG_PATH) + '/filename',
                str(CONFIG_PATH) + '/filename'),
        # ({'netcdf_output': '', 'odf_output': ''}, , , , ,),

    ],
)
def test_outputs(config_dict, netcdf_output, odf_output, netcdf_path, odf_path, log_path):
    config_dict = {'input': {**{'input_files': INPUT_FILES}, **config_dict}}
    pconfig = ProcessConfig(config_dict=config_dict)

    assert pconfig.netcdf_output == netcdf_output
    assert pconfig.odf_output == odf_output

    assert pconfig.netcdf_path == netcdf_path
    assert pconfig.odf_path == odf_path
    assert pconfig.log_path == log_path


def test_outputs_error():
    config_dict = {'input': {**{'input_files': INPUT_FILES},
                             **{'netcdf_output': '../notafolder/filename','odf_output': False}}}
    with pytest.raises(ValueError):
        ProcessConfig(config_dict=config_dict)