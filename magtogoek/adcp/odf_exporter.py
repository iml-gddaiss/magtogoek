"""
module to map xarray dataset to Odf
"""
import os
import re
from pathlib import Path

import pandas as pd
import xarray as xr
from magtogoek.odf_format import Odf, odf_time_format
from magtogoek.utils import json2dict

# Add a int suffix (_01) to parameter codes increasing with each new parameter of the same type.
# - dtype : sing or doub
# Missing Metadata are in the magtogoek/files/odf_parameter.json.

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

PARAMETERS_TYPES = {
    "int8": "BYTE",
    "int16": "SHORT",
    "int32": "INT",
    "int64": "LONG",
    "float16": "HALF",
    "float32": "SING",
    "float64": "DOUB",
    "|S1": "SYTM",
    "datetime64[ns]": "SYTM",
}
PARAMETER = ["time", "depth", "u", "u_QC", "v", "v_QC", "w", "w_QC", "e"]
print(__file__)
print(os.path.dirname(__file__))
PARAMETERS_METADATA_PATH = os.path.join(
    os.path.dirname(__file__), "../files/odf_parameters_metadata.json"
)
CRUISE_ATTRS = {
    "country_institute_code": ("dataset", "country_institute_code"),
    "organization": ("dataset", "organization"),
    "chief_scientist": ("dataset", "chief_scientist"),
    "start_date": ("dataset", "start_date"),
    "end_date": ("dataset", "end_date"),
    "cruise_number": ("dataset", "cruise_number"),
    "cruise_name": ("dataset", "cruise_name"),
    "cruise_description": ("dataset", "cruise_description"),
    "platform": ("sensor_metadata", "platform_name"),  # NOTE SHOULD BE GOOD
}
EVENT_ATTRS = {
    "data_type": ("dataset", "data_type"),
    "event_number": ("dataset", "event_number"),
    "orig_creation_date": ("dataset", "date_created"),
    "start_date_time": ("dataset", "start_date"),
    "end_date_time": ("dataset", "end_date"),
    "min_depth": ("dataset", "geospatial_vertical_min"),
    "max_depth": ("dataset", "geospatial_vertical_max"),
    "sampling_interval": ("dataset", "delta_t_sec"),
    "sounding": ("dataset", "sounding"),
    "event_qualifier1": ("global_attrs", "event_qualifier1"),
    "event_qualifier2": ("global_attrs", "event_qualifier2"),
    "event_comments": ("global_attrs", "event_comments"),
}
INSTRUMENT_ATTRS = {  # NOTE SHOULD BE GOOD
    "inst_type": ("dataset", "manufacturer"),
    "model": ("dataset", "model"),
    "serial_number": ("dataset", "serial_number"),
    "description": ("dataset", "comments"),
}
BUOY_ATTRS = {
    "name": ("sensor_metadata", "platform_name"),
    "type": ("buoy_specs", "type"),
    "model": ("buoy_specs", "model"),
    "height": ("buoy_specs", "height"),
    "diameter": ("buoy_specs", "diameter"),
    "weight": ("buoy_specs", "weight"),
    "description": ("buoy_specs", "description"),
}
BUOY_INSTRUMENT_ATTRS = {
    "type": ("dataset", "manufacturer"),
    "model": ("dataset", "model"),
    "serial_number": ("dataset", "serial_number"),
    "description": ("dataset", "comments"),  # FIXME BUOY DESCRIPTION buoy_specs ?
    "inst_start_date_time": ("dataset", "time_coverage_start"),
    "inst_end_date_time": ("dataset", "time_coverage_end"),
}

BUOY_INSTRUMENT_CONFIGURATION = {
    "Mode": ("dataset", "orientation"),
    "Ping_Type": ("dataset", "ping_type"),
    "Frequency": ("dataset", "frequency"),
    "Firmware_Version": ("dataset", "firmware_version"),
    "Ping_per_Ensemble": ("dataset", "ping_per_ensemble"),
    "Ensemble_Length_s": ("dataset", "delta_t_sec"),
    "Ping_Interval_s": (),  # Computed
    "ADCP_Depth_m": ("dataset", "sensor_depth"),
    "Distance_ADCP_to_First_Bin_Center_m": ("dataset", "bin1dist"),
    "Bin_Size_m": ("dataset", "bin_size"),
    "Bin_Count": ("dataset", "bin_count"),  # Computed
    "Blank_m": ("dataset", "blank"),
    "Transmit_Pulse_Length_m": ("dataset", "transmit_pulse_length_m"),
    "Magnetic_Declination": (),  # Computed
    "Comments": ("sensor_metadata_sensors", "comments"),  # FIXME Description ?
}


def make_odf(
    dataset, sensor_metadata: dict, global_attrs: dict, generic_to_p01_name: dict = None
):
    """
    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    sensor_metadata :
        Metadata from the platform file.
    gloabal_attrs :
        Global attributes parameter from the configFile.
    generic_to_p01_name :
        map from the generic to the BODC p01 variables names

    """
    odf = Odf()

    _make_cruise_header(odf, dataset, sensor_metadata)
    _make_event_header(odf, dataset, global_attrs)
    _make_odf_header(odf)
    if sensor_metadata["platform_type"] == "buoy":
        _make_buoy_header(odf, sensor_metadata)
        _make_buoy_instrument_header(odf, dataset, sensor_metadata)
    else:
        _make_instrument_header(odf, dataset)
    _make_parameter_headers(odf, dataset, generic_to_p01_name)
    _make_history_header(odf, dataset)

    return odf


def _make_cruise_header(odf, dataset, sensor_metadata):
    """Use cruise_attrs """
    for key, value in CRUISE_ATTRS.items():
        if value[0] == "dataset":
            if value[1] in dataset.attrs:
                if "date" in key:
                    odf.cruise[key] = odf_time_format(dataset.attrs[value[1]])
                else:
                    odf.cruise[key] = dataset.attrs[value[1]]
        if value[0] == "sensor_metadata":
            if value[1] in sensor_metadata:
                odf.cruise[key] = sensor_metadata[value[1]]

    if sensor_metadata["platform_type"] == "buoy":
        odf.cruise["platform"] = "Oceanographic Buoy"
    else:
        odf.cruise["platform"] = sensor_metadata["platform_name"]


def _make_event_header(odf, dataset, global_attrs):
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
        if value[0] == "global_attrs":
            if value[1] in global_attrs:
                odf.event[key] = global_attrs[value[1]]
    if "lat" in dataset:
        odf.event["initial_latitude"] = dataset.lat[0]
        odf.event["end_latitude"] = dataset.lat[-1]
    elif "latitude" in dataset.attrs:
        odf.event["initial_latitude"] = dataset.attrs["latitude"]
        odf.event["end_latitude"] = dataset.attrs["latitude"]
    if "lon" in dataset:
        odf.event["initial_longitude"] = dataset.lon[0]
        odf.event["end_longitude"] = dataset.lon[-1]
    elif "longitude" in dataset.attrs:
        odf.event["initial_longitude"] = dataset.attrs["longitude"]
        odf.event["end_longitude"] = dataset.attrs["longitude"]

    odf.event["creation_date"] = odf_time_format(pd.Timestamp.now())

    if "sounding" in dataset.attrs:
        if dataset.attrs["sounding"] and odf.event["max_depth"]:
            odf.event["depth_off_bottom"] = (
                dataset.attrs["sounding"] - odf.event["max_depth"]
            )
        else:
            odf.event["depth_off_bottom"] = 0
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


def _make_instrument_header(odf, dataset):
    """
    inst_type
    model
    serial_number
    description
    """
    for key, value in INSTRUMENT_ATTRS.items():
        if value[0] == "dataset":
            if value[1] in dataset.attrs:
                if "date" in key and dataset.attrs[value[1]]:
                    odf.instrument[key] = odf_time_format(dataset.attrs[value[1]])
                else:
                    odf.instrument[key] = dataset.attrs[value[1]]


def _make_quality_header():
    """TODO Multiple"""


def _make_buoy_header(odf, sensor_metadata):
    """
    Use BUOY_ATTRS
    """
    for key, value in BUOY_ATTRS.items():
        if value[0] == "buoy_specs":

            if value[1] in sensor_metadata["buoy_specs"]:
                odf.buoy[key] = sensor_metadata["buoy_specs"][value[1]]
        if value[0] == "sensor_metadata":
            if value[1] in sensor_metadata:
                odf.buoy[key] = sensor_metadata[value[1]]


def _make_buoy_instrument_header(odf, dataset, sensor_metadata):
    """Uses buoy_instrument_attrs
    Missing: comments and sensors
    """
    instrument = "ADCP_01"
    odf.add_buoy_instrument(instrument)
    for key, value in BUOY_INSTRUMENT_ATTRS.items():
        if value[0] == "dataset":
            if value[1] in dataset.attrs:
                if "date" in key and dataset.attrs[value[1]]:
                    odf.buoy_instrument[instrument][key] = odf_time_format(
                        dataset.attrs[value[1]]
                    )
                else:
                    odf.buoy_instrument[instrument][key] = dataset.attrs[value[1]]

    _make_buoy_instrument_comment(odf, instrument, dataset, sensor_metadata)


def _make_buoy_instrument_comment(odf, instrument, dataset, sensor_metadata):
    """

    Note
    ----
    LagLength was removed from the original ODF adcp format.
    """
    configuration = "CONFIGURATION_01"
    for key, value in BUOY_INSTRUMENT_CONFIGURATION.items():
        if key == "Ping_Interval_s":
            if "ping_per_ensemble" in dataset.attrs and "delta_t_sec" in dataset.attrs:
                if dataset.attrs["ping_per_ensemble"] and dataset.attrs["delta_t_sec"]:
                    v = round(
                        dataset.attrs["ping_per_ensemble"]
                        / dataset.attrs["delta_t_sec"],
                        2,
                    )
        elif key == "Magnetic_Declination":
            if (
                "magnetic_declination" in dataset.attrs
                and "magnetic_declination_units" in dataset.attrs
            ):
                v = (
                    str(dataset.attrs["magnetic_declination"])
                    + " "
                    + dataset.attrs["magnetic_declination_units"]
                )
        elif key == "Bin_Count":
            v = len(dataset.depth)
        elif value[0] == "dataset" and value[1] in dataset.attrs:
            v = dataset.attrs[value[1]]
        elif value[0] == "sensor_metadata":
            v = sensor_metadata[value[1]]
        else:
            v = ""
        odf.buoy_instrument[instrument]["buoy_instrument_comments"].append(
            configuration + "." + key + ": " + str(v)
        )


def _make_history_header(odf, dataset):
    """
    One history header is made by log datetime entry.
    THe historie header is made with dataset.attrs['quality_comments']
    """
    process = [
        "Data processed by Magtogoek Proccesing Software. More at " + REPOSITORY_ADDRESS
    ]
    creation_date = pd.Timestamp.now().strftime("%d-%b-%Y %H:%M:%S.%f").upper()[:-4]

    regex = "(\[.*\])\s+([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})"
    histories = dataset.attrs["quality_comments"].strip("\n").split("\n")

    for history in histories:
        m = re.findall(regex, history)
        if m:
            odf.add_history({"creation_date": creation_date, "process": process})
            process = [m[0][0]]
            creation_date = m[0][1]
        else:
            process.append(history)
    odf.add_history({"creation_date": creation_date, "process": process})


def _make_parameter_headers(odf, dataset, generic_to_p01_name=None):
    """
    Parameters
    ----------
    odf :
    dataset :
        Dataset to which add the navigation data.
    generic_to_p01_name :
        map from the generic to the BODC p01 variables names
    """

    parameters_metadata = json2dict(PARAMETERS_METADATA_PATH)  # FIXME

    if generic_to_p01_name:
        for param in PARAMETER:
            if param in generic_to_p01_name:
                parameters_metadata[
                    generic_to_p01_name[param]
                ] = parameters_metadata.pop(param)

    data = dataset[list(parameters_metadata.keys())].to_dataframe().reset_index()

    for var in parameters_metadata:
        if var in dataset:
            items = {}
            for key, value in parameters_metadata[var].items():
                items[key] = value

            items["depth"] = dataset.attrs["sensor_depth"]
            if "_QC" not in var:
                items["magnetic_variation"] = dataset.attrs["magnetic_declination"]
            items["type"] = PARAMETERS_TYPES[str(dataset[var].data.dtype)]

            if "null_value" not in items:
                if "_FillValue" in dataset[var].encoding:
                    items["null_value"] = dataset[var].encoding["_FillValue"]
                else:
                    items["null_value"] = None

            odf.add_parameter(
                code=items["code"],
                data=data[var].fillna(items["null_value"]),
                items=items,
            )


if __name__ == "__main__":
    from magtogoek.adcp.process import _get_config, _load_platform
    from magtogoek.configfile import load_configfile

    _nc_file = "../../test/files/iml6_2017_wh.nc"
    _platform_files = "../../test/files/iml_platforms.json"
    _config_file = "../../test/files/adcp_iml6_2017.ini"

    _dataset = xr.open_dataset(_nc_file)
    _params, _global_attrs = _get_config(load_configfile(_config_file))
    _params["platform_file"] = _platform_files
    _sensor_metadata = _load_platform(_params)

    _p01_to_generic_name = {
        "u": "LCEWAP01",
        "u_QC": "LCEWAP01_QC",
        "v": "LCNSAP01",
        "v_QC": "LCNSAP01_QC",
        "w": "LRZAAP01",
        "w_QC": "LRZAAP01_QC",
        "e": "LERRAP01",
    }

    _odf = make_odf(_dataset, _sensor_metadata, _global_attrs, _p01_to_generic_name)
