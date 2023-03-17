from typing import List, Union

import pandas as pd
import xarray as xr

from magtogoek.utils import get_files_from_expression


def winch_txt_reader(files: Union[str, List[str]]):
    datasets = []
    for fn in get_files_from_expression(files):
        with open(fn, 'r') as f:
            time = pd.to_datetime(f.readline().strip('\n'), format='%H:%M:%S %y/%m/%d')

            while True:
                l = f.readline()

                if "D" in l:
                    break

            df = pd.read_csv(f,
                             names=['temperature', 'conductivity', 'depth', 'salinity', 'unknown0', 'unknown1'],
                             na_values={'unknown1': 'S0001'}
                             )#, index_col='depth')

            ds = xr.Dataset.from_dataframe(df)

            ds=ds.assign_coords({'time': time})
   #          ds = xr.Dataset({
   #              'temperature': (['depth', 'time'], df['temperature']]),
   #              'conductivity': (['depth', 'time'], df['conductivity'].values]),
   #              # 'depth': (['depth', 'time'], df['depth']),
   #              'unknown0': (['depth', 'time'], df['unknown0'].values]),
   #              'unknown1': (['depth', 'time'], df['unknown1'].values]),
   #          },
   # #             coords={'time': time, 'depth': df['depth'].values}
   #          )

        datasets.append(ds)

    return datasets


if __name__ == "__main__":
    # import matplotlib

    import numpy as np
    import matplotlib.pyplot as plt

    # winch_path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/WINCH_MISSIONS/'
    #
    # # filename = 'WDATA_PMZA-RIKI_2021-06-11_093141.txt'
    # filename = "*"
    #
    # datasets = winch_txt_reader(winch_path + filename)
    #
    # #ds = xr.concat(datasets, 'time')
    #
    # surface_datasets = []
    #
    # for _ds in datasets:
    #     _slice = _ds.where(_ds.depth < 15).where(_ds.depth > 2).mean('index')
    #     if 'temperature' in _slice:
    #         surface_datasets.append(_slice)
    #
    # ds_yoyo = xr.concat(surface_datasets,'time')

    # UNRELATED WIND AVERAGED DIRECTION EXAMPLE
    # wind_speed = np.array([0, 2, 4, 6, 20, 30, 40])
    #
    # wind_direction = np.array([0, 2, 10, 20, 40, 55, 56])
    #
    # heading = np.array([10, 10, 10, 10, 12, 16, 30])
    #
    # absolute_wind_direction = (wind_direction + heading) % 360
    #
    # #fig0 = plt.figure()
    # fig0, axes = plt.subplots(4, 1, sharex=True)
    # axes[0].plot(wind_speed)
    # axes[0].set_ylabel('wind speed')
    # axes[1].plot(wind_direction)
    # axes[1].set_ylabel('wind direction')
    #
    # axes[2].plot(heading)
    # axes[2].set_ylabel('heading')
    #
    # axes[3].plot(absolute_wind_direction)
    # axes[3].set_ylabel('absolute wind direction')
    #
    # ###############
    # average_wind_direction = np.sum(((wind_speed * wind_direction))) / wind_speed.sum()
    #
    # wind_direction_mean = np.mean(wind_direction)
    #
    # ################
    #
    # fig1, axe = plt.subplots(figsize=(12, 8), nrows=1, ncols=1,
    #                          subplot_kw={"projection": "polar"}, constrained_layout=True)
    #
    # axe.plot(np.deg2rad(wind_direction), wind_speed,  clip_on=False)
    #
    # axe.vlines(np.deg2rad(average_wind_direction), 0, 30, colors='red', zorder=3, label='mean wind direction')
    # axe.vlines(np.deg2rad(wind_direction_mean), 0, 30, colors='black', zorder=3, label='wind direction mean')
    #
    # axe.set_theta_zero_location("N")
    # axe.set_theta_direction(-1)
    #
    # fig1.legend()
    #
    #
    # ###################
    #
    # real_time_correction = np.sum(((wind_speed * absolute_wind_direction))) / wind_speed.sum()
    #
    # post_correction = average_wind_direction + np.mean(heading)
    #
    # ###################
    #
    # fig2, axe = plt.subplots(figsize=(12, 8), nrows=1, ncols=1,
    #                          subplot_kw={"projection": "polar"}, constrained_layout=True)
    #
    # axe.plot(np.deg2rad(absolute_wind_direction), wind_speed, clip_on=False)
    #
    # axe.vlines(np.deg2rad(real_time_correction), 0, 30, colors='red', zorder=3, label='real time correction')
    # axe.vlines(np.deg2rad(post_correction), 0, 30, colors='black', zorder=3, label='post correction')
    #
    # axe.set_theta_zero_location("N")
    # axe.set_theta_direction(-1)
    #
    # fig2.legend()
    # plt.show()
    #
    #
    #
