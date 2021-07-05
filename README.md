# Magtogoek 
*Name origin: Magtogoek is Algonquin name for the Saint-Lawrence River which mean "the path that walks".*

## PACKAGE
Magtogoek is a python package and command line application (CLI) to process ocean data. At the moment,
only Accoustisc Doopler Current Profiler (ADCP) data can be processed. This package is developped by the (DAISS EN) at the Maurice-Lamontagne Institute (Departement of Fisheries and Ocean Canada).

### Supported data type.
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
$: mkdir ~/magtogoek
$: cd ~/magtogoek
$: git clone https://github.com/JeromeJGuay/magtogoek
$: pip install magtogoek
```
## REQUIREMENTS
Magtogoek requires the external package pycurrents from UH Currents Group at the University of Hawaii to process Teledyne data. Visit [pycurrents webesite](https://currents.soest.hawaii.edu/ocn_data_analysis/installation.html) for more details.


```shell
$: cd ~/magtogoek
$: hg clone https://currents.soest.hawaii.edu/hgstage/pycurrents
$: pip install pycurrents
```

## CLI APPLICATION USAGE
Magtogoek is only accessible from the terminal in the python evironnement that it was installed in. 
The CLI application is called as `mtgk`. 
More information  on the applican is available using the command -h/--help and --info.

### Magtogoek structure and processing flow.
Magtogoek main objective is to process instrument data from raw instrument data format to netcdf format following CF metadata convention. 

To do so, Magtogoek uses json file format to store the instrument metadata in what is called a platform file and ini file callad configuration file to configure data processing. 
Quick data processing is also available. (See below)

Platform file are structured as follow:

```json
{
    __PLATFORM_ID__: {
        "platform_name": null,
        "platform_type": null,
        "paltform_model": null,
        "mooring_number": null,
        "sounding": null,
        "longitude": null,
        "latitude": null,
        "platform_specs": {},
        "sensors": {
            __SENSOR_ID__: {
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
Note that in Magtogoek, instruments are refered to as sensors. 

The different sensors(instruemnts) of a a platform (ship, mooring, buoy, drifet, Rossete, etc) can therefore be place in the same platform limiting the risk of error in the platform metadata across. 
Platform\_id should include the year or the version of the platform and a new platform should be added if any modification is made to a sensor or to the platform.
This make it easy to reprocesses old data without having to modifie the platform file or configuration file. 
While processing data a platform\_file, platform\_id and sensor\_id have to be provided to add sensor metadata.

A plaform file is made with the command `config platoform`:
#### Config
```Shell
$: mtgk config  platform FILENAME 
```

Configuration files are made with the command `config` followed by a specific sensors.
                        
#### Config
```Shell
$: mtgk config adcp FILENAME 
```

#### Process
```Shell
$: mtgk process CONFIG_NAME [options]
```


#### Quick process
```Shell
$: mtgk quick [adcp,] FILENAME [options]
```






## ACKOWLEDGMENT
A special thanks goes to UH Currents Group for their work on Pycurrents.

