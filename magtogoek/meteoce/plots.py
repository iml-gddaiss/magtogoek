"""
"""

from pathlib import Path
from typing import List, Union, Dict, Tuple

import xarray as xr
import matplotlib.pyplot as plt

from magtogoek.tools import round_up, flag_data


FONT = {"family": "serif", "color": "darkred", "weight": "normal", "size": 12}
BINARY_CMAP = plt.get_cmap("viridis_r", 2)

plt.style.use("seaborn-dark-palette")


def map_varname(varnames: Union[List[str], Tuple[str, ...]], varname_map: Dict) -> List[str]:
    return [varname_map[varname] for varname in varnames if (varname in varname_map)]


def make_meteoce_figure(
        dataset: xr.Dataset,
        single: bool = False,
        flag_thres: int = 2,
        save_path: str = None,
        show_fig: bool = True
):
    """

    Looks for 'ancillary_variables' attributes on variables for QC flagging.

    Parameters
    ----------
    dataset
    single :
        If True, figures are plotted one at a time.
    flag_thres :
        Value with QC flag of `flag_thres` or lower will be plotted ([0, ..., flag_thres])
    save_path :
        Write figures to file.
    show_fig :
         Show figure if True.

    Returns
    -------

    """
    figures = {}


    ####
    # CALL PLOTS HERE
    ####

    # buoy
    plots_vars = {'gsp_var': ['lon', 'lat', 'u_ship', 'v_ship'],
                  'gyro_var': ['heading', 'roll_', 'pitch', 'roll_std', 'pitch_std'],
                  'vel_var': ['u', 'v', 'w'],
                  'bt_vel_var': ['bt_u', 'bt_v', 'bt_w'],
                  'wind_var': ['mean_wind_speed', 'max_wind_speed', 'mean_wind_direction', 'max_wind_direction'],
                  'meteo_var': ['atm_temperature', 'atm_humidity', 'atm_pressure'],
                  'wave_var': ['wave_mean_height', 'wave_maximal_height', 'wave_period', 'wave_direction'],
                  'ctdo_var': ['temperature', 'conductivity', 'salinity', 'density', 'dissolved_oxygen'],
                  'ph_par': ['ph', 'par'],
                  'triplet_var': ['scattering', 'chlorophyll', 'fdom'],
                  'co2_var': ['co2_a', 'co2_w']}

    varname_map = {}
    for var in dataset:
        if 'generic_name' in dataset[var].attrs:
            varname_map[dataset[var].attrs['generic_name']] = var

    for fig_name, variables in plots_vars.items():
        _variables = map_varname(variables, varname_map)
        if any(x in dataset.variables for x in _variables):
            figures[fig_name] = plot_sensor_data(dataset, _variables, flag_thres=flag_thres)

    if single is True and show_fig is True:
        for count, fig in enumerate(figures.values()):
            fig.show()
            input(f"({count + 1}/{len(figures.keys())}) Press [enter] to plot the next figure.\033[1A \033[9C")

    if save_path is not None:
        stem = ''
        if Path(save_path).is_dir():
            path = Path(save_path)
        else:
            path = Path(save_path).parent
            stem = str(Path(save_path).stem) + '_'

        print(f'Figure saved at: {path}/')
        for name, fig in figures.items():
            fig.savefig(path.joinpath(stem + f'{name}.png'))

    if show_fig is True:
        plt.ion()
        plt.show(block=False)
        input("Press Enter to continue ...")
        plt.close('all')

    else:
        plt.close('all')


# a figure(function) by instrument.
# COLOR FLAG VALUE

def plot_sensor_data(dataset: xr.Dataset, varnames: List[str], flag_thres: int = 2):
    varnames = [var for var in varnames if var in dataset.variables]
    # noinspection PyTypeChecker
    fig, axes = plt.subplots(figsize=(12, 8), nrows=len(varnames), ncols=1, sharex=True, squeeze=False)
    axes = axes.flatten()
    for var, ax in zip(varnames, axes):
        da = dataset[var]
        if 'ancillary_variables' in dataset[var].attrs:
            if dataset[var].attrs['ancillary_variables'] in dataset:
                da = flag_data(dataset, var=var, flag_thres=flag_thres)
        ax.plot(dataset.time, da)
        ax.set_ylabel(f"{var}\n[{dataset[var].units}]", fontdict=FONT)
        ax.tick_params(labelbottom=False)
    axes[-1].tick_params(labelbottom=True)
    axes[-1].set_xlabel("time", fontdict=FONT)

    return fig