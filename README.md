# Magtogoek
Magtogoek is the Algonquin name for the Saint-Lawrence River which mean "the path that walks". 
## PACKAGE (LINUX/MacOS ONLY)
Magtogoek is a python package and command line application (CLI) to process ocean data. At the moment,
only Accoustisc Doopler Current Profiler (ADCP) data can be processed. 

## INSTALLATION
Clone the respository and and install it with `pip install`. Follow the instruction below. 

```shell
$: mkdir ~/magtogoek
$: cd ~/magtogoek
$: git clone https://github.com/JeromeJGuay/magtogoek
$: pip install magtogoek
```
## REQUIREMENTS
Magtogoek requires the external package pycurrents from UH Currents Group at the University of Hawaii.
Visit [https://currents.soest.hawaii.edu/ocn_data_analysis/installation.html] for more details.


```shell
$: cd ~/magtogoek
$: hg clone https://currents.soest.hawaii.edu/hgstage/pycurrents
$: pip install pycurrents
```
## USAGE

```Shell
$: mtgk quick 
```

