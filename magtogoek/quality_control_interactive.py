import numpy as np
#import datetime
#import matplotlib.dates as mdate
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.widgets as mwidgets
import matplotlib.backend_bases as mevent

#RED = mcolors.to_rgba('red')
BLUE = mcolors.to_rgba('deepskyblue')
#DBLUE = mcolors.to_rgba('darkblue')
GREEN = mcolors.to_rgba('lime')
#GOLD = mcolors.to_rgba('gold')
ORANGE = mcolors.to_rgba('orange')

class SelectFromCollection:
    def __init__(self, axe, collection, alpha_other=0.3):
        self.canvas = axe.figure.canvas
        self.collection = collection
        self.alpha_other = alpha_other

        self.xys = collection.get_offsets()
        self.Npts = len(self.xys)

        # Ensure that we have separate colors for each object

        self.default_fc = BLUE
        self.fc = np.tile(self.default_fc, (self.Npts, 1))
        self.collection.set_facecolors(self.fc)
        self.collection.set_edgecolor('k')
        self.collection.set_linewidth(.1)

        self.rect_selection = mwidgets.RectangleSelector(axe, onselect=self.onselect, useblit=True)

        self.selection_buffer = None

        self.selected_indices = set()

    def onselect(self, click_event, release_event): #MouseEvent

        # reset to selections colors
        self.fc[:, :] = self.default_fc
        self.fc[list(self.selected_indices), :-1] = GREEN[:-1]

        _ext = list(self.rect_selection.extents)
        xx, yy = np.array(pts.get_offsets()).T
        self.selection_buffer = np.where((xx >= _ext[0]) & (xx <= _ext[1]) & (yy >= _ext[2]) & (yy <= _ext[3]))[0]

        if click_event.button == mevent.MouseButton.RIGHT:
            self.selection_buffer = list(set(self.selection_buffer) & self.selected_indices)

        # set selection_buffer colors
        self.fc[self.selection_buffer, :-1] = ORANGE[:-1]

        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

    def disconnect(self):
        self.rect_selection.disconnect_events()
        self.fc[:, :] = self.default_fc
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()


    def append(self): # 'a'
        self.selected_indices = set(list(self.selected_indices) + list(self.selection_buffer))
        self.selection_buffer = None

        # set selection colors
        self.fc[:, :] = self.default_fc
        self.fc[list(self.selected_indices), :-1] = GREEN[:-1]

        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

    def remove(self): # 'r'
        self.selected_indices -= set(self.selection_buffer)
        self.selection_buffer = None

        self.fc[:, :] = self.default_fc
        self.fc[list(self.selected_indices), :-1] = GREEN[:-1]
        self.collection.set_facecolors(self.fc)
        self.canvas.draw_idle()

def selector_factory(axe, collection, indices: list):
    selector = SelectFromCollection(axe, collection)
    def point_selection_event(event):
        nonlocal  indices
        if event.key == "enter":
            selector.disconnect()
            indices += list(selector.selected_indices)
            fig.canvas.draw()
        elif event.key == "a":
            selector.append()
        elif event.key == "r":
            selector.remove()

    fig = axe.get_figure()

    fig.canvas.mpl_connect("key_press_event", point_selection_event)

def zoom_factory(axe, base_scale = 1.2, max_zoom_in = 10):

    max_left, max_right = axe.get_xlim()

    zoom_count = 0

    def zoom_fun(event):
        nonlocal zoom_count
        # get the current x and y limits
        cur_xlim = axe.get_xlim()

        # get cursor location
        xdata = event.xdata  # get event x location

        if xdata is None:
            return None

        # set the range
        # Get distance from the cursor to the edge of the figure frame

        x_left = xdata - cur_xlim[0]
        x_right = cur_xlim[1] - xdata

        scale_factor = 1
        if event.button == 'up':
            # deal with zoom in
            if zoom_count < max_zoom_in:
                scale_factor = 1/base_scale
                zoom_count += 1
        elif event.button == 'down':
            # deal with zoom out
            if zoom_count > 0:
                scale_factor = base_scale
                zoom_count -= 1
            else:
                scale_factor = 10

        if scale_factor != 1:
            new_x_left = xdata - x_left * scale_factor
            new_x_right = xdata + x_right * scale_factor

            if new_x_left < max_left:
                new_x_left = max_left
            if new_x_right > max_right:
                new_x_right = max_right

            # set new limits
            axe.set_xlim([new_x_left, new_x_right])


            axe.figure.canvas.draw_idle() # force re-draw the next time the GUI refreshes

    fig = axe.get_figure() # get the figure of interest
    # attach the call back
    fig.canvas.mpl_connect('scroll_event',zoom_fun)


if __name__ == '__main__':
    import xarray as xr
    import matplotlib.pyplot as plt

    plt.close('all')

    path = '/home/jeromejguay/ImlSpace/Data/pmza_2023/IML-4/iml4_meteoce_2023.nc'

    generic_var = 'atm_temperature'
    ds=xr.open_dataset(path)

    var_map = {ds[v].attrs['generic_name']:v for v in ds.variables}

    bodc_var = var_map[generic_var]
    data = ds[bodc_var]

    ancillary_var = ds[bodc_var].attrs["ancillary_variables"]

    fig, ax = plt.subplots()
    ax.plot(data.time, data.values, '--', zorder = 0)
    pts = ax.scatter(data.time, data.values, zorder=1)

    ax.get_xlim()
    ax.get_ylim()

    indices_list = []

    selector_factory(ax, collection=pts, indices=indices_list)
    zoom_factory(ax, base_scale=2)

    #ds[ancillary_var][indices_list] = 9

    plt.show()

