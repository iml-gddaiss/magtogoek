"""
module to map xarray dataset to Odf
"""
import re

import pandas as pd
import xarray as xr
from magtogoek.odf_format import Odf, odf_time_format

# Add a int suffix (_01) to parameter codes increasing with each new parameter of the same type.
# - dtype : sing or doub
# Missing Metadata are in the magtogoek/files/odf_parameter.json.

TIME_TYPE = "SYTM"
TIME_FILL_VALUE = "17-NOV-1858 00:00:00.00"
REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

CRUISE_ATTRS = {
    "country_institute_code": ("dataset", "country_institute_code"),
    "cruise_number": ("dataset", "cruise_number"),
    "organization": ("dataset", "organization"),
    "chief_scientist": ("dataset", "chief_scientist"),
    "start_date": ("dataset", "start_date"),
    "end_date": ("dataset", "end_date"),
    "platform": ("dataset", "platform"),
    "cruise_name": ("dataset", "cruise_name"),
    "cruise_description": ("dataset", "cruise_description"),  # FIXME MISSING
    "platform": ("platform", "platform_name"),
}
EVENT_ATTRS = {
    "data_type": ("dataset", "data_type"),
    "event_number": ("dataset", "event_number"),
    "orig_creation_date": ("dataset", "date_created"),
    "start_date_time": ("dataset", "start_date_time"),
    "end_date_time": ("dataset", "end_date_time"),
    "min_depth": ("dataset", "geospatial_vertical_min"),
    "max_depth": ("dataset", "geospatial_vertical_max"),
    "sampling_interval": ("dataset", "sampling_interval"),
    "sounding": ("dataset", "sounding"),
    "event_qualifier1": ("config", "event_qualifier1"),  # FIXME MISSING
    "event_qualifier2": ("config", "event_qualifier2"),  # FIXME MISSING
    "event_comments": ("config", "event_comments"),  # FIXME MISSING
}
BUOY_ATTRS = {
    "name": ("platform", "platform_name"),
    "type": ("platform_specs", "type"),
    "model": ("platform_specs", "model"),
    "height": ("platform_specs", "height"),
    "diameter": ("platform_specs", "diameter"),
    "weight": ("platform_specs", "weight"),
    "description": ("platform_specs", "description"),
}
BUOY_INSTRUMENT_ATTRS = {
    "type": ("dataset", "manufacturer"),
    "model": ("dataset", "model"),
    "serial_number": ("dataset", "serial_number"),
    "description": ("dataset", "description"),
    "inst_start_date_time": ("dataset", "time_coverage_start"),
    "inst_end_date_time": ("dataset", "time_coverage_end"),
}


def _make_cruise_header(odf, dataset, config):
    """Use cruise_attrs """
    for key, value in CRUISE_ATTRS.items():
        if value[0] == "dataset":
            if value[1] in dataset.attrs:
                if "date" in key:
                    odf.cruise[key] = odf_time_format(dataset.attrs[value[1]])
                else:
                    odf.cruise[key] = dataset.attrs[value[1]]
        if value[0] == "platform":
            if value[1] in platform:
                odf.cruise[key] = platform[value[1]]


def _make_event_header(odf, dataset, config):
    """
    Make the event header.

    Notes
    -----
    `depth_off_bottom` is `0` if "sounding" is missing.
    """
    for key, value in EVENT_ATTRS.items():
        if value[0] == "dataset":
            if value[1] in dataset.attrs:
                if "date" in key:
                    odf.event[key] = odf_time_format(dataset.attrs[value[1]])
                else:
                    odf.event[key] = dataset.attrs[value[1]]
        if value[0] == "config":
            if value[1] in config:
                odf.event[key] = config[value[1]]
    odf.event["initial_latitude"] = dataset.lat[0]
    odf.event["initial_longitude"] = dataset.lon[0]
    odf.event["end_latitude"] = dataset.lat[-1]
    odf.event["end_longitude"] = dataset.lon[-1]
    odf.event["creation_date"] = odf_time_format(pd.Timestamp.now())
    if "sounding" in ds.attrs:
        odf.event["depth_off_bottom"] = (
            dataset.attrs["sounding"] - odf.event["max_depth"]
        )
    else:
        odf.event["depth_off_bottom"] = 0


def _make_odf_header(odf):
    """
    Make field specification with:
    data_type, cruise_number, event_number, event_qualifier1, event_qualifier2
    Joins with `_` and add the extension `.ODF`.
    """
    name_part = [
        odf.event["data_type"],
        odf.cruise["cruise_number"],
        odf.event["event_number"],
        odf.event["event_qualifier1"],
        odf.event["event_qualifier2"],
    ]
    odf.odf["file_specification"] = "_".join(name_part).strip("_") + ".ODF"


def _make_buoy_header(odf, platform):
    """
    Use BUOY_ATTRS
    """
    for key, value in BUOY_ATTRS.items():
        if value[0] == "platform_specs":
            if value[1] in platform["platform_specs"]:
                odf.buoy[key] = platform["platform_specs"][value[1]]
        if value[0] == "platform":
            if value[1] in platform:
                odf.buoy[key] = platform[value[1]]


def _make_buoy_instrument_header(odf, dataset):
    """Uses buoy_instrument_attrs
    Missing: comments and sensors
    """
    instrument = "ADCP_01"
    odf.add_buoy_instrument(instrument)
    for key, value in BUOY_INSTRUMENT_ATTRS.items():
        if value[0] == "dataset":
            if value[1] in dataset.attrs:
                if "date" in key:
                    odf.buoy_instrument[instrument][key] = odf_time_format(
                        dataset.attrs[value[1]]
                    )
                else:
                    odf.buoy_instrument[instrument][key] = dataset.attrs[value[1]]

    # _make_buoy_instrument_comment(odf, dataset)
    # _make_buoy_instrument_sensors(odf, dataset)


def _make_buoy_instrument_comment(odf, dataset):
    """TODO
        dataset.atttrs  'CONFIGURATION_01. FIXME
    Mode:                                        : orientation
    Ping_per_Ensemble: 100.0',                        : ping_per_ensemble
    Ping_Intervalle_pings_s: 0.6',                      : delta_t_sec
    Duree_dun_ensemble_s: 60.0',                       : sampling_interval
    Profondeur_de_lADCP_m: 1.0',                       : sensor_depth
    Distance_ADCP_au_centre_du_premier_bin_m: 9.75',   : dist_1_bin
    Taille_dun_bin_m: 8.0',                            : bin_size
    Nombre_de_bins: 30',                               : bin_count
    Blank_m: ',                                        : blank
    Lag_length_m: ',                                   : FIXME MISSING FROM LOADER
    Transmit_Pulse_Length_m: ',                        : transmit_pulse_length_cm (cm to m)
    Declinaison_magnetique_deg: 17.36 W',              : magnetic_declination + _unist
    Commentaire: .',                                   : comments (mettre derniere calibration ?)
    """


def _make_buoy_instrument_sensors(odf, dataset):
    """SKIPPED un peux useless pour l'adcp
    temperature_01
    compas_01
    inclinometer_01
    pressions_01
    """


def _make_history_header(odf, dataset):
    """
    One history header is made by log datetime entry.
    """
    process = [
        "Data processed by Magtogoek Proccesing Software. More at " + REPOSITORY_ADDRESS
    ]
    creation_date = pd.Timestamp.now().strftime("%d-%b-%Y %H:%M:%S.%f").upper()[:-4]

    regex = "(\[.*\])\s+([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})"
    histories = dataset.attrs["history"].strip("\n").split("\n")

    for history in histories:
        m = re.findall(regex, history)
        if m:
            odf.add_history({"creation_date": creation_date, "process": process})
            process = [m[0][0]]
            creation_date = m[0][1]
        else:
            process.append(history)
    odf.add_history({"creation_date": creation_date, "process": process})


def _make_parameter_headers():
    """
    TODO MAKE A DICTIONNARY GF3_CODE:{ITEMS}
    name : GF3 code plus _XX increament.
    units : from odf
    print_field_value = from odf
    print_decimal_value = from odf
    """


if __name__ == "__main__":
    from magtogoek.adcp.process import _get_config
    from magtogoek.configfile import load_configfile
    from magtogoek.utils import json2dict

    nc_file = "../../test/files/iml6_2017_wh.nc"
    platform_file = "../../test/files/iml_platforms.json"
    config_file = "../../test/files/adcp_iml6_2017.ini"

    ds = xr.open_dataset(nc_file)
    platform = json2dict(platform_file)["IML6_2017"]
    _, config = _get_config(load_configfile(config_file))

    odf = Odf()

    _make_cruise_header(odf, ds, platform)
    _make_event_header(odf, ds, config)
    _make_odf_header(odf)
    _make_buoy_header(odf, platform)
    _make_buoy_instrument_header(odf, ds)
    _make_history_header(odf, ds)
