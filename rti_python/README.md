# rti_python
RTI Library in Python


Rowe Technologies Inc. Python library

There is currently no main file to run.  This library contains core library files to create a python application.


# Dependencies
Must use Python version 3.5

OSX and Linux
```javascript
pip3 install -r requirements.txt -UI --user
```
 
 
Windows
```javascript
set-executionpolicy RemotedSigned
/venv/Scripts/activate.ps1
python -m pip install -r requirements.txt -UI --user
```


### Upgrade Dependcies to Latest Version
```term
pip install -r requirements.txt --upgrade
```

# Decode Binary Data to Ensemble Object
All the dataset definitions are in the Ensemble folder

```python
from rti_python.Codecs.AdcpCodec import AdcpCodec

# ADCP Codec to decode the ADCP data
adcp_codec = AdcpCodec()
adcp_codec.ensemble_event += process_ensemble

# Pass data to codec to decode ADCP data
adcp_codec.add(serial_raw_bytes)

def process_ensemble(sender, ens):
    """"
    Process the next incoming ensemble.
    """
    if ens.IsEnsembleData:
        print(str(ens.EnsembleData.EnsembleNumber))
```


# Read in a File and decode the data
```python
from rti_python.Utilities.read_binary_file import ReadBinaryFile

    def process_ens_func(sender, ens):
        """
        Receive the data from the file.  It will process the file.
        When an ensemble is found, it will call this function with the
        complete ensemble.
        :param ens: Ensemble to process.
        :return:
        """
        if ens.IsEnsembleData:
            print(str(ens.EnsembleData.EnsembleNumber))

# Create the file reader to read the binary file
read_binary = ReadBinaryFile()
read_binary.ensemble_event += process_ens_func

# Just define the file path
file_path = "/path/to/file/ensembles.ens"

# Pass the file path to the reader
read_binary.playback(file_path)
```


# Check for Bad Velocity in data
```python
if Ensemble.is_bad_velocity(vel_value):
    print("Bad Velocity Value")
else:
    print("Good Velocity Value")
```

# Serial Communication
```python
from rti_python.Comm.adcp_serial_port import AdcpSerialPort
import threading
import logging
import serial

comm_port = "COM5"
baud = 115200

serial_port = AdcpSerialPort(comm_port, baud)

# Start the read thread
serial_thread_alive = True
serial_thread = threading.Thread(name="Serial Terminal Thread", target=serial_thread_worker)
serial_thread.start()

def serial_thread_worker():
    """
    Thread worker to handle reading the serial port.
    :return:
    """
    while serial_thread_alive:
        try:
            if serial_port.raw_serial.in_waiting:
                # Read the data from the serial port
                serial_raw_bytes = serial_port.read(serial_port.raw_serial.in_waiting)

                # PASS THE RAW DATA TO THE CODEC TO BE DECODED
                # AND/OR
                # CONVERT THE BYTES TO ASCII TO SEE MESSAGES FROM ADCP
                # AND/OR
                # RECORD THE RAW DATA

        except serial.SerialException as se:
            logging.error("Error using the serial port.\n" + str(se))
            self.disconnect_serial()
        except Exception as ex:
            logging.error("Error processing the data.\n" + str(ex))
            self.disconnect_serial()
```

# Folder Structures

## ADCP
All the available commands and subsystem types.  This also contains the prediction model

## Codecs
Decode the ADCP data from different formats.

## Ensemble
Ensemble data formats

## Unittest
All the unittests.


## Waves
Waves MATLAB formats

## Writer
Write the ensemble data to a file format.

## Logging
Edit the log.py file to turn on or off some logging options.

