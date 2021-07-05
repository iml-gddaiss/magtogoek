Magtogoek 
===========
*Name origin: Magtogoek is Algonquin name for the Saint-Lawrence River which mean "the path that walks".*

PACKAGE
--------

Magtogoek is a python package and command line application (CLI) to process ocean data. 
At the moment, only Accoustisc Doopler Current Profiler (ADCP) data can be processed. 
This package is developped by the Scientific Advice, Information and Support Branch at the Fisheries and Ocean Canada Maurice-Lamontagne Institute.

[Magtogoek documentation here](https://jeromejguay.github.io/magtogoek/)

Supported data type
^^^^^^^^^^^^^^^^^^^
* ADCP : Accoustisc Doopler Current Profiler 
  - RDI Teledyne: WorkHorse, SentinelV, OceanSurveilor **(Only available on Linux/MacOS Only)**
    Magtogoek uses the pycurrents package made by UH Currents Group of the University of Hawaii.
    Virtual Machine can be easly install on Windows machine see below.(TODO)
  - RTI Rowtech : 
    Magtogoek has a custom reader for RTI ENS files made using functions provided by Rowtech on
    their (repository TODO)[TODO].
* More to come.

## INSTALLATION
Clone the respository and and install it with `pip install`. Follow the instruction below. 

```shell
:$ mkdir ~/magtogoek
:$ cd ~/magtogoek
:$ git clone https://github.com/JeromeJGuay/magtogoek
:$ pip install magtogoek
```
## REQUIREMENTS
Magtogoek requires the external python package pycurrents made by UH Currents Group at the University of Hawaii to process Teledyne data. Visit [pycurrents webesite](https://currents.soest.hawaii.edu/ocn_data_analysis/installation.html) for more details.

### Pycurrents installation instruction:

```shell
:$ cd ~/magtogoek
:$ hg clone https://currents.soest.hawaii.edu/hgstage/pycurrents
:$ pip install pycurrents
```

## CLI APPLICATION USAGE
Magtogoek is only accessible from the terminal in the python evironnement that it was installed in. 
The CLI application is called as `mtgk`. 
More information  on the applican is available using the command -h/--help and --info.

### Magtogoek structure and processing flow.
Magtogoek main objective is to process instrument data from raw instrument data format to netcdf format following the CF metadata convention. 
However Magtogoek can also read, modify and export to ODF (Ocean Data Format) which is a use by Fisheries an Oceans Canada.

Data can be processed in two ways: Using the `quick` command or the `process` command. 
The `quick` commands allows to process instrument data directly from the command line where the default processing parameters can be modified with optionnal arguments.
The `process` commands allows the users to add more metadata to the output netcdf files using configuration files which are `.ini` files.

#### `mtgk quick`
```Shell
:$ mtgk quick [adcp,] FILENAME [options]
```

#### `mtgk process`
Configuration files are made with the command `config` followed by a specific sensors. 
Optionnal arguments can also be use to set some values in the configuration file directly from the terminal.
                        
```Shell
:$ mtgk config [adcp, ] FILENAME options
```
Once filled out, configuration files can by passed to the `process` command as follow

```Shell
:$ mtgk process CONFIG_NAME
```

#### platform files
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

The different sensors of a the same platform can be place in the same platform limiting the risk of error in the platform metadata across. 
Platform\_id should include the year or the version of the platform and a new platform should be added if any modification is made to a sensor or to the platform.
This make it easy to reprocesses old data without having to modifie the platform file or configuration file. 
While processing data a platform\_file, platform\_id and sensor\_id have to be provided to add sensor metadata.
In future version of Magtogoek, a single platform files could be use to store all the sensors metadata. 
That way, only the platform\_id and sensor\_id would be required to add sensors and platform metadata. 

Exemple of platform and configuration files are available in th `test` section of the Magtogoek project. 
Data are also included to test the `quick` and `process` command.

### Other command.

Magtogoek has additionals functionnalities under `check` and `compute` commands. 
    You can get info and help on these commands using the --info or -h options.

## ACKOWLEDGMENT
A special thanks goes to UH Currents Group for their work on Pycurrents.

