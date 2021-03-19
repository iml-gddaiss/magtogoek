from PyCRC.CRCCCITT import CRCCCITT


PACKET_MIN_SIZE = 5             # Minimum number of bytes in a packet

kGetModInfo = 1                 # 1 Queries the modules type and firmware revision number
kModInfoResp = 2                # 2 Response to kGetModInfo
kSetDataComponents = 3          # 3 Sets the data components to be output
kGetData = 4                    # 4 Queries the module for data
kDataResp = 5                   # 5 Response to kGetData
kSetConfig = 6                  # 6 Sets internal configuration in the module
kGetConfig = 7                  # 7 Queries the module for the current internal configuration value
kConfigResp = 8                 # 8 Response to kGetConfig
kSave = 9                       # 9 Commands the module to save internal and user calibration
kStartCal = 10                  # 10 Commands module to start user calibration
kStopCal = 11                   # 11 Commands the module to stop user calibration
kSetParam = 12                  # 12 Sets the FIR filter settings for the magnetometer and accelerometer sensors
kGetParam = 13                  # 13 Queries for the FIR filter settings for the magnetometer and accelerometer sensors
kParamResp = 14                 # 14 Contains the FIR filter setting for the magnetometer and accelerometer sensors
kPowerDown = 15                 # 15 Used to completely power - down the module
kSaveDone = 16                  # 16 Response to kSave
kUserCalSampCount = 17          # 17 Sent from the module after taking a calibration sample point
kUserCalScore = 18              # 18 Contains the calibration score
kSetConfigDone = 19             # 19 Response to kSetConfig
kSetParamDone = 20              # 20 Response to kSetParam
kStartIntervalMode = 21         # 21 Commands the module to output data at a fixed interval
kStopIntervalMode = 22          # 22 Commands the module to stop data output at a fixed interval
kPowerUp = 23                   # 23 Sent after wake up from power down mode
kSetAcqParams = 24              # 24 Sets the sensor acquistion parameters
kGetAcqParams = 25              # 25 Queries for the sensor acquisition parameters
kAcqParamsDone = 26             # 26 Response to kSetAcqParams
kAcqParamsResp = 27             # 27 Response to kGetAcqParams
kPowerDoneDown = 28             # 28 Response to kPowerDown
kFactoryUserCal = 29            # 29 Clears user magnetometer calibration coefficients
kFactoryUserCalDone = 30        # 30 Response to kFactoryUserCal
kTakeUserCalSample = 31         # 31 Commands the unit to take a sample during user calibration
kFactoryInclCal = 36            # 36 Clears user accelerometer calibration coefficients
kFactoryInclCalDone = 37        # 37 Response to kFactoryInclCal

# Param IDs
kFIRConfig = 1                  # 3 - AxisID(UInt8) + Count(UInt8) + Value(Float64) + ...

# Data Component IDs
kHeading = 5                    # 5 - type Float32
kDistortion = 8                 # 8 - type boolean
kCalStatus = 9                  # 9 - type boolean
kPAligned = 21                  # 21 - type Float32
kRAligned = 22                  # 22 - type Float32
kIZAligned = 23                 # 23 - type Float32
kPAngle = 24                    # 24 - type Float32
kRAngle = 25                    # 25 - type Float32
kXAligned = 27                  # 27 - type Float32
kYAligned = 28                  # 28 - type Float32
kZAligned = 29                  # 29 - type Float32

# Configuration Parameter IDs
kDeclination = 1                # 1 - type Float32
kTrueNorth = 2                  # 2 - type boolean
kBigEndian = 6                  # 6 - type boolean
kMountingRef = 10               # 10 - type UInt8
kUserCalStableCheck = 11        # 11 - type boolean
kUserCalNumPoints = 12          # 12 - type UInt32
kUserCalAutoSampling = 13       # 13 – type boolean
kBaudRate = 14                  # 14 – UInt8

# Mounting Reference IDs
kMountedStandard = 1
kMountedXUp = 2
kMountedYUp = 3
kMountedStdPlus90 = 4
kMountedStdPlus180 = 5
kMountedStdPlus270 = 6

# Result IDs
kErrNone = 0                    # 0 No Error
kErrSave = 1                    # 1 Error Saving


kXAxis = 1                      # Config Axis ID: X.
kYAxis = 2                      # Config Axis ID: Y.
kZAxis = 3                      # Config Axis ID: Z.
kPAxis = 4                      # Config Axis ID: Pitch(Accelerator).
kRAxis = 5                      # Config Axis ID: Roll(Accelerator).
kIZAxis = 6                     # Config Axis ID: Z(Accelerator).


def create_msg(frame_type, payload):
    index = 0
    crc = 0
    count = 0

    # Determine the payload size
    packet_frame_length = 0
    if not payload:
        packet_frame_length = len(payload)

    # Get the number of bytes
    count = packet_frame_length + PACKET_MIN_SIZE

    # Create a buffer
    buffer = [None]*count

    # Store the total len of the packet including the len
    # byteCount (2), the Frame ID (1), the data (len(data)), and the crc (2)
    # If no data is sent, the min len is 5
    buffer[index] = count >> 8
    index += 1
    buffer[index] = count & 0xff
    index += 1

    # Store the frame ID
    buffer[index] = frame_type

    # Add the payload
    if not payload:
        for i in range(payload):
            buffer[index] = payload[i]
            index += 1

    # Compute the CRC
    crc = CRCCCITT().calculate(input_data=bytes(buffer))
    buffer[index] = crc >> 8
    index += 1
    buffer[index] = crc & 0xFF
    index += 1
