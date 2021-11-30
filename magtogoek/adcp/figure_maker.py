"""
author: Jérôme Guay
date: Nov. 29, 2021
"""
import matplotlib.colorbar as clb
import matplotlib.colors as mplc
import matplotlib.pyplot as plt

font = {"family": "serif", "color": "darkred", "weight": "normal", "size": 14}
binary_cmap = mplc.ListedColormap(["limegreen", "orangered"])
plt.style.use("seaborn-dark-palette")


def make_fig8():
    """
    """
    plt.close("all")

    plt.style.use("seaborn-dark-palette")

    fig = plt.figure(figsize=(8.5, 11))
    axes = []

    f_L, f_B, f_W, f_H = 0.1, 0.77, 0.44, 0.20
    h_spacing, v_spacing = 0.012, 0.025

    for j in range(4):
        axes.append(
            [
                fig.add_axes(
                    [f_L + (f_W + h_spacing) * i, f_B - (f_H + v_spacing) * j, f_W, f_H]
                )
                for i in range(2)
            ]
        )

    return fig, axes


def plot_test(dataset):

    fig, axes = make_fig8()
    axes = [item for sublist in axes for item in sublist]

    for bit, test_name in enumerate(ds.attrs["binary_mask_tests"]):
        mask = (ds.binary_mask.astype(int) & 2 ** bit).astype(bool)
        axes[bit].invert_yaxis()
        axes[bit].pcolormesh(ds.time, ds.depth, mask, cmap=binary_cmap, shading="auto")
        axes[bit].set_title(test_name, fontdict=font)

        if bit != 2:
            axes[bit].tick_params(labelleft=False)
        else:
            axes[bit].set_ylabel("depth [m]", fontdict=font)
        if bit != 6:
            axes[bit].tick_params(labelbottom=False)
            axes[bit].set_xlabel("")
        else:
            axes[bit].set_xlabel("time", fontdict=font)

    cbar_axe = fig.add_axes([0.54 + 0.012, 0.075, 0.44, 0.01])
    cbar = clb.ColorbarBase(
        cbar_axe, cmap=binary_cmap, ticks=[0.25, 0.75], orientation="horizontal",
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
        "horizontal",
        "vertical",
        "error",
        "roll",
        "pitch",
        #        "sidelobe",
    ]
    ds = xr.open_dataset(nc_file)
    ds.attrs["binary_mask_tests"] = test
    fig = plot_test(ds)
    fig.show()
