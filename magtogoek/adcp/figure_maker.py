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
FONT = {"family": "serif", "color": "darkred", "weight": "normal", "size": 12}
BINARY_CMAP = plt.get_cmap("viridis_r", 2)
VEL_CMAP = cmo.balance


def cartesian2northpolar(x, y):
    """Return the azimut and the radius."""
    azimut = (np.arctan2(x, y) + 2 * np.pi) % (2 * np.pi)
    radius = np.hypot(x, y)
    return azimut, radius


def polar_histo(dataset: xr.Dataset, x_vel="u", y_vel="v", flag_thres: int = 2):
    u = dataset[x_vel].where(dataset[x_vel + "_QC"] <= flag_thres).data.flatten()
    v = dataset[y_vel].where(dataset[y_vel + "_QC"] <= flag_thres).data.flatten()
    ii = np.isfinite(u) & np.isfinite(v)

    azimut, radius = cartesian2northpolar(u[ii], v[ii])

    rN, aN = 30, 180
    r_max, a_max = np.round(np.max(radius), 2) + 0.1, 2 * np.pi
    rbins, abins = np.linspace(0, r_max, rN), np.linspace(0, a_max, aN)

    return np.histogram2d(azimut, radius, bins=(abins, rbins))


def plot_velocity_polar_hist(dataset, nrows=3, ncols=3):
    naxes = int(nrows * ncols)
    bin_depths = np.linspace(dataset.depth.min(), dataset.depth.max(), naxes + 1)
    fig, axes = plt.subplots(
        figsize=(12, 8),
        nrows=nrows,
        ncols=ncols,
        subplot_kw={"projection": "polar"},
        constrained_layout=True,
    )
    axes = axes.flatten()
    for index in range(naxes):
        histo, a_edges, r_edges = polar_histo(
            dataset.sel(depth=slice(bin_depths[index], bin_depths[index + 1]))
        )
        # histo[histo < 1] = np.nan
        _ = axes[index].pcolormesh(
            a_edges, r_edges, histo.T, cmap=cmo.amp, shading="auto"
        )
        axes[index].set_title(
            f"{round((bin_depths[index] + bin_depths[index+1])/2,0)} m", fontdict=FONT,
        )
        axes[index].grid(True)
        axes[index].set_theta_zero_location("N")
        axes[index].set_theta_direction(-1)
        axes[index].set_rgrids([0.25, 0.5, 0.75, 1.00], angle=55)
    # axes[index].text(-0.08, 1.1, s="North", fontdict=FONT)
    # axes[index].text(np.pi / 2 + 0.02, 1.11, s="East", fontdict=FONT)

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
            dataset.time, dataset.depth, vel_da, shading="auto", cmap=VEL_CMAP,
        )
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
        fig, 111, nrows_ncols=(3, 3), axes_pad=0.3, share_all=True, aspect=False
    )

    # Add data to image grid
    for index, test_name in enumerate(dataset.attrs["binary_mask_tests"]):
        value = dataset.attrs["binary_mask_tests_value"][index]
        if value is not None:
            mask = (dataset.binary_mask.astype(int) & 2 ** index).astype(bool)

            im = axes[index].pcolormesh(
                dataset.time, dataset.depth, mask, cmap=BINARY_CMAP, shading="auto"
            )
            axes[index].set_title(test_name + f": {value}", fontdict=FONT)
            axes[index].tick_params(labelleft=False)
            axes[index].tick_params(labelbottom=False)
            axes[index].set_xlabel("")

    axes[-1].invert_yaxis()
    axes[3].set_ylabel("depth [m]", fontdict=FONT)
    axes[7].tick_params(rotation=-30)
    axes[7].set_xlabel("time", fontdict=FONT)

    cbar_axe = fig.add_axes([0.15, 0.08, 0.2, 0.005])
    cbar = clb.ColorbarBase(
        cbar_axe, cmap=BINARY_CMAP, ticks=[0.25, 0.75], orientation="horizontal",
    )
    cbar.set_ticklabels(["Passed", "Failed"])

    return fig


if __name__ == "__main__":
    import xarray as xr

    nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml6_2017_wh.nc"
    nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml4_2017_.nc"
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

    #    fig_test = plot_test_fields(ds)

    fig_polar = plot_velocity_polar_hist(ds, 2, 4)
    #    fig_vel = plot_velocity_fields(ds)

    plt.show()
