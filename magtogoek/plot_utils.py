import matplotlib.pyplot as plt


def grid_subplot(axe: plt.Axes, nrows: int, ncols: int):
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