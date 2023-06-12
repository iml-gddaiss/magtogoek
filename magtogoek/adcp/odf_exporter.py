"""
module to map xarray dataset to Odf

Notes TODO
-----

-> make this more general and apply it to meteoce
-> in order to make odf buoy instrument header, the platform file need to be used.
--> `parameters` need to be changed to something like sub-sensor.
--> the sub-sensor ID<s are user define.
--> Add a `name` field and `code` to the sub_sensor
--> if calibrations is empty: do not write it.




"""
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import xarray as xr
from typing import List, Union, Tuple, Dict, Optional
from magtogoek import CONFIGURATION_PATH
from magtogoek.odf_format import Odf, odf_time_format, ODF_PARAMETERS_TYPES
from magtogoek.platforms import PlatformMetadata, InstrumentMetadata, SensorMetadata
from magtogoek.utils import json2dict

REPOSITORY_ADDRESS = "https://github.com/JeromeJGuay/magtogoek"

BEAM_PARAMETERS = ("time", "depth", "v1", "v2", "v3", "v4")
VEL_PARAMTERS = ("time", "depth", "u", "v", "w", "e")
ANC_PARAMTERS = ('time', 'pitch', 'roll_', 'heading', 'pres', 'temperature', 'lon', 'lat')
QC_PARAMETERS = ('u', 'v', 'w', 'pres', 'temperature')

PARAMETERS_METADATA_PATH = CONFIGURATION_PATH.joinpath("odf_parameters_metadata.json")
PARAMETERS_METADATA = json2dict(PARAMETERS_METADATA_PATH)


def make_odf(
        dataset: xr.Dataset,
        platform_metadata: PlatformMetadata,
        adcp_id: str,
        global_attributes: dict,
        p01_codes_map: dict,
        use_bodc_name: bool = True,
        event_qualifier2: str = 'VEL',
        output_path: Optional[str] = None, ):
    """

    Parameters
    ----------
    dataset :
        Dataset to which add the navigation data.
    platform_metadata :
        Metadata from the platform file.
    adcp_id
     :

    global_attributes :
        Global attributes parameter from the configFile.
    p01_codes_map :

    use_bodc_name:
        If True, map from the generic to the BODC p01 variables names.
    event_qualifier2:
        Either `'VEL'` or `'ANC'`.
    output_path:
        If a path(str) is provided, there is two possibilities: if the path is only a directory, the file name
        will be made from the odf['file_specification']. If a file name is also provided, the 'event_qualifier2'
        will be appended to it if it's not present in the `output_path`.

    """
    odf = Odf()

    _make_cruise_header(odf, platform_metadata, global_attributes)
    _make_event_header(odf, dataset, global_attributes, event_qualifier2, p01_codes_map)
    _make_odf_header(odf)

    if platform_metadata.platform.platform_type == "buoy":
        _make_buoy_header(odf, platform_metadata)
        _make_buoy_instrument_headers(odf, platform_metadata)
        _make_adcp_buoy_instrument_header(odf=odf, dataset=dataset, platform_metadata=platform_metadata, adcp_id
        =adcp_id
                                          )
        #_make_adcp_buoy_instrument_comments(odf, adcp_id
        # , dataset, platform_metadata)
    else:
        _make_instrument_header(odf, dataset)

    _make_quality_header(odf, dataset)
    _make_history_header(odf, dataset)

    if event_qualifier2 == 'VEL':
        if dataset.attrs['coord_system'] == 'beam':
            parameters = BEAM_PARAMETERS
        else:
            parameters = VEL_PARAMTERS
    else:
        parameters = ANC_PARAMTERS

    _make_parameter_headers(odf, dataset, parameters, p01_codes_map, use_bodc_name)

    if output_path is not None:
        output_path = Path(output_path)
        if output_path.is_dir():
            output_path = output_path.joinpath(odf.odf["file_specification"])
        else:
            if event_qualifier2 not in output_path.name:
                output_path = Path(str(output_path.with_suffix('')) + f'_{event_qualifier2}')
            odf.odf["file_specification"] = output_path.name

        output_path = Path(output_path).with_suffix(".ODF")
        odf.save(output_path)
        print(f"odf {event_qualifier2.upper()} file made -> {output_path}")

    return odf


def _make_cruise_header(odf: Odf, platform_metadata: PlatformMetadata, config_attrs: dict):
    odf.cruise["country_institute_code"] = config_attrs["country_institute_code"]
    odf.cruise["organization"] = config_attrs["organization"]
    odf.cruise["chief_scientist"] = config_attrs["chief_scientist"]
    odf.cruise["start_date"] = odf_time_format(config_attrs["start_date"])
    odf.cruise["end_date"] = odf_time_format(config_attrs["end_date"])
    odf.cruise["cruise_number"] = config_attrs["cruise_number"]
    odf.cruise["cruise_name"] = config_attrs["cruise_name"]
    odf.cruise["cruise_description"] = config_attrs["cruise_description"]

    odf.cruise["platform"] = platform_metadata.platform.platform_name
    if platform_metadata.platform.platform_type == "buoy":
        odf.cruise["platform"] = "Oceanographic Buoy"


def _make_event_header(odf, dataset, config_attrs, event_qualifier2, p01_codes_map: dict):
    """
    Make the event header.

    Notes
    -----
    `depth_off_bottom` is `0` if "sounding" is missing.
    """
    odf.event['data_type'] = dataset.attrs['data_type'].upper()
    odf.event["creation_date"] = odf_time_format(datetime.now())
    odf.event['orig_creation_date'] = odf_time_format(dataset.attrs['date_created'])
    if 'delta_t_sec' in dataset.attrs:
        odf.event['sampling_interval'] = dataset.attrs['delta_t_sec']
    odf.event["event_number"] = config_attrs["event_number"]
    odf.event["event_qualifier1"] = config_attrs["event_qualifier1"]
    odf.event["event_qualifier2"] = event_qualifier2
    if 'sounding' in dataset.attrs:
        odf.event['sounding'] = dataset.attrs['sounding']
    odf.event["event_comments"] = config_attrs["event_comments"]
    _set_event_header_geospatials(odf, dataset, p01_codes_map)


def _set_event_header_geospatials(odf: Odf, dataset: xr.Dataset, p01_codes_map: dict) -> None:
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

    if odf.event['event_qualifier2'] == 'ANC':
        if 'xducer_depth' in dataset:
            odf.event['min_depth'] = dataset['xducer_depth'].values.min()
            odf.event['max_depth'] = dataset['xducer_depth'].values.max()
        elif p01_codes_map['xducer_depth'] in dataset:
            odf.event['min_depth'] = dataset[p01_codes_map['xducer_depth']].values.min()
            odf.event['max_depth'] = dataset[p01_codes_map['xducer_depth']].values.max()
        else:
            odf.event['min_depth'] = dataset.attrs['sensor_depth']
            odf.event['max_depth'] = dataset.attrs['sensor_depth']
    else:
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
    key_map = [
        ("inst_type", "manufacturer"),
        ("description", "comments"),
        ("model", "model"),
        ("serial_number", "serial_number")
    ]

    for (odf_key, netcdf_key) in key_map:
        if netcdf_key in dataset.attrs:
            odf.instrument[odf_key] = dataset.attrs[netcdf_key]


def _make_buoy_header(odf: Odf, platform_metadata: PlatformMetadata):
    """
    Uses values in the Buoy_Specs section of the platform_file.
    """
    odf.buoy["name"] = platform_metadata.platform.platform_name or ''
    odf.buoy['type'] = platform_metadata.buoy_specs.type or ''
    odf.buoy['model'] = platform_metadata.buoy_specs.model or ''
    odf.buoy['height'] = platform_metadata.buoy_specs.height or ''
    odf.buoy['diameter'] = platform_metadata.buoy_specs.diameter or ''
    odf.buoy['weight'] = platform_metadata.buoy_specs.weight or ''
    odf.buoy['description'] = platform_metadata.buoy_specs.description or ''


def _make_adcp_buoy_instrument_header(
        odf: Odf, dataset: xr.Dataset,
        platform_metadata: PlatformMetadata,
        adcp_id
        : str,
):
    """TODO TEST"""

    if adcp_id\
            not in odf.buoy_instrument:
        odf.add_buoy_instrument(adcp_id
                                )

    key_map = [
        ('type', 'manufacturer'),
        ('model', 'model'),
        ('serial_number', 'serial_number'),
        ('description', 'description')
    ]

    for (odf_key, netcdf_key) in key_map:
        if netcdf_key in dataset.attrs:
            odf.buoy_instrument[adcp_id
            ][odf_key] = dataset.attrs[netcdf_key]

    _make_adcp_buoy_instrument_comments(odf, adcp_id
                                        , dataset, platform_metadata)


def _make_adcp_buoy_instrument_comments(
        odf: Odf,
        adcp_id
        : str,
        dataset: xr.Dataset,
        platform_metadata: PlatformMetadata
):
    """

    BUOY_INSTRUMENT_HEADER
      .
      .
      BUOY_INSTRUMENT_COMMENTS= '',
      .
      .

    """
    configuration = "CONFIGURATION_01"
    buoy_instrument_comments = []
    key_map = [
        ("Mode", "orientation"),
        ("Ping_Type", "ping_type"),
        ("Frequency", "frequency"),
        ("Firmware_Version", "firmware_version"),
        ("Ping_per_Ensemble", "ping_per_ensemble"),
        ("Ensemble_Length_s", "delta_t_sec"),
        ("ADCP_Depth_m", "sensor_depth"),
        ("Distance_ADCP_to_First_Bin_Center_m", "bin1dist"),
        ("Bin_Size_m", "bin_size"),
        ("Blank_m", "blank"),
        ("Transmit_Pulse_Length_m", "transmit_pulse_length_m")
    ]

    for odf_key, netcdf_key in key_map:
        if netcdf_key in dataset.attrs:
            buoy_instrument_comments.append((odf_key, dataset.attrs[netcdf_key]))

    if "ping_per_ensemble" in dataset.attrs and "delta_t_sec" in dataset.attrs:
        if dataset.attrs["ping_per_ensemble"] and dataset.attrs["delta_t_sec"]:
            ping_interval_s = dataset.attrs["ping_per_ensemble"] / dataset.attrs["delta_t_sec"]
            buoy_instrument_comments.append(("Ping_Interval_s", round(ping_interval_s, 2)))

    if "magnetic_declination" in dataset.attrs and "magnetic_declination_units" in dataset.attrs:
        magnetic_declination = f"{dataset.attrs['magnetic_declination']} {dataset.attrs['magnetic_declination_units']}"

        buoy_instrument_comments.append(("Magnetic_Declination", magnetic_declination))

    buoy_instrument_comments += [
        ("Bin_Count", len(dataset.depth)),
        ("Comments", platform_metadata.instruments[adcp_id].comments)
    ]

    odf.buoy_instrument[adcp_id
    ]["buoy_instrument_comments"] = []
    for (key, value) in buoy_instrument_comments:
        odf.buoy_instrument[adcp_id
        ]["buoy_instrument_comments"].append(
            _build_comments_string([configuration, key], value)
        )


def _make_buoy_instrument_headers(
        odf: Odf,
        platform_metadata: PlatformMetadata
):
    """
    TODO TEST
    Uses the data from the platform metadata
    """
    for instrument_id, instrument_metadata in platform_metadata.instruments.items():
        _add_buoy_instrument_header(
            odf=odf,
            instrument_id=instrument_id,
            instrument_metadata=instrument_metadata
        )


def _add_buoy_instrument_header(
        odf: Odf,
        instrument_id: str,
        instrument_metadata: InstrumentMetadata
):
    """
    FIXME test
    Uses the data from the platform metadata
    """

    odf.add_buoy_instrument(instrument_id)

    odf.buoy_instrument[instrument_id]['inst_start_date_time'] = odf.event['start_date_time']
    odf.buoy_instrument[instrument_id]['inst_end_date_time'] = odf.event['end_date_time']

    odf.buoy_instrument[instrument_id]['type'] = instrument_metadata.manufacturer
    odf.buoy_instrument[instrument_id]['model'] = instrument_metadata.model
    odf.buoy_instrument[instrument_id]['serial_number'] = instrument_metadata.serial_number
    odf.buoy_instrument[instrument_id]['description'] = instrument_metadata.description

    _add_buoy_instrument_comments(odf, instrument_id, instrument_metadata)

    for sensor, sensor_metadata in instrument_metadata.sensors.items():
        _add_buoy_instrument_sensors(sensor, odf, instrument_id, sensor_metadata)


def _add_buoy_instrument_comments(odf: Odf, instrument_id: str, instrument_metadata: InstrumentMetadata):
    """
    TODO TEST | get depth/height info from the dataset ????
    """
    buoy_instruments_comments = [
        (["Firmware_Version"], instrument_metadata.firmware_version),
        (["Comments"], instrument_metadata.comments)
    ]

    if instrument_metadata.sensor_depth is not None:
        buoy_instruments_comments.append((["Depth_m"], instrument_metadata.sensor_depth))

    if instrument_metadata.sensor_height is not None:
        buoy_instruments_comments.append((["Height_m"], instrument_metadata.sensor_depth))

    for (key, value) in buoy_instruments_comments:
        odf.buoy_instrument[instrument_id]["buoy_instrument_comments"].append(
            _build_comments_string(["CONFIGURATION_01"] + key, value)
        )


def _add_buoy_instrument_sensors(sensor: str, odf: Odf, instrument_id: str, sensor_metadata: SensorMetadata):
    sensor_comments = [
        ("CODE", sensor_metadata.code),
        ("Name", sensor_metadata.name),
        ("Manufacturer", odf.buoy_instrument[instrument_id]['type']),
        ("Model", odf.buoy_instrument[instrument_id]['model']),
        ("Serial_number", odf.buoy_instrument[instrument_id]['serial_number']),
        ("Description", sensor_metadata.description),
        ("Start_date", odf.buoy_instrument[instrument_id]['inst_start_date_time']),
        ("End_date", odf.buoy_instrument[instrument_id]['inst_end_date_time']),
        ("Comments", sensor_metadata.comments)
    ]

    for (key, value) in sensor_comments:
        odf.buoy_instrument[instrument_id]["sensors"].append(
            _build_comments_string([sensor.upper(), key], value)
        )

    calibration = sensor_metadata.calibration
    if calibration:
        calibration_comments = {
            'date': odf_time_format(calibration.date) if calibration.date else None,
            'number_of_coefficients': calibration.number_of_coefficients,
            'coefficients': calibration.coefficients,
            'calibration_equation': calibration.calibration_equation,
            'calibration_units': calibration.calibration_units,
            'archiving_units': calibration.archiving_units,
            'conversion_factor': calibration.conversion_factor,
            'comments': calibration.comments,
        }

        for key, value in calibration_comments.items():
            odf.buoy_instrument[instrument_id]["sensors"].append(
                _build_comments_string([sensor.upper(), "CALIBRATION_01", key], value)
            )


def _build_comments_string(keys: List, value: Union[int, float, str]):
    """Build the comments string

    >>> ".".join(keys) + f": {value}"
    """
    return ".".join(keys) + f": {value or ''}"


def _make_quality_header(odf: Odf, dataset):
    """
    """
    comments = dataset.attrs['quality_comments'].strip("\n").split("\n")
    time_stamp = _find_section_timestamp(comments.pop())

    odf.quality["quality_date"] = odf_time_format(datetime.now())
    if time_stamp:
        odf.quality["quality_date"] = odf_time_format(time_stamp)

    odf.quality["quality_tests"] = comments
    keys = ['flag_reference', 'flag_values', 'flag_meanings']
    for key in keys:
        odf.quality["quality_comments"].append(key + ': ' + str(dataset.attrs[key]))


def _make_history_header(odf, dataset):
    """Make one or more history_header.
    1 - Default process comments is added with a Timestamp (datetime.now()).
    2 - Looks for log section `[Loading adcp data], [Data transformation]` in
        dataset.attrs['history'] and add the log messages that follow.
    3 - New history_header are made for each TimeStamp found with the log section.
    """
    processing = ["Data processed by Magtogoek Processing Software. More at " + REPOSITORY_ADDRESS]
    creation_date = odf_time_format(datetime.now())

    iter_logbook = iter(re.split(r"(\[.*])", dataset.attrs["history"]))
    for log_entry in iter_logbook:
        if log_entry in ["[Loading adcp data]", "[Data transformation]"]:
            logs = next(iter_logbook).strip("\n").split("\n")
            time_stamp = _find_section_timestamp(logs[0])
            if time_stamp is not None:
                del logs[0]
                odf.add_history({"creation_date": creation_date, "process": processing})
                creation_date = odf_time_format(pd.Timestamp(time_stamp))
                processing = []
            processing += logs
    odf.add_history({"creation_date": creation_date, "process": processing})


def _make_parameter_headers(odf, dataset, variables: List[str], p01_codes_map: dict, bodc_name=False):
    """
    Parameters
    ----------
    odf:
    dataset:
        Dataset to which add the navigation data.
    variables:
       variables to put in the ODF.
    bodc_name:
        If True, map from the generic to the BODC p01 variables names.
    Notes
    -----
    The variable order in the ODF will be the same as in the variables list parameter.
    """

    parameters_metadata = {}
    parameters = []
    qc_parameters = []

    for var in variables:
        if bodc_name is True and var not in ('time', 'depth'):
            dataset_variable_name = p01_codes_map[var]
        else:
            dataset_variable_name = var

        if dataset_variable_name in dataset.variables:
            parameters.append(dataset_variable_name)
            parameters_metadata[dataset_variable_name] = PARAMETERS_METADATA[var]
            if var in QC_PARAMETERS and dataset_variable_name + '_QC' in dataset.variables:
                qc_parameters.append(dataset_variable_name + '_QC')

    dims = ['time', 'depth'] if 'depth' in variables else ['time']
    data = dataset[parameters + qc_parameters].to_dataframe().reset_index().sort_values(dims)

    qc_increment = 1
    for var in parameters:
        add_qc_var = var + '_QC' in qc_parameters

        items = {"depth": dataset.attrs["sensor_depth"],
                 'magnetic_variation': dataset.attrs["magnetic_declination"],
                 "type": ODF_PARAMETERS_TYPES[str(dataset[var].data.dtype)]}
        items.update(parameters_metadata[var])

        qc_mask = data[var + '_QC'].values <= 2 if add_qc_var is True else None

        null_value = items["null_value"] if "null_value" in items else dataset[var].encoding["_FillValue"]

        odf.add_parameter(code=items["code"],
                          data=data[var].values,
                          null_value=null_value,
                          items=items,
                          qc_mask=qc_mask)

        if add_qc_var is True:
            qc_items = {
                "code": "QQQQ_" + str(qc_increment).zfill(2),
                "name": "Quality flag: " + items['name'],
                "units": "none",
                "print_field_width": 1,
                "print_decimal_places": 0,
                "null_value": 9,
                "type": ODF_PARAMETERS_TYPES[str(dataset[var + '_QC'].data.dtype)]
            }
            odf.add_parameter(code=qc_items["code"],
                              data=data[var + '_QC'].values,
                              null_value=9,
                              items=qc_items,
                              qc_mask=None)
            qc_increment += 1


def _find_section_timestamp(s: str) -> str:
    r""" String of Section - Timestamp

    regex : ([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})'
    """
    regex = r"([0-9]{4}-[0-9]{2}-[0-9]{2}\s[0-9]{2}:[0-9]{2}:[0-9]{2})"
    match = re.findall(regex, s)
    if match:
        return match[0]
    return None