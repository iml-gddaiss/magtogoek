#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""FIXME This is a awesome
    python script!
Author: JeromeJGuay
Date: January 30 2021
"""

from typing import Any, Dict, List, Tuple, Type

import numpy as np
import pandas as pd
import xarray as xr


def add_attrs2vars(dataset: Type[xr.Dataset], var_metadata_dict: Type[Dict]):
    """
    FIXME
    """
    for var in dataset.var():
        for attr_key, attr_item in var_metadata_dict[var]['attrs'].items():
            dataset[var].attrs[attr_key] = attr_item
        for encoding_key, encoding_item in var_metadata_dict[var][
                'encoding'].items():
            dataset[var].encoding[encoding_key] = encoding_item


def csv2dict(csv_file):
    """
    FIXME
    """
    var_metadata_dict = dict()

    md = pd.read_csv(csv_file, index_col=0).to_dict()
    for var, item in md.items():
        var_metadata_dict[var] = dict(attrs=dict(), encoding=dict())
        for prefix, attr in item.items():
            x, y = prefix.split('/')
            if x == 'attrs' and type(attr) is str:
                var_metadata_dict[var][x][y] = attr
            if x == 'encoding' and type(attr) is str:
                var_metadata_dict[var][x][y] = attr

    return var_metadata_dict


class VarMetadata(dict):
    """FIXME
    """
    def __init__(self,
                 dataset: Tuple[Type[xr.Dataset], str],
                 standard: bool = False):
        """FIXME
        """
        self.dataset = dataset
        self._metadata2dict()
        del self.dataset

        self.data_attrs = {
            'units', 'long_name', 'ancillary_variables', 'sensor_type',
            'generic_name', 'comment', 'legacy_GF3_code', 'sdn_parameter_name',
            'sdn_uom_urn', 'sdn_uom_name', 'standard_name'
        }

        self.data_encoding = {'dtype'}

    def _metadata2dict(self):
        """
        FIXME
        """
        if isinstance(self.dataset, (xr.DataArray, xr.Dataset)):
            #           self['data_vars'] = dict()
            #           self['coords'] = dict()
            for var in self.dataset.var():
                self[var] = dict(attrs=self.dataset[var].attrs,
                                 encoding=self.dataset[var].encoding)

            for coord in self.dataset.coords.keys():
                self[coord] = dict(attrs=self.dataset[coord].attrs,
                                   encoding=self.dataset[coord].encoding)
            return

        if isinstance(self.dataset, str):
            self.dataset = xr.open_dataset(self.dataset)
            self._metadata2dict()
        else:
            raise TypeError('Wrong input type')

    def filter_metadata(self):
        """
        keep only data_attrs and data_encoding
        """
        for var in self.keys():
            for attr in set(self[var]['attrs'].keys()).difference(
                    self.data_attrs):
                if attr in self[var]['attrs']:
                    self[var]['attrs'].pop(attr)

            for encoding in set(self[var]['encoding'].keys()).difference(
                    self.data_encoding):
                if encoding in self[var]['encoding']:
                    self[var]['encoding'].pop(encoding)

    def set_data_attrs(self, data_attrs):
        """
        """
        self.data_attrs = set(data_attrs)

    def set_data_encoding(self, data_encoding):
        """
        """
        self.data_encoding = set(data_encoding)

    def to_csv(self, output_fn):
        """
        FIXME
        """
        pd.DataFrame(self.csv_dict).to_csv(output_fn)

    def csv_format(self):
        """
        FIXME
        """
        self.csv_dict = dict()
        for var in self:
            self.csv_dict[var] = dict()
            for key, item in self[var]['attrs'].items():
                self.csv_dict[var]['attrs' + '/' + key] = item
            for key, item in self[var]['encoding'].items():
                self.csv_dict[var]['encoding' + '/' + key] = item


if __name__ == "__main__":
    #ds = xr.Dataset({})
    #for var, i in md_dict.items():
    #    ds = ds.assign({var: (['na'], np.array([]))})
    #    ds = ds.attrs = i['attrs']
    #    ds = ds.encoding = i['encoding']

    fn_c = '/home/jeromeguay/Shared_Folder/WorkSpace/Data/Caroline/MADCP_2018014_NS1_8336_900.nc'
    fn_h = '/home/jeromeguay/Workspace/Project/pycurrents_ADCP_processing/ncdata/a1_20050503_20050504_0221m.adcp.L1.nc'

    ds_c = xr.open_dataset(fn_c)
    ds_h = xr.open_dataset(fn_h)

    attrs_h = set(ds_h.attrs.keys())
    attrs_c = set(ds_c.attrs.keys())
