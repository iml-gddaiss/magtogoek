"""
author: Jérôme Guay
date: Nov. 29, 2021
"""
import sys
import warnings

import cmocean as cmo
import matplotlib as mpl
import matplotlib.colorbar as clb
import matplotlib.pyplot as plt
import numpy as np
import xarray as xr
from magtogoek.tools import cartesian2northpolar
from mpl_toolkits.axes_grid1 import ImageGrid

# warnings.simplefilter("error", UserWarning)

FONT = {"family": "serif", "color": "darkred", "weight": "normal", "size": 12}
BINARY_CMAP = plt.get_cmap("viridis_r", 2)
VEL_CMAP = cmo.cm.balance
plt.style.use("seaborn-dark-palette")


def grid_subplot(axe, nrows, ncols):
    for c in range(ncols - 1):
        axe.plot(
            [(c + 1) / ncols, (c + 1) / ncols],
            [0, 1],
            color="black",
            lw=0.5,
            ls="--",
            transform=axe.figure.transFigure,
            clip_on=False,
        )
    for r in range(nrows - 1):
        axe.plot(
            [0, 1],
            [(r + 1) / nrows, (r + 1) / nrows],
            color="black",
            lw=0.5,
            ls="--",
            transform=axe.figure.transFigure,
            clip_on=False,
        )


def flag_data(dataset, var, flag_thres: int = 2):
    return dataset[var].where(dataset[var + "_QC"].data <= flag_thres).data


def polar_histo(dataset: xr.Dataset, x_vel, y_vel, r_max):
    u = flag_data(dataset, x_vel).flatten()
    v = flag_data(dataset, y_vel).flatten()
    ii = np.isfinite(u) & np.isfinite(v)

    azimut, radius = cartesian2northpolar(u[ii], v[ii])

    rN, aN = 30, 180
    rbins, abins = np.linspace(0, r_max, rN), np.linspace(0, 2 * np.pi, aN)

    return np.histogram2d(azimut, radius, bins=(abins, rbins))


def plot_velocity_polar_hist(
    dataset, nrows=3, ncols=3, x_vel="u", y_vel="v",
):
    naxes = int(nrows * ncols)
    r_max = np.nanmax(np.hypot(flag_data(dataset, x_vel), flag_data(dataset, y_vel)))
    r_max = np.ceil(r_max * 5) / 5
    r_ticks = np.round(np.linspace(0, r_max, 6), 2)[1:]

    bin_depths = np.linspace(dataset.depth.min(), dataset.depth.max(), naxes + 1)

    fig, axes = plt.subplots(
        figsize=(12, 8),
        nrows=nrows,
        ncols=ncols,
        subplot_kw={"projection": "polar"},
        constrained_layout=True,
    )
    axes = axes.flatten()
    grid_subplot(axes[0], nrows, ncols)
    for index in range(naxes):
        histo, a_edges, r_edges = polar_histo(
            dataset.sel(depth=slice(bin_depths[index], bin_depths[index + 1])),
            x_vel,
            y_vel,
            r_max,
        )

        histo[histo < 1] = np.nan
        if np.isfinite(histo).any():
            histo /= np.nanmax(histo)
            pc = axes[index].pcolormesh(
                a_edges, r_edges, histo.T, cmap=cmo.cm.amp, shading="flat",
            )
        axes[index].set_title(
            f"Depth: {round((bin_depths[index] + bin_depths[index+1])/2,0)} m",
            fontdict=FONT,
            loc="left",
        )
        axes[index].grid(True)
        axes[index].set_theta_zero_location("N")
        axes[index].set_theta_direction(-1)
        axes[index].set_rgrids(r_ticks, angle=0)
        axes[index].set_yticklabels([])

        rlabels_rpos = np.hypot(1.3 * r_max, r_ticks)
        rlabels_tpos = np.arctan2(1.3 * r_max, r_ticks)

        for label, rpos, tpos, rtick in zip(
            r_ticks, rlabels_rpos, rlabels_tpos, r_ticks
        ):
            axes[index].text(
                tpos,
                rpos,
                f"{label:.2f}",
                fontsize=10,
                clip_on=False,
                va="center",
                rotation=0,
            )
            axes[index].plot(
                (0, tpos), (rtick, rpos), "--", lw=0.6, c="k", clip_on=False,
            )
        axes[index].set_ylim(0, r_max)
        axes[index].text(
            np.arctan2(1.6 * r_max, np.mean(r_ticks)),
            np.hypot(1.6 * r_max, np.mean(r_ticks)),
            "velocity [m s$^{-1}$]",
            rotation=90,
            va="center",
            fontsize=12,
        )
        axes[index].set_facecolor("lightslategrey")
        axes[index].set_xlabel("absolute bearing [deg]", fontsize=12)

    return fig


def plot_velocity_fields(dataset: xr.Dataset, flag_thres: int = 2):
    fig = plt.figure(figsize=(12, 8))

    axes = ImageGrid(
        fig,
        111,
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
        vmax = np.ceil(np.max(np.abs(vel_da)) * 5) / 5
        im = axes[index].pcolormesh(
            dataset.time,
            dataset.depth,
            vel_da,
            shading="auto",
            cmap=VEL_CMAP,
            vmin=-vmax,
            vmax=vmax,
        )
        cax = axes[index].cax
        cbar = plt.colorbar(im, cax)
        cax.set_ylabel(dataset[var].attrs["units"], fontdict=FONT)
        cbar.set_ticks(np.linspace(-vmax, vmax, 5))
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
    for index, test_name in enumerate(dataset.attrs["binary_mask_tests"]):
        value = dataset.attrs["binary_mask_tests_value"][index]
        if value is not None:
            mask = (dataset.binary_mask.astype(int) & 2 ** index).astype(bool)
            im = axes[index].pcolormesh(
                dataset.time, dataset.depth, mask, cmap=BINARY_CMAP, shading="auto"
            )
            axes[index].set_title(test_name + f": {value}", fontdict=FONT)
        axes[index].tick_params(labelleft=False, labelbottom=False)

    axes[-1].invert_yaxis()
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


if __name__ == "__main__":
    import xarray as xr

    # nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml6_2017_wh.nc"
    # nc_file = "/home/jeromejguay/ImlSpace/Projects/magtogoek/test/files/iml4_2017_sw.nc"
    # nc_file = "/home/jeromejguay/ImlSpace/Data/MPO/iml42020/MADCP_BOUEE2020_RIMOUSKI_553_VEL.nc"
    nc_file = "/home/jeromejguay/ImlSpace/Data/MPO/iml42020/iml4_2020_no_mcorr.nc"
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
    # fig_polar = plot_velocity_polar_hist(ds, 2, 3)
    # fig_vel = plot_velocity_fields(ds)

    plt.show()
