import pytest
from pathlib import Path
from magtogoek.process_common import BaseProcessConfig, resolve_output_paths, _resolve_outputs

INPUT_FILE = str(Path('input_file').absolute())
CONFIG_FILE = Path().cwd().joinpath("config_filename")

@pytest.mark.parametrize(
    "config_dict, netcdf_path, odf_path, log_path, event_qualifier",
    [
        (
            {'netcdf_output': True, 'odf_output': False},
            [str(CONFIG_FILE) + f'_{i}' for i in range(2)],
            [None, None], [str(CONFIG_FILE) + f'_{i}' for i in range(2)],
            ['meteoce' for i in range(2)]
        ),
        (
            {'netcdf_output': False, 'odf_output': True},
            [None, None],
            [str(CONFIG_FILE.parent) for i in range(2)],
            [str(CONFIG_FILE) + f"_{i}" for i in range(2)],
            ["meteoce" + f"_{i}" for i in range(2)]
        ),
        (
            {'netcdf_output': 'filename', 'odf_output': False},
            [str(CONFIG_FILE.parent.joinpath(f"filename_{i}")) for i in range(2)],
            [None, None],
            [str(CONFIG_FILE.parent.joinpath(f"filename_{i}")) for i in range(2)],
            ["meteoce" for i in range(2)]
        ),
        (
            {'netcdf_output': False, 'odf_output': 'filename'},
            [None, None],
            [str(CONFIG_FILE.parent.joinpath(f"filename_{i}")) for i in range(2)],
            [str(CONFIG_FILE.parent.joinpath(f"filename_{i}")) for i in range(2)],
            ["meteoce" for i in range(2)]
        ),
        (
            {'netcdf_output': "../magtogoek/", 'odf_output': False},
            ["../magtogoek/"+str(CONFIG_FILE.stem) + f'_{i}' for i in range(2)],
            [None, None],
            ["../magtogoek/"+str(CONFIG_FILE.stem) + f'_{i}' for i in range(2)],
            ['meteoce' for i in range(2)]
         ),
        (
            {'netcdf_output': "../magtogoek/filename_nc", 'odf_output': False},
            ["../magtogoek/filename_nc" + f'_{i}' for i in range(2)],
            [None, None],
            ["../magtogoek/filename_nc" + f'_{i}' for i in range(2)],
            ['meteoce' for i in range(2)]
         ),
        (
            {'netcdf_output': False, 'odf_output': "../magtogoek/"},
            [None, None],
            ["../magtogoek" for i in range(2)],
            ["../magtogoek/"+str(CONFIG_FILE.stem) + f'_{i}' for i in range(2)],
            ["meteoce" + f"_{i}" for i in range(2)]
         ),
        (
            {'netcdf_output': False, 'odf_output': "../magtogoek/filename_odf"},
            [None, None],
            ["../magtogoek/filename_odf" + f'_{i}' for i in range(2)],
            ["../magtogoek/filename_odf" + f'_{i}' for i in range(2)],
            ['meteoce' for i in range(2)]
         ),
    ],
)
def test_process_no_merge_decorator(config_dict, netcdf_path, odf_path, log_path, event_qualifier):
    """With a configfile"""
    config_dict = {
        'header': {'sensor_type': 'adcp', 'config_file': str(CONFIG_FILE)},
        'input': {**{'input_files': [INPUT_FILE + f'_{i}' for i in range(2)]}, **config_dict},
        'CRUISE': {"event_qualifier1": "meteoce"},
        'output': {"merge_output_files": False}
                   }
    pconfig = BaseProcessConfig(config_dict=config_dict)
    pconfig.merge_output_files = False
    _assert_process_wrapper(pconfig, netcdf_path, odf_path, log_path, event_qualifier)


@resolve_output_paths
def _assert_process_wrapper(pconfig: BaseProcessConfig, netcdf_path: list, odf_path: list, log_path: list, event_qualifier: list):
    # print(pconfig.netcdf_path, netcdf_path.pop(0))
    # print(pconfig.odf_path, odf_path.pop(0))
    # print(pconfig.log_path, log_path.pop(0))
    # print(pconfig.metadata['event_qualifier1'], event_qualifier.pop(0))

    assert pconfig.netcdf_path == netcdf_path.pop(0)
    assert pconfig.odf_path == odf_path.pop(0)
    assert pconfig.log_path == log_path.pop(0)
    assert pconfig.metadata['event_qualifier1'] == event_qualifier.pop(0)



@pytest.mark.parametrize(
    "config_file, config_dict, netcdf_output, odf_output, netcdf_path, odf_path, log_path",
    [
        (str(CONFIG_FILE), {'netcdf_output': True, 'odf_output': True}, True, True, str(CONFIG_FILE), str(CONFIG_FILE.parent), str(CONFIG_FILE)),
        (str(CONFIG_FILE), {'netcdf_output': True, 'odf_output': False}, True, False, str(CONFIG_FILE), None, str(CONFIG_FILE)),
        (str(CONFIG_FILE), {'netcdf_output': False, 'odf_output': True}, False, True, None, str(CONFIG_FILE.parent), str(CONFIG_FILE)),
        (str(CONFIG_FILE), {'netcdf_output': False, 'odf_output': False}, True, False, str(CONFIG_FILE), None, str(CONFIG_FILE)),
        (str(CONFIG_FILE), {'netcdf_output': 'filename', 'odf_output': True}, True, True, str(CONFIG_FILE.parent)+'/filename', str(CONFIG_FILE.parent), str(CONFIG_FILE.parent) + '/filename'),
        (str(CONFIG_FILE), {'netcdf_output': '../magtogoek/filename_nc', 'odf_output': '../magtogoek/filename_odf'}, True, True, '../magtogoek/filename_nc', '../magtogoek/filename_odf', '../magtogoek/filename_nc',),
        (str(CONFIG_FILE), {'netcdf_output': False, 'odf_output': 'filename'}, False, True, None, str(CONFIG_FILE.parent) + '/filename', str(Path(CONFIG_FILE).parent) + '/filename'),

        (None, {'netcdf_output': True, 'odf_output': True}, True, True, INPUT_FILE, str(Path(INPUT_FILE).parent), INPUT_FILE),
        (None, {'netcdf_output': True, 'odf_output': False}, True, False, INPUT_FILE, None, INPUT_FILE),
        (None, {'netcdf_output': False, 'odf_output': True}, False, True, None, str(Path(INPUT_FILE).parent), INPUT_FILE),
        (None, {'netcdf_output': False, 'odf_output': False}, True, False, INPUT_FILE, None, INPUT_FILE),
        (None, {'netcdf_output': 'filename', 'odf_output': True}, True, True, str(Path(INPUT_FILE).parent) + '/filename', str(Path(INPUT_FILE).parent), str(Path(INPUT_FILE).parent) + '/filename'),
        (None, {'netcdf_output': '../magtogoek/filename_nc', 'odf_output': '../magtogoek/filename_odf'}, True, True, '../magtogoek/filename_nc', '../magtogoek/filename_odf', '../magtogoek/filename_nc',),
        (None, {'netcdf_output': False, 'odf_output': 'filename'}, False, True, None, str(Path(INPUT_FILE).parent) + '/filename', str(Path(INPUT_FILE).parent) + '/filename'),
    ],
)
def test_resolve_outputs(config_file, config_dict, netcdf_output, odf_output, netcdf_path, odf_path, log_path):
    """With a configfile"""
    config_dict = {'header': {'sensor_type': 'adcp', 'config_file': config_file},
                   'input': {**{'input_files': INPUT_FILE}, **config_dict}}
    pconfig = BaseProcessConfig(config_dict=config_dict)
    _resolve_outputs(pconfig)

    assert pconfig.netcdf_output == netcdf_output
    assert pconfig.odf_output == odf_output

    assert pconfig.netcdf_path == netcdf_path
    assert pconfig.odf_path == odf_path
    assert pconfig.log_path == log_path

def test_outputs_error():
    config_dict = {
        'header': {'sensor_type': 'adcp'},
        'input': {
            **{'input_files': INPUT_FILE},
            **{'netcdf_output': '../notafolder/filename', 'odf_output': False}
        }
    }
    with pytest.raises(ValueError):
        pconfig = BaseProcessConfig(config_dict=config_dict)
        _resolve_outputs(pconfig)


@pytest.mark.parametrize(
    "config_dict, figure_output, figure_path",
    [
        ({'netcdf_output': True, 'make_figures': True}, True, None),
        ({'netcdf_output': True, 'make_figures': True, "headless": True}, True, INPUT_FILE),
        ({'netcdf_output': True, 'make_figures': "../magtogoek"}, True, "../magtogoek/" + Path(INPUT_FILE).stem),
        ({'netcdf_output': True, 'make_figures': "../magtogoek/my_figs"}, True, "../magtogoek/my_figs"),
        ({'netcdf_output': 'filename', 'make_figures': "../magtogoek"}, True, "../magtogoek/filename"),
        ({'netcdf_output': 'filename', 'make_figures': "my_figs"}, True, str(Path(INPUT_FILE).parent.joinpath('my_figs'))),
        ({'netcdf_output': 'filename', 'make_figures': "my_figs", "headless": True}, True,
         str(Path(INPUT_FILE).parent.joinpath('my_figs'))),
    ]
)
def test_figures_outputs(config_dict, figure_output, figure_path):
    config_dict = {'header': {'sensor_type': 'adcp'},
                   'input': {**{'input_files': INPUT_FILE}, **config_dict}}
    pconfig = BaseProcessConfig(config_dict=config_dict)
    _resolve_outputs(pconfig)
    assert pconfig.figures_output == figure_output
    assert pconfig.figures_path == figure_path
