# Use pathlib instead of os
# mostly copied from jeanlucshaw adcp2nc
# TODO: add temporary attributes to files, like sensors, serial, depth. ie:
# -----: ie: _vartmp_adcp_serial_number = platform['adcp'].serial_number

## Add magnetic declination to option
# TODO add Minimum depth option.
# TODO add depth below which is flag

# TODO add compass ajustment
# def _get_from_expression(expression):
#    """TODO """
#    # list(Path().glob(expression))

## Other options
#    t_offset = args.t_offset / 24 if args.t_offset else 0
#
#    min_depth = args.mindep or 0
#
#    qc = not args.no_qc

# Get output path
#    if isinstance(args.files, list):
#        abs_path = os.path.abspath(args.files[0])
#    else:
#        abs_path = os.path.abspath(args.files)
#    path = '%s/' % os.path.dirname(abs_path)

# -----------------------------------#
# Binary reading and quality control#
# -----------------------------------#
# Read teledyne ADCP data

## TODO find path ext from filenames
# if args.adcptype in ["wh", "bb", "os"]:
#    ds = load_rdi_binary(
#        args.files,
#        args.adcptype,
#        force_dw=args.force_dw,
#        force_up=args.force_up,
#        min_depth=min_depth,
#    )
#    brand = "RDI"
#    sonar = args.adcptype
#    qc_kw = {**qc_defaults, **rdi_qc_defaults, **user_qc_kw}

# If model == Sentinel V, read in vertical beam data

## Read rowetech seawatch binaries directly
# elif args.adcptype == "sw":
#    ds = load_rtb_binary(args.files)
#    brand = "RTI"
#    sonar = args.adcptype
#    qc_kw = {**qc_defaults, **rti_qc_defaults, **user_qc_kw}

## Read rowetech seawatch binaries converted to pd0
# elif args.adcptype == "sw_pd0":
#    ds = load_rdi_binary(
#        args.files,
#        "wh",
#        force_dw=args.force_dw,
#        force_up=args.force_up,
#        min_depth=min_depth,
#    )
#    brand = "RTI"
#    sonar = "sw"
#    qc_kw = {**qc_defaults, **rdi_qc_defaults, **user_qc_kw}

## Sonar unknown
# else:
#    raise ValueError("Sonar type %s not recognized" % args.adcptype)


## Quality control
#  if qc:
#      ds = adcp_qc(ds, **qc_kw)


## Data Encoding
## Format data
# if bodc_name:
#    change var name and add new attrs.
## add variables_attrs
## add global_attrs

## if odf_file_name is False and netcdf_file_name is False:
#   netcdf_file_name = (inputfile remove ext .nc in local dir)
## export to odf
# if isinstance(odf_file_name, list):
#   export to odf
## Set creation date attribute
# ds.attrs['history'] = 'Created: %s' % datetime.now().strftime("%Y/%m/%d %H:%M:%S")
