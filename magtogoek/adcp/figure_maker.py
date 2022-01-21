"""
author: Jérôme Guay
date: Nov. 29, 2021


This modules contains the essential figure to do a visual inspection of the data.
"""

from itertools import cycle
from typing import List, Union

import cmocean as cmo
import matplotlib.colorbar as clb
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from magtogoek.plot_utils import grid_subplot
from magtogoek.tools import round_up, flag_data, polar_histo

FONT = {"family": "serif", "color": "darkred", "weight": "normal", "size": 12}
BINARY_CMAP = plt.get_cmap("viridis_r", 2)
VEL_CMAP = cmo.cm.balance
plt.style.use("seaborn-dark-palette")


def get_extent(dataset: xr.Dataset) -> List:
    return [
        mdates.date2num(dataset.time.data[0]),
        mdates.date2num(dataset.time.data[-1]),
        dataset.depth.data[-1],
        dataset.depth.data[0]
    ]


def make_adcp_figure(dataset: xr.Dataset, single: bool = False, flag_thres=2):
    """

    Parameters
    ----------
    dataset
    single :
        If True, figures are plotted one at a time.
    flag_thres

    Returns
    -------

    """

    figs = []

    figs.append(plot_vel_series(dataset, dataset.depth.data[0:3], flag_thres=flag_thres))

    figs.append(plot_pearson_corr(dataset, flag_thres=flag_thres))

    figs.append(plot_geospatial(dataset))

    figs.append(plot_anc(dataset))

    if all(v in dataset for v in ["bt_u", "bt_v", "bt_w"]):
        figs.append(plot_bt_vel(dataset))

    if "binary_mask_tests" in dataset.attrs:
        figs.append(plot_test_fields(dataset))

    figs.append(plot_velocity_polar_hist(dataset, 2, 3, flag_thres=flag_thres))

    figs.append(plot_velocity_fields(dataset, flag_thres=flag_thres))

    if single is True:
        for count, fig in enumerate(figs):
            fig.show()
            input(f"({count + 1}/{len(figs)}) Press [enter] to plot the next figure.\033[1A \033[9C")
    plt.show()


def plot_velocity_polar_hist(dataset: xr.Dataset, nrows: int = 3, ncols: int = 3,
                             x_vel: str = "u", y_vel: str = "v", flag_thres: int = 2):
    naxes = int(nrows * ncols)
    r_max = np.nanmax(np.hypot(flag_data(dataset, x_vel, flag_thres), flag_data(dataset, y_vel, flag_thres)))
    r_max = round_up(r_max, 0.2)
    r_ticks = np.round(np.linspace(0, r_max, 6), 2)[1:]

    bin_depths = np.linspace(dataset.depth.min(), dataset.depth.max(), naxes + 1)

    fig, axes = plt.subplots(figsize=(12, 8), nrows=nrows, ncols=ncols,
                             subplot_kw={"projection": "polar"}, constrained_layout=True)
    axes = axes.flatten()
    grid_subplot(axes[0], nrows, ncols)
    for index in range(naxes):
        histo, a_edges, r_edges = polar_histo(
            dataset.sel(depth=slice(bin_depths[index], bin_depths[index + 1])),
            x_vel, y_vel, r_max)
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


def plot_velocity_fields(dataset: xr.Dataset, flag_thres: int = 2):
    fig, axes = plt.subplots(
        figsize=(12, 8), nrows=3, ncols=1, sharex=True, sharey=True,
    )
    for var, axe in zip(["u", "v", "w"], axes):
        vel_da = dataset[var].where(dataset[var + "_QC"] <= flag_thres)
        vmax = round_up(np.max(np.abs(vel_da)), 0.1)
        extent = get_extent(dataset)
        im = axe.imshow(
            vel_da, aspect="auto", cmap=VEL_CMAP, extent=extent, vmin=-vmax, vmax=vmax, interpolation='none',
        )
        axe.xaxis_date()

        cbar = plt.colorbar(im, location="right", ax=axe, pad=0.01)
        cbar.set_label(dataset[var].attrs["units"], fontdict=FONT)
        cbar.set_ticks(np.linspace(-vmax, vmax, 5))
        axe.set_title(var, fontdict=FONT)
        axe.tick_params(rotation=-30)

    axes[1].set_ylabel("depth [m]", fontdict=FONT)
    axes[2].set_xlabel("time", fontdict=FONT)

    return fig


def plot_test_fields(dataset: xr.Dataset):
    """
    """
    extent = get_extent(dataset)
    fig, axes = plt.subplots(figsize=(12, 8), nrows=3, ncols=3, sharex=True, sharey=True)
    axes = axes.flatten()
    for index, test_name in enumerate(dataset.attrs["binary_mask_tests"]):
        value = dataset.attrs["binary_mask_tests_values"][index]
        if value is not None:
            mask = (dataset.binary_mask.astype(int) & 2 ** index).astype(bool)
            axes[index].imshow(mask, aspect="auto", cmap=BINARY_CMAP, extent=extent,interpolation='none',)
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


def plot_vel_series(dataset: xr.Dataset, depths: Union[float, List[float]], flag_thres: int = 2):
    fig, axes = plt.subplots(figsize=(12, 8), nrows=3, ncols=1, sharex=True, sharey=True)
    axes[0].tick_params(labelbottom=False)
    axes[1].tick_params(labelbottom=False)

    colors = plt.cm.viridis(np.linspace(0, 1, len(depths)))
    for var, ax in zip(["u", "v", "w"], axes):
        da = dataset[var].where(dataset[var + "_QC"] <= flag_thres)
        clines = cycle(["solid", "dotted", "dashed", "dashdotted"])
        for depth, c in zip(depths, colors):
            ax.plot(dataset.time, da.sel(depth=depth), linestyle=next(clines), c=c, label=str(depth) + " m")
        ax.set_ylabel(f"{var}\n[{dataset[var].units}]", fontdict=FONT)
    axes[2].set_xlabel("time", fontdict=FONT)
    axes[2].legend(title="depth")

    return fig


def plot_pearson_corr(dataset, flag_thres: int = 2):
    vel = ["u", "v", "w"]
    corr = {v: [] for v in vel}
    for var in vel:
        da = dataset[var].where(dataset[var + "_QC"] <= flag_thres)
        for d in range(dataset.dims["depth"] - 2):
            corr[var].append(xr.corr(da[d], da[d + 2], "time"))
    fig, axe = plt.subplots(figsize=(6, 8))
    for var in vel:
        axe.plot(corr[var], dataset.depth[:-2], label=var)
    axe.invert_yaxis()
    axe.set_ylabel("depth [m]", fontdict=FONT)
    axe.set_xlabel("pearson correlation\n for consecutive bin", fontdict=FONT)
    axe.legend()

    return fig


def plot_geospatial(dataset):
    _gs_var = ["xducer_depth", "heading", "roll_", "pitch", "lon", "lat"]
    gs_var = [v for v in _gs_var if v in dataset.variables]
    fig, axes = plt.subplots(figsize=(12, 8), nrows=len(gs_var), ncols=1, sharex=True, squeeze=False)
    axes = axes.flatten()
    for var, ax in zip(gs_var, axes):
        ax.plot(dataset.time, dataset[var])
        ax.set_ylabel(f"{var}\n[{dataset[var].units}]", fontdict=FONT)
        ax.tick_params(labelbottom=False)
    axes[-1].tick_params(labelbottom=True)
    axes[-1].set_xlabel("time", fontdict=FONT)

    return fig


def plot_anc(dataset, flag_thres: int = 2):
    _anc_var = ["temperature", "pres"]
    anc_var = [var for var in _anc_var if var in dataset.variables]
    fig, axes = plt.subplots(figsize=(12, 8), nrows=len(anc_var), ncols=1, sharex=True, squeeze=False)
    axes = axes.flatten()
    for var, ax in zip(anc_var, axes):
        ax.plot(dataset.time, flag_data(dataset, var, flag_thres=flag_thres))
        ax.set_ylabel(f"{var}\n[{dataset[var].units}]", fontdict=FONT)
        ax.tick_params(labelbottom=False)
    axes[-1].tick_params(labelbottom=True)
    axes[-1].set_xlabel("time", fontdict=FONT)

    return fig


def plot_bt_vel(dataset: xr.Dataset):
    fig, axes = plt.subplots(figsize=(12, 8), nrows=3, ncols=1, sharex=True, sharey=True)
    axes[0].tick_params(labelbottom=False)
    axes[1].tick_params(labelbottom=False)
    for var, ax in zip(["bt_u", "bt_v", "bt_w"], axes):
        ax.plot(dataset.time, dataset[var])
        ax.set_ylabel(f"{var}\n[{dataset[var].units}]", fontdict=FONT)
    axes[2].set_xlabel("time", fontdict=FONT)

    return fig


if __name__ == "__main__":
    import xarray as xr

    # nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml6_2017_wh.nc"
    # nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml4_2017_sw.nc"
    # nc_file = "/home/jeromejguay/ImlSpace/Data/MPO/iml42020/MADCP_BOUEE2020_RIMOUSKI_553_VEL.nc"
    # nc_file = "/home/jeromejguay/ImlSpace/Data/MPO/iml42020/iml4_2020_no_mcorr.nc"
    nc_file = "/home/jeromejguay/ImlSpace/Data/IML-4 (PMZA-RIKI)/2021-IML4-ADCP-24418/iml4adcp2021.nc"

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
    dataset = xr.open_dataset(nc_file)
    dataset.attrs["binary_mask_tests"] = test
    dataset.attrs["binary_mask_tests_values"] = [0, 64, 90, 5.0, 5.0, 5.0, 20, 20, None]

    make_adcp_figure(dataset, single=False)
