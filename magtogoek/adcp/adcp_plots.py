"""
author: Jérôme Guay
date: Nov. 29, 2021


This modules contains the essential figure to do a visual inspection of the data.


# Use ancillary_variables for QC. modify on the flag data function tools.
"""
import logging
from itertools import cycle
from typing import List, Union, Dict, Tuple
from pathlib import Path

import cmocean as cmo
import matplotlib.colorbar as clb
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from magtogoek.plot_utils import grid_subplot
from magtogoek.tools import round_up, flag_data, polar_histo

# plt.switch_backend('Qt5Agg')

FONT = {"family": "serif", "color": "darkred", "weight": "normal", "size": 12}
BINARY_CMAP = plt.get_cmap("viridis_r", 2)
VEL_CMAP = cmo.cm.balance
plt.style.use("seaborn-dark-palette")

GEO_VAR = ["heading", "roll_", "pitch", "lon", "lat"]
ANC_VAR = ["xducer_depth", "temperature", "pres"]


def map_varname(varnames: Union[List[str], Tuple[str, ...]], varname_map: Dict) -> List[str]:
    return [varname_map[varname] for varname in varnames if (varname in varname_map)]


def get_extent(dataset: xr.Dataset) -> List:
    return [
        mdates.date2num(dataset.time.data[0]),
        mdates.date2num(dataset.time.data[-1]),
        dataset.depth.data[-1],
        dataset.depth.data[0]
    ]


def make_adcp_figure(dataset: xr.Dataset,
                     single: bool = False,
                     flag_thres: int = 2,
                     vel_only: bool = False,
                     save_path: str = None,
                     show_fig: bool = True):
    """

    Looks for 'ancillary_variables' attributes on variables for QC flagging.

    Parameters
    ----------
    dataset
    single :
        If True, figures are plotted one at a time.
    flag_thres :
        Value with QC flag of `flag_thres` or lower will be plotted ([0, ..., flag_thres])
    vel_only :
        Make only velocity data figures.
    save_path :
        Write figures to file.
    show_fig :
         Show figure if True.

    Returns
    -------

    """

    if dataset.attrs['coord_system'] == "beam":
        velocity_variables = ("v1", "v2", "v3", "v4")
        velocity_bt_variables = ("bt_v1", "bt_v2", "bt_v3", "bt_v4", "bt_depth")
    else:
        velocity_variables = ("u", "v", "w")
        velocity_bt_variables = ("bt_u", "bt_v", "bt_w", "bt_depth")

    figs, names = [], []

    varname_map = {}
    for var in dataset:
        if 'generic_name' in dataset[var].attrs:
            varname_map[dataset[var].attrs['generic_name']] = var

    if vel_only is False:
        geo_var = map_varname(GEO_VAR, varname_map)
        if len(geo_var) > 0:
            figs.append(plot_sensor_data(dataset, varnames=geo_var))
            names.append(f'sensor_data_geo')

        anc_var = map_varname(ANC_VAR, varname_map)
        if len(anc_var) > 0:
            figs.append(plot_sensor_data(dataset, varnames=anc_var))
            names.append(f'sensor_data_anc')

        bt_uvw_var = map_varname(velocity_bt_variables, varname_map)
        if len(bt_uvw_var) > 0 and all(v in dataset for v in bt_uvw_var):
            figs.append(plot_bt_vel(dataset, bt_var=bt_uvw_var))
            names.append(f'bt_vel')

    uvw_var = map_varname(velocity_variables, varname_map)
    if len(uvw_var) > 0:
        if vel_only is False:
            depths = dataset.depth.data[0:3]
            if dataset.attrs['orientation'] == "up":
                depths = dataset.depth.data[-3:]
            figs.append(plot_vel_series(dataset, depths=depths, uvw=uvw_var, flag_thres=flag_thres))
            figs.append(plot_pearson_corr(dataset, vel_var=uvw_var, flag_thres=flag_thres))
            names.extend(('vel_series', 'pearson_corr'))
        if dataset.attrs['coord_system'] != 'beam':
            polar_fig = plot_velocity_polar_hist(dataset, nrows=2, ncols=3, uv=uvw_var[:2], flag_thres=flag_thres)
            if polar_fig is not None:
                figs.append(polar_fig)

        field_fig = plot_velocity_fields(dataset, vel_var=uvw_var, flag_thres=flag_thres)
        if field_fig is not None:
            figs.append(field_fig)
        names.extend(('velocity_polar_hist', 'velocity_fields'))

    if "binary_mask" in dataset:
        figs.append(plot_test_fields(dataset))
        names.append('test_fields')

    if single is True and show_fig is True:
        for count, fig in enumerate(figs):
            fig.show()
            input(f"({count + 1}/{len(figs)}) Press [enter] to plot the next figure.\033[1A \033[9C")

    if save_path is not None:
        stem = ''
        if Path(save_path).is_dir():
            path = Path(save_path)
        else:
            path = Path(save_path).parent
            stem = str(Path(save_path).stem) + '_'
        for name, fig in zip(names, figs):
            fig.savefig(path.joinpath(stem + f'{name}.png'))

    if show_fig is True:
        logging.info(f'make adcp_figure show fig: {show_fig}')
        plt.ion()
        plt.show(block=False)
        input("Press Enter to continue ...")
        plt.close('all')

    else:
        plt.close('all')


def plot_velocity_polar_hist(dataset: xr.Dataset, nrows: int = 3, ncols: int = 3,
                             uv: List[str] = ("u", "v"),  flag_thres: int = 2):
    naxes = int(nrows * ncols)
    flagged_u = flag_data(dataset, var=uv[0], flag_thres=flag_thres).data
    flagged_v = flag_data(dataset, var=uv[1], flag_thres=flag_thres).data

    if not (np.isfinite(flagged_u).any() and np.isfinite(flagged_v).any()):
        return None

    r_max = np.nanmax(np.hypot(
        flag_data(dataset, var=uv[0], flag_thres=flag_thres).data,
        flag_data(dataset, var=uv[1], flag_thres=flag_thres).data
    ))

    r_max = round_up(r_max, 0.2)
    r_ticks = np.round(np.linspace(0, r_max, 6), 2)[1:]

    bin_depths = np.linspace(dataset.depth.min(), dataset.depth.max(), naxes + 1)

    fig, axes = plt.subplots(figsize=(12, 8), nrows=nrows, ncols=ncols,
                             subplot_kw={"projection": "polar"}, constrained_layout=True)
    if naxes > 1:
        axes = axes.flatten()
    else:
        axes = [axes]
    grid_subplot(axes[0], nrows, ncols)
    for index in range(naxes):
        histo, a_edges, r_edges = polar_histo(
            dataset.sel(depth=slice(bin_depths[index], bin_depths[index + 1])),
            uv[0], uv[1], r_max)
        histo[histo < 1] = np.nan
        if np.isfinite(histo).any():
            histo /= np.nanmax(histo)
            axes[index].grid(False)
            axes[index].pcolormesh(a_edges, r_edges, histo.T, cmap=cmo.cm.amp, shading="flat")
        axes[index].set_title(
            f"depth: {round((bin_depths[index] + bin_depths[index + 1]) / 2, 0)} m", fontdict=FONT, loc="left"
        )
        axes[index].grid(True)
        axes[index].set_theta_zero_location("N")
        axes[index].set_theta_direction(-1)
        axes[index].set_rgrids(r_ticks, angle=0)
        axes[index].set_yticklabels([])

        rlabels_rpos = np.hypot(1.3 * r_max, r_ticks)
        rlabels_tpos = np.arctan2(1.3 * r_max, r_ticks)

        for label, rpos, tpos, rtick in zip(r_ticks, rlabels_rpos, rlabels_tpos, r_ticks):
            axes[index].text(tpos, rpos, f"{label:.2f}", fontsize=10, clip_on=False, va="center", rotation=0)
            axes[index].plot(
                (0, tpos), (rtick, rpos), "--", lw=0.6, c="k", clip_on=False
            )
        axes[index].set_ylim(0, r_max)
        axes[index].text(np.arctan2(1.6 * r_max, np.mean(r_ticks)), np.hypot(1.6 * r_max, np.mean(r_ticks)),
                         "velocity [m s$^{-1}$]", rotation=90, va="center", fontsize=12)
        axes[index].set_facecolor("lightslategrey")
        axes[index].set_xlabel("absolute bearing [deg]", fontsize=12)

    return fig


def plot_velocity_fields(dataset: xr.Dataset, vel_var: List[str] = ("u", "v", "w"), flag_thres: int = 2):
    # noinspection PyTypeChecker
    fig, axes = plt.subplots(
        figsize=(12, 8), nrows=len(vel_var), ncols=1, sharex=True, sharey=True,
    )
    for var, axe in zip(vel_var, axes):
        vel_da = flag_data(dataset=dataset, var=var, flag_thres=flag_thres)
        vmax = round_up(np.max(np.abs(vel_da)), 0.1)
        if not np.isfinite(vmax):
            vmax=1
        extent = get_extent(dataset)
        im = axe.imshow(
            vel_da, aspect="auto", cmap=VEL_CMAP, extent=extent, vmin=-vmax, vmax=vmax, interpolation='none',
        )
        axe.xaxis_date()

        cbar = plt.colorbar(im, location="right", ax=axe, pad=0.01)
        #cbar.set_label(dataset[var].attrs["units"], fontdict=FONT) #FIXME
        cbar.set_label('FIXME')
        cbar.set_ticks(np.linspace(-vmax, vmax, 5))
        axe.set_title(var, fontdict=FONT)
        axe.tick_params(rotation=-30)

    axes[1].set_ylabel("depth [m]", fontdict=FONT)
    axes[-1].set_xlabel("time", fontdict=FONT)

    return fig


def plot_test_fields(dataset: xr.Dataset):
    """
    """
    extent = get_extent(dataset)
    # noinspection PyTypeChecker
    fig, axes = plt.subplots(figsize=(12, 8), nrows=3, ncols=3, sharex=True, sharey=True)
    axes = axes.flatten()
    for index, test_name in enumerate(dataset.attrs["binary_mask_tests"]):
        value = dataset.attrs["binary_mask_tests_values"][index]
        if value is not None:
            mask = (dataset.binary_mask.astype(int) & 2 ** index).astype(bool)
            axes[index].imshow(mask, aspect="auto", cmap=BINARY_CMAP, extent=extent, interpolation='none', )
            axes[index].xaxis_date()
            axes[index].set_title(test_name + f": {value}", fontdict=FONT)
        axes[index].tick_params(labelleft=False, labelbottom=False)

    axes[3].set_ylabel("depth [m]", fontdict=FONT)
    axes[3].tick_params(labelleft=True)
    axes[7].tick_params(labelbottom=True)
    axes[7].set_xlabel("time", fontdict=FONT)
    axes[7].tick_params(axis="x", rotation=-30)

    cbar_axe = fig.add_axes([0.15, 0.08, 0.2, 0.005])
    cbar = clb.ColorbarBase(
        cbar_axe, cmap=BINARY_CMAP, ticks=[1 / 4, 3 / 4], orientation="horizontal"
    )
    cbar.set_ticklabels(["Passed", "Failed"])

    return fig


def plot_vel_series(dataset: xr.Dataset, depths: Union[float, List[float]],
                    uvw: List[str] = ("u", "v", "w"), flag_thres: int = 2):
    # noinspection PyTypeChecker
    fig, axes = plt.subplots(figsize=(12, 8), nrows=len(uvw), ncols=1, sharex=True, sharey=True)
    axes[0].tick_params(labelbottom=False)
    axes[1].tick_params(labelbottom=False)

    colors = plt.cm.viridis(np.linspace(0, 1, len(depths)))
    for var, ax in zip(uvw, axes):
        da = flag_data(dataset=dataset, var=var, flag_thres=flag_thres)
        clines = cycle(["solid", "dotted", "dashed", "dashdotted"])
        for depth, c in zip(depths, colors):
            ax.plot(dataset.time, da.sel(depth=depth), linestyle=next(clines), c=c, label=f"{depth:.02f} m")
        #ax.set_ylabel(f"{var}\n[{dataset[var].attrs['units']}]", fontdict=FONT) #FIXME
        ax.set_ylabel("FIXME")
    axes[-1].set_xlabel("time", fontdict=FONT)
    axes[2].legend(title="depth")

    return fig


def plot_pearson_corr(dataset: xr.Dataset, vel_var: List[str] = ("u", "v", "w"), flag_thres: int = 2):
    corr = {v: [] for v in vel_var}
    for var in vel_var:
        da = flag_data(dataset=dataset, var=var)
        for d in range(dataset.dims["depth"] - 2):
            if np.isfinite(da[d]).any() and np.isfinite(da[d + 2]).any():
                corr[var].append(xr.corr(da[d], da[d + 2], "time"))
            else:
                corr[var].append(np.nan)
    fig, axe = plt.subplots(figsize=(6, 8))
    for var in vel_var:
        axe.plot(corr[var], dataset.depth[:-2], label=var)
    axe.invert_yaxis()
    axe.set_ylabel("depth [m]", fontdict=FONT)
    axe.set_xlabel("pearson correlation\n for consecutive bin", fontdict=FONT)
    axe.legend()

    return fig


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


def plot_bt_vel(dataset: xr.Dataset, bt_var: List[str] = ("bt_u", "bt_v", "bt_w", "bt_depth")):
    # noinspection PyTypeChecker
    fig, axes = plt.subplots(figsize=(12, 8), nrows=len(bt_var), ncols=1, sharex=True, sharey=True)
    axes[0].tick_params(labelbottom=False)
    axes[1].tick_params(labelbottom=False)
    for var, ax in zip(bt_var, axes):
        ax.plot(dataset.time, dataset[var])
        ax.set_ylabel(f"{var}\n[{dataset[var].units}]", fontdict=FONT)
    axes[-1].set_xlabel("time", fontdict=FONT)

    return fig


if __name__ == "__main__":
    import xarray as xr

    # nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml6_2017_wh.nc"
    # nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml4_2017_sw.nc"
    nc_file = "/home/jeromejguay/ImlSpace/Data/MPO/iml42020/MADCP_BOUEE2020_RIMOUSKI_553_VEL.nc"
    # nc_file = "/home/jeromejguay/ImlSpace/Data/MPO/iml42020/iml4_2020_no_mcorr.nc"
    # nc_file = "/home/jeromejguay/ImlSpace/Data/IML-4 (PMZA-RIKI)/2021-IML4-ADCP-24418/iml4adcp2021.nc"

    test = [
        "amp",
        "corr",
        "pg",
        "horizontal vel",
        "vertical vel",
        "error",
        "roll",
        "pitch",
        "sidelobe",
    ]
    _dataset = xr.open_dataset(nc_file)
    _dataset.attrs["binary_mask_tests"] = test
    _dataset.attrs["binary_mask_tests_values"] = [0, 64, 90, 5.0, 5.0, 5.0, 20, 20, None]

    make_adcp_figure(_dataset, single=False)
