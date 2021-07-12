# Magtogoek 
*Name origin: Magtogoek is Algonquin for the Saint-Lawrence River which mean "the path that walks".*

Magtogoek is a python package and command line application (CLI) for processing ocean data. 
At the moment, only Accoustisc Doopler Current Profiler (ADCP) data can be processed. 
This package is developped by the Scientific Advice, Information and Support Branch at the Fisheries and Ocean Canada Maurice-Lamontagne Institute.

Supported data type:

* ADCP : Accoustisc Doopler Current Profiler **(Only available on Linux/MacOS Only)**
  - RDI Teledyne: WorkHorse, SentinelV, OceanSurveilor 
    Magtogoek uses the pycurrents package made by UH Currents Group of the University of Hawaii.
    Virtual Machine can be easly install on Windows machine see below.(TODO)
  - RTI Rowtech : 
    Magtogoek has a custom reader for RTI ENS files made using functions provided by Rowtech on
    their [repository](https://github.com/rowetechinc/RTI).
  - The RTI reader in `magtogoek.adcp.rti_reader can be use independently to read raw data but no processing is carried out from reader.
* More to come.

## Installation
### Install via `git clone`
Clone the respository from the [github repository](https://github.com/JeromeJGuay/magtogoek) and and install it with `pip install`. 
```shell
$ git clone https://github.com/JeromeJGuay/magtogoek
$ pip install -e magtogoek
```
The `-e` option will not copy the project to the pip package directory. 
Instead, the python will import the package from the `git` folder.
Running the `git pull` command will update the package from the github main branch latest version.
### Requirements
Python ~3.7

Magtogoek requires the external python package pycurrents made by UH Currents Group at the University of Hawaii to process Teledyne data. Pycurrents is only available on unix system. Visit [pycurrents website](https://currents.soest.hawaii.edu/ocn_data_analysis/installation.html) for more details.
Pycurrents can be clone from their [mercurial respository](https://currents.soest.hawaii.edu/hgstage/pycurrents) and install with `pip install`.
```shell
$ hg clone https://currents.soest.hawaii.edu/hgstage/pycurrents
$ pip install pycurrents
```
## Quick start
From the terminal, within the same python environnement it was installed in, type `mtgk` to run the CLI application. 
Using the command -h/--help and --info will give you informations on the different commands.

Magtogoek main purpose is to process raw instrument data and export them to netcdf format following the CF metadata convention. 
Magtogoek can also read, modify and export to ODF format (Ocean Data Format).
ODF is a text format used by Fisheries an Oceans Canada.

#### Processing data
Data can be processed in two ways: Using the `quick` command or the `process` command. 
Both command will produce a `.log` text files of the processing history.
The `quick` commands allows to process instrument data directly from the command line where the default processing parameters/values can be modified with optionnal arguments.
```Shell
$ mtgk quick [adcp,] [input_files] [OPTIONS]
```
The `process` commands allows the users to add more metadata to the output netcdf files using configuration files which are `.ini` files.
```Shell
$ mtgk config [adcp,] [config_name] [OPTIONS]
```
Configuration files are made with the command `config` followed by a specific sensors. 
Optionnal arguments can also be use to set some values in the configuration file directly from the terminal.
Once filled out, configuration files can by passed to the `process` command,
```Shell
$ mtgk process [config_file]

```

#### Metadata storage: platform files
Magtogoek uses `json` files to store sensors (instruments) and platforms metadata which refered to as platform files.
A platform can be anything that has some instruments/sensors e.g. ship, mooring, buoy, drifter, rossete, etc.
Platforms are json object containing a json object for each sensors. 
The PLATFORM\_ID for the platform should include the year or the version of the platform and a new platform should be added if modifications are made to a sensor or to the platform.
When processing data, a platform\_file, platform\_id and sensor\_id have to be provided to add platform and sensor metadata.
A plaform file is made with the command `config platform`:
```Shell
$ mtgk config platform FILENAME 
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
In future version of Magtogoek, a single platform files could be use to store all the sensors metadata. 
That way, only the platform\_id and sensor\_id would be required to add sensors and platform metadata. 
The `"platform_specs"` object is used by the ODF exporter to write the `BUOY_HEADER` metadata.
To add platform or sensors, copy and paste sections with all the keys.
### Examples
Example of platform and configuration files are available in th `test` section of the Magtogoek project. 
Data are also included to test the `quick` and `process` command.
Supposing you are in the test/files directory of the project, the `iml4_2017_sw_01.ENS` and `iml4_2017_sw_02.ENS` Rowtech files can be process using the `adcp_iml4_2017.ini` config file and the `process` command,
```shell
../magtogoek/test/files$ mtgk process adcp_iml4_2017.ini
```
or with th `quick` command:
```shell
../magtogoek/test/files$ mtgk quick adcp iml4_2017_sw_0*.ENS -s sw -y 2017 -n iml4_2017_sw_quick
```


### Other command.

Magtogoek has additionals functionnalities under `check` and `compute` commands.
To come: `odf2nc` command to transform ODF files to netcdf.
You can get info and help on these commands using the --info or -h options.

## More tools
Information on the following functions and object usage is accessible with the `help()` function.
#### Navgiation 
```python
from magtogoek.navigation import load_navigation
from magtogoek.navigation import compute_navigation
```
#### ODF file format
```python
from magtogoek.odf_format import Odf
```
## Acknowledgement
A special thanks goes to UH Currents Group for their work on Pycurrents.

