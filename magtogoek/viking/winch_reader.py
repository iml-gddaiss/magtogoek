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
    import matplotlib


    import matplotlib.pyplot as plt
    winch_path = '/home/jeromejguay/ImlSpace/Data/iml4_2021/WINCH_MISSIONS/'

    # filename = 'WDATA_PMZA-RIKI_2021-06-11_093141.txt'
    filename = "*"

    datasets = winch_txt_reader(winch_path + filename)

    #ds = xr.concat(datasets, 'time')

    surface_datasets = []

    for _ds in datasets:
        _slice = _ds.where(_ds.depth < 15).where(_ds.depth > 2).mean('index')
        if 'temperature' in _slice:
            surface_datasets.append(_slice)

    ds_yoyo = xr.concat(surface_datasets,'time')
