"""
module to map xarray dataset to Odf
"""
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import xarray as xr
from magtogoek.odf_format import Odf, odf_time_format
from magtogoek.utils import json2dict

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

ADCP_COMMENTS_SENSOR = {
    'PRESPR01': {'sensor': 'PRESSURE_SENSOR_01', 'comments': {'CODE':'DEPH_01', 'Name':'pressure'}},
    'HEADCM01': {'sensor': 'COMPAS_SENSOR_01', 'comments': {'CODE':'HEAD_01', 'Name':'compas'}},
    'ROLLGP01': {'sensor': 'INClINOMETER_SENSOR_01', 'comments': {'CODE':'ROLL_01', 'Name':'tilt'}},
    'TEMPPR01': {'sensor': 'TEMPERATURE_SENSOR_01', 'comments': {'CODE':'TE90_01', 'Name':'temperature'}}
}

PARAMETERS_TYPES = {
    "int8": "INT",  # "BYTE",  # -128, 127
    "int16": "INT",  # SHORT  # -32768, 32767
    "int32": "INT",
    "int64": "LONG",
    "float16": "HALF",
    "float32": "SING",
    "float64": "DOUB",
    "|S1": "SYTM",
    "datetime64[ns]": "SYTM",
}
#TE90, HEAD_01, ROLL_01, DEPH_01
VEL_PARAMETERS = ("time", "depth", "u", "v", "w", "e")
ANC_PARAMETERS = ('time', 'pitch', 'roll_', 'heading', 'pres','temperature', 'xducer_depth','lon','lat')
QC_PARAMETERS = ('u','v','w', 'pres', 'temperature')
PARAMETERS_METADATA_RELATIVE_PATH = "../files/odf_parameters_metadata.json"
PARAMETERS_METADATA_ABSOLUTE_PATH = (
    Path(__file__)
    .resolve()
    .parent.joinpath(PARAMETERS_METADATA_RELATIVE_PATH)
    .resolve()
)


def make_odf(
        dataset: xr.Dataset,
        platform_metadata: dict,
        config_attrs: dict,
        generic_to_p01_name: dict = None,
        output_path: str = None,
):
    """
    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    platform_metadata :
        Metadata from the platform file.
    config_attrs :
        Global attributes parameter from the configFile.
    generic_to_p01_name :
        map from the generic to the BODC p01 variables names.
    output_path :

    """
    odf = Odf()

    _make_cruise_header(odf, platform_metadata, config_attrs)
    _make_event_header(odf, dataset, config_attrs)
    _make_odf_header(odf)
    if platform_metadata['platform']["platform_type"] == "buoy":
        _make_buoy_header(odf, platform_metadata)
        _make_adcp_buoy_instrument_header(odf, dataset, platform_metadata)
        _make_sensor_buoy_instrument_header(odf, platform_metadata)
    else:
        _make_instrument_header(odf, dataset)
    _make_quality_header(odf, dataset)
    _make_history_header(odf, dataset)
    _make_parameter_headers(odf, dataset, generic_to_p01_name, VEL_PARAMETERS)

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path.joinpath(odf.odf["file_specification"])
        else:
            odf.odf["file_specification"] = output_path.name
        output_path = Path(output_path).with_suffix(".ODF")
        odf.save(output_path)

    return odf


def _make_cruise_header(odf, platform_metadata, config_attrs):
    odf.cruise["country_institute_code"] = config_attrs["country_institute_code"]
    odf.cruise["organization"] = config_attrs["organization"]
    odf.cruise["chief_scientist"] = config_attrs["chief_scientist"]
    odf.cruise["start_date"] = odf_time_format(config_attrs["start_date"])
    odf.cruise["end_date"] = odf_time_format(config_attrs["end_date"])
    odf.cruise["cruise_number"] = config_attrs["cruise_number"]
    odf.cruise["cruise_name"] = config_attrs["cruise_name"]
    odf.cruise["cruise_description"] = config_attrs["cruise_description"]

    odf.cruise["platform"] = platform_metadata['platform']["platform_name"]
    if platform_metadata['platform']["platform_type"] == "buoy":
        odf.cruise["platform"] = "Oceanographic Buoy"


def _make_event_header(odf, dataset, config_attrs):
    """
    Make the event header.

    Notes
    -----
    `depth_off_bottom` is `0` if "sounding" is missing.
    """
    odf.event['data_type'] = 'madcp'
    odf.event["creation_date"] = odf_time_format(datetime.now())
    odf.event['orig_creation_date'] = odf_time_format(dataset.attrs['date_created'])
    if 'delta_t_sec' in dataset.attrs:
        odf.event['sampling_interval'] = dataset.attrs['delta_t_sec']
    odf.event["event_number"] = config_attrs["event_number"]
    odf.event["event_qualifier1"] = config_attrs["event_qualifier1"]
    odf.event["event_qualifier2"] = config_attrs["event_qualifier2"]
    if 'sounding' in dataset.attrs:
        odf.event['sounding'] = dataset.attrs['sounding']
    odf.event["event_comments"] = config_attrs["event_comments"]

    _set_event_header_geospatials(odf, dataset)


def _set_event_header_geospatials(odf: Odf, dataset: xr.Dataset) -> None:
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
    odf.event['start_date_time'] = odf_time_format(dataset.time.values.min())
    odf.event['end_date_time'] = odf_time_format(dataset.time.values.max())

    odf.event['min_depth'] = dataset.depth.values.min()
    odf.event['max_depth'] = dataset.depth.values.max()

    if "lat" in dataset and "lon" in dataset:
        odf.event["initial_latitude"] = dataset.lat.values[0]
        odf.event["end_latitude"] = dataset.lat.values[-1]
        odf.event["initial_longitude"] = dataset.lon.values[0]
        odf.event["end_longitude"] = dataset.lon.values[-1]
    elif "latitude" in dataset.attrs and "longitude" in dataset.attrs:
        odf.event["initial_latitude"] = dataset.attrs["latitude"]
        odf.event["end_latitude"] = dataset.attrs["latitude"]
        odf.event["initial_longitude"] = dataset.attrs["longitude"]
        odf.event["end_longitude"] = dataset.attrs["longitude"]

    odf.event["depth_off_bottom"] = 0
    if odf.event["sounding"] is not None:
        odf.event["depth_off_bottom"] = odf.event['sounding'] - odf.event['max_depth']


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

    odf.odf["file_specification"] = "_".join(name_part).strip("_").upper() + ".ODF"


def _make_instrument_header(odf, dataset):
    """
    inst_type
    model
    serial_number
    description
    """
    # FIXME maybe rename it to instrument_comments.
    for key_odf, key_nc in (('inst_type', 'manufacturer'), ("description", "comments")):
        if key_nc in dataset.attrs:
            odf.instrument[key_odf] = dataset.attrs[key_nc]
    for key in ['model', 'serial_number']:
        if key in dataset.attrs:
            odf.instrument[key] = dataset.attrs[key]


def _make_buoy_header(odf, platform_metadata):
    """
    Use BUOY_ATTRS
    """
    odf.buoy["name"] = platform_metadata["platform"]["platform_name"]
    if 'buoy_specs' in platform_metadata:
        for key in ['type', 'model', 'diameter', 'weight', 'height', 'description']:
            if key in platform_metadata['buoy_specs']:
                odf.buoy[key] = platform_metadata["buoy_specs"][key]


def _make_adcp_buoy_instrument_header(odf, dataset, platform_metadata):
    """Uses buoy_instrument_attrs
    """
    sensor = platform_metadata['adcp_id']
    odf.add_buoy_instrument(sensor)
    header = odf.buoy_instrument[sensor]

    for key_odf, key_nc in (('type', 'manufacturer'),):
        if key_nc in dataset.attrs:
            header[key_odf] = dataset.attrs[key_nc]
    for key in ['model', 'serial_number', 'description']:
        if key in dataset.attrs:
            header[key] = dataset.attrs[key]

    header["inst_start_date_time"] = odf_time_format(dataset.time.values.min())
    header["inst_end_date_time"] = odf_time_format(dataset.time.values.max())

    _make_buoy_instrument_comments(odf, sensor, dataset, platform_metadata)
    _make_buoy_instrument_sensor(odf, sensor, dataset)


def _make_sensor_buoy_instrument_header(odf: Odf, platform_metadata: dict):
    """

    Parameters
    ----------
    odf
    platform_metadata

    Returns
    -------
# FIXME
    """
    configuration = "CONFIGURATION_01"
    for sensor, metadata in platform_metadata['sensors'].items():
        odf.add_buoy_instrument(sensor)
        if 'sensor_type' in metadata:
            odf.buoy_instrument[sensor]['type'] = metadata['sensor_type']
        for key in ['model', 'serial_number', 'description']:
            if key in metadata:
                odf.buoy_instrument[sensor][key] = metadata[key]
        comments = {}
        keys =(("Firmware_Version", "firmware_version"),
               ("depth_m", "sensor_depth"),
               ("Comments", "comments"))
        for key_odf, meta_key in keys:
            comments[key_odf] = metadata[meta_key]

        for key, value in comments.items():
            odf.buoy_instrument[sensor]["buoy_instrument_comments"].append(
                configuration + "." + key + ": " + str(value)
                )


def _make_buoy_instrument_comments(odf: Odf, sensor: str, dataset: xr.Dataset, platform_metadata: dict):
    """

    Note
    ----
    LagLength was removed from the original ODF adcp format.
    """
    configuration = "CONFIGURATION_01"
    comments = {}
    keys = (("Mode", "orientation"),
            ("Ping_Type", "ping_type"),
            ("Frequency", "frequency"),
            ("Firmware_Version", "firmware_version"),
            ("Ping_per_Ensemble", "ping_per_ensemble"),
            ("Ensemble_Length_s", "delta_t_sec"),
            ("ADCP_Depth_m", "sensor_depth"),
            ("Distance_ADCP_to_First_Bin_Center_m", "bin1dist"),
            ("Bin_Size_m", "bin_size"),
            ("Blank_m", "blank"),
            ("Transmit_Pulse_Length_m", "transmit_pulse_length_m"))
    for key_odf, key_nc in keys:
        if key_nc in dataset.attrs:
            comments[key_odf] = dataset.attrs[key_nc]

    if "ping_per_ensemble" in dataset.attrs and "delta_t_sec" in dataset.attrs:
        if dataset.attrs["ping_per_ensemble"] and dataset.attrs["delta_t_sec"]:
            comments["Ping_Interval_s"] = round(
                dataset.attrs["ping_per_ensemble"]
                / dataset.attrs["delta_t_sec"],
                2,
            )
    if "magnetic_declination" in dataset.attrs:
        if "magnetic_declination_units" in dataset.attrs:
            comments["Magnetic_Declination"] = (
                    str(dataset.attrs["magnetic_declination"])
                    + " "
                    + dataset.attrs["magnetic_declination_units"]
            )
    comments["Bin_Count"] = len(dataset.depth)
    comments['Comments'] = platform_metadata['adcp']['comments']

    for key, value in comments.items():
        odf.buoy_instrument[sensor]["buoy_instrument_comments"].append(
            configuration + "." + key + ": " + str(value)
        )


def _make_buoy_instrument_sensor(odf: Odf, instrument: str, dataset: xr.Dataset):
    """

    Parameters
    ----------
    odf

    dataset

    Returns
    -------
    """
    dataset_attrs = {'Manufacturer':'manufacturer', 'Depth':'sensor_depth', 'Serial_Number':'serial_number'}
    for var, item in ADCP_COMMENTS_SENSOR.items():
        if var in dataset.variables:
            for key, value in item['comments'].items():
                odf.buoy_instrument[instrument]["sensors"].append(item['sensor'] + "." + key + ': ' + value)
            for key, value in dataset_attrs.items():
                if value in dataset.attrs:
                    odf.buoy_instrument[instrument]["sensors"].append(
                        item['sensor'] + "." + key + ': ' + str(dataset.attrs[value])
                    )


def _make_quality_header(odf, dataset):
    """
    """
    comments = dataset.attrs['quality_comments'].strip("\n").split("\n")
    time_stamp = _find_section_timestamp(comments.pop())

    odf.quality["quality_date"] = odf_time_format(datetime.now())
    if time_stamp:
        odf.quality["quality_date"] = odf_time_format(time_stamp)

    odf.quality["quality_tests"] = comments
    keys = ['flags_reference', 'flags_values', 'flags_meanings']
    for key in keys:
        odf.quality["quality_comments"].append(key + ': ' + str(dataset.attrs[key]))


def _make_history_header(odf, dataset):
    """Make one or more history_header.
    1 - Default process comments is added with a Timestamp (datetime.now()).
    2 - Looks for log section `[Loading adcp data], [Data transformation]` in
        dataset.attrs['logbook'] and add the log messages that follow.
    3 - New history_header are made for each TimeStamp found with the log section.
    """
    process = ["Data processed by Magtogoek Processing Software. More at " + REPOSITORY_ADDRESS]
    creation_date = odf_time_format(datetime.now())

    iter_logbook = iter(re.split(r"(\[.*])", dataset.attrs["logbook"]))
    for log_entry in iter_logbook:
        if log_entry in ["[Loading adcp data]", "[Data transformation]"]:
            logs = next(iter_logbook).strip("\n").split("\n")
            time_stamp = _find_section_timestamp(logs[0])
            if time_stamp is not None:
                del logs[0]
                odf.add_history({"creation_date": creation_date, "process": process})
                creation_date = odf_time_format(pd.Timestamp(time_stamp))
                process = []
            process += logs
    odf.add_history({"creation_date": creation_date, "process": process})


def _make_parameter_headers(odf, dataset, parameters: tp.List[str], generic_to_p01_name=None):
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
        for param in parameters:
            if param in generic_to_p01_name:
                parameters_metadata[
                    generic_to_p01_name[param]
                ] = parameters_metadata.pop(param)

    data = dataset[list(parameters_metadata.keys())].to_dataframe().reset_index().sort_values(['time', 'depth'])
    qc_count = 1
    for var in parameters_metadata:
        if var in dataset.variables:
            items = {}
            qc_mask = None
            items.update(parameters_metadata[var])
            items["depth"] = dataset.attrs["sensor_depth"]
            if "_QC" not in var:
                items["magnetic_variation"] = dataset.attrs["magnetic_declination"]
            if var + '_QC' in dataset.variables:
                qc_mask = data[var + '_QC'].values <= 2
            items["type"] = PARAMETERS_TYPES[str(dataset[var].data.dtype)]

            null_value = None
            if "null_value" in items:
                null_value = items["null_value"]
            elif "_FillValue" in dataset[var].encoding:
                null_value = dataset[var].encoding["_FillValue"]

            odf.add_parameter(code=items["code"],
                              data=data[var].values,
                              null_value=null_value,
                              items=items,
                              qc_mask=qc_mask)

            if var in QC_PARAMETERS and var+'_QC' in dataset.variables:
                qc_items = {
                    "code": "QQQQ_"+str(qc_count).zfill(2),
                    "name": "Quality flag: " + items['name'],
                    "units": "none",
                    "print_field_width": 1,
                    "print_decimal_places": 0,
                    "null_value":9
                }
                odf.add_parameter(code=items["code"],
                                  data=data[var+'_QC'].values,
                                  null_value=9,
                                  items=qc_items,
                                  qc_mask=None)
                qc_count += 1

def _find_section_timestamp(s: str) -> str:
    r""" String of Section - Timestamp

    regex : ([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})'
    """
    regex = r"([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})"
    match = re.findall(regex, s)
    if match:
        return match[0]
    return None


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
