
The header section is auto generated. 
```dosini
[HEADER]
sensor_type                   = Auto generated. Field use by the `process` command. Do not change.
made_by                       = Auto generated.
last_updated                  = Auto generated. 
```

In the `input` and `output` sections, empty fileds are considered False.
If both `netcdf_output` and `odf_output` are false, `netcdf_output` will automatically be set to true.
```dosini
[INPUT]
input_files                   = REQUIRED. `path/to/filenames`: Multiple files can be put on the same line or on multiple lines.
platform_file                 = `path/to/platform` file.
platform_id                   = platform id (key) in the platform file.
sensor_id                     = sensor id (key) in the platform file.

[OUTPUT]
netcdf_output                 = `path/to/filenames` or (True, 1). If True or 1, netcdf_output = input_files.nc.
odf_output                    = `path/to/filenames` or (True, 1). If True or 1, odf_output is made from the `odf[files_specifications]`.
```

The `NETCDF_CF` section contains the metadata fields required by the CF conventions. Not necessary for ODF ouput.
```dosini
[NETCDF_CF]
Conventions                   = Auto generated.
title                         = -
institution                   = -
summary                       = -
references                    = Auto generated.
comments                      = -
naming_authority              = Auto generated.
source                        = Orginal method that produced the data. Ex: Numerical model (name), or instrument sampling (type).
```

The `PROJECT`, `CRUISE` and `GLOBAL_ATTRIBUTES` sections contains metadata. 
The netcdf global attributes will contains all the keys present in these sections, even if the field are left empty. 
Removing them will remove them from the netcdf global attributes.
```dosini
[PROJECT]
project                       = -
sea_name                      = -
sea_code                      = -

[CRUISE]
country_institute_code        = -
cruise_number                 = -
cruise_name                   = -
cruise_description            = -
organization                  = -
chief_scientist               = -
start_date                    = -
end_date                      = -
event_number                  = -
event_qualifier1              = -
event_qualifier2              = -
event_comments                = -

[GLOBAL_ATTRIBUTES]
date_created                  = -
data_type                     = -
data_subtype                  = -
cdm_data_type                 = -
country_code                  = -
publisher_email               = -
creator_type                  = -
publisher_name                = -
keywords                      = -
keywords_vocabulary           = -
standard_name_vocabulary      = Auto generated.
aknowledgment                 = -
```

In the `ADCP_PROCESSING`, `ADCP_QUALITY_CONTROL` and `ADCP_OUTPUT` sections, empty fileds are considered False. 
```dosini
[ADCP_PROCESSING]
yearbase                      = REQUIRED: YYYY, Year during which the sampling started.
adcp_orientation              = Adcp orientation: Either looking `up` or `down`.
sonar                         = REQUIRED: One of [`os`, `wh`, `sv`, `sw`, `sw_pd0`].
navigation_file               = `path/to/netcdf_file` with navigation data. See `mtgk compute nav --info`.
magnetic_declination          = Declination of the magnetic north in degree east. If True, this value overwrite the one in the adcp raw file.
sensor_depth                  = Sensor depth in meter. Will overwrite the one found in the adcp file.
keep_bt                       = If True, bottom track data are kept and can be used for motion correction.

[ADCP_QUALITY_CONTROL]
quality_control               = If True, quality control is carried out.
amplitude_threshold           = Value Between 0-255: Lower limit.
percentgood_threshold         = Value Between 0-100: Lower limit.
correlation_threshold         = Value Between 0-255: Lower limit.
horizontal_velocity_threshold = Upper limit.
vertical_velocity_threshold   = Upper limit.
error_velocity_threshold      = Upper limit.
sidelobes_correction          = If True sidelobe correction is carried.
bottom_depth                  = A bottom depth value can be set for sidelobe correction if needed.
pitch_threshold               = Value Between 0-180: Upper limit.
roll_threshold                = Value Between 0-180: Upper limit.
leading_trim                  = Removes a count of leading data or data before a given date or datetime.
                                Formats: Date ("YYYYMMDDT" or "YYYYMMDDThhmmss.ssss") or Count (integer).
                                Date ex: 2000-01-01T00:00:00.0000 -> 20000101T0000000000 or 20000101T.
trailing_trim                 = Removes a count of trailing data or data after a given date or datetime.
                                Formats: Date ("YYYYMMDDT" or "YYYYMMDDThhmmss.ssss") or Count (integer) 
                                Date ex: 2000-01-01T00:00:00.0000 -> 20000101T0000000000 or 20000101T.
depth_range                   = Value in meter. Cut the bin outside this range. Either min or min, max.
motion_correction_mode        = bt

[ADCP_OUTPUT]
merge_output_files            = If True, merge the input_files into a single output.
bodc_name                     = If True, Netcdf variables will have bodc parameter code name.
force_platform_metadata       = If True, Metadata from the platform file will overwrite those found in the raw file.
drop_percent_good             = If True, percent good data are drop from the netcdf output.
drop_correlation              = If True, correlation data are drop from the netcdf output.
drop_amplitude                = If True, amplitude data are drop from the netcdf output.
make_figures                  = If True figure are made and saved next the output files. (NOT YET AVAILABLE)
make_log                      = If True, a log book (text file) is made and saved next to the output file.
```
