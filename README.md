# Magtogoek 
*Name origin: Magtogoek is Algonquin name for the Saint-Lawrence River which mean "the path that walks".*

## Package


Magtogoek is a python package and command line application (CLI) to process ocean data. 
At the moment, only Accoustisc Doopler Current Profiler (ADCP) data can be processed. 
This package is developped by the Scientific Advice, Information and Support Branch at the Fisheries and Ocean Canada Maurice-Lamontagne Institute.

<[Magtogoek documentation here](https://jeromejguay.github.io/magtogoek/)>

### Supported data type:

* ADCP : Accoustisc Doopler Current Profiler 
  - RDI Teledyne: WorkHorse, SentinelV, OceanSurveilor **(Only available on Linux/MacOS Only)**
    Magtogoek uses the pycurrents package made by UH Currents Group of the University of Hawaii.
    Virtual Machine can be easly install on Windows machine see below.(TODO)
  - RTI Rowtech : 
    Magtogoek has a custom reader for RTI ENS files made using functions provided by Rowtech on
    their (repository TODO)[TODO].
* More to come.

## Installation
First make a directory to clone the project to.
```shell
:$ mkdir ~/magtogoek
:$ cd ~/magtogoek
```
The clone the respository and and install it with `pip install`. 

```shell
:$ git clone https://github.com/JeromeJGuay/magtogoek
:$ pip install magtogoek
```
## Requirements
Magtogoek requires the external python package pycurrents made by UH Currents Group at the University of Hawaii to process Teledyne data. Pycurrents is only available on unix system. Visit [pycurrents webesite](https://currents.soest.hawaii.edu/ocn_data_analysis/installation.html) for more details.

### Pycurrents installation instruction:
Pycurrents can be clone in the same directory as magtogoek. Use `pip install` again to install it.
```shell
:$ cd ~/magtogoek
:$ hg clone https://currents.soest.hawaii.edu/hgstage/pycurrents
:$ pip install pycurrents
```

## CLI application usage
Magtogoek is accessible from the terminal in the python evironnement it was installed in. 
The CLI application is called by typing `mtgk`. 
More information on the CLI application is available using the command -h/--help and --info.

### Magtogoek structure and processing flow.
Magtogoek main objective is to process instrument data from raw instrument data format to netcdf format following the CF metadata convention. 
However Magtogoek can also read, modify and export to ODF (Ocean Data Format).
ODF is a text format used by Fisheries an Oceans Canada.

#### Processing data
Data can be processed in two ways: Using the `quick` command or the `process` command. 
The `quick` commands allows to process instrument data directly from the command line where the default processing parameters can be modified with optionnal arguments.
```Shell
:$ mtgk quick [adcp,] FILENAME [options]
```
The `process` commands allows the users to add more metadata to the output netcdf files using configuration files which are `.ini` files.
```Shell
:$ mtgk config [adcp, ] FILENAME options
```
Configuration files are made with the command `config` followed by a specific sensors. 
Optionnal arguments can also be use to set some values in the configuration file directly from the terminal.
Once filled out, configuration files can by passed to the `process` command,
```Shell
:$ mtgk process CONFIG_NAME
```

#### Metadata storage: platform files
Magtogoek uses `json` files to store instruments and platforms metadata which refered to as platform files.
Note that in Magtogoek, instruments are refered to as sensors. 
Platform could be anything that has some instruments/sensors e.g. ship, mooring, buoy, drifter, rossete, etc.

A plaform file is made with the command `config platform`:
```Shell
:$ mtgk config  platform FILENAME 
```
Platform files are structured as follow:

```json
{
    "__PLATFORM_ID__": {
        "platform_name": null,
        "platform_type": null,
        "paltform_model": null,
        "mooring_number": null,
        "sounding": null,
        "longitude": null,
        "latitude": null,
        "platform_specs": {},
        "sensors": {
            "__SENSOR_ID__": {
                "sensor_type": null,
                "sensor_depth": null,
                "serial_number": null,
                "manufacturer": null,
                "model": null,
                "firmware_version": null,
                "chief_scientist": null,
                "description": null
            }
        }
    }
}
```

Since a platform can have multiple sensors, platform metadata is shared across its sensors.
Platform\_id should include the year or the version of the platform and a new platform should be added if modifications are made to a sensor or to the platform.
This will make it easy to reprocesses old data without needing modification to platform the file or configuration file. 
When processing data, a platform\_file, platform\_id and sensor\_id have to be provided to add platform and sensor metadata.
In future version of Magtogoek, a single platform files could be use to store all the sensors metadata. 
That way, only the platform\_id and sensor\_id would be required to add sensors and platform metadata. 

Exemple of platform and configuration files are available in th `test` section of the Magtogoek project. 
Data are also included to test the `quick` and `process` command.

### Other command.

Magtogoek has additionals functionnalities under `check` and `compute` commands.
To come: `odf2nc` command to transform ODF files to netcdf.
You can get info and help on these commands using the --info or -h options.

## Tools

### Navgiation (to come)
```python
from magtogoek.navigation import navigation
```

## Acknowledgement
A special thanks goes to UH Currents Group for their work on Pycurrents.

