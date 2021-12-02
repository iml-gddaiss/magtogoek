"""
author: Jérôme Guay
date: Nov. 29, 2021
"""
import warnings

import cmocean.cm as cmo
import matplotlib as mpl
import matplotlib.colorbar as clb
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from mpl_toolkits.axes_grid1 import ImageGrid

warnings.filterwarnings("ignore", module="matplotlib\..*")

# ESTIMATE THE START and END time
FONT = {"family": "serif", "color": "darkred", "weight": "normal", "size": 14}
BINARY_CMAP = plt.get_cmap("viridis_r", 2)
VEL_CMAP = cmo.balance


def plot_polar_velocities(dataset: xr.Dataset, uv=('u','v'),flag_thres: int = 2):
    """
    """
    u = dataset[uv[0]].where(dataset[uv[0]+'_QC'] <= flag_thres).data.flatten()
    v = dataset[uv[1]].where(dataset[uv[1]+'_QC'] <= flag_thres).data.flatten()
    vels = np.sqrt(u ** 2 + v ** 2)
    with np.errstate(divide="ignore", invalid="ignore"):
        angles = np.rad2deg(np.arctan(v / u))
    fig, ax = plt.subplots(figsize=(12, 8), subplot_kw={"projection": "polar"})

    im = ax.scatter(angles, vels, s=5, alpha=0.3)
    ax.set_rticks(np.arange(0, 2.2, 0.2))  # Less radial ticks
    ax.set_rmax(np.nanmax(vels))
    ax.set_rlabel_position(-22.5)  # Move radial labels away from plotted line
    ax.grid(True)

    return fig


def plot_velocity_fields(dataset: xr.Dataset, flag_thres: int = 2):
    fig = plt.figure(figsize=(12, 8))

    axes = ImageGrid(
        fig,
        111,  # as in plt.subplot(111)
        nrows_ncols=(3, 1),
        axes_pad=0.3,
        share_all=True,
        aspect=False,
        cbar_location="right",
        cbar_mode="each",
        cbar_size="2%",
    )
    for index, var in enumerate(["u", "v", "w"]):
        vel_da = dataset[var].where(dataset[var + "_QC"] <= flag_thres)
        max = np.round(np.max(vel_da.reduce(np.abs)), 2)
        im = axes[index].pcolormesh(
            dataset.time,
            dataset.depth,
            vel_da,
            shading="auto",
            cmap=VEL_CMAP,)
        cax = axes[index].cax
        plt.colorbar(im, cax)
        axes[index].cax.set_ylabel(vel_da.attrs["units"], fontdict=FONT)
        axes[index].set_title(var, fontdict=FONT)
        axes[index].tick_params(rotation=-30)
    axes[-1].invert_yaxis()

    axes[1].set_ylabel("depth [m]", fontdict=FONT)
    axes[2].set_xlabel("time", fontdict=FONT)

    return fig


def plot_test_fields(dataset):
    """
    """
    fig = plt.figure(figsize=(12, 8))

    axes = ImageGrid(
        fig,
        111,  # as in plt.subplot(111)
        nrows_ncols=(3, 3),
        axes_pad=0.3,
        share_all=True,
        aspect=False,
    )

    # Add data to image grid
    for index, test_name in enumerate(dataset.attrs["binary_mask_tests"]):
        value = dataset.attrs["binary_mask_tests_value"][index]
        if value is not None:
            mask = (dataset.binary_mask.astype(int) & 2 ** index).astype(bool)

            im = axes[index].pcolormesh(
                ds.time, ds.depth, mask, cmap=BINARY_CMAP, shading="auto"
            )
            axes[index].set_title(test_name + f": {value}", fontdict=FONT)

        if index != 3:
            axes[index].tick_params(labelleft=False)
        else:
            axes[index].set_ylabel("depth [m]", fontdict=FONT)
        if index != 7:
            axes[index].tick_params(labelbottom=False)
            axes[index].set_xlabel("")
        else:
            axes[index].tick_params(rotation=-30)
            axes[index].set_xlabel("time", fontdict=FONT)

        axes[index].invert_yaxis()

    cbar_axe = fig.add_axes([0.15, 0.08, 0.2, 0.005])
    cbar = clb.ColorbarBase(
        cbar_axe, cmap=BINARY_CMAP, ticks=[0.25, 0.75], orientation="horizontal",
    )
    cbar.set_ticklabels(["Passed", "Failed"])

    return fig


if __name__ == "__main__":
    import xarray as xr

    nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml6_2017_wh.nc"
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
    ds = xr.open_dataset(nc_file)
    ds.attrs["binary_mask_tests"] = test
    ds.attrs["binary_mask_tests_value"] = [0, 64, 90, 5.0, 5.0, 5.0, 20, 20, None]

    fig_test = plot_test_fields(ds)
    fig_test.show()

    fig_polar = plot_polar_velocities(ds)
    fig_polar.show()

    fig_vel = plot_velocity_fields(ds)
    fig_vel.show()
