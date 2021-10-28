"""
module to map xarray dataset to Odf
"""
import re
from collections import namedtuple
from pathlib import Path

from datetime import datetime
import xarray as xr
from magtogoek.odf_format import Odf, odf_time_format
from magtogoek.utils import json2dict

# - dtype : sing or doub

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

PARAMETERS_TYPES = {
    "int8": "BYTE", #-128, 127
    "int16": "SHORT", #-32768, 32767
    "int32": "INT",
    "int64": "LONG",
    "float16": "HALF",
    "float32": "SING",
    "float64": "DOUB",
    "|S1": "SYTM",
    "datetime64[ns]": "SYTM",
}

PARAMETERS = ("time", "depth", "u", "u_QC", "v", "v_QC", "w", "w_QC", "e")
PARAMETERS_METADATA_RELATIVE_PATH = "../files/odf_parameters_metadata.json"
PARAMETERS_METADATA_ABSOLUTE_PATH = (
    Path(__file__)
    .resolve()
    .parent.joinpath(PARAMETERS_METADATA_RELATIVE_PATH)
    .resolve()
)

meta_map = namedtuple('meta_map', ['source', 'key'], defaults=[None, None])


EVENT_ATTRS = {
    "data_type": meta_map("dataset", "data_type"), #dataset
    "orig_creation_date": meta_map("dataset", "date_created"),

    "sampling_interval": meta_map("dataset", "delta_t_sec"),
    "event_number": meta_map("global_attrs", "event_number"),
    "event_qualifier1": meta_map("global_attrs", "event_qualifier1"),
    "event_qualifier2": meta_map("global_attrs", "event_qualifier2"),
    "event_comments": meta_map("global_attrs", "event_comments"),
}
INSTRUMENT_ATTRS = {  # NOTE SHOULD BE GOOD
    "inst_type": meta_map("dataset", "manufacturer"),
    "model": meta_map("dataset", "model"),
    "serial_number": meta_map("dataset", "serial_number"),
    "description": meta_map("dataset", "comments"),
}
BUOY_ATTRS = {
    "name": meta_map("sensor_metadata", "platform_name"),
    "type": meta_map("buoy_specs", "type"),
    "model": meta_map("buoy_specs", "model"),
    "height": meta_map("buoy_specs", "height"),
    "diameter": meta_map("buoy_specs", "diameter"),
    "weight": meta_map("buoy_specs", "weight"),
    "description": meta_map("buoy_specs", "description"),
}
BUOY_INSTRUMENT_ATTRS = {
    "type": meta_map("dataset", "manufacturer"),
    "model": meta_map("dataset", "model"),
    "serial_number": meta_map("dataset", "serial_number"),
    "description": meta_map("dataset", "comments"),  # FIXME BUOY DESCRIPTION buoy_specs ?
    "inst_start_date_time": meta_map("dataset", "time_coverage_start"),
    "inst_end_date_time": meta_map("dataset", "time_coverage_end"),
}
BUOY_INSTRUMENT_CONFIGURATION = {
    "Mode": meta_map("dataset", "orientation"),
    "Ping_Type": meta_map("dataset", "ping_type"),
    "Frequency": meta_map("dataset", "frequency"),
    "Firmware_Version": meta_map("dataset", "firmware_version"),
    "Ping_per_Ensemble": meta_map("dataset", "ping_per_ensemble"),
    "Ensemble_Length_s": meta_map("dataset", "delta_t_sec"),
    "Ping_Interval_s": None,
    "ADCP_Depth_m": meta_map("dataset", "sensor_depth"),
    "Distance_ADCP_to_First_Bin_Center_m": meta_map("dataset", "bin1dist"),
    "Bin_Size_m": meta_map("dataset", "bin_size"),
    "Bin_Count": None,
    "Blank_m": meta_map("dataset", "blank"),
    "Transmit_Pulse_Length_m": meta_map("dataset", "transmit_pulse_length_m"),
    "Magnetic_Declination": None,
    "Comments": meta_map("sensor_metadata_sensors", "comments"),  # FIXME Description ?
}

def make_odf(
    dataset: xr.Dataset,
    sensor_metadata: dict,
    global_attrs: dict,
    generic_to_p01_name: dict = None,
    output_path: str = None
):
    """
    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    sensor_metadata :
        Metadata from the platform file.
    global_attrs :
        Global attributes parameter from the configFile.
    generic_to_p01_name :
        map from the generic to the BODC p01 variables names

    """
    odf = Odf()

    _make_cruise_header(odf, sensor_metadata, global_attrs)
    _make_event_header(odf, dataset, global_attrs)
    _make_odf_header(odf)
    if sensor_metadata["platform_type"] == "buoy":
        _make_buoy_header(odf, sensor_metadata)
        _make_buoy_instrument_header(odf, dataset, sensor_metadata)
    else:
        _make_instrument_header(odf, dataset)
    _make_parameter_headers(odf, dataset, generic_to_p01_name)
    _make_history_header(odf, dataset)

    output_path = Path(output_path)

    if output_path:

    return odf


def _make_cruise_header(odf, sensor_metadata, global_attrs):
    odf.cruise["country_institute_code"] = global_attrs["country_institute_code"]
    odf.cruise["organization"] = global_attrs["organization"]
    odf.cruise["chief_scientist"] = global_attrs["chief_scientist"]
    odf.cruise["start_date"] = odf_time_format(global_attrs["start_date"])
    odf.cruise["end_date"] = odf_time_format(global_attrs["end_date"])
    odf.cruise["cruise_number"] = global_attrs["cruise_number"]
    odf.cruise["cruise_name"] = global_attrs["cruise_name"]
    odf.cruise["cruise_description"] = global_attrs["cruise_description"]

    odf.cruise["platform"] = sensor_metadata["platform_name"]
    if sensor_metadata["platform_type"] == "buoy":
        odf.cruise["platform"] = "Oceanographic Buoy"


def _make_event_header(odf, dataset, global_attrs):
    """
    Make the event header.

    Notes
    -----
    `depth_off_bottom` is `0` if "sounding" is missing.
    """
    for key, value in EVENT_ATTRS.items():
        if value.source == "dataset":
            if value.key in dataset.attrs:
                if "date" in key:
                    odf.event['orig_creation_date'] = odf_time_format(dataset.attrs['date_created'])
                else:
                    odf.event[key] = dataset.attrs[value.key]
        if value.source == "global_attrs":
            if value.key in global_attrs:
                odf.event[key] = global_attrs[value.key]

     odf.event["creation_date"] = odf_time_format(datetime.now())


def _set_geospatials(odf: Odf, dataset: xr.Dataset) -> None:
    """ Set geospatial metadata from dataset.

    Sets :
     - initial_latitude, end_latitude
     - initial_latitude, end_longitude
     - depth_off_bottom

    Parameters
    ----------
    odf :
    dataset :

    """
    if "lat" in dataset and "lon" in dataset:
        odf.event["initial_latitude"] = dataset.lat[0]
        odf.event["end_latitude"] = dataset.lat[-1]
        odf.event["initial_longitude"] = dataset.lon[0]
        odf.event["end_longitude"] = dataset.lon[-1]
    elif "latitude" in dataset.attrs and "longitude" in dataset.attrs:
        odf.event["initial_latitude"] = dataset.attrs["latitude"]
        odf.event["end_latitude"] = dataset.attrs["latitude"]
        odf.event["initial_longitude"] = dataset.attrs["longitude"]
        odf.event["end_longitude"] = dataset.attrs["longitude"]

    odf.event["depth_off_bottom"] = 0
    if "sounding" in dataset.attrs:
        if dataset.attrs["sounding"] and dataset.attrs["geospatial_vertical_max"]:
            odf.event["depth_off_bottom"] = (
                dataset.attrs["sounding"] - odf.event["max_depth"]
                )


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
        if value.source == "dataset":
            if value.key in dataset.attrs:
                if "date" in key and dataset.attrs[value.key]:
                    odf.instrument[key] = odf_time_format(dataset.attrs[value.key])
                else:
                    odf.instrument[key] = dataset.attrs[value.key]


def _make_quality_header():
    """TODO Multiple"""


def _make_buoy_header(odf, sensor_metadata):
    """
    Use BUOY_ATTRS
    """
    for key, value in BUOY_ATTRS.items():
        if value.source == "buoy_specs":

            if value.key in sensor_metadata["buoy_specs"]:
                odf.buoy[key] = sensor_metadata["buoy_specs"][value.key]
        if value.source == "sensor_metadata":
            if value.key in sensor_metadata:
                odf.buoy[key] = sensor_metadata[value.key]


def _make_buoy_instrument_header(odf, dataset, sensor_metadata):
    """Uses buoy_instrument_attrs
    Missing: comments and sensors
    """
    instrument = "ADCP_01"
    odf.add_buoy_instrument(instrument)
    for key, value in BUOY_INSTRUMENT_ATTRS.items():
        if value.source == "dataset":
            if value.key in dataset.attrs:
                if "date" in key and dataset.attrs[value.key]:
                    odf.buoy_instrument[instrument][key] = odf_time_format(
                        dataset.attrs[value.key]
                    )
                else:
                    odf.buoy_instrument[instrument][key] = dataset.attrs[value.key]

    _make_buoy_instrument_comment(odf, instrument, dataset, sensor_metadata)


def _make_buoy_instrument_comment(odf, instrument, dataset, sensor_metadata):
    """

    Note
    ----
    LagLength was removed from the original ODF adcp format.
    """
    configuration = "CONFIGURATION_01"
    for key, value in BUOY_INSTRUMENT_CONFIGURATION.items():
        v = ""
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
        elif value.source == "dataset" and value.key in dataset.attrs:
            v = dataset.attrs[value.key]
        elif value.source == "sensor_metadata":
            v = sensor_metadata[value.key]

        odf.buoy_instrument[instrument]["buoy_instrument_comments"].append(
            configuration + "." + key + ": " + str(v)
        )


def _make_history_header(odf, dataset):
    """
    One history header is made by log datetime entry.
    THe histories header is made with dataset.attrs['quality_comments']
    """
    process = [
        "Data processed by Magtogoek Processing Software. More at " + REPOSITORY_ADDRESS
    ]
    creation_date = datetime.now().strftime("%d-%b-%Y %H:%M:%S.%f").upper()[:-4]

    regex = r"(\[.*\])\s+([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})"
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
    Notes
    -----
    The PARAMETERS global variable order is important.
    """

    parameters_metadata = json2dict(PARAMETERS_METADATA_ABSOLUTE_PATH)

    if generic_to_p01_name:
        for param in PARAMETERS:
            if param in generic_to_p01_name:
                parameters_metadata[
                    generic_to_p01_name[param]
                ] = parameters_metadata.pop(param)

    data = dataset[list(parameters_metadata.keys())].to_dataframe().reset_index().sort_values(['time', 'depth'])

    for var in parameters_metadata:
        if var in dataset:
            items = {}
            items.update(parameters_metadata[var])

            items["depth"] = dataset.attrs["sensor_depth"]
            if "_QC" not in var:
                items["magnetic_variation"] = dataset.attrs["magnetic_declination"]
            items["type"] = PARAMETERS_TYPES[str(dataset[var].data.dtype)]

            null_value = None
            if "null_value" in items:
                null_value = items["null_value"]
            elif "_FillValue" in dataset[var].encoding:
                null_value = dataset[var].encoding["_FillValue"]

            odf.add_parameter(code=items["code"], data=data[var].values, null_value=null_value, items=items)


if __name__ == "__main__":
    #    from magtogoek.adcp.process import _get_config, _load_platform
    #    from magtogoek.configfile import load_configfile

    _nc_file = "../../test/files/iml6_2017_wh.nc"
    _platform_files = "../../test/files/iml_platforms.json"
    _config_file = "../../test/files/adcp_iml6_2017.ini"

    #    _dataset = xr.open_dataset(_nc_file)
    #    _params, _global_attrs = _get_config(load_configfile(_config_file))
    #    _params["platform_file"] = _platform_files
    #    _sensor_metadata = _load_platform(_params)

    _p01_to_generic_name = {
        "u": "LCEWAP01",
        "u_QC": "LCEWAP01_QC",
        "v": "LCNSAP01",
        "v_QC": "LCNSAP01_QC",
        "w": "LRZAAP01",
        "w_QC": "LRZAAP01_QC",
        "e": "LERRAP01",
    }

#    _odf = make_odf(_dataset, _sensor_metadata, _global_attrs, _p01_to_generic_name)
