"""
March 2024
"""
from typing import List, Union

from csv import reader
import pandas as pd
import xarray as xr

from magtogoek.utils import get_files_from_expression

DATA_START_DELIMITER = "D"
LINE_SAMPLE_PREFIX = "[S]"

UNITS_MAP = {
                'temperature': "degree_C",
                'conductivity': "S/m",
                'pressure': "db",
                'salinity': "PSU",
                'fluorescence': "micro-g/l",
                'oxygen': "micromol/l",
             }

def winch_reader(files: Union[str, List[str]]):
    """Made for 2024 Metis Winch Files format.
    """
    datasets = []
    for fn in get_files_from_expression(files):
        with open(fn, 'r') as f:
            header = []
            while True:
                line = f.readline()

                if line.strip('\n') == DATA_START_DELIMITER:
                    break
                else:
                    header.append(line.strip("**"))

            data = [(v0.strip(LINE_SAMPLE_PREFIX), *values)  for v0, *values in reader(f, delimiter=',') if LINE_SAMPLE_PREFIX in v0]

            df = pd.DataFrame(
                data,
                dtype=float,
                columns=['temperature', 'conductivity', 'pressure', 'salinity', 'fluorescence', 'oxygen'],
            )

            ds = xr.Dataset.from_dataframe(df)

            for var in set(ds.variables) & set(UNITS_MAP.keys()):
                ds[var].attrs['units'] = UNITS_MAP[var]


            # Adding global attributes from winch files.
            global_attrs = {}
            for line in header:
                k, v = line.replace("\t", "").strip('\n').split(":", 1)
                global_attrs[k.strip()] = v.strip()

            ds.attrs.update(global_attrs)

        datasets.append(ds)

    return datasets


if __name__ == "__main__":
    test_files = "/home/jeromejguay/ImlSpace/Data/pmza_2024/IML4-test/winch/"

    files = get_files_from_expression(test_files+"WDATA*.txt")

    dss = winch_reader(files=files)

    ds = dss[0]