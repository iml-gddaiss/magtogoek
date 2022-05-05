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
        {'netcdf_output': 'filename', 'odf_output': True}, True, True, str(CONFIG_PATH) + '/filename', str(CONFIG_PATH),
        str(CONFIG_PATH) + '/filename'),
        ({'netcdf_output': '../magtogoek/filename_nc', 'odf_output': '../magtogoek/filename_odf'},
         True, True, '../magtogoek/filename_nc', '../magtogoek/filename_odf', '../magtogoek/filename_nc',),
        ({'netcdf_output': False, 'odf_output': 'filename'}, False, True, None, str(CONFIG_PATH) + '/filename',
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
                             **{'netcdf_output': '../notafolder/filename', 'odf_output': False}}}
    with pytest.raises(ValueError):
        ProcessConfig(config_dict=config_dict)


@pytest.mark.parametrize(
    "config_dict, figure_output, figure_path",
    [
        ({'netcdf_output': True, 'make_figures': True}, True, None),
        ({'netcdf_output': True, 'make_figures': True, "headless": True}, True, INPUT_FILES),
        ({'netcdf_output': True, 'make_figures': "../magtogoek"}, True, "../magtogoek/"+Path(INPUT_FILES).stem),
        ({'netcdf_output': True, 'make_figures': "../magtogoek/my_figs"}, True, "../magtogoek/my_figs"),
        ({'netcdf_output': 'filename', 'make_figures': "../magtogoek"}, True, "../magtogoek/filename"),
        ({'netcdf_output': 'filename', 'make_figures': "my_figs"}, True, str(CONFIG_PATH.joinpath('my_figs'))),
        ({'netcdf_output': 'filename', 'make_figures': "my_figs", "headless": True}, True, str(CONFIG_PATH.joinpath('my_figs'))),
    ]
)
def test_figures_outputs(config_dict, figure_output, figure_path):
    config_dict = {'input': {**{'input_files': INPUT_FILES}, **config_dict}}
    pconfig = ProcessConfig(config_dict=config_dict)
    assert pconfig.figures_output == figure_output
    assert pconfig.figures_path == figure_path
