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

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

TYPES = {"float16": "HALF", "float32": "SING", "float64": "DOUB", "|S1": "SYTM"}

PARAMETERS = {
    "time": {
        "code": "STYM_01",
        "name": "Time Format DD-MMM-YYYY 00:00:00.00",
        "units": "GMT",
        "print_field_width": 23,
        "print_decimal_width": 0,
        "null_value": "17-NOV-1858 00:00:00.00",
    },
    "depth": {
        "code": "DEPH_01",
        "name": "Sensor Depth below Sea Surface",
        "units": "metres",
        "print_field_width": 10,
        "print_decimal_width": 3,
    },
    "LCEWAP01": {
        "code": "EWCT_01",
        "name": "East (true) Component of Current",
        "units": "m/s",
        "print_field_width": 10,
        "print_decimal_width": 4,
    },
    "LCEWAP01_QC": {
        "code": "QQQQ_01",
        "name": "Quality flag: East (true) Component of Current",
        "units": "none",
        "print_field_width": 1,
        "print_decimal_width": 0,
    },
    "LCNSAP01": {
        "code": "NSCT_01",
        "name": "North (true) Component of Current",
        "units": "m/s",
        "print_field_width": 10,
        "print_decimal_width": 4,
    },
    "LCNSAP01_QC": {
        "code": "QQQQ_02",
        "name": "Quality flag: North (true) Component of Current",
        "units": "none",
        "print_field_width": 1,
        "print_decimal_width": 0,
    },
    "LRZAAP01": {
        "code": "VCSP_01",
        "name": "Vertical Current Speed (positive up)",
        "units": "m/s",
        "print_field_width": 10,
        "print_decimal_width": 4,
    },
    "LRZAAP01_QC": {
        "code": "QQQQ_03",
        "name": "Quality flag: Vertical Current Speed (positive up)",
        "units": "none",
        "print_field_width": 1,
        "print_decimal_width": 0,
    },
    "LERRAP01": {
        "code": "ERRV_01",
        "name": "Error Velocity (ADCP)",
        "units": "m/s",
        "print_field_width": 10,
        "print_decimal_width": 4,
    },
}

CRUISE_ATTRS = {
    "country_institute_code": ("dataset", "country_institute_code"),
    "cruise_number": ("dataset", "cruise_number"),
    "organization": ("dataset", "organization"),
    "chief_scientist": ("dataset", "chief_scientist"),
    "start_date": ("dataset", "start_date"),
    "end_date": ("dataset", "end_date"),
    "sensor_metadata": ("dataset", "sensor_metadata"),
    "cruise_name": ("dataset", "cruise_name"),
    "cruise_description": ("dataset", "cruise_description"),  # FIXME MISSING
    "sensor_metadata": ("sensor_metadata", "sensor_metadata_name"),
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
    "event_qualifier1": ("global_attrs", "event_qualifier1"),  # FIXME MISSING
    "event_qualifier2": ("global_attrs", "event_qualifier2"),  # FIXME MISSING
    "event_comments": ("global_attrs", "event_comments"),  # FIXME MISSING
}
BUOY_ATTRS = {
    "name": ("sensor_metadata", "platform_name"),
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

BUOY_INSTRUMENT_CONFIGURATION = {
    "Mode": ("dataset", "orientation"),
    "Ping_Type": ("dataset", "ping_type"),
    "Frequency": ("dataset", "frequency"),
    "Firmware_Version": ("dataset", "firmware_version"),
    "Ping_per_Ensemble": ("dataset", "ping_per_ensemble"),
    "Ensemble_Length_s": ("dataset", "delta_t_sec"),
    "Ping_Interval_s": (),
    "ADCP_Depth_m": ("dataset", "sensor_depth"),
    "Distance_ADCP_to_First_Bin_Center_m": ("dataset", "dist1bin"),
    "Bin_Size_m": ("dataset", "bin_size"),
    "Bin_Count": ("dataset", "bin_count"),
    "Blank_m": ("dataset", "blank"),
    "Transmit_Pulse_Length_m": ("dataset", "transmit_pulse_length_m"),
    "Magnetic_Declination": (),
    "Comments": ("sensor_metadata_sensors", "comments"),
}


def _make_cruise_header(odf, dataset, global_attrs):
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
        df.event["end_latitude"] = dataset.lat[-1]
    if "lon" in dataset:
        odf.event["initial_longitude"] = dataset.lon[0]
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


def _make_buoy_header(odf, sensor_metadata):
    """
    Use BUOY_ATTRS
    """
    for key, value in BUOY_ATTRS.items():
        if value[0] == "platform_specs":
            if value[1] in sensor_metadata["platform_specs"]:
                odf.buoy[key] = sensor_metadata["platform_specs"][value[1]]
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
                if "date" in key:
                    odf.buoy_instrument[instrument][key] = odf_time_format(
                        dataset.attrs[value[1]]
                    )
                else:
                    odf.buoy_instrument[instrument][key] = dataset.attrs[value[1]]

    _make_buoy_instrument_comment(odf, instrument, dataset, sensor_metadata)


def _make_buoy_instrument_comment(odf, instrument, dataset, sensor_metadata):
    """FIXME
    To compute:
         Ping_Intervalle_pings_s ping_per_ensemble / delta_t_sec
         Magnetique_Declination                : ('datasret','magnetic_declination + _units'

    Note
    ----
    LagLength was removed from the original ODF adcp format.
    """
    global_attrsuration = "CONFIGURATION_01"
    for key, value in BUOY_INSTRUMENT_CONFIGURATION.items():
        if (
            key == "Ping_Interval_s"
            and "ping_per_ensemble" in dataset.attrs
            and "delta_t_sec" in dataset.attrs
        ):
            v = round(
                dataset.attrs["ping_per_ensemble"] / dataset.attrs["delta_t_sec"], 2
            )
        elif (
            key == "Magnetic_Declination"
            and "magnetic_declination" in dataset.attrs
            and "magnetic_declination_units" in dataset.attrs
        ):
            v = (
                str(dataset.attrs["magnetic_declination"])
                + " "
                + dataset.attrs["magnetic_declination_units"]
            )

        elif value[0] == "dataset" and value[1] in dataset.attrs:
            v = dataset.attrs[value[1]]
        elif value[0] == "sensor_metadata":
            v = sensor_metadata[value[1]]
        else:
            v = "N/A"
        odf.buoy_instrument[instrument]["buoy_instrument_comments"].append(
            global_attrsuration + "." + key + ": " + str(v)
        )


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


def _make_parameter_headers(odf, dataset):
    """
     PARAMETERS:
      name
      code (increment + '_01')
      units
      print_field_value
      print_decimal_value
      null_value (time_string)
      type (time_String)

    Dataset
     depth:              dataset[var].attrs['sensor_depth']
     magnetic_variation: dataset[var].attrs['magnetic_declination']
     null_value:         dataset[var].encoding['_FillValue']
     type:               TYPES[str(dataset[var].encoding['dtype'])]
    """

    data = (
        dataset[list(PARAMETERS.keys())].to_dataframe().reset_index()
    )  # .reindex(columns=list(PARAMETERS.keys()))
    for var in PARAMETERS:
        if var in dataset:
            items = {}
            for key, value in PARAMETERS[var].items():
                items[key] = value

            items["depth"] = dataset.attrs["sensor_depth"]
            items["magnetic_variation"] = dataset.attrs["magnetic_declination"]

            items["type"] = TYPES[str(dataset[var].encoding["dtype"])]
            if "_FillValue" in dataset[var].encoding:
                items["null_value"] = dataset[var].encoding["_FillValue"]
            elif "null_value" in value:
                items["null_value"] = value["null_value"]
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
    from magtogoek.utils import json2dict

    nc_file = "../../test/files/iml6_2017_wh.nc"
    platform_files = "../../test/files/iml_platforms.json"
    config_file = "../../test/files/adcp_iml6_2017.ini"

    ds = xr.open_dataset(nc_file)
    params, global_attrs = _get_config(load_configfile(config_file))
    params["platform_file"] = platform_files
    sensor_metadata = _load_platform(params)

    odf = Odf()

    _make_cruise_header(odf, ds, sensor_metadata)
    _make_event_header(odf, ds, global_attrs)
    _make_odf_header(odf)
    _make_buoy_header(odf, sensor_metadata)
    _make_buoy_instrument_header(odf, ds, sensor_metadata)
    _make_parameter_headers(odf, ds)
    _make_history_header(odf, ds)
