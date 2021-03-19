import pytest
import os
import scipy.io as sio
import datetime
import rti_python.Codecs.WaveForceCodec as wfc
import rti_python.Ensemble.AncillaryData as AncillaryData
import rti_python.Ensemble.EnsembleData as EnsembleData
import rti_python.Ensemble.RangeTracking as RangeTracking
import rti_python.Ensemble.BeamVelocity as BeamVelocity
import rti_python.Ensemble.EarthVelocity as EarthVelocity
import rti_python.Ensemble.Correlation as CorrelationData
import rti_python.Ensemble.Ensemble as Ensemble


def test_constructor():
    codec = wfc.WaveForceCodec()

    assert codec.height_source == pytest.approx(4, 0, False)
    assert codec.Bin1 == pytest.approx(8, 0, False)
    assert codec.Bin2 == pytest.approx(9, 0, False)
    assert codec.Bin3 == pytest.approx(10, 0, False)
    assert codec.PressureSensorDepth == pytest.approx(30, 0, False)
    assert codec.EnsInBurst == pytest.approx(2048, 0, False)
    assert len(codec.selected_bin) == pytest.approx(3, 0, False)
    assert codec.CorrThreshold == pytest.approx(0.25, 0.0, False)
    assert codec.PressureOffset == pytest.approx(0.0, 0.0, False)


def test_init():
    codec = wfc.WaveForceCodec()

    assert codec.EnsInBurst == pytest.approx(2048, 0, False)
    assert codec.FilePath == os.path.expanduser('~')
    assert codec.Lat == pytest.approx(0.0, 0.1, False)
    assert codec.Lon == pytest.approx(0.0, 0.1, False)
    assert codec.height_source == pytest.approx(4, 0, False)
    assert codec.Bin1 == pytest.approx(8, 0, False)
    assert codec.Bin2 == pytest.approx(9, 0, False)
    assert codec.Bin3 == pytest.approx(10, 0, False)
    assert codec.CorrThreshold == pytest.approx(0.25, 0.0, False)
    assert codec.PressureOffset == pytest.approx(0.0, 0.0, False)
    assert codec.PressureSensorDepth == pytest.approx(30, 0, False)
    assert codec.EnsInBurst == pytest.approx(2048, 0, False)
    assert len(codec.selected_bin) == pytest.approx(3, 0, False)


def test_init_1():
    codec = wfc.WaveForceCodec(1024, os.path.expanduser('~'), 31.0, 118.5, 5, 6, 7, 22, 1, 0.84, 1.3)

    assert codec.EnsInBurst == pytest.approx(1024, 0, False)
    assert codec.FilePath == os.path.expanduser('~')
    assert codec.Lat == pytest.approx(31.0, 0.1, False)
    assert codec.Lon == pytest.approx(118.5, 0.1, False)
    assert codec.height_source == pytest.approx(1, 0, False)
    assert codec.Bin1 == pytest.approx(5, 0, False)
    assert codec.Bin2 == pytest.approx(6, 0, False)
    assert codec.Bin3 == pytest.approx(7, 0, False)
    assert codec.CorrThreshold == pytest.approx(0.84, 0.0, False)
    assert codec.PressureOffset == pytest.approx(1.3, 0.0, False)
    assert codec.PressureSensorDepth == pytest.approx(22, 0, False)
    assert len(codec.selected_bin) == pytest.approx(3, 0, False)


def test_update():
    codec = wfc.WaveForceCodec()
    codec.update_settings(1024, os.path.expanduser('~'), 31.0, 118.5, 5, 6, 7, 22, 1, 0.84, 1.3)

    assert codec.EnsInBurst == pytest.approx(1024, 0, False)
    assert codec.FilePath == os.path.expanduser('~')
    assert codec.Lat == pytest.approx(31.0, 0.1, False)
    assert codec.Lon == pytest.approx(118.5, 0.1, False)
    assert codec.height_source == pytest.approx(1, 0, False)
    assert codec.height_source == pytest.approx(1, 0, False)
    assert codec.Bin1 == pytest.approx(5, 0, False)
    assert codec.Bin2 == pytest.approx(6, 0, False)
    assert codec.Bin3 == pytest.approx(7, 0, False)
    assert codec.CorrThreshold == pytest.approx(0.84, 0.0, False)
    assert codec.PressureOffset == pytest.approx(1.3, 0.0, False)
    assert codec.PressureSensorDepth == pytest.approx(22, 0, False)
    assert len(codec.selected_bin) == pytest.approx(3, 0, False)

def test_first_time():
    #assert 736740.4324085647 == wfc.WaveForceCodec.python_time_to_matlab(2019, 2, 19, 10, 22, 39, 10)
    assert 737475.4323958333 == wfc.WaveForceCodec.datetime_to_matlab(datetime.datetime(2019, 2, 19, 10, 22, 39, 10*10000))
    assert wfc.WaveForceCodec.matlab_to_python_datetime(737475.4323958333) == datetime.datetime(2019, 2, 19, 10, 22, 38, 999998)
    #assert datetime.datetime(2019, 2, 19, 10, 22, 39, 10*10000) == wfc.WaveForceCodec.matlab_to_python_time(736740.4324085647)
    #assert datetime.datetime(2019, 2, 19, 10, 22, 39, 10*10000) == wfc.WaveForceCodec.matlab_to_python_time(wfc.WaveForceCodec.datetime_to_matlab(datetime.datetime(2019, 2, 19, 10, 22, 39, 10*10000)))
    #assert datetime.datetime(2019, 2, 19, 10, 22, 39, 10 * 10000) == wfc.WaveForceCodec.matlab_to_python_time(wfc.WaveForceCodec.python_time_to_matlab(2019, 2, 19, 10, 22, 39, 10))
    #assert wfc.WaveForceCodec.datetime2matlabdn(datetime.datetime(2019, 2, 19, 10, 22, 39, 10*10000)) == wfc.WaveForceCodec.python_time_to_matlab(2019, 2, 19, 10, 22, 39, 10)
    #assert datetime.datetime(2019, 2, 19, 10, 22, 39, 10*10000) == wfc.WaveForceCodec.matlab_to_python_time(736740.4324085647 - 0.000011574)



def test_add_ens():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    num_ens_in_burst = 3

    codec = wfc.WaveForceCodec(num_ens_in_burst, curr_dir, 32.0, 118.0, 3, 4, 5, 30, 4)
    codec.process_data_event += waves_rcv

    # Create Ensembles
    ancillary_data1 = AncillaryData.AncillaryData(17, 1)
    ancillary_data1.Heading = 22.0
    ancillary_data1.Pitch = 10.0
    ancillary_data1.Roll = 1.0
    ancillary_data1.TransducerDepth = 30.2
    ancillary_data1.WaterTemp = 23.5
    ancillary_data1.BinSize = 1
    ancillary_data1.FirstBinRange = 3

    ancillary_data2 = AncillaryData.AncillaryData(17, 1)
    ancillary_data2.Heading = 23.0
    ancillary_data2.Pitch = 13.0
    ancillary_data2.Roll = 3.0
    ancillary_data2.TransducerDepth = 33.2
    ancillary_data2.WaterTemp = 26.5
    ancillary_data2.BinSize = 1
    ancillary_data2.FirstBinRange = 3

    ancillary_data3 = AncillaryData.AncillaryData(17, 1)
    ancillary_data3.Heading = 24.0
    ancillary_data3.Pitch = 14.0
    ancillary_data3.Roll = 4.0
    ancillary_data3.TransducerDepth = 34.2
    ancillary_data3.WaterTemp = 27.5
    ancillary_data3.BinSize = 1
    ancillary_data3.FirstBinRange = 3

    ensemble_data1 = EnsembleData.EnsembleData(19, 1)
    ensemble_data1.EnsembleNumber = 1
    ensemble_data1.NumBeams = 4
    ensemble_data1.NumBins = 10
    ensemble_data1.Year = 2019
    ensemble_data1.Month = 2
    ensemble_data1.Day = 19
    ensemble_data1.Hour = 10
    ensemble_data1.Minute = 22
    ensemble_data1.Second = 39
    ensemble_data1.HSec = 10

    ensemble_data2 = EnsembleData.EnsembleData(19, 1)
    ensemble_data2.EnsembleNumber = 1
    ensemble_data2.NumBeams = 4
    ensemble_data2.NumBins = 10
    ensemble_data2.Year = 2019
    ensemble_data2.Month = 2
    ensemble_data2.Day = 19
    ensemble_data2.Hour = 10
    ensemble_data2.Minute = 23
    ensemble_data2.Second = 39
    ensemble_data2.HSec = 10

    ensemble_data3 = EnsembleData.EnsembleData(19, 1)
    ensemble_data3.EnsembleNumber = 1
    ensemble_data3.NumBeams = 4
    ensemble_data3.NumBins = 10
    ensemble_data3.Year = 2019
    ensemble_data3.Month = 2
    ensemble_data3.Day = 19
    ensemble_data3.Hour = 10
    ensemble_data3.Minute = 24
    ensemble_data3.Second = 39
    ensemble_data3.HSec = 10

    range_track1 = RangeTracking.RangeTracking()
    range_track1.NumBeams = 4
    range_track1.Range.append(38.0)
    range_track1.Range.append(39.0)
    range_track1.Range.append(40.0)
    range_track1.Range.append(41.0)

    range_track2 = RangeTracking.RangeTracking()
    range_track2.NumBeams = 4
    range_track2.Range.append(20.5)
    range_track2.Range.append(21.6)
    range_track2.Range.append(22.7)
    range_track2.Range.append(23.8)

    range_track3 = RangeTracking.RangeTracking()
    range_track3.NumBeams = 4
    range_track3.Range.append(33.1)
    range_track3.Range.append(34.2)
    range_track3.Range.append(35.3)
    range_track3.Range.append(36.4)


    ensemble1 = Ensemble.Ensemble()
    ensemble1.AddAncillaryData(ancillary_data1)
    ensemble1.AddEnsembleData(ensemble_data1)
    ensemble1.AddRangeTracking(range_track1)

    ensemble2 = Ensemble.Ensemble()
    ensemble2.AddAncillaryData(ancillary_data2)
    ensemble2.AddEnsembleData(ensemble_data2)
    ensemble2.AddRangeTracking(range_track2)

    ensemble3 = Ensemble.Ensemble()
    ensemble3.AddAncillaryData(ancillary_data3)
    ensemble3.AddEnsembleData(ensemble_data3)
    ensemble3.AddRangeTracking(range_track3)

    codec.add(ensemble1)
    codec.add(ensemble2)
    codec.add(ensemble3)


def waves_rcv(self, file_name):

    assert True == os.path.isfile(file_name)

    # Read in the MATLAB file
    mat_data = sio.loadmat(file_name)

    # Lat and Lon
    assert 32.0 == mat_data['lat'][0][0]
    assert 118.0 == mat_data['lon'][0][0]

    # Wave Cell Depths
    assert 6.0 == mat_data['whv'][0][0]
    assert 7.0 == mat_data['whv'][0][1]
    assert 8.0 == mat_data['whv'][0][2]

    # First Ensemble Time
    assert 737475.4323958333 == mat_data['wft'][0][0]

    # Time between Ensembles
    assert 60.0 == mat_data['wdt'][0][0]

    # Pressure Sensor Height
    assert 30 == mat_data['whp'][0][0]

    # Heading
    assert 22.0 == mat_data['whg'][0][0]
    assert 23.0 == mat_data['whg'][1][0]
    assert 24.0 == mat_data['whg'][2][0]

    # Pitch
    assert 10.0 == mat_data['wph'][0][0]
    assert 13.0 == mat_data['wph'][1][0]
    assert 14.0 == mat_data['wph'][2][0]

    # Roll
    assert 1.0 == mat_data['wrl'][0][0]
    assert 3.0 == mat_data['wrl'][1][0]
    assert 4.0 == mat_data['wrl'][2][0]

    # Pressure
    assert 30.2 == pytest.approx(mat_data['wps'][0][0], 0.1)
    assert 33.2 == pytest.approx(mat_data['wps'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wps'][2][0], 0.1)

    # Water Temp
    assert 23.5 == pytest.approx(mat_data['wts'][0][0], 0.1)
    assert 26.5 == pytest.approx(mat_data['wts'][1][0], 0.1)
    assert 27.5 == pytest.approx(mat_data['wts'][2][0], 0.1)

    # Average Range and Pressure
    assert 37.64 == pytest.approx(mat_data['wah'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['wah'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['wah'][2][0], 0.1)

    # Range Tracking
    assert 38.0 == pytest.approx(mat_data['wr0'][0][0], 0.1)
    assert 20.5 == pytest.approx(mat_data['wr0'][1][0], 0.1)
    assert 33.1 == pytest.approx(mat_data['wr0'][2][0], 0.1)

    assert 39.0 == pytest.approx(mat_data['wr1'][0][0], 0.1)
    assert 21.6 == pytest.approx(mat_data['wr1'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wr1'][2][0], 0.1)

    assert 40.0 == pytest.approx(mat_data['wr2'][0][0], 0.1)
    assert 22.7 == pytest.approx(mat_data['wr2'][1][0], 0.1)
    assert 35.3 == pytest.approx(mat_data['wr2'][2][0], 0.1)

    assert 41.0 == pytest.approx(mat_data['wr3'][0][0], 0.1)
    assert 23.8 == pytest.approx(mat_data['wr3'][1][0], 0.1)
    assert 36.4 == pytest.approx(mat_data['wr3'][2][0], 0.1)

    # Selected Wave Height Source
    # Average height
    #assert 37.64 == pytest.approx(mat_data['whs'][0][0], 0.1)
    #assert 24.36 == pytest.approx(mat_data['whs'][1][0], 0.1)
    #assert 34.64 == pytest.approx(mat_data['whs'][2][0], 0.1)


def test_add_ens_with_vert():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    num_ens_in_burst = 3

    codec = wfc.WaveForceCodec(num_ens_in_burst, curr_dir, 32.0, 118.0, 3, 4, 5, 30, 4, 25.0, 0.0)
    codec.process_data_event += waves_rcv_with_vert

    # Create Ensembles
    ancillary_data1 = AncillaryData.AncillaryData(17, 1)
    ancillary_data1.Heading = 22.0
    ancillary_data1.Pitch = 10.0
    ancillary_data1.Roll = 1.0
    ancillary_data1.TransducerDepth = 30.2
    ancillary_data1.WaterTemp = 23.5
    ancillary_data1.BinSize = 1
    ancillary_data1.FirstBinRange = 3

    ancillary_data2 = AncillaryData.AncillaryData(17, 1)
    ancillary_data2.Heading = 23.0
    ancillary_data2.Pitch = 13.0
    ancillary_data2.Roll = 3.0
    ancillary_data2.TransducerDepth = 33.2
    ancillary_data2.WaterTemp = 26.5
    ancillary_data2.BinSize = 1
    ancillary_data2.FirstBinRange = 3

    ancillary_data3 = AncillaryData.AncillaryData(17, 1)
    ancillary_data3.Heading = 24.0
    ancillary_data3.Pitch = 14.0
    ancillary_data3.Roll = 4.0
    ancillary_data3.TransducerDepth = 34.2
    ancillary_data3.WaterTemp = 27.5
    ancillary_data3.BinSize = 1
    ancillary_data3.FirstBinRange = 3

    ensemble_data1 = EnsembleData.EnsembleData(19, 1)
    ensemble_data1.EnsembleNumber = 1
    ensemble_data1.NumBeams = 4
    ensemble_data1.NumBins = 10
    ensemble_data1.Year = 2019
    ensemble_data1.Month = 2
    ensemble_data1.Day = 19
    ensemble_data1.Hour = 10
    ensemble_data1.Minute = 22
    ensemble_data1.Second = 39
    ensemble_data1.HSec = 10

    ensemble_data2 = EnsembleData.EnsembleData(19, 1)
    ensemble_data2.EnsembleNumber = 2
    ensemble_data2.NumBeams = 1
    ensemble_data2.NumBins = 10
    ensemble_data2.Year = 2019
    ensemble_data2.Month = 2
    ensemble_data2.Day = 19
    ensemble_data2.Hour = 10
    ensemble_data2.Minute = 23
    ensemble_data2.Second = 39
    ensemble_data2.HSec = 10

    ensemble_data3 = EnsembleData.EnsembleData(19, 1)
    ensemble_data3.EnsembleNumber = 3
    ensemble_data3.NumBeams = 4
    ensemble_data3.NumBins = 10
    ensemble_data3.Year = 2019
    ensemble_data3.Month = 2
    ensemble_data3.Day = 19
    ensemble_data3.Hour = 10
    ensemble_data3.Minute = 24
    ensemble_data3.Second = 39
    ensemble_data3.HSec = 10

    ensemble_data4 = EnsembleData.EnsembleData(19, 1)
    ensemble_data4.EnsembleNumber = 4
    ensemble_data4.NumBeams = 1
    ensemble_data4.NumBins = 10
    ensemble_data4.Year = 2019
    ensemble_data4.Month = 2
    ensemble_data4.Day = 19
    ensemble_data4.Hour = 10
    ensemble_data4.Minute = 25
    ensemble_data4.Second = 39
    ensemble_data4.HSec = 10

    ensemble_data5 = EnsembleData.EnsembleData(19, 1)
    ensemble_data5.EnsembleNumber = 5
    ensemble_data5.NumBeams = 4
    ensemble_data5.NumBins = 10
    ensemble_data5.Year = 2019
    ensemble_data5.Month = 2
    ensemble_data5.Day = 19
    ensemble_data5.Hour = 10
    ensemble_data5.Minute = 26
    ensemble_data5.Second = 39
    ensemble_data5.HSec = 10

    ensemble_data6 = EnsembleData.EnsembleData(19, 1)
    ensemble_data6.EnsembleNumber = 6
    ensemble_data6.NumBeams = 1
    ensemble_data6.NumBins = 10
    ensemble_data6.Year = 2019
    ensemble_data6.Month = 2
    ensemble_data6.Day = 19
    ensemble_data6.Hour = 10
    ensemble_data6.Minute = 27
    ensemble_data6.Second = 39
    ensemble_data6.HSec = 10

    ensemble_data7 = EnsembleData.EnsembleData(19, 1)
    ensemble_data7.EnsembleNumber = 7
    ensemble_data7.NumBeams = 4
    ensemble_data7.NumBins = 10
    ensemble_data7.Year = 2019
    ensemble_data7.Month = 2
    ensemble_data7.Day = 19
    ensemble_data7.Hour = 10
    ensemble_data7.Minute = 28
    ensemble_data7.Second = 39
    ensemble_data7.HSec = 10

    range_track1 = RangeTracking.RangeTracking()
    range_track1.NumBeams = 4
    range_track1.Range.append(38.0)
    range_track1.Range.append(39.0)
    range_track1.Range.append(40.0)
    range_track1.Range.append(41.0)

    range_track2 = RangeTracking.RangeTracking()
    range_track2.NumBeams = 1
    range_track2.Range.append(37.0)

    range_track3 = RangeTracking.RangeTracking()
    range_track3.NumBeams = 4
    range_track3.Range.append(20.5)
    range_track3.Range.append(21.6)
    range_track3.Range.append(22.7)
    range_track3.Range.append(23.8)

    range_track4 = RangeTracking.RangeTracking()
    range_track4.NumBeams = 1
    range_track4.Range.append(25.3)

    range_track5 = RangeTracking.RangeTracking()
    range_track5.NumBeams = 4
    range_track5.Range.append(33.1)
    range_track5.Range.append(34.2)
    range_track5.Range.append(35.3)
    range_track5.Range.append(36.4)

    range_track6 = RangeTracking.RangeTracking()
    range_track6.NumBeams = 1
    range_track6.Range.append(34.9)

    range_track7 = RangeTracking.RangeTracking()
    range_track7.NumBeams = 4
    range_track7.Range.append(32.1)
    range_track7.Range.append(35.2)
    range_track7.Range.append(33.3)
    range_track7.Range.append(36.4)

    ensemble1 = Ensemble.Ensemble()
    ensemble1.AddAncillaryData(ancillary_data1)
    ensemble1.AddEnsembleData(ensemble_data1)
    ensemble1.AddRangeTracking(range_track1)

    ensemble2 = Ensemble.Ensemble()
    ensemble2.AddAncillaryData(ancillary_data2)
    ensemble2.AddEnsembleData(ensemble_data2)
    ensemble2.AddRangeTracking(range_track2)

    ensemble3 = Ensemble.Ensemble()
    ensemble3.AddAncillaryData(ancillary_data3)
    ensemble3.AddEnsembleData(ensemble_data3)
    ensemble3.AddRangeTracking(range_track3)

    ensemble4 = Ensemble.Ensemble()
    ensemble4.AddAncillaryData(ancillary_data1)
    ensemble4.AddEnsembleData(ensemble_data4)
    ensemble4.AddRangeTracking(range_track4)

    ensemble5 = Ensemble.Ensemble()
    ensemble5.AddAncillaryData(ancillary_data2)
    ensemble5.AddEnsembleData(ensemble_data5)
    ensemble5.AddRangeTracking(range_track5)

    ensemble6 = Ensemble.Ensemble()
    ensemble6.AddAncillaryData(ancillary_data3)
    ensemble6.AddEnsembleData(ensemble_data6)
    ensemble6.AddRangeTracking(range_track6)

    ensemble7 = Ensemble.Ensemble()
    ensemble7.AddAncillaryData(ancillary_data3)
    ensemble7.AddEnsembleData(ensemble_data7)
    ensemble7.AddRangeTracking(range_track7)

    codec.add(ensemble1)
    codec.add(ensemble2)
    codec.add(ensemble3)
    codec.add(ensemble4)
    codec.add(ensemble5)
    codec.add(ensemble6)
    codec.add(ensemble7)


def waves_rcv_with_vert(self, file_name):

    assert True == os.path.isfile(file_name)

    # Read in the MATLAB file
    mat_data = sio.loadmat(file_name)

    # Lat and Lon
    assert 32.0 == mat_data['lat'][0][0]
    assert 118.0 == mat_data['lon'][0][0]

    # Wave Cell Depths
    assert 6.0 == mat_data['whv'][0][0]
    assert 7.0 == mat_data['whv'][0][1]
    assert 8.0 == mat_data['whv'][0][2]

    # First Ensemble Time
    assert 737475.4323958333 == mat_data['wft'][0][0]

    # Time between Ensembles
    assert 60.0 == mat_data['wdt'][0][0]

    # Pressure Sensor Height
    assert 30 == mat_data['whp'][0][0]

    # Heading
    assert 22.0 == mat_data['whg'][0][0]
    assert 24.0 == mat_data['whg'][1][0]
    assert 23.0 == mat_data['whg'][2][0]

    # Pitch
    assert 10.0 == mat_data['wph'][0][0]
    assert 14.0 == mat_data['wph'][1][0]
    assert 13.0 == mat_data['wph'][2][0]

    # Roll
    assert 1.0 == mat_data['wrl'][0][0]
    assert 4.0 == mat_data['wrl'][1][0]
    assert 3.0 == mat_data['wrl'][2][0]

    # Pressure
    assert 30.2 == pytest.approx(mat_data['wps'][0][0], 0.1)
    assert 33.2 == pytest.approx(mat_data['wps'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wps'][2][0], 0.1)

    # Water Temp
    assert 23.5 == pytest.approx(mat_data['wts'][0][0], 0.1)
    assert 26.5 == pytest.approx(mat_data['wts'][1][0], 0.1)
    assert 27.5 == pytest.approx(mat_data['wts'][2][0], 0.1)

    # Average Range and Pressure
    assert 37.64 == pytest.approx(mat_data['wah'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['wah'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['wah'][2][0], 0.1)

    # Range Tracking
    assert 38.0 == pytest.approx(mat_data['wr0'][0][0], 0.1)
    assert 20.5 == pytest.approx(mat_data['wr0'][1][0], 0.1)
    assert 33.1 == pytest.approx(mat_data['wr0'][2][0], 0.1)

    assert 39.0 == pytest.approx(mat_data['wr1'][0][0], 0.1)
    assert 21.6 == pytest.approx(mat_data['wr1'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wr1'][2][0], 0.1)

    assert 40.0 == pytest.approx(mat_data['wr2'][0][0], 0.1)
    assert 22.7 == pytest.approx(mat_data['wr2'][1][0], 0.1)
    assert 35.3 == pytest.approx(mat_data['wr2'][2][0], 0.1)

    assert 41.0 == pytest.approx(mat_data['wr3'][0][0], 0.1)
    assert 23.8 == pytest.approx(mat_data['wr3'][1][0], 0.1)
    assert 36.4 == pytest.approx(mat_data['wr3'][2][0], 0.1)

    # Selected Wave Height Source
    # Average height
    assert 37.64 == pytest.approx(mat_data['whs'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['whs'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['whs'][2][0], 0.1)

    # Vertical Beam Pressure
    assert 33.2 == pytest.approx(mat_data['wzp'][0][0], 0.1)
    assert 30.2 == pytest.approx(mat_data['wzp'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wzp'][2][0], 0.1)

    # Vertical Beam Range Tracking
    assert 37.0 == pytest.approx(mat_data['wzr'][0][0], 0.1)
    assert 25.3 == pytest.approx(mat_data['wzr'][1][0], 0.1)
    assert 34.9 == pytest.approx(mat_data['wzr'][2][0], 0.1)


def test_add_ens_ENU_short():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    num_ens_in_burst = 3

    codec = wfc.WaveForceCodec(num_ens_in_burst, curr_dir, 32.0, 118.0, 3, 4, 5, 30, 4, 25.0, 0.0)
    codec.process_data_event += waves_rcv_with_ENU_short

    # Create Ensembles
    ancillary_data1 = AncillaryData.AncillaryData(17, 1)
    ancillary_data1.Heading = 22.0
    ancillary_data1.Pitch = 10.0
    ancillary_data1.Roll = 1.0
    ancillary_data1.TransducerDepth = 30.2
    ancillary_data1.WaterTemp = 23.5
    ancillary_data1.BinSize = 1
    ancillary_data1.FirstBinRange = 3

    ancillary_data2 = AncillaryData.AncillaryData(17, 1)
    ancillary_data2.Heading = 23.0
    ancillary_data2.Pitch = 13.0
    ancillary_data2.Roll = 3.0
    ancillary_data2.TransducerDepth = 33.2
    ancillary_data2.WaterTemp = 26.5
    ancillary_data2.BinSize = 1
    ancillary_data2.FirstBinRange = 3

    ancillary_data3 = AncillaryData.AncillaryData(17, 1)
    ancillary_data3.Heading = 24.0
    ancillary_data3.Pitch = 14.0
    ancillary_data3.Roll = 4.0
    ancillary_data3.TransducerDepth = 34.2
    ancillary_data3.WaterTemp = 27.5
    ancillary_data3.BinSize = 1
    ancillary_data3.FirstBinRange = 3

    ensemble_data1 = EnsembleData.EnsembleData(19, 1)
    ensemble_data1.EnsembleNumber = 1
    ensemble_data1.NumBeams = 4
    ensemble_data1.NumBins = 10
    ensemble_data1.Year = 2019
    ensemble_data1.Month = 2
    ensemble_data1.Day = 19
    ensemble_data1.Hour = 10
    ensemble_data1.Minute = 22
    ensemble_data1.Second = 39
    ensemble_data1.HSec = 10

    ensemble_data2 = EnsembleData.EnsembleData(19, 1)
    ensemble_data2.EnsembleNumber = 2
    ensemble_data2.NumBeams = 1
    ensemble_data2.NumBins = 10
    ensemble_data2.Year = 2019
    ensemble_data2.Month = 2
    ensemble_data2.Day = 19
    ensemble_data2.Hour = 10
    ensemble_data2.Minute = 23
    ensemble_data2.Second = 39
    ensemble_data2.HSec = 10

    ensemble_data3 = EnsembleData.EnsembleData(19, 1)
    ensemble_data3.EnsembleNumber = 3
    ensemble_data3.NumBeams = 4
    ensemble_data3.NumBins = 10
    ensemble_data3.Year = 2019
    ensemble_data3.Month = 2
    ensemble_data3.Day = 19
    ensemble_data3.Hour = 10
    ensemble_data3.Minute = 24
    ensemble_data3.Second = 39
    ensemble_data3.HSec = 10

    ensemble_data4 = EnsembleData.EnsembleData(19, 1)
    ensemble_data4.EnsembleNumber = 4
    ensemble_data4.NumBeams = 1
    ensemble_data4.NumBins = 10
    ensemble_data4.Year = 2019
    ensemble_data4.Month = 2
    ensemble_data4.Day = 19
    ensemble_data4.Hour = 10
    ensemble_data4.Minute = 25
    ensemble_data4.Second = 39
    ensemble_data4.HSec = 10

    ensemble_data5 = EnsembleData.EnsembleData(19, 1)
    ensemble_data5.EnsembleNumber = 5
    ensemble_data5.NumBeams = 4
    ensemble_data5.NumBins = 10
    ensemble_data5.Year = 2019
    ensemble_data5.Month = 2
    ensemble_data5.Day = 19
    ensemble_data5.Hour = 10
    ensemble_data5.Minute = 26
    ensemble_data5.Second = 39
    ensemble_data5.HSec = 10

    ensemble_data6 = EnsembleData.EnsembleData(19, 1)
    ensemble_data6.EnsembleNumber = 6
    ensemble_data6.NumBeams = 1
    ensemble_data6.NumBins = 10
    ensemble_data6.Year = 2019
    ensemble_data6.Month = 2
    ensemble_data6.Day = 19
    ensemble_data6.Hour = 10
    ensemble_data6.Minute = 27
    ensemble_data6.Second = 39
    ensemble_data6.HSec = 10

    ensemble_data7 = EnsembleData.EnsembleData(19, 1)
    ensemble_data7.EnsembleNumber = 7
    ensemble_data7.NumBeams = 4
    ensemble_data7.NumBins = 10
    ensemble_data7.Year = 2019
    ensemble_data7.Month = 2
    ensemble_data7.Day = 19
    ensemble_data7.Hour = 10
    ensemble_data7.Minute = 28
    ensemble_data7.Second = 39
    ensemble_data7.HSec = 10

    range_track1 = RangeTracking.RangeTracking()
    range_track1.NumBeams = 4
    range_track1.Range.append(38.0)
    range_track1.Range.append(39.0)
    range_track1.Range.append(40.0)
    range_track1.Range.append(41.0)

    range_track2 = RangeTracking.RangeTracking()
    range_track2.NumBeams = 1
    range_track2.Range.append(37.0)

    range_track3 = RangeTracking.RangeTracking()
    range_track3.NumBeams = 4
    range_track3.Range.append(20.5)
    range_track3.Range.append(21.6)
    range_track3.Range.append(22.7)
    range_track3.Range.append(23.8)

    range_track4 = RangeTracking.RangeTracking()
    range_track4.NumBeams = 1
    range_track4.Range.append(25.3)

    range_track5 = RangeTracking.RangeTracking()
    range_track5.NumBeams = 4
    range_track5.Range.append(33.1)
    range_track5.Range.append(34.2)
    range_track5.Range.append(35.3)
    range_track5.Range.append(36.4)

    range_track6 = RangeTracking.RangeTracking()
    range_track6.NumBeams = 1
    range_track6.Range.append(34.9)

    range_track7 = RangeTracking.RangeTracking()
    range_track7.NumBeams = 4
    range_track7.Range.append(32.1)
    range_track7.Range.append(35.2)
    range_track7.Range.append(33.3)
    range_track7.Range.append(36.4)

    num_bins = 10
    num_beams = 4
    earth_vel1 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel1.Velocities[0][0] = -1.3
    earth_vel1.Velocities[0][1] = 0.65
    earth_vel1.Velocities[0][2] = -0.02
    earth_vel1.Velocities[0][3] = 0.1
    earth_vel1.Velocities[1][0] = -1.6
    earth_vel1.Velocities[1][1] = 0.56
    earth_vel1.Velocities[1][2] = -0.01
    earth_vel1.Velocities[1][3] = 0.08
    earth_vel1.Velocities[2][0] = -1.28
    earth_vel1.Velocities[2][1] = 0.36
    earth_vel1.Velocities[2][2] = -0.12
    earth_vel1.Velocities[2][3] = 0.13
    earth_vel1.Velocities[3][0] = -1.45
    earth_vel1.Velocities[3][1] = 0.25
    earth_vel1.Velocities[3][2] = -0.1
    earth_vel1.Velocities[3][3] = 0.11
    earth_vel1.Velocities[4][0] = -1.67
    earth_vel1.Velocities[4][1] = 0.67
    earth_vel1.Velocities[4][2] = -0.027
    earth_vel1.Velocities[4][3] = 0.17

    earth_vel3 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel3.Velocities[0][0] = -11.3
    earth_vel3.Velocities[0][1] = 1.65
    earth_vel3.Velocities[0][2] = -1.02
    earth_vel3.Velocities[0][3] = 1.1
    earth_vel3.Velocities[1][0] = -11.6
    earth_vel3.Velocities[1][1] = 1.56
    earth_vel3.Velocities[1][2] = -1.01
    earth_vel3.Velocities[1][3] = 1.08
    earth_vel3.Velocities[2][0] = -11.28
    earth_vel3.Velocities[2][1] = 1.36
    earth_vel3.Velocities[2][2] = -1.12
    earth_vel3.Velocities[2][3] = 1.13
    earth_vel3.Velocities[3][0] = -11.45
    earth_vel3.Velocities[3][1] = 1.25
    earth_vel3.Velocities[3][2] = -1.1
    earth_vel3.Velocities[3][3] = 1.11
    earth_vel3.Velocities[4][0] = -11.67
    earth_vel3.Velocities[4][1] = 1.67
    earth_vel3.Velocities[4][2] = -1.027
    earth_vel3.Velocities[4][3] = 1.17

    earth_vel5 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel5.Velocities[0][0] = -12.3
    earth_vel5.Velocities[0][1] = 2.65
    earth_vel5.Velocities[0][2] = -2.02
    earth_vel5.Velocities[0][3] = 2.1
    earth_vel5.Velocities[1][0] = -12.6
    earth_vel5.Velocities[1][1] = 2.56
    earth_vel5.Velocities[1][2] = -2.01
    earth_vel5.Velocities[1][3] = 2.08
    earth_vel5.Velocities[2][0] = -12.28
    earth_vel5.Velocities[2][1] = 2.36
    earth_vel5.Velocities[2][2] = -2.12
    earth_vel5.Velocities[2][3] = 2.13
    earth_vel5.Velocities[3][0] = -12.45
    earth_vel5.Velocities[3][1] = 2.25
    earth_vel5.Velocities[3][2] = -2.1
    earth_vel5.Velocities[3][3] = 2.11
    earth_vel5.Velocities[4][0] = -12.67
    earth_vel5.Velocities[4][1] = 2.67
    earth_vel5.Velocities[4][2] = -2.027
    earth_vel5.Velocities[4][3] = 2.17

    ensemble1 = Ensemble.Ensemble()
    ensemble1.AddAncillaryData(ancillary_data1)
    ensemble1.AddEnsembleData(ensemble_data1)
    ensemble1.AddRangeTracking(range_track1)
    ensemble1.AddEarthVelocity(earth_vel1)

    ensemble2 = Ensemble.Ensemble()
    ensemble2.AddAncillaryData(ancillary_data2)
    ensemble2.AddEnsembleData(ensemble_data2)
    ensemble2.AddRangeTracking(range_track2)

    ensemble3 = Ensemble.Ensemble()
    ensemble3.AddAncillaryData(ancillary_data3)
    ensemble3.AddEnsembleData(ensemble_data3)
    ensemble3.AddRangeTracking(range_track3)
    ensemble3.AddEarthVelocity(earth_vel3)

    ensemble4 = Ensemble.Ensemble()
    ensemble4.AddAncillaryData(ancillary_data1)
    ensemble4.AddEnsembleData(ensemble_data4)
    ensemble4.AddRangeTracking(range_track4)

    ensemble5 = Ensemble.Ensemble()
    ensemble5.AddAncillaryData(ancillary_data2)
    ensemble5.AddEnsembleData(ensemble_data5)
    ensemble5.AddRangeTracking(range_track5)
    #ensemble5.AddEarthVelocity(earth_vel5)

    ensemble6 = Ensemble.Ensemble()
    ensemble6.AddAncillaryData(ancillary_data3)
    ensemble6.AddEnsembleData(ensemble_data6)
    ensemble6.AddRangeTracking(range_track6)

    ensemble7 = Ensemble.Ensemble()
    ensemble7.AddAncillaryData(ancillary_data3)
    ensemble7.AddEnsembleData(ensemble_data7)
    ensemble7.AddRangeTracking(range_track7)

    codec.add(ensemble1)
    codec.add(ensemble2)
    codec.add(ensemble3)
    codec.add(ensemble4)
    codec.add(ensemble5)
    codec.add(ensemble6)
    codec.add(ensemble7)


def waves_rcv_with_ENU_short(self, file_name):

    assert True == os.path.isfile(file_name)

    # Read in the MATLAB file
    mat_data = sio.loadmat(file_name)

    # Lat and Lon
    assert 32.0 == mat_data['lat'][0][0]
    assert 118.0 == mat_data['lon'][0][0]

    # Wave Cell Depths
    assert 6.0 == mat_data['whv'][0][0]
    assert 7.0 == mat_data['whv'][0][1]
    assert 8.0 == mat_data['whv'][0][2]

    # First Ensemble Time
    assert 737475.4323958333 == mat_data['wft'][0][0]

    # Time between Ensembles
    assert 60.0 == mat_data['wdt'][0][0]

    # Pressure Sensor Height
    assert 30 == mat_data['whp'][0][0]

    # Heading
    assert 22.0 == mat_data['whg'][0][0]
    assert 24.0 == mat_data['whg'][1][0]
    assert 23.0 == mat_data['whg'][2][0]

    # Pitch
    assert 10.0 == mat_data['wph'][0][0]
    assert 14.0 == mat_data['wph'][1][0]
    assert 13.0 == mat_data['wph'][2][0]

    # Roll
    assert 1.0 == mat_data['wrl'][0][0]
    assert 4.0 == mat_data['wrl'][1][0]
    assert 3.0 == mat_data['wrl'][2][0]

    # Pressure
    assert 30.2 == pytest.approx(mat_data['wps'][0][0], 0.1)
    assert 33.2 == pytest.approx(mat_data['wps'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wps'][2][0], 0.1)

    # Water Temp
    assert 23.5 == pytest.approx(mat_data['wts'][0][0], 0.1)
    assert 26.5 == pytest.approx(mat_data['wts'][1][0], 0.1)
    assert 27.5 == pytest.approx(mat_data['wts'][2][0], 0.1)

    # Average Range and Pressure
    assert 37.64 == pytest.approx(mat_data['wah'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['wah'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['wah'][2][0], 0.1)

    # Range Tracking
    assert 38.0 == pytest.approx(mat_data['wr0'][0][0], 0.1)
    assert 20.5 == pytest.approx(mat_data['wr0'][1][0], 0.1)
    assert 33.1 == pytest.approx(mat_data['wr0'][2][0], 0.1)

    assert 39.0 == pytest.approx(mat_data['wr1'][0][0], 0.1)
    assert 21.6 == pytest.approx(mat_data['wr1'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wr1'][2][0], 0.1)

    assert 40.0 == pytest.approx(mat_data['wr2'][0][0], 0.1)
    assert 22.7 == pytest.approx(mat_data['wr2'][1][0], 0.1)
    assert 35.3 == pytest.approx(mat_data['wr2'][2][0], 0.1)

    assert 41.0 == pytest.approx(mat_data['wr3'][0][0], 0.1)
    assert 23.8 == pytest.approx(mat_data['wr3'][1][0], 0.1)
    assert 36.4 == pytest.approx(mat_data['wr3'][2][0], 0.1)

    # Selected Wave Height Source
    # Average height
    assert 37.64 == pytest.approx(mat_data['whs'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['whs'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['whs'][2][0], 0.1)

    # Vertical Beam Pressure
    assert 33.2 == pytest.approx(mat_data['wzp'][0][0], 0.1)
    assert 30.2 == pytest.approx(mat_data['wzp'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wzp'][2][0], 0.1)

    # Vertical Beam Range Tracking
    assert 37.0 == pytest.approx(mat_data['wzr'][0][0], 0.1)
    assert 25.3 == pytest.approx(mat_data['wzr'][1][0], 0.1)
    assert 34.9 == pytest.approx(mat_data['wzr'][2][0], 0.1)

    # Earth East Velocity
    assert -1.45 == pytest.approx(mat_data['wus'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wus'][1][0], 0.1)
    #assert -11.45 == pytest.approx(mat_data['wus'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wus'][1][1], 0.1)

    # Earth North Velocity
    assert 0.25 == pytest.approx(mat_data['wvs'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wvs'][1][0], 0.1)
    #assert 1.25 == pytest.approx(mat_data['wvs'][0][1], 0.1)
    #assert 1.67 == pytest.approx(mat_data['wvs'][1][1], 0.1)

    # Earth Vertical Velocity
    assert -0.1 == pytest.approx(mat_data['wzs'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wzs'][1][0], 0.1)
    #assert -1.1 == pytest.approx(mat_data['wzs'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wzs'][1][1], 0.1)


def test_add_ens_ENU():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    num_ens_in_burst = 3

    codec = wfc.WaveForceCodec(num_ens_in_burst, curr_dir, 32.0, 118.0, 3, 4, 5, 30, 4, 25.0, 0.0)
    codec.process_data_event += waves_rcv_with_ENU

    # Create Ensembles
    ancillary_data1 = AncillaryData.AncillaryData(17, 1)
    ancillary_data1.Heading = 22.0
    ancillary_data1.Pitch = 10.0
    ancillary_data1.Roll = 1.0
    ancillary_data1.TransducerDepth = 30.2
    ancillary_data1.WaterTemp = 23.5
    ancillary_data1.BinSize = 1
    ancillary_data1.FirstBinRange = 3

    ancillary_data2 = AncillaryData.AncillaryData(17, 1)
    ancillary_data2.Heading = 23.0
    ancillary_data2.Pitch = 13.0
    ancillary_data2.Roll = 3.0
    ancillary_data2.TransducerDepth = 33.2
    ancillary_data2.WaterTemp = 26.5
    ancillary_data2.BinSize = 1
    ancillary_data2.FirstBinRange = 3

    ancillary_data3 = AncillaryData.AncillaryData(17, 1)
    ancillary_data3.Heading = 24.0
    ancillary_data3.Pitch = 14.0
    ancillary_data3.Roll = 4.0
    ancillary_data3.TransducerDepth = 34.2
    ancillary_data3.WaterTemp = 27.5
    ancillary_data3.BinSize = 1
    ancillary_data3.FirstBinRange = 3

    ensemble_data1 = EnsembleData.EnsembleData(19, 1)
    ensemble_data1.EnsembleNumber = 1
    ensemble_data1.NumBeams = 4
    ensemble_data1.NumBins = 10
    ensemble_data1.Year = 2019
    ensemble_data1.Month = 2
    ensemble_data1.Day = 19
    ensemble_data1.Hour = 10
    ensemble_data1.Minute = 22
    ensemble_data1.Second = 39
    ensemble_data1.HSec = 10

    ensemble_data2 = EnsembleData.EnsembleData(19, 1)
    ensemble_data2.EnsembleNumber = 2
    ensemble_data2.NumBeams = 1
    ensemble_data2.NumBins = 10
    ensemble_data2.Year = 2019
    ensemble_data2.Month = 2
    ensemble_data2.Day = 19
    ensemble_data2.Hour = 10
    ensemble_data2.Minute = 23
    ensemble_data2.Second = 39
    ensemble_data2.HSec = 10

    ensemble_data3 = EnsembleData.EnsembleData(19, 1)
    ensemble_data3.EnsembleNumber = 3
    ensemble_data3.NumBeams = 4
    ensemble_data3.NumBins = 10
    ensemble_data3.Year = 2019
    ensemble_data3.Month = 2
    ensemble_data3.Day = 19
    ensemble_data3.Hour = 10
    ensemble_data3.Minute = 24
    ensemble_data3.Second = 39
    ensemble_data3.HSec = 10

    ensemble_data4 = EnsembleData.EnsembleData(19, 1)
    ensemble_data4.EnsembleNumber = 4
    ensemble_data4.NumBeams = 1
    ensemble_data4.NumBins = 10
    ensemble_data4.Year = 2019
    ensemble_data4.Month = 2
    ensemble_data4.Day = 19
    ensemble_data4.Hour = 10
    ensemble_data4.Minute = 25
    ensemble_data4.Second = 39
    ensemble_data4.HSec = 10

    ensemble_data5 = EnsembleData.EnsembleData(19, 1)
    ensemble_data5.EnsembleNumber = 5
    ensemble_data5.NumBeams = 4
    ensemble_data5.NumBins = 10
    ensemble_data5.Year = 2019
    ensemble_data5.Month = 2
    ensemble_data5.Day = 19
    ensemble_data5.Hour = 10
    ensemble_data5.Minute = 26
    ensemble_data5.Second = 39
    ensemble_data5.HSec = 10

    ensemble_data6 = EnsembleData.EnsembleData(19, 1)
    ensemble_data6.EnsembleNumber = 6
    ensemble_data6.NumBeams = 1
    ensemble_data6.NumBins = 10
    ensemble_data6.Year = 2019
    ensemble_data6.Month = 2
    ensemble_data6.Day = 19
    ensemble_data6.Hour = 10
    ensemble_data6.Minute = 27
    ensemble_data6.Second = 39
    ensemble_data6.HSec = 10

    ensemble_data7 = EnsembleData.EnsembleData(19, 1)
    ensemble_data7.EnsembleNumber = 7
    ensemble_data7.NumBeams = 4
    ensemble_data7.NumBins = 10
    ensemble_data7.Year = 2019
    ensemble_data7.Month = 2
    ensemble_data7.Day = 19
    ensemble_data7.Hour = 10
    ensemble_data7.Minute = 28
    ensemble_data7.Second = 39
    ensemble_data7.HSec = 10

    range_track1 = RangeTracking.RangeTracking()
    range_track1.NumBeams = 4
    range_track1.Range.append(38.0)
    range_track1.Range.append(39.0)
    range_track1.Range.append(40.0)
    range_track1.Range.append(41.0)

    range_track2 = RangeTracking.RangeTracking()
    range_track2.NumBeams = 1
    range_track2.Range.append(37.0)

    range_track3 = RangeTracking.RangeTracking()
    range_track3.NumBeams = 4
    range_track3.Range.append(20.5)
    range_track3.Range.append(21.6)
    range_track3.Range.append(22.7)
    range_track3.Range.append(23.8)

    range_track4 = RangeTracking.RangeTracking()
    range_track4.NumBeams = 1
    range_track4.Range.append(25.3)

    range_track5 = RangeTracking.RangeTracking()
    range_track5.NumBeams = 4
    range_track5.Range.append(33.1)
    range_track5.Range.append(34.2)
    range_track5.Range.append(35.3)
    range_track5.Range.append(36.4)

    range_track6 = RangeTracking.RangeTracking()
    range_track6.NumBeams = 1
    range_track6.Range.append(34.9)

    range_track7 = RangeTracking.RangeTracking()
    range_track7.NumBeams = 4
    range_track7.Range.append(32.1)
    range_track7.Range.append(35.2)
    range_track7.Range.append(33.3)
    range_track7.Range.append(36.4)

    num_bins = 10
    num_beams = 4
    earth_vel1 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel1.Velocities[0][0] = -1.3
    earth_vel1.Velocities[0][1] = 0.65
    earth_vel1.Velocities[0][2] = -0.02
    earth_vel1.Velocities[0][3] = 0.1
    earth_vel1.Velocities[1][0] = -1.6
    earth_vel1.Velocities[1][1] = 0.56
    earth_vel1.Velocities[1][2] = -0.01
    earth_vel1.Velocities[1][3] = 0.08
    earth_vel1.Velocities[2][0] = -1.28
    earth_vel1.Velocities[2][1] = 0.36
    earth_vel1.Velocities[2][2] = -0.12
    earth_vel1.Velocities[2][3] = 0.13
    earth_vel1.Velocities[3][0] = -1.45
    earth_vel1.Velocities[3][1] = 0.25
    earth_vel1.Velocities[3][2] = -0.1
    earth_vel1.Velocities[3][3] = 0.11
    earth_vel1.Velocities[4][0] = -1.67
    earth_vel1.Velocities[4][1] = 0.67
    earth_vel1.Velocities[4][2] = -0.027
    earth_vel1.Velocities[4][3] = 0.17

    earth_vel3 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel3.Velocities[0][0] = -11.3
    earth_vel3.Velocities[0][1] = 1.65
    earth_vel3.Velocities[0][2] = -1.02
    earth_vel3.Velocities[0][3] = 1.1
    earth_vel3.Velocities[1][0] = -11.6
    earth_vel3.Velocities[1][1] = 1.56
    earth_vel3.Velocities[1][2] = -1.01
    earth_vel3.Velocities[1][3] = 1.08
    earth_vel3.Velocities[2][0] = -11.28
    earth_vel3.Velocities[2][1] = 1.36
    earth_vel3.Velocities[2][2] = -1.12
    earth_vel3.Velocities[2][3] = 1.13
    earth_vel3.Velocities[3][0] = -11.45
    earth_vel3.Velocities[3][1] = 1.25
    earth_vel3.Velocities[3][2] = -1.1
    earth_vel3.Velocities[3][3] = 1.11
    earth_vel3.Velocities[4][0] = -11.67
    earth_vel3.Velocities[4][1] = 1.67
    earth_vel3.Velocities[4][2] = -1.027
    earth_vel3.Velocities[4][3] = 1.17

    earth_vel5 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel5.Velocities[0][0] = -12.3
    earth_vel5.Velocities[0][1] = 2.65
    earth_vel5.Velocities[0][2] = -2.02
    earth_vel5.Velocities[0][3] = 2.1
    earth_vel5.Velocities[1][0] = -12.6
    earth_vel5.Velocities[1][1] = 2.56
    earth_vel5.Velocities[1][2] = -2.01
    earth_vel5.Velocities[1][3] = 2.08
    earth_vel5.Velocities[2][0] = -12.28
    earth_vel5.Velocities[2][1] = 2.36
    earth_vel5.Velocities[2][2] = -2.12
    earth_vel5.Velocities[2][3] = 2.13
    earth_vel5.Velocities[3][0] = -12.45
    earth_vel5.Velocities[3][1] = 2.25
    earth_vel5.Velocities[3][2] = -2.1
    earth_vel5.Velocities[3][3] = 2.11
    earth_vel5.Velocities[4][0] = -12.67
    earth_vel5.Velocities[4][1] = 2.67
    earth_vel5.Velocities[4][2] = -2.027
    earth_vel5.Velocities[4][3] = 2.17

    ensemble1 = Ensemble.Ensemble()
    ensemble1.AddAncillaryData(ancillary_data1)
    ensemble1.AddEnsembleData(ensemble_data1)
    ensemble1.AddRangeTracking(range_track1)
    ensemble1.AddEarthVelocity(earth_vel1)

    ensemble2 = Ensemble.Ensemble()
    ensemble2.AddAncillaryData(ancillary_data2)
    ensemble2.AddEnsembleData(ensemble_data2)
    ensemble2.AddRangeTracking(range_track2)

    ensemble3 = Ensemble.Ensemble()
    ensemble3.AddAncillaryData(ancillary_data3)
    ensemble3.AddEnsembleData(ensemble_data3)
    ensemble3.AddRangeTracking(range_track3)
    ensemble3.AddEarthVelocity(earth_vel3)

    ensemble4 = Ensemble.Ensemble()
    ensemble4.AddAncillaryData(ancillary_data1)
    ensemble4.AddEnsembleData(ensemble_data4)
    ensemble4.AddRangeTracking(range_track4)

    ensemble5 = Ensemble.Ensemble()
    ensemble5.AddAncillaryData(ancillary_data2)
    ensemble5.AddEnsembleData(ensemble_data5)
    ensemble5.AddRangeTracking(range_track5)
    ensemble5.AddEarthVelocity(earth_vel5)

    ensemble6 = Ensemble.Ensemble()
    ensemble6.AddAncillaryData(ancillary_data3)
    ensemble6.AddEnsembleData(ensemble_data6)
    ensemble6.AddRangeTracking(range_track6)

    ensemble7 = Ensemble.Ensemble()
    ensemble7.AddAncillaryData(ancillary_data3)
    ensemble7.AddEnsembleData(ensemble_data7)
    ensemble7.AddRangeTracking(range_track7)

    codec.add(ensemble1)
    codec.add(ensemble2)
    codec.add(ensemble3)
    codec.add(ensemble4)
    codec.add(ensemble5)
    codec.add(ensemble6)
    codec.add(ensemble7)


def waves_rcv_with_ENU(self, file_name):

    assert True == os.path.isfile(file_name)

    # Read in the MATLAB file
    mat_data = sio.loadmat(file_name)

    # Lat and Lon
    assert 32.0 == mat_data['lat'][0][0]
    assert 118.0 == mat_data['lon'][0][0]

    # Wave Cell Depths
    assert 6.0 == mat_data['whv'][0][0]
    assert 7.0 == mat_data['whv'][0][1]
    assert 8.0 == mat_data['whv'][0][2]

    # First Ensemble Time
    assert 737475.4323958333 == mat_data['wft'][0][0]

    # Time between Ensembles
    assert 60.0 == mat_data['wdt'][0][0]

    # Pressure Sensor Height
    assert 30 == mat_data['whp'][0][0]

    # Heading
    assert 22.0 == mat_data['whg'][0][0]
    assert 24.0 == mat_data['whg'][1][0]
    assert 23.0 == mat_data['whg'][2][0]

    # Pitch
    assert 10.0 == mat_data['wph'][0][0]
    assert 14.0 == mat_data['wph'][1][0]
    assert 13.0 == mat_data['wph'][2][0]

    # Roll
    assert 1.0 == mat_data['wrl'][0][0]
    assert 4.0 == mat_data['wrl'][1][0]
    assert 3.0 == mat_data['wrl'][2][0]

    # Pressure
    assert 30.2 == pytest.approx(mat_data['wps'][0][0], 0.1)
    assert 33.2 == pytest.approx(mat_data['wps'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wps'][2][0], 0.1)

    # Water Temp
    assert 23.5 == pytest.approx(mat_data['wts'][0][0], 0.1)
    assert 26.5 == pytest.approx(mat_data['wts'][1][0], 0.1)
    assert 27.5 == pytest.approx(mat_data['wts'][2][0], 0.1)

    # Average Range and Pressure
    assert 37.64 == pytest.approx(mat_data['wah'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['wah'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['wah'][2][0], 0.1)

    # Range Tracking
    assert 38.0 == pytest.approx(mat_data['wr0'][0][0], 0.1)
    assert 20.5 == pytest.approx(mat_data['wr0'][1][0], 0.1)
    assert 33.1 == pytest.approx(mat_data['wr0'][2][0], 0.1)

    assert 39.0 == pytest.approx(mat_data['wr1'][0][0], 0.1)
    assert 21.6 == pytest.approx(mat_data['wr1'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wr1'][2][0], 0.1)

    assert 40.0 == pytest.approx(mat_data['wr2'][0][0], 0.1)
    assert 22.7 == pytest.approx(mat_data['wr2'][1][0], 0.1)
    assert 35.3 == pytest.approx(mat_data['wr2'][2][0], 0.1)

    assert 41.0 == pytest.approx(mat_data['wr3'][0][0], 0.1)
    assert 23.8 == pytest.approx(mat_data['wr3'][1][0], 0.1)
    assert 36.4 == pytest.approx(mat_data['wr3'][2][0], 0.1)

    # Selected Wave Height Source
    # Average height
    assert 37.64 == pytest.approx(mat_data['whs'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['whs'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['whs'][2][0], 0.1)

    # Vertical Beam Pressure
    assert 33.2 == pytest.approx(mat_data['wzp'][0][0], 0.1)
    assert 30.2 == pytest.approx(mat_data['wzp'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wzp'][2][0], 0.1)

    # Vertical Beam Range Tracking
    assert 37.0 == pytest.approx(mat_data['wzr'][0][0], 0.1)
    assert 25.3 == pytest.approx(mat_data['wzr'][1][0], 0.1)
    assert 34.9 == pytest.approx(mat_data['wzr'][2][0], 0.1)

    # Earth East Velocity
    assert -1.45 == pytest.approx(mat_data['wus'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wus'][1][0], 0.1)
    assert 88.88 == pytest.approx(mat_data['wus'][2][0], 0.1)
    assert -11.45 == pytest.approx(mat_data['wus'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wus'][1][1], 0.1)
    assert 88.88 == pytest.approx(mat_data['wus'][2][1], 0.1)
    assert -12.45 == pytest.approx(mat_data['wus'][0][2], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][1][2], 0.1)
    assert 88.88 == pytest.approx(mat_data['wus'][2][2], 0.1)

    # Earth North Velocity
    assert 0.25 == pytest.approx(mat_data['wvs'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wvs'][1][0], 0.1)
    assert 88.88 == pytest.approx(mat_data['wvs'][2][0], 0.1)
    assert 1.25 == pytest.approx(mat_data['wvs'][0][1], 0.1)
    assert 1.67 == pytest.approx(mat_data['wvs'][1][1], 0.1)
    assert 88.88 == pytest.approx(mat_data['wvs'][2][1], 0.1)
    assert 2.25 == pytest.approx(mat_data['wvs'][0][2], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][1][2], 0.1)
    assert 88.88 == pytest.approx(mat_data['wvs'][2][2], 0.1)

    # Earth Vertical Velocity
    assert -0.1 == pytest.approx(mat_data['wzs'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wzs'][1][0], 0.1)
    assert 88.88 == pytest.approx(mat_data['wvs'][2][0], 0.1)
    assert -1.1 == pytest.approx(mat_data['wzs'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wzs'][1][1], 0.1)
    assert 88.88 == pytest.approx(mat_data['wvs'][2][1], 0.1)
    assert -2.1 == pytest.approx(mat_data['wzs'][0][2], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][1][2], 0.1)
    assert 88.88 == pytest.approx(mat_data['wvs'][2][2], 0.1)


def test_add_ens_ENU1():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    num_ens_in_burst = 3

    codec = wfc.WaveForceCodec(num_ens_in_burst, curr_dir, 32.0, 118.0, 3, 4, 5, 30, 4, 25.0, 0.0)
    codec.process_data_event += waves_rcv_with_ENU1

    # Create Ensembles
    ancillary_data1 = AncillaryData.AncillaryData(17, 1)
    ancillary_data1.Heading = 22.0
    ancillary_data1.Pitch = 10.0
    ancillary_data1.Roll = 1.0
    ancillary_data1.TransducerDepth = 30.2
    ancillary_data1.WaterTemp = 23.5
    ancillary_data1.BinSize = 1
    ancillary_data1.FirstBinRange = 3

    ancillary_data2 = AncillaryData.AncillaryData(17, 1)
    ancillary_data2.Heading = 23.0
    ancillary_data2.Pitch = 13.0
    ancillary_data2.Roll = 3.0
    ancillary_data2.TransducerDepth = 33.2
    ancillary_data2.WaterTemp = 26.5
    ancillary_data2.BinSize = 1
    ancillary_data2.FirstBinRange = 3

    ancillary_data3 = AncillaryData.AncillaryData(17, 1)
    ancillary_data3.Heading = 24.0
    ancillary_data3.Pitch = 14.0
    ancillary_data3.Roll = 4.0
    ancillary_data3.TransducerDepth = 34.2
    ancillary_data3.WaterTemp = 27.5
    ancillary_data3.BinSize = 1
    ancillary_data3.FirstBinRange = 3

    ensemble_data1 = EnsembleData.EnsembleData(19, 1)
    ensemble_data1.EnsembleNumber = 1
    ensemble_data1.NumBeams = 4
    ensemble_data1.NumBins = 10
    ensemble_data1.Year = 2019
    ensemble_data1.Month = 2
    ensemble_data1.Day = 19
    ensemble_data1.Hour = 10
    ensemble_data1.Minute = 22
    ensemble_data1.Second = 39
    ensemble_data1.HSec = 10

    ensemble_data2 = EnsembleData.EnsembleData(19, 1)
    ensemble_data2.EnsembleNumber = 2
    ensemble_data2.NumBeams = 1
    ensemble_data2.NumBins = 10
    ensemble_data2.Year = 2019
    ensemble_data2.Month = 2
    ensemble_data2.Day = 19
    ensemble_data2.Hour = 10
    ensemble_data2.Minute = 23
    ensemble_data2.Second = 39
    ensemble_data2.HSec = 10

    ensemble_data3 = EnsembleData.EnsembleData(19, 1)
    ensemble_data3.EnsembleNumber = 3
    ensemble_data3.NumBeams = 4
    ensemble_data3.NumBins = 10
    ensemble_data3.Year = 2019
    ensemble_data3.Month = 2
    ensemble_data3.Day = 19
    ensemble_data3.Hour = 10
    ensemble_data3.Minute = 24
    ensemble_data3.Second = 39
    ensemble_data3.HSec = 10

    ensemble_data4 = EnsembleData.EnsembleData(19, 1)
    ensemble_data4.EnsembleNumber = 4
    ensemble_data4.NumBeams = 1
    ensemble_data4.NumBins = 10
    ensemble_data4.Year = 2019
    ensemble_data4.Month = 2
    ensemble_data4.Day = 19
    ensemble_data4.Hour = 10
    ensemble_data4.Minute = 25
    ensemble_data4.Second = 39
    ensemble_data4.HSec = 10

    ensemble_data5 = EnsembleData.EnsembleData(19, 1)
    ensemble_data5.EnsembleNumber = 5
    ensemble_data5.NumBeams = 4
    ensemble_data5.NumBins = 10
    ensemble_data5.Year = 2019
    ensemble_data5.Month = 2
    ensemble_data5.Day = 19
    ensemble_data5.Hour = 10
    ensemble_data5.Minute = 26
    ensemble_data5.Second = 39
    ensemble_data5.HSec = 10

    ensemble_data6 = EnsembleData.EnsembleData(19, 1)
    ensemble_data6.EnsembleNumber = 6
    ensemble_data6.NumBeams = 1
    ensemble_data6.NumBins = 10
    ensemble_data6.Year = 2019
    ensemble_data6.Month = 2
    ensemble_data6.Day = 19
    ensemble_data6.Hour = 10
    ensemble_data6.Minute = 27
    ensemble_data6.Second = 39
    ensemble_data6.HSec = 10

    ensemble_data7 = EnsembleData.EnsembleData(19, 1)
    ensemble_data7.EnsembleNumber = 7
    ensemble_data7.NumBeams = 4
    ensemble_data7.NumBins = 10
    ensemble_data7.Year = 2019
    ensemble_data7.Month = 2
    ensemble_data7.Day = 19
    ensemble_data7.Hour = 10
    ensemble_data7.Minute = 28
    ensemble_data7.Second = 39
    ensemble_data7.HSec = 10

    range_track1 = RangeTracking.RangeTracking()
    range_track1.NumBeams = 4
    range_track1.Range.append(38.0)
    range_track1.Range.append(39.0)
    range_track1.Range.append(40.0)
    range_track1.Range.append(41.0)

    range_track2 = RangeTracking.RangeTracking()
    range_track2.NumBeams = 1
    range_track2.Range.append(37.0)

    range_track3 = RangeTracking.RangeTracking()
    range_track3.NumBeams = 4
    range_track3.Range.append(20.5)
    range_track3.Range.append(21.6)
    range_track3.Range.append(22.7)
    range_track3.Range.append(23.8)

    range_track4 = RangeTracking.RangeTracking()
    range_track4.NumBeams = 1
    range_track4.Range.append(25.3)

    range_track5 = RangeTracking.RangeTracking()
    range_track5.NumBeams = 4
    range_track5.Range.append(33.1)
    range_track5.Range.append(34.2)
    range_track5.Range.append(35.3)
    range_track5.Range.append(36.4)

    range_track6 = RangeTracking.RangeTracking()
    range_track6.NumBeams = 1
    range_track6.Range.append(34.9)

    range_track7 = RangeTracking.RangeTracking()
    range_track7.NumBeams = 4
    range_track7.Range.append(32.1)
    range_track7.Range.append(35.2)
    range_track7.Range.append(33.3)
    range_track7.Range.append(36.4)

    num_bins = 10
    num_beams = 4
    earth_vel1 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel1.Velocities[0][0] = -1.3
    earth_vel1.Velocities[0][1] = 0.65
    earth_vel1.Velocities[0][2] = -0.02
    earth_vel1.Velocities[0][3] = 0.1
    earth_vel1.Velocities[1][0] = -1.6
    earth_vel1.Velocities[1][1] = 0.56
    earth_vel1.Velocities[1][2] = -0.01
    earth_vel1.Velocities[1][3] = 0.08
    earth_vel1.Velocities[2][0] = -1.28
    earth_vel1.Velocities[2][1] = 0.36
    earth_vel1.Velocities[2][2] = -0.12
    earth_vel1.Velocities[2][3] = 0.13
    earth_vel1.Velocities[3][0] = -1.45
    earth_vel1.Velocities[3][1] = 0.25
    earth_vel1.Velocities[3][2] = -0.1
    earth_vel1.Velocities[3][3] = 0.11
    earth_vel1.Velocities[4][0] = -1.67
    earth_vel1.Velocities[4][1] = 0.67
    earth_vel1.Velocities[4][2] = -0.027
    earth_vel1.Velocities[4][3] = 0.17
    earth_vel1.Velocities[5][0] = -2.67
    earth_vel1.Velocities[5][1] = 2.67
    earth_vel1.Velocities[5][2] = -2.027
    earth_vel1.Velocities[5][3] = 2.17

    earth_vel3 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel3.Velocities[0][0] = -11.3
    earth_vel3.Velocities[0][1] = 1.65
    earth_vel3.Velocities[0][2] = -1.02
    earth_vel3.Velocities[0][3] = 1.1
    earth_vel3.Velocities[1][0] = -11.6
    earth_vel3.Velocities[1][1] = 1.56
    earth_vel3.Velocities[1][2] = -1.01
    earth_vel3.Velocities[1][3] = 1.08
    earth_vel3.Velocities[2][0] = -11.28
    earth_vel3.Velocities[2][1] = 1.36
    earth_vel3.Velocities[2][2] = -1.12
    earth_vel3.Velocities[2][3] = 1.13
    earth_vel3.Velocities[3][0] = -11.45
    earth_vel3.Velocities[3][1] = 1.25
    earth_vel3.Velocities[3][2] = -1.1
    earth_vel3.Velocities[3][3] = 1.11
    earth_vel3.Velocities[4][0] = -11.67
    earth_vel3.Velocities[4][1] = 1.67
    earth_vel3.Velocities[4][2] = -1.027
    earth_vel3.Velocities[4][3] = 1.17
    earth_vel3.Velocities[5][0] = -12.67
    earth_vel3.Velocities[5][1] = 2.67
    earth_vel3.Velocities[5][2] = -2.027
    earth_vel3.Velocities[5][3] = 2.17

    earth_vel5 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel5.Velocities[0][0] = -12.3
    earth_vel5.Velocities[0][1] = 2.65
    earth_vel5.Velocities[0][2] = -2.02
    earth_vel5.Velocities[0][3] = 2.1
    earth_vel5.Velocities[1][0] = -12.6
    earth_vel5.Velocities[1][1] = 2.56
    earth_vel5.Velocities[1][2] = -2.01
    earth_vel5.Velocities[1][3] = 2.08
    earth_vel5.Velocities[2][0] = -12.28
    earth_vel5.Velocities[2][1] = 2.36
    earth_vel5.Velocities[2][2] = -2.12
    earth_vel5.Velocities[2][3] = 2.13
    earth_vel5.Velocities[3][0] = -12.45
    earth_vel5.Velocities[3][1] = 2.25
    earth_vel5.Velocities[3][2] = -2.1
    earth_vel5.Velocities[3][3] = 2.11
    earth_vel5.Velocities[4][0] = -12.67
    earth_vel5.Velocities[4][1] = 2.67
    earth_vel5.Velocities[4][2] = -2.027
    earth_vel5.Velocities[4][3] = 2.17
    earth_vel5.Velocities[5][0] = -13.67
    earth_vel5.Velocities[5][1] = 3.67
    earth_vel5.Velocities[5][2] = -3.027
    earth_vel5.Velocities[5][3] = 3.17

    ensemble1 = Ensemble.Ensemble()
    ensemble1.AddAncillaryData(ancillary_data1)
    ensemble1.AddEnsembleData(ensemble_data1)
    ensemble1.AddRangeTracking(range_track1)
    ensemble1.AddEarthVelocity(earth_vel1)

    ensemble2 = Ensemble.Ensemble()
    ensemble2.AddAncillaryData(ancillary_data2)
    ensemble2.AddEnsembleData(ensemble_data2)
    ensemble2.AddRangeTracking(range_track2)

    ensemble3 = Ensemble.Ensemble()
    ensemble3.AddAncillaryData(ancillary_data3)
    ensemble3.AddEnsembleData(ensemble_data3)
    ensemble3.AddRangeTracking(range_track3)
    ensemble3.AddEarthVelocity(earth_vel3)

    ensemble4 = Ensemble.Ensemble()
    ensemble4.AddAncillaryData(ancillary_data1)
    ensemble4.AddEnsembleData(ensemble_data4)
    ensemble4.AddRangeTracking(range_track4)

    ensemble5 = Ensemble.Ensemble()
    ensemble5.AddAncillaryData(ancillary_data2)
    ensemble5.AddEnsembleData(ensemble_data5)
    ensemble5.AddRangeTracking(range_track5)
    ensemble5.AddEarthVelocity(earth_vel5)

    ensemble6 = Ensemble.Ensemble()
    ensemble6.AddAncillaryData(ancillary_data3)
    ensemble6.AddEnsembleData(ensemble_data6)
    ensemble6.AddRangeTracking(range_track6)

    ensemble7 = Ensemble.Ensemble()
    ensemble7.AddAncillaryData(ancillary_data3)
    ensemble7.AddEnsembleData(ensemble_data7)
    ensemble7.AddRangeTracking(range_track7)

    codec.add(ensemble1)
    codec.add(ensemble2)
    codec.add(ensemble3)
    codec.add(ensemble4)
    codec.add(ensemble5)
    codec.add(ensemble6)
    codec.add(ensemble7)


def waves_rcv_with_ENU1(self, file_name):

    assert True == os.path.isfile(file_name)

    # Read in the MATLAB file
    mat_data = sio.loadmat(file_name)

    # Lat and Lon
    assert 32.0 == mat_data['lat'][0][0]
    assert 118.0 == mat_data['lon'][0][0]

    # Wave Cell Depths
    assert 6.0 == mat_data['whv'][0][0]
    assert 7.0 == mat_data['whv'][0][1]
    assert 8.0 == mat_data['whv'][0][2]

    # First Ensemble Time
    assert 737475.4323958333 == mat_data['wft'][0][0]

    # Time between Ensembles
    assert 60.0 == mat_data['wdt'][0][0]

    # Pressure Sensor Height
    assert 30 == mat_data['whp'][0][0]

    # Heading
    assert 22.0 == mat_data['whg'][0][0]
    assert 24.0 == mat_data['whg'][1][0]
    assert 23.0 == mat_data['whg'][2][0]

    # Pitch
    assert 10.0 == mat_data['wph'][0][0]
    assert 14.0 == mat_data['wph'][1][0]
    assert 13.0 == mat_data['wph'][2][0]

    # Roll
    assert 1.0 == mat_data['wrl'][0][0]
    assert 4.0 == mat_data['wrl'][1][0]
    assert 3.0 == mat_data['wrl'][2][0]

    # Pressure
    assert 30.2 == pytest.approx(mat_data['wps'][0][0], 0.1)
    assert 33.2 == pytest.approx(mat_data['wps'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wps'][2][0], 0.1)

    # Water Temp
    assert 23.5 == pytest.approx(mat_data['wts'][0][0], 0.1)
    assert 26.5 == pytest.approx(mat_data['wts'][1][0], 0.1)
    assert 27.5 == pytest.approx(mat_data['wts'][2][0], 0.1)

    # Average Range and Pressure
    assert 37.64 == pytest.approx(mat_data['wah'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['wah'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['wah'][2][0], 0.1)

    # Range Tracking
    assert 38.0 == pytest.approx(mat_data['wr0'][0][0], 0.1)
    assert 20.5 == pytest.approx(mat_data['wr0'][1][0], 0.1)
    assert 33.1 == pytest.approx(mat_data['wr0'][2][0], 0.1)

    assert 39.0 == pytest.approx(mat_data['wr1'][0][0], 0.1)
    assert 21.6 == pytest.approx(mat_data['wr1'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wr1'][2][0], 0.1)

    assert 40.0 == pytest.approx(mat_data['wr2'][0][0], 0.1)
    assert 22.7 == pytest.approx(mat_data['wr2'][1][0], 0.1)
    assert 35.3 == pytest.approx(mat_data['wr2'][2][0], 0.1)

    assert 41.0 == pytest.approx(mat_data['wr3'][0][0], 0.1)
    assert 23.8 == pytest.approx(mat_data['wr3'][1][0], 0.1)
    assert 36.4 == pytest.approx(mat_data['wr3'][2][0], 0.1)

    # Selected Wave Height Source
    # Average height
    assert 37.64 == pytest.approx(mat_data['whs'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['whs'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['whs'][2][0], 0.1)

    # Vertical Beam Pressure
    assert 33.2 == pytest.approx(mat_data['wzp'][0][0], 0.1)
    assert 30.2 == pytest.approx(mat_data['wzp'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wzp'][2][0], 0.1)

    # Vertical Beam Range Tracking
    assert 37.0 == pytest.approx(mat_data['wzr'][0][0], 0.1)
    assert 25.3 == pytest.approx(mat_data['wzr'][1][0], 0.1)
    assert 34.9 == pytest.approx(mat_data['wzr'][2][0], 0.1)

    # Earth East Velocity
    assert -1.45 == pytest.approx(mat_data['wus'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wus'][1][0], 0.1)
    assert -2.67 == pytest.approx(mat_data['wus'][2][0], 0.1)
    assert -11.45 == pytest.approx(mat_data['wus'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wus'][1][1], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][2][1], 0.1)
    assert -12.45 == pytest.approx(mat_data['wus'][0][2], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][1][2], 0.1)
    assert -13.67 == pytest.approx(mat_data['wus'][2][2], 0.1)

    # Earth North Velocity
    assert 0.25 == pytest.approx(mat_data['wvs'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wvs'][1][0], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][2][0], 0.1)
    assert 1.25 == pytest.approx(mat_data['wvs'][0][1], 0.1)
    assert 1.67 == pytest.approx(mat_data['wvs'][1][1], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][2][1], 0.1)
    assert 2.25 == pytest.approx(mat_data['wvs'][0][2], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][1][2], 0.1)
    assert 3.67 == pytest.approx(mat_data['wvs'][2][2], 0.1)

    # Earth Vertical Velocity
    assert -0.1 == pytest.approx(mat_data['wzs'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wzs'][1][0], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][2][0], 0.1)
    assert -1.1 == pytest.approx(mat_data['wzs'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wzs'][1][1], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][2][1], 0.1)
    assert -2.1 == pytest.approx(mat_data['wzs'][0][2], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][1][2], 0.1)
    assert -3.027 == pytest.approx(mat_data['wzs'][2][2], 0.1)


def test_add_ens_Beam():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    num_ens_in_burst = 3

    codec = wfc.WaveForceCodec(num_ens_in_burst, curr_dir, 32.0, 118.0, 3, 4, 5, 30, 4, 0.25, 0.0)
    codec.process_data_event += waves_rcv_with_Beam

    # Create Ensembles
    ancillary_data1 = AncillaryData.AncillaryData(17, 1)
    ancillary_data1.Heading = 22.0
    ancillary_data1.Pitch = 10.0
    ancillary_data1.Roll = 1.0
    ancillary_data1.TransducerDepth = 30.2
    ancillary_data1.WaterTemp = 23.5
    ancillary_data1.BinSize = 1
    ancillary_data1.FirstBinRange = 3

    ancillary_data2 = AncillaryData.AncillaryData(17, 1)
    ancillary_data2.Heading = 23.0
    ancillary_data2.Pitch = 13.0
    ancillary_data2.Roll = 3.0
    ancillary_data2.TransducerDepth = 33.2
    ancillary_data2.WaterTemp = 26.5
    ancillary_data2.BinSize = 1
    ancillary_data2.FirstBinRange = 3

    ancillary_data3 = AncillaryData.AncillaryData(17, 1)
    ancillary_data3.Heading = 24.0
    ancillary_data3.Pitch = 14.0
    ancillary_data3.Roll = 4.0
    ancillary_data3.TransducerDepth = 34.2
    ancillary_data3.WaterTemp = 27.5
    ancillary_data3.BinSize = 1
    ancillary_data3.FirstBinRange = 3

    ensemble_data1 = EnsembleData.EnsembleData(19, 1)
    ensemble_data1.EnsembleNumber = 1
    ensemble_data1.NumBeams = 4
    ensemble_data1.NumBins = 10
    ensemble_data1.Year = 2019
    ensemble_data1.Month = 2
    ensemble_data1.Day = 19
    ensemble_data1.Hour = 10
    ensemble_data1.Minute = 22
    ensemble_data1.Second = 39
    ensemble_data1.HSec = 10

    ensemble_data2 = EnsembleData.EnsembleData(19, 1)
    ensemble_data2.EnsembleNumber = 2
    ensemble_data2.NumBeams = 1
    ensemble_data2.NumBins = 10
    ensemble_data2.Year = 2019
    ensemble_data2.Month = 2
    ensemble_data2.Day = 19
    ensemble_data2.Hour = 10
    ensemble_data2.Minute = 23
    ensemble_data2.Second = 39
    ensemble_data2.HSec = 10

    ensemble_data3 = EnsembleData.EnsembleData(19, 1)
    ensemble_data3.EnsembleNumber = 3
    ensemble_data3.NumBeams = 4
    ensemble_data3.NumBins = 10
    ensemble_data3.Year = 2019
    ensemble_data3.Month = 2
    ensemble_data3.Day = 19
    ensemble_data3.Hour = 10
    ensemble_data3.Minute = 24
    ensemble_data3.Second = 39
    ensemble_data3.HSec = 10

    ensemble_data4 = EnsembleData.EnsembleData(19, 1)
    ensemble_data4.EnsembleNumber = 4
    ensemble_data4.NumBeams = 1
    ensemble_data4.NumBins = 10
    ensemble_data4.Year = 2019
    ensemble_data4.Month = 2
    ensemble_data4.Day = 19
    ensemble_data4.Hour = 10
    ensemble_data4.Minute = 25
    ensemble_data4.Second = 39
    ensemble_data4.HSec = 10

    ensemble_data5 = EnsembleData.EnsembleData(19, 1)
    ensemble_data5.EnsembleNumber = 5
    ensemble_data5.NumBeams = 4
    ensemble_data5.NumBins = 10
    ensemble_data5.Year = 2019
    ensemble_data5.Month = 2
    ensemble_data5.Day = 19
    ensemble_data5.Hour = 10
    ensemble_data5.Minute = 26
    ensemble_data5.Second = 39
    ensemble_data5.HSec = 10

    ensemble_data6 = EnsembleData.EnsembleData(19, 1)
    ensemble_data6.EnsembleNumber = 6
    ensemble_data6.NumBeams = 1
    ensemble_data6.NumBins = 10
    ensemble_data6.Year = 2019
    ensemble_data6.Month = 2
    ensemble_data6.Day = 19
    ensemble_data6.Hour = 10
    ensemble_data6.Minute = 27
    ensemble_data6.Second = 39
    ensemble_data6.HSec = 10

    ensemble_data7 = EnsembleData.EnsembleData(19, 1)
    ensemble_data7.EnsembleNumber = 7
    ensemble_data7.NumBeams = 4
    ensemble_data7.NumBins = 10
    ensemble_data7.Year = 2019
    ensemble_data7.Month = 2
    ensemble_data7.Day = 19
    ensemble_data7.Hour = 10
    ensemble_data7.Minute = 28
    ensemble_data7.Second = 39
    ensemble_data7.HSec = 10

    range_track1 = RangeTracking.RangeTracking()
    range_track1.NumBeams = 4
    range_track1.Range.append(38.0)
    range_track1.Range.append(39.0)
    range_track1.Range.append(40.0)
    range_track1.Range.append(41.0)

    range_track2 = RangeTracking.RangeTracking()
    range_track2.NumBeams = 1
    range_track2.Range.append(37.0)

    range_track3 = RangeTracking.RangeTracking()
    range_track3.NumBeams = 4
    range_track3.Range.append(20.5)
    range_track3.Range.append(21.6)
    range_track3.Range.append(22.7)
    range_track3.Range.append(23.8)

    range_track4 = RangeTracking.RangeTracking()
    range_track4.NumBeams = 1
    range_track4.Range.append(25.3)

    range_track5 = RangeTracking.RangeTracking()
    range_track5.NumBeams = 4
    range_track5.Range.append(33.1)
    range_track5.Range.append(34.2)
    range_track5.Range.append(35.3)
    range_track5.Range.append(36.4)

    range_track6 = RangeTracking.RangeTracking()
    range_track6.NumBeams = 1
    range_track6.Range.append(34.9)

    range_track7 = RangeTracking.RangeTracking()
    range_track7.NumBeams = 4
    range_track7.Range.append(32.1)
    range_track7.Range.append(35.2)
    range_track7.Range.append(33.3)
    range_track7.Range.append(36.4)

    num_bins = 10
    num_beams = 4
    earth_vel1 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel1.Velocities[0][0] = -1.3
    earth_vel1.Velocities[0][1] = 0.65
    earth_vel1.Velocities[0][2] = -0.02
    earth_vel1.Velocities[0][3] = 0.1
    earth_vel1.Velocities[1][0] = -1.6
    earth_vel1.Velocities[1][1] = 0.56
    earth_vel1.Velocities[1][2] = -0.01
    earth_vel1.Velocities[1][3] = 0.08
    earth_vel1.Velocities[2][0] = -1.28
    earth_vel1.Velocities[2][1] = 0.36
    earth_vel1.Velocities[2][2] = -0.12
    earth_vel1.Velocities[2][3] = 0.13
    earth_vel1.Velocities[3][0] = -1.45
    earth_vel1.Velocities[3][1] = 0.25
    earth_vel1.Velocities[3][2] = -0.1
    earth_vel1.Velocities[3][3] = 0.11
    earth_vel1.Velocities[4][0] = -1.67
    earth_vel1.Velocities[4][1] = 0.67
    earth_vel1.Velocities[4][2] = -0.027
    earth_vel1.Velocities[4][3] = 0.17
    earth_vel1.Velocities[5][0] = -2.67
    earth_vel1.Velocities[5][1] = 2.67
    earth_vel1.Velocities[5][2] = -2.027
    earth_vel1.Velocities[5][3] = 2.17

    earth_vel3 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel3.Velocities[0][0] = -11.3
    earth_vel3.Velocities[0][1] = 1.65
    earth_vel3.Velocities[0][2] = -1.02
    earth_vel3.Velocities[0][3] = 1.1
    earth_vel3.Velocities[1][0] = -11.6
    earth_vel3.Velocities[1][1] = 1.56
    earth_vel3.Velocities[1][2] = -1.01
    earth_vel3.Velocities[1][3] = 1.08
    earth_vel3.Velocities[2][0] = -11.28
    earth_vel3.Velocities[2][1] = 1.36
    earth_vel3.Velocities[2][2] = -1.12
    earth_vel3.Velocities[2][3] = 1.13
    earth_vel3.Velocities[3][0] = -11.45
    earth_vel3.Velocities[3][1] = 1.25
    earth_vel3.Velocities[3][2] = -1.1
    earth_vel3.Velocities[3][3] = 1.11
    earth_vel3.Velocities[4][0] = -11.67
    earth_vel3.Velocities[4][1] = 1.67
    earth_vel3.Velocities[4][2] = -1.027
    earth_vel3.Velocities[4][3] = 1.17
    earth_vel3.Velocities[5][0] = -12.67
    earth_vel3.Velocities[5][1] = 2.67
    earth_vel3.Velocities[5][2] = -2.027
    earth_vel3.Velocities[5][3] = 2.17

    earth_vel5 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel5.Velocities[0][0] = -12.3
    earth_vel5.Velocities[0][1] = 2.65
    earth_vel5.Velocities[0][2] = -2.02
    earth_vel5.Velocities[0][3] = 2.1
    earth_vel5.Velocities[1][0] = -12.6
    earth_vel5.Velocities[1][1] = 2.56
    earth_vel5.Velocities[1][2] = -2.01
    earth_vel5.Velocities[1][3] = 2.08
    earth_vel5.Velocities[2][0] = -12.28
    earth_vel5.Velocities[2][1] = 2.36
    earth_vel5.Velocities[2][2] = -2.12
    earth_vel5.Velocities[2][3] = 2.13
    earth_vel5.Velocities[3][0] = -12.45
    earth_vel5.Velocities[3][1] = 2.25
    earth_vel5.Velocities[3][2] = -2.1
    earth_vel5.Velocities[3][3] = 2.11
    earth_vel5.Velocities[4][0] = -12.67
    earth_vel5.Velocities[4][1] = 2.67
    earth_vel5.Velocities[4][2] = -2.027
    earth_vel5.Velocities[4][3] = 2.17
    earth_vel5.Velocities[5][0] = -13.67
    earth_vel5.Velocities[5][1] = 3.67
    earth_vel5.Velocities[5][2] = -3.027
    earth_vel5.Velocities[5][3] = 3.17

    # Beam Velocity
    beam_vel1 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel1.Velocities[0][0] = -1.3
    beam_vel1.Velocities[0][1] = 0.65
    beam_vel1.Velocities[0][2] = -0.02
    beam_vel1.Velocities[0][3] = 0.1
    beam_vel1.Velocities[1][0] = -1.6
    beam_vel1.Velocities[1][1] = 0.56
    beam_vel1.Velocities[1][2] = -0.01
    beam_vel1.Velocities[1][3] = 0.08
    beam_vel1.Velocities[2][0] = -1.28
    beam_vel1.Velocities[2][1] = 0.36
    beam_vel1.Velocities[2][2] = -0.12
    beam_vel1.Velocities[2][3] = 0.13
    beam_vel1.Velocities[3][0] = -1.45
    beam_vel1.Velocities[3][1] = 0.25
    beam_vel1.Velocities[3][2] = -0.1
    beam_vel1.Velocities[3][3] = 0.11
    beam_vel1.Velocities[4][0] = -1.67
    beam_vel1.Velocities[4][1] = 0.67
    beam_vel1.Velocities[4][2] = -0.027
    beam_vel1.Velocities[4][3] = 0.17
    beam_vel1.Velocities[5][0] = -2.67
    beam_vel1.Velocities[5][1] = 2.67
    beam_vel1.Velocities[5][2] = -2.027
    beam_vel1.Velocities[5][3] = 2.17

    beam_vel3 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel3.Velocities[0][0] = -11.3
    beam_vel3.Velocities[0][1] = 1.65
    beam_vel3.Velocities[0][2] = -1.02
    beam_vel3.Velocities[0][3] = 1.1
    beam_vel3.Velocities[1][0] = -11.6
    beam_vel3.Velocities[1][1] = 1.56
    beam_vel3.Velocities[1][2] = -1.01
    beam_vel3.Velocities[1][3] = 1.08
    beam_vel3.Velocities[2][0] = -11.28
    beam_vel3.Velocities[2][1] = 1.36
    beam_vel3.Velocities[2][2] = -1.12
    beam_vel3.Velocities[2][3] = 1.13
    beam_vel3.Velocities[3][0] = -11.45
    beam_vel3.Velocities[3][1] = 1.25
    beam_vel3.Velocities[3][2] = -1.1
    beam_vel3.Velocities[3][3] = 1.11
    beam_vel3.Velocities[4][0] = -11.67
    beam_vel3.Velocities[4][1] = 1.67
    beam_vel3.Velocities[4][2] = -1.027
    beam_vel3.Velocities[4][3] = 1.17
    beam_vel3.Velocities[5][0] = -12.67
    beam_vel3.Velocities[5][1] = 2.67
    beam_vel3.Velocities[5][2] = -2.027
    beam_vel3.Velocities[5][3] = 2.17

    beam_vel5 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel5.Velocities[0][0] = -12.3
    beam_vel5.Velocities[0][1] = 2.65
    beam_vel5.Velocities[0][2] = -2.02
    beam_vel5.Velocities[0][3] = 2.1
    beam_vel5.Velocities[1][0] = -12.6
    beam_vel5.Velocities[1][1] = 2.56
    beam_vel5.Velocities[1][2] = -2.01
    beam_vel5.Velocities[1][3] = 2.08
    beam_vel5.Velocities[2][0] = -12.28
    beam_vel5.Velocities[2][1] = 2.36
    beam_vel5.Velocities[2][2] = -2.12
    beam_vel5.Velocities[2][3] = 2.13
    beam_vel5.Velocities[3][0] = -12.45
    beam_vel5.Velocities[3][1] = 2.25
    beam_vel5.Velocities[3][2] = -2.1
    beam_vel5.Velocities[3][3] = 2.11
    beam_vel5.Velocities[4][0] = -12.67
    beam_vel5.Velocities[4][1] = 2.67
    beam_vel5.Velocities[4][2] = -2.027
    beam_vel5.Velocities[4][3] = 2.17
    beam_vel5.Velocities[5][0] = -13.67
    beam_vel5.Velocities[5][1] = 3.67
    beam_vel5.Velocities[5][2] = -3.027
    beam_vel5.Velocities[5][3] = 3.17

    ensemble1 = Ensemble.Ensemble()
    ensemble1.AddAncillaryData(ancillary_data1)
    ensemble1.AddEnsembleData(ensemble_data1)
    ensemble1.AddRangeTracking(range_track1)
    ensemble1.AddEarthVelocity(earth_vel1)
    ensemble1.AddBeamVelocity(beam_vel1)

    ensemble2 = Ensemble.Ensemble()
    ensemble2.AddAncillaryData(ancillary_data2)
    ensemble2.AddEnsembleData(ensemble_data2)
    ensemble2.AddRangeTracking(range_track2)

    ensemble3 = Ensemble.Ensemble()
    ensemble3.AddAncillaryData(ancillary_data3)
    ensemble3.AddEnsembleData(ensemble_data3)
    ensemble3.AddRangeTracking(range_track3)
    ensemble3.AddEarthVelocity(earth_vel3)
    ensemble3.AddBeamVelocity(beam_vel3)

    ensemble4 = Ensemble.Ensemble()
    ensemble4.AddAncillaryData(ancillary_data1)
    ensemble4.AddEnsembleData(ensemble_data4)
    ensemble4.AddRangeTracking(range_track4)

    ensemble5 = Ensemble.Ensemble()
    ensemble5.AddAncillaryData(ancillary_data2)
    ensemble5.AddEnsembleData(ensemble_data5)
    ensemble5.AddRangeTracking(range_track5)
    ensemble5.AddEarthVelocity(earth_vel5)
    ensemble5.AddBeamVelocity(beam_vel5)

    ensemble6 = Ensemble.Ensemble()
    ensemble6.AddAncillaryData(ancillary_data3)
    ensemble6.AddEnsembleData(ensemble_data6)
    ensemble6.AddRangeTracking(range_track6)

    ensemble7 = Ensemble.Ensemble()
    ensemble7.AddAncillaryData(ancillary_data3)
    ensemble7.AddEnsembleData(ensemble_data7)
    ensemble7.AddRangeTracking(range_track7)

    codec.add(ensemble1)
    codec.add(ensemble2)
    codec.add(ensemble3)
    codec.add(ensemble4)
    codec.add(ensemble5)
    codec.add(ensemble6)
    codec.add(ensemble7)


def waves_rcv_with_Beam(self, file_name):

    assert True == os.path.isfile(file_name)

    # Read in the MATLAB file
    mat_data = sio.loadmat(file_name)

    # Lat and Lon
    assert 32.0 == mat_data['lat'][0][0]
    assert 118.0 == mat_data['lon'][0][0]

    # Wave Cell Depths
    assert 6.0 == mat_data['whv'][0][0]
    assert 7.0 == mat_data['whv'][0][1]
    assert 8.0 == mat_data['whv'][0][2]

    # First Ensemble Time
    assert 737475.4323958333 == mat_data['wft'][0][0]

    # Time between Ensembles
    assert 60.0 == mat_data['wdt'][0][0]

    # Pressure Sensor Height
    assert 30 == mat_data['whp'][0][0]

    # Heading
    assert 22.0 == mat_data['whg'][0][0]
    assert 24.0 == mat_data['whg'][1][0]
    assert 23.0 == mat_data['whg'][2][0]

    # Pitch
    assert 10.0 == mat_data['wph'][0][0]
    assert 14.0 == mat_data['wph'][1][0]
    assert 13.0 == mat_data['wph'][2][0]

    # Roll
    assert 1.0 == mat_data['wrl'][0][0]
    assert 4.0 == mat_data['wrl'][1][0]
    assert 3.0 == mat_data['wrl'][2][0]

    # Pressure
    assert 30.2 == pytest.approx(mat_data['wps'][0][0], 0.1)
    assert 33.2 == pytest.approx(mat_data['wps'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wps'][2][0], 0.1)

    # Water Temp
    assert 23.5 == pytest.approx(mat_data['wts'][0][0], 0.1)
    assert 26.5 == pytest.approx(mat_data['wts'][1][0], 0.1)
    assert 27.5 == pytest.approx(mat_data['wts'][2][0], 0.1)

    # Average Range and Pressure
    assert 37.64 == pytest.approx(mat_data['wah'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['wah'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['wah'][2][0], 0.1)

    # Range Tracking
    assert 38.0 == pytest.approx(mat_data['wr0'][0][0], 0.1)
    assert 20.5 == pytest.approx(mat_data['wr0'][1][0], 0.1)
    assert 33.1 == pytest.approx(mat_data['wr0'][2][0], 0.1)

    assert 39.0 == pytest.approx(mat_data['wr1'][0][0], 0.1)
    assert 21.6 == pytest.approx(mat_data['wr1'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wr1'][2][0], 0.1)

    assert 40.0 == pytest.approx(mat_data['wr2'][0][0], 0.1)
    assert 22.7 == pytest.approx(mat_data['wr2'][1][0], 0.1)
    assert 35.3 == pytest.approx(mat_data['wr2'][2][0], 0.1)

    assert 41.0 == pytest.approx(mat_data['wr3'][0][0], 0.1)
    assert 23.8 == pytest.approx(mat_data['wr3'][1][0], 0.1)
    assert 36.4 == pytest.approx(mat_data['wr3'][2][0], 0.1)

    # Selected Wave Height Source
    # Average height
    assert 37.64 == pytest.approx(mat_data['whs'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['whs'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['whs'][2][0], 0.1)

    # Vertical Beam Pressure
    assert 33.2 == pytest.approx(mat_data['wzp'][0][0], 0.1)
    assert 30.2 == pytest.approx(mat_data['wzp'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wzp'][2][0], 0.1)

    # Vertical Beam Range Tracking
    assert 37.0 == pytest.approx(mat_data['wzr'][0][0], 0.1)
    assert 25.3 == pytest.approx(mat_data['wzr'][1][0], 0.1)
    assert 34.9 == pytest.approx(mat_data['wzr'][2][0], 0.1)

    # Earth East Velocity
    assert -1.45 == pytest.approx(mat_data['wus'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wus'][1][0], 0.1)
    assert -2.67 == pytest.approx(mat_data['wus'][2][0], 0.1)
    assert -11.45 == pytest.approx(mat_data['wus'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wus'][1][1], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][2][1], 0.1)
    assert -12.45 == pytest.approx(mat_data['wus'][0][2], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][1][2], 0.1)
    assert -13.67 == pytest.approx(mat_data['wus'][2][2], 0.1)

    # Earth North Velocity
    assert 0.25 == pytest.approx(mat_data['wvs'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wvs'][1][0], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][2][0], 0.1)
    assert 1.25 == pytest.approx(mat_data['wvs'][0][1], 0.1)
    assert 1.67 == pytest.approx(mat_data['wvs'][1][1], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][2][1], 0.1)
    assert 2.25 == pytest.approx(mat_data['wvs'][0][2], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][1][2], 0.1)
    assert 3.67 == pytest.approx(mat_data['wvs'][2][2], 0.1)

    # Earth Vertical Velocity
    assert -0.1 == pytest.approx(mat_data['wzs'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wzs'][1][0], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][2][0], 0.1)
    assert -1.1 == pytest.approx(mat_data['wzs'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wzs'][1][1], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][2][1], 0.1)
    assert -2.1 == pytest.approx(mat_data['wzs'][0][2], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][1][2], 0.1)
    assert -3.027 == pytest.approx(mat_data['wzs'][2][2], 0.1)

    # Beam 0 Velocity
    assert -1.45 == pytest.approx(mat_data['wb0'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wb0'][1][0], 0.1)
    assert -2.67 == pytest.approx(mat_data['wb0'][2][0], 0.1)
    assert -11.45 == pytest.approx(mat_data['wb0'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wb0'][1][1], 0.1)
    assert -12.67 == pytest.approx(mat_data['wb0'][2][1], 0.1)
    assert -12.45 == pytest.approx(mat_data['wb0'][0][2], 0.1)
    assert -12.67 == pytest.approx(mat_data['wb0'][1][2], 0.1)
    assert -13.67 == pytest.approx(mat_data['wb0'][2][2], 0.1)

    # Beam 1 Velocity
    assert 0.25 == pytest.approx(mat_data['wb1'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wb1'][1][0], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][2][0], 0.1)
    assert 1.25 == pytest.approx(mat_data['wb1'][0][1], 0.1)
    assert 1.67 == pytest.approx(mat_data['wb1'][1][1], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][2][1], 0.1)
    assert 2.25 == pytest.approx(mat_data['wb1'][0][2], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][1][2], 0.1)
    assert 3.67 == pytest.approx(mat_data['wb1'][2][2], 0.1)

    # Beam 3 Velocity
    assert -0.1 == pytest.approx(mat_data['wb2'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wb2'][1][0], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][2][0], 0.1)
    assert -1.1 == pytest.approx(mat_data['wb2'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wb2'][1][1], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][2][1], 0.1)
    assert -2.1 == pytest.approx(mat_data['wb2'][0][2], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][1][2], 0.1)
    assert -3.027 == pytest.approx(mat_data['wb2'][2][2], 0.1)

    # Beam 4 Velocity
    assert 0.11 == pytest.approx(mat_data['wb3'][0][0], 0.1)
    assert 0.17 == pytest.approx(mat_data['wb3'][1][0], 0.1)
    assert 2.17 == pytest.approx(mat_data['wb3'][2][0], 0.1)
    assert 1.11 == pytest.approx(mat_data['wb3'][0][1], 0.1)
    assert 1.17 == pytest.approx(mat_data['wb3'][1][1], 0.1)
    assert 2.17 == pytest.approx(mat_data['wb3'][2][1], 0.1)
    assert 2.11 == pytest.approx(mat_data['wb3'][0][2], 0.1)
    assert 2.17 == pytest.approx(mat_data['wb3'][1][2], 0.1)
    assert 3.17 == pytest.approx(mat_data['wb3'][2][2], 0.1)


def test_add_ens_VertBeam():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    num_ens_in_burst = 3

    codec = wfc.WaveForceCodec(num_ens_in_burst, curr_dir, 32.0, 118.0, 3, 4, 5, 30, 4, 25.0, 0.0)
    codec.process_data_event += waves_rcv_with_VertBeam

    # Create Ensembles
    ancillary_data1 = AncillaryData.AncillaryData(17, 1)
    ancillary_data1.Heading = 22.0
    ancillary_data1.Pitch = 10.0
    ancillary_data1.Roll = 1.0
    ancillary_data1.TransducerDepth = 30.2
    ancillary_data1.WaterTemp = 23.5
    ancillary_data1.BinSize = 1
    ancillary_data1.FirstBinRange = 3

    ancillary_data2 = AncillaryData.AncillaryData(17, 1)
    ancillary_data2.Heading = 23.0
    ancillary_data2.Pitch = 13.0
    ancillary_data2.Roll = 3.0
    ancillary_data2.TransducerDepth = 33.2
    ancillary_data2.WaterTemp = 26.5
    ancillary_data2.BinSize = 1
    ancillary_data2.FirstBinRange = 3

    ancillary_data3 = AncillaryData.AncillaryData(17, 1)
    ancillary_data3.Heading = 24.0
    ancillary_data3.Pitch = 14.0
    ancillary_data3.Roll = 4.0
    ancillary_data3.TransducerDepth = 34.2
    ancillary_data3.WaterTemp = 27.5
    ancillary_data3.BinSize = 1
    ancillary_data3.FirstBinRange = 3

    ensemble_data1 = EnsembleData.EnsembleData(19, 1)
    ensemble_data1.EnsembleNumber = 1
    ensemble_data1.NumBeams = 4
    ensemble_data1.NumBins = 10
    ensemble_data1.Year = 2019
    ensemble_data1.Month = 2
    ensemble_data1.Day = 19
    ensemble_data1.Hour = 10
    ensemble_data1.Minute = 22
    ensemble_data1.Second = 39
    ensemble_data1.HSec = 10

    ensemble_data2 = EnsembleData.EnsembleData(19, 1)
    ensemble_data2.EnsembleNumber = 2
    ensemble_data2.NumBeams = 1
    ensemble_data2.NumBins = 10
    ensemble_data2.Year = 2019
    ensemble_data2.Month = 2
    ensemble_data2.Day = 19
    ensemble_data2.Hour = 10
    ensemble_data2.Minute = 23
    ensemble_data2.Second = 39
    ensemble_data2.HSec = 10

    ensemble_data3 = EnsembleData.EnsembleData(19, 1)
    ensemble_data3.EnsembleNumber = 3
    ensemble_data3.NumBeams = 4
    ensemble_data3.NumBins = 10
    ensemble_data3.Year = 2019
    ensemble_data3.Month = 2
    ensemble_data3.Day = 19
    ensemble_data3.Hour = 10
    ensemble_data3.Minute = 24
    ensemble_data3.Second = 39
    ensemble_data3.HSec = 10

    ensemble_data4 = EnsembleData.EnsembleData(19, 1)
    ensemble_data4.EnsembleNumber = 4
    ensemble_data4.NumBeams = 1
    ensemble_data4.NumBins = 10
    ensemble_data4.Year = 2019
    ensemble_data4.Month = 2
    ensemble_data4.Day = 19
    ensemble_data4.Hour = 10
    ensemble_data4.Minute = 25
    ensemble_data4.Second = 39
    ensemble_data4.HSec = 10

    ensemble_data5 = EnsembleData.EnsembleData(19, 1)
    ensemble_data5.EnsembleNumber = 5
    ensemble_data5.NumBeams = 4
    ensemble_data5.NumBins = 10
    ensemble_data5.Year = 2019
    ensemble_data5.Month = 2
    ensemble_data5.Day = 19
    ensemble_data5.Hour = 10
    ensemble_data5.Minute = 26
    ensemble_data5.Second = 39
    ensemble_data5.HSec = 10

    ensemble_data6 = EnsembleData.EnsembleData(19, 1)
    ensemble_data6.EnsembleNumber = 6
    ensemble_data6.NumBeams = 1
    ensemble_data6.NumBins = 10
    ensemble_data6.Year = 2019
    ensemble_data6.Month = 2
    ensemble_data6.Day = 19
    ensemble_data6.Hour = 10
    ensemble_data6.Minute = 27
    ensemble_data6.Second = 39
    ensemble_data6.HSec = 10

    ensemble_data7 = EnsembleData.EnsembleData(19, 1)
    ensemble_data7.EnsembleNumber = 7
    ensemble_data7.NumBeams = 4
    ensemble_data7.NumBins = 10
    ensemble_data7.Year = 2019
    ensemble_data7.Month = 2
    ensemble_data7.Day = 19
    ensemble_data7.Hour = 10
    ensemble_data7.Minute = 28
    ensemble_data7.Second = 39
    ensemble_data7.HSec = 10

    range_track1 = RangeTracking.RangeTracking()
    range_track1.NumBeams = 4
    range_track1.Range.append(38.0)
    range_track1.Range.append(39.0)
    range_track1.Range.append(40.0)
    range_track1.Range.append(41.0)

    range_track2 = RangeTracking.RangeTracking()
    range_track2.NumBeams = 1
    range_track2.Range.append(37.0)

    range_track3 = RangeTracking.RangeTracking()
    range_track3.NumBeams = 4
    range_track3.Range.append(20.5)
    range_track3.Range.append(21.6)
    range_track3.Range.append(22.7)
    range_track3.Range.append(23.8)

    range_track4 = RangeTracking.RangeTracking()
    range_track4.NumBeams = 1
    range_track4.Range.append(25.3)

    range_track5 = RangeTracking.RangeTracking()
    range_track5.NumBeams = 4
    range_track5.Range.append(33.1)
    range_track5.Range.append(34.2)
    range_track5.Range.append(35.3)
    range_track5.Range.append(36.4)

    range_track6 = RangeTracking.RangeTracking()
    range_track6.NumBeams = 1
    range_track6.Range.append(34.9)

    range_track7 = RangeTracking.RangeTracking()
    range_track7.NumBeams = 4
    range_track7.Range.append(32.1)
    range_track7.Range.append(35.2)
    range_track7.Range.append(33.3)
    range_track7.Range.append(36.4)

    num_bins = 10
    num_beams = 4
    earth_vel1 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel1.Velocities[0][0] = -1.3
    earth_vel1.Velocities[0][1] = 0.65
    earth_vel1.Velocities[0][2] = -0.02
    earth_vel1.Velocities[0][3] = 0.1
    earth_vel1.Velocities[1][0] = -1.6
    earth_vel1.Velocities[1][1] = 0.56
    earth_vel1.Velocities[1][2] = -0.01
    earth_vel1.Velocities[1][3] = 0.08
    earth_vel1.Velocities[2][0] = -1.28
    earth_vel1.Velocities[2][1] = 0.36
    earth_vel1.Velocities[2][2] = -0.12
    earth_vel1.Velocities[2][3] = 0.13
    earth_vel1.Velocities[3][0] = -1.45
    earth_vel1.Velocities[3][1] = 0.25
    earth_vel1.Velocities[3][2] = -0.1
    earth_vel1.Velocities[3][3] = 0.11
    earth_vel1.Velocities[4][0] = -1.67
    earth_vel1.Velocities[4][1] = 0.67
    earth_vel1.Velocities[4][2] = -0.027
    earth_vel1.Velocities[4][3] = 0.17
    earth_vel1.Velocities[5][0] = -2.67
    earth_vel1.Velocities[5][1] = 2.67
    earth_vel1.Velocities[5][2] = -2.027
    earth_vel1.Velocities[5][3] = 2.17

    earth_vel3 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel3.Velocities[0][0] = -11.3
    earth_vel3.Velocities[0][1] = 1.65
    earth_vel3.Velocities[0][2] = -1.02
    earth_vel3.Velocities[0][3] = 1.1
    earth_vel3.Velocities[1][0] = -11.6
    earth_vel3.Velocities[1][1] = 1.56
    earth_vel3.Velocities[1][2] = -1.01
    earth_vel3.Velocities[1][3] = 1.08
    earth_vel3.Velocities[2][0] = -11.28
    earth_vel3.Velocities[2][1] = 1.36
    earth_vel3.Velocities[2][2] = -1.12
    earth_vel3.Velocities[2][3] = 1.13
    earth_vel3.Velocities[3][0] = -11.45
    earth_vel3.Velocities[3][1] = 1.25
    earth_vel3.Velocities[3][2] = -1.1
    earth_vel3.Velocities[3][3] = 1.11
    earth_vel3.Velocities[4][0] = -11.67
    earth_vel3.Velocities[4][1] = 1.67
    earth_vel3.Velocities[4][2] = -1.027
    earth_vel3.Velocities[4][3] = 1.17
    earth_vel3.Velocities[5][0] = -12.67
    earth_vel3.Velocities[5][1] = 2.67
    earth_vel3.Velocities[5][2] = -2.027
    earth_vel3.Velocities[5][3] = 2.17

    earth_vel5 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel5.Velocities[0][0] = -12.3
    earth_vel5.Velocities[0][1] = 2.65
    earth_vel5.Velocities[0][2] = -2.02
    earth_vel5.Velocities[0][3] = 2.1
    earth_vel5.Velocities[1][0] = -12.6
    earth_vel5.Velocities[1][1] = 2.56
    earth_vel5.Velocities[1][2] = -2.01
    earth_vel5.Velocities[1][3] = 2.08
    earth_vel5.Velocities[2][0] = -12.28
    earth_vel5.Velocities[2][1] = 2.36
    earth_vel5.Velocities[2][2] = -2.12
    earth_vel5.Velocities[2][3] = 2.13
    earth_vel5.Velocities[3][0] = -12.45
    earth_vel5.Velocities[3][1] = 2.25
    earth_vel5.Velocities[3][2] = -2.1
    earth_vel5.Velocities[3][3] = 2.11
    earth_vel5.Velocities[4][0] = -12.67
    earth_vel5.Velocities[4][1] = 2.67
    earth_vel5.Velocities[4][2] = -2.027
    earth_vel5.Velocities[4][3] = 2.17
    earth_vel5.Velocities[5][0] = -13.67
    earth_vel5.Velocities[5][1] = 3.67
    earth_vel5.Velocities[5][2] = -3.027
    earth_vel5.Velocities[5][3] = 3.17

    # Beam Velocity
    beam_vel1 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel1.Velocities[0][0] = -1.3
    beam_vel1.Velocities[0][1] = 0.65
    beam_vel1.Velocities[0][2] = -0.02
    beam_vel1.Velocities[0][3] = 0.1
    beam_vel1.Velocities[1][0] = -1.6
    beam_vel1.Velocities[1][1] = 0.56
    beam_vel1.Velocities[1][2] = -0.01
    beam_vel1.Velocities[1][3] = 0.08
    beam_vel1.Velocities[2][0] = -1.28
    beam_vel1.Velocities[2][1] = 0.36
    beam_vel1.Velocities[2][2] = -0.12
    beam_vel1.Velocities[2][3] = 0.13
    beam_vel1.Velocities[3][0] = -1.45
    beam_vel1.Velocities[3][1] = 0.25
    beam_vel1.Velocities[3][2] = -0.1
    beam_vel1.Velocities[3][3] = 0.11
    beam_vel1.Velocities[4][0] = -1.67
    beam_vel1.Velocities[4][1] = 0.67
    beam_vel1.Velocities[4][2] = -0.027
    beam_vel1.Velocities[4][3] = 0.17
    beam_vel1.Velocities[5][0] = -2.67
    beam_vel1.Velocities[5][1] = 2.67
    beam_vel1.Velocities[5][2] = -2.027
    beam_vel1.Velocities[5][3] = 2.17

    beam_vel2 = BeamVelocity.BeamVelocity(num_bins, 1)
    beam_vel2.Velocities[0][0] = -3.3
    beam_vel2.Velocities[1][0] = -3.6
    beam_vel2.Velocities[2][0] = -3.28
    beam_vel2.Velocities[3][0] = -3.45
    beam_vel2.Velocities[4][0] = -3.67
    beam_vel2.Velocities[5][0] = -3.67

    beam_vel3 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel3.Velocities[0][0] = -11.3
    beam_vel3.Velocities[0][1] = 1.65
    beam_vel3.Velocities[0][2] = -1.02
    beam_vel3.Velocities[0][3] = 1.1
    beam_vel3.Velocities[1][0] = -11.6
    beam_vel3.Velocities[1][1] = 1.56
    beam_vel3.Velocities[1][2] = -1.01
    beam_vel3.Velocities[1][3] = 1.08
    beam_vel3.Velocities[2][0] = -11.28
    beam_vel3.Velocities[2][1] = 1.36
    beam_vel3.Velocities[2][2] = -1.12
    beam_vel3.Velocities[2][3] = 1.13
    beam_vel3.Velocities[3][0] = -11.45
    beam_vel3.Velocities[3][1] = 1.25
    beam_vel3.Velocities[3][2] = -1.1
    beam_vel3.Velocities[3][3] = 1.11
    beam_vel3.Velocities[4][0] = -11.67
    beam_vel3.Velocities[4][1] = 1.67
    beam_vel3.Velocities[4][2] = -1.027
    beam_vel3.Velocities[4][3] = 1.17
    beam_vel3.Velocities[5][0] = -12.67
    beam_vel3.Velocities[5][1] = 2.67
    beam_vel3.Velocities[5][2] = -2.027
    beam_vel3.Velocities[5][3] = 2.17

    beam_vel4 = BeamVelocity.BeamVelocity(num_bins, 1)
    beam_vel4.Velocities[0][0] = -4.3
    beam_vel4.Velocities[1][0] = -4.6
    beam_vel4.Velocities[2][0] = -4.28
    beam_vel4.Velocities[3][0] = -4.45
    beam_vel4.Velocities[4][0] = -4.67
    beam_vel4.Velocities[5][0] = -4.67

    beam_vel5 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel5.Velocities[0][0] = -12.3
    beam_vel5.Velocities[0][1] = 2.65
    beam_vel5.Velocities[0][2] = -2.02
    beam_vel5.Velocities[0][3] = 2.1
    beam_vel5.Velocities[1][0] = -12.6
    beam_vel5.Velocities[1][1] = 2.56
    beam_vel5.Velocities[1][2] = -2.01
    beam_vel5.Velocities[1][3] = 2.08
    beam_vel5.Velocities[2][0] = -12.28
    beam_vel5.Velocities[2][1] = 2.36
    beam_vel5.Velocities[2][2] = -2.12
    beam_vel5.Velocities[2][3] = 2.13
    beam_vel5.Velocities[3][0] = -12.45
    beam_vel5.Velocities[3][1] = 2.25
    beam_vel5.Velocities[3][2] = -2.1
    beam_vel5.Velocities[3][3] = 2.11
    beam_vel5.Velocities[4][0] = -12.67
    beam_vel5.Velocities[4][1] = 2.67
    beam_vel5.Velocities[4][2] = -2.027
    beam_vel5.Velocities[4][3] = 2.17
    beam_vel5.Velocities[5][0] = -13.67
    beam_vel5.Velocities[5][1] = 3.67
    beam_vel5.Velocities[5][2] = -3.027
    beam_vel5.Velocities[5][3] = 3.17

    beam_vel6 = BeamVelocity.BeamVelocity(num_bins, 1)
    beam_vel6.Velocities[0][0] = -5.3
    beam_vel6.Velocities[1][0] = -5.6
    beam_vel6.Velocities[2][0] = -5.28
    beam_vel6.Velocities[3][0] = -5.45
    beam_vel6.Velocities[4][0] = -5.67
    beam_vel6.Velocities[5][0] = -5.67

    ensemble1 = Ensemble.Ensemble()
    ensemble1.AddAncillaryData(ancillary_data1)
    ensemble1.AddEnsembleData(ensemble_data1)
    ensemble1.AddRangeTracking(range_track1)
    ensemble1.AddEarthVelocity(earth_vel1)
    ensemble1.AddBeamVelocity(beam_vel1)

    ensemble2 = Ensemble.Ensemble()
    ensemble2.AddAncillaryData(ancillary_data2)
    ensemble2.AddEnsembleData(ensemble_data2)
    ensemble2.AddRangeTracking(range_track2)
    ensemble2.AddBeamVelocity(beam_vel2)

    ensemble3 = Ensemble.Ensemble()
    ensemble3.AddAncillaryData(ancillary_data3)
    ensemble3.AddEnsembleData(ensemble_data3)
    ensemble3.AddRangeTracking(range_track3)
    ensemble3.AddEarthVelocity(earth_vel3)
    ensemble3.AddBeamVelocity(beam_vel3)

    ensemble4 = Ensemble.Ensemble()
    ensemble4.AddAncillaryData(ancillary_data1)
    ensemble4.AddEnsembleData(ensemble_data4)
    ensemble4.AddRangeTracking(range_track4)
    ensemble4.AddBeamVelocity(beam_vel4)

    ensemble5 = Ensemble.Ensemble()
    ensemble5.AddAncillaryData(ancillary_data2)
    ensemble5.AddEnsembleData(ensemble_data5)
    ensemble5.AddRangeTracking(range_track5)
    ensemble5.AddEarthVelocity(earth_vel5)
    ensemble5.AddBeamVelocity(beam_vel5)

    ensemble6 = Ensemble.Ensemble()
    ensemble6.AddAncillaryData(ancillary_data3)
    ensemble6.AddEnsembleData(ensemble_data6)
    ensemble6.AddRangeTracking(range_track6)
    ensemble6.AddBeamVelocity(beam_vel6)

    ensemble7 = Ensemble.Ensemble()
    ensemble7.AddAncillaryData(ancillary_data3)
    ensemble7.AddEnsembleData(ensemble_data7)
    ensemble7.AddRangeTracking(range_track7)

    codec.add(ensemble1)
    codec.add(ensemble2)
    codec.add(ensemble3)
    codec.add(ensemble4)
    codec.add(ensemble5)
    codec.add(ensemble6)
    codec.add(ensemble7)


def waves_rcv_with_VertBeam(self, file_name):

    assert True == os.path.isfile(file_name)

    # Read in the MATLAB file
    mat_data = sio.loadmat(file_name)

    # Lat and Lon
    assert 32.0 == mat_data['lat'][0][0]
    assert 118.0 == mat_data['lon'][0][0]

    # Wave Cell Depths
    assert 6.0 == mat_data['whv'][0][0]
    assert 7.0 == mat_data['whv'][0][1]
    assert 8.0 == mat_data['whv'][0][2]

    # First Ensemble Time
    assert 737475.4323958333 == mat_data['wft'][0][0]

    # Time between Ensembles
    assert 60.0 == mat_data['wdt'][0][0]

    # Pressure Sensor Height
    assert 30 == mat_data['whp'][0][0]

    # Heading
    assert 22.0 == mat_data['whg'][0][0]
    assert 24.0 == mat_data['whg'][1][0]
    assert 23.0 == mat_data['whg'][2][0]

    # Pitch
    assert 10.0 == mat_data['wph'][0][0]
    assert 14.0 == mat_data['wph'][1][0]
    assert 13.0 == mat_data['wph'][2][0]

    # Roll
    assert 1.0 == mat_data['wrl'][0][0]
    assert 4.0 == mat_data['wrl'][1][0]
    assert 3.0 == mat_data['wrl'][2][0]

    # Pressure
    assert 30.2 == pytest.approx(mat_data['wps'][0][0], 0.1)
    assert 33.2 == pytest.approx(mat_data['wps'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wps'][2][0], 0.1)

    # Water Temp
    assert 23.5 == pytest.approx(mat_data['wts'][0][0], 0.1)
    assert 26.5 == pytest.approx(mat_data['wts'][1][0], 0.1)
    assert 27.5 == pytest.approx(mat_data['wts'][2][0], 0.1)

    # Average Range and Pressure
    assert 37.64 == pytest.approx(mat_data['wah'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['wah'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['wah'][2][0], 0.1)

    # Range Tracking
    assert 38.0 == pytest.approx(mat_data['wr0'][0][0], 0.1)
    assert 20.5 == pytest.approx(mat_data['wr0'][1][0], 0.1)
    assert 33.1 == pytest.approx(mat_data['wr0'][2][0], 0.1)

    assert 39.0 == pytest.approx(mat_data['wr1'][0][0], 0.1)
    assert 21.6 == pytest.approx(mat_data['wr1'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wr1'][2][0], 0.1)

    assert 40.0 == pytest.approx(mat_data['wr2'][0][0], 0.1)
    assert 22.7 == pytest.approx(mat_data['wr2'][1][0], 0.1)
    assert 35.3 == pytest.approx(mat_data['wr2'][2][0], 0.1)

    assert 41.0 == pytest.approx(mat_data['wr3'][0][0], 0.1)
    assert 23.8 == pytest.approx(mat_data['wr3'][1][0], 0.1)
    assert 36.4 == pytest.approx(mat_data['wr3'][2][0], 0.1)

    # Selected Wave Height Source
    # Average height
    assert 37.64 == pytest.approx(mat_data['whs'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['whs'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['whs'][2][0], 0.1)

    # Vertical Beam Pressure
    assert 33.2 == pytest.approx(mat_data['wzp'][0][0], 0.1)
    assert 30.2 == pytest.approx(mat_data['wzp'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wzp'][2][0], 0.1)

    # Vertical Beam Range Tracking
    assert 37.0 == pytest.approx(mat_data['wzr'][0][0], 0.1)
    assert 25.3 == pytest.approx(mat_data['wzr'][1][0], 0.1)
    assert 34.9 == pytest.approx(mat_data['wzr'][2][0], 0.1)

    # Earth East Velocity
    assert -1.45 == pytest.approx(mat_data['wus'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wus'][1][0], 0.1)
    assert -2.67 == pytest.approx(mat_data['wus'][2][0], 0.1)
    assert -11.45 == pytest.approx(mat_data['wus'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wus'][1][1], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][2][1], 0.1)
    assert -12.45 == pytest.approx(mat_data['wus'][0][2], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][1][2], 0.1)
    assert -13.67 == pytest.approx(mat_data['wus'][2][2], 0.1)

    # Earth North Velocity
    assert 0.25 == pytest.approx(mat_data['wvs'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wvs'][1][0], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][2][0], 0.1)
    assert 1.25 == pytest.approx(mat_data['wvs'][0][1], 0.1)
    assert 1.67 == pytest.approx(mat_data['wvs'][1][1], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][2][1], 0.1)
    assert 2.25 == pytest.approx(mat_data['wvs'][0][2], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][1][2], 0.1)
    assert 3.67 == pytest.approx(mat_data['wvs'][2][2], 0.1)

    # Earth Vertical Velocity
    assert -0.1 == pytest.approx(mat_data['wzs'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wzs'][1][0], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][2][0], 0.1)
    assert -1.1 == pytest.approx(mat_data['wzs'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wzs'][1][1], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][2][1], 0.1)
    assert -2.1 == pytest.approx(mat_data['wzs'][0][2], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][1][2], 0.1)
    assert -3.027 == pytest.approx(mat_data['wzs'][2][2], 0.1)

    # Beam 0 Velocity
    assert -1.45 == pytest.approx(mat_data['wb0'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wb0'][1][0], 0.1)
    assert -2.67 == pytest.approx(mat_data['wb0'][2][0], 0.1)
    assert -11.45 == pytest.approx(mat_data['wb0'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wb0'][1][1], 0.1)
    assert -12.67 == pytest.approx(mat_data['wb0'][2][1], 0.1)
    assert -12.45 == pytest.approx(mat_data['wb0'][0][2], 0.1)
    assert -12.67 == pytest.approx(mat_data['wb0'][1][2], 0.1)
    assert -13.67 == pytest.approx(mat_data['wb0'][2][2], 0.1)

    # Beam 1 Velocity
    assert 0.25 == pytest.approx(mat_data['wb1'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wb1'][1][0], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][2][0], 0.1)
    assert 1.25 == pytest.approx(mat_data['wb1'][0][1], 0.1)
    assert 1.67 == pytest.approx(mat_data['wb1'][1][1], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][2][1], 0.1)
    assert 2.25 == pytest.approx(mat_data['wb1'][0][2], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][1][2], 0.1)
    assert 3.67 == pytest.approx(mat_data['wb1'][2][2], 0.1)

    # Beam 3 Velocity
    assert -0.1 == pytest.approx(mat_data['wb2'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wb2'][1][0], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][2][0], 0.1)
    assert -1.1 == pytest.approx(mat_data['wb2'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wb2'][1][1], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][2][1], 0.1)
    assert -2.1 == pytest.approx(mat_data['wb2'][0][2], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][1][2], 0.1)
    assert -3.027 == pytest.approx(mat_data['wb2'][2][2], 0.1)

    # Beam 4 Velocity
    assert 0.11 == pytest.approx(mat_data['wb3'][0][0], 0.1)
    assert 0.17 == pytest.approx(mat_data['wb3'][1][0], 0.1)
    assert 2.17 == pytest.approx(mat_data['wb3'][2][0], 0.1)
    assert 1.11 == pytest.approx(mat_data['wb3'][0][1], 0.1)
    assert 1.17 == pytest.approx(mat_data['wb3'][1][1], 0.1)
    assert 2.17 == pytest.approx(mat_data['wb3'][2][1], 0.1)
    assert 2.11 == pytest.approx(mat_data['wb3'][0][2], 0.1)
    assert 2.17 == pytest.approx(mat_data['wb3'][1][2], 0.1)
    assert 3.17 == pytest.approx(mat_data['wb3'][2][2], 0.1)

    # Vertical Beam Velocity
    assert -3.45 == pytest.approx(mat_data['wz0'][0][0], 0.1)
    assert -3.67 == pytest.approx(mat_data['wz0'][1][0], 0.1)
    assert -3.67 == pytest.approx(mat_data['wz0'][2][0], 0.1)
    assert -4.45 == pytest.approx(mat_data['wz0'][0][1], 0.1)
    assert -4.67 == pytest.approx(mat_data['wz0'][1][1], 0.1)
    assert -4.67 == pytest.approx(mat_data['wz0'][2][1], 0.1)
    assert -5.45 == pytest.approx(mat_data['wz0'][0][2], 0.1)
    assert -5.67 == pytest.approx(mat_data['wz0'][1][2], 0.1)
    assert -5.67 == pytest.approx(mat_data['wz0'][2][2], 0.1)


def test_add_ens_Corr():
    curr_dir = os.path.dirname(os.path.realpath(__file__))
    num_ens_in_burst = 3

    codec = wfc.WaveForceCodec(num_ens_in_burst, curr_dir, 32.0, 118.0, 3, 4, 5, 30, 4, 0.25, 0.0, False)
    codec.process_data_event += waves_rcv_ens_Corr

    # Create Ensembles
    ancillary_data1 = AncillaryData.AncillaryData(17, 1)
    ancillary_data1.Heading = 22.0
    ancillary_data1.Pitch = 10.0
    ancillary_data1.Roll = 1.0
    ancillary_data1.TransducerDepth = 30.2
    ancillary_data1.WaterTemp = 23.5
    ancillary_data1.BinSize = 1
    ancillary_data1.FirstBinRange = 3

    ancillary_data2 = AncillaryData.AncillaryData(17, 1)
    ancillary_data2.Heading = 23.0
    ancillary_data2.Pitch = 13.0
    ancillary_data2.Roll = 3.0
    ancillary_data2.TransducerDepth = 33.2
    ancillary_data2.WaterTemp = 26.5
    ancillary_data2.BinSize = 1
    ancillary_data2.FirstBinRange = 3

    ancillary_data3 = AncillaryData.AncillaryData(17, 1)
    ancillary_data3.Heading = 24.0
    ancillary_data3.Pitch = 14.0
    ancillary_data3.Roll = 4.0
    ancillary_data3.TransducerDepth = 34.2
    ancillary_data3.WaterTemp = 27.5
    ancillary_data3.BinSize = 1
    ancillary_data3.FirstBinRange = 3

    ensemble_data1 = EnsembleData.EnsembleData(19, 1)
    ensemble_data1.EnsembleNumber = 1
    ensemble_data1.NumBeams = 4
    ensemble_data1.NumBins = 10
    ensemble_data1.Year = 2019
    ensemble_data1.Month = 2
    ensemble_data1.Day = 19
    ensemble_data1.Hour = 10
    ensemble_data1.Minute = 22
    ensemble_data1.Second = 39
    ensemble_data1.HSec = 10

    ensemble_data2 = EnsembleData.EnsembleData(19, 1)
    ensemble_data2.EnsembleNumber = 2
    ensemble_data2.NumBeams = 1
    ensemble_data2.NumBins = 10
    ensemble_data2.Year = 2019
    ensemble_data2.Month = 2
    ensemble_data2.Day = 19
    ensemble_data2.Hour = 10
    ensemble_data2.Minute = 23
    ensemble_data2.Second = 39
    ensemble_data2.HSec = 10

    ensemble_data3 = EnsembleData.EnsembleData(19, 1)
    ensemble_data3.EnsembleNumber = 3
    ensemble_data3.NumBeams = 4
    ensemble_data3.NumBins = 10
    ensemble_data3.Year = 2019
    ensemble_data3.Month = 2
    ensemble_data3.Day = 19
    ensemble_data3.Hour = 10
    ensemble_data3.Minute = 24
    ensemble_data3.Second = 39
    ensemble_data3.HSec = 10

    ensemble_data4 = EnsembleData.EnsembleData(19, 1)
    ensemble_data4.EnsembleNumber = 4
    ensemble_data4.NumBeams = 1
    ensemble_data4.NumBins = 10
    ensemble_data4.Year = 2019
    ensemble_data4.Month = 2
    ensemble_data4.Day = 19
    ensemble_data4.Hour = 10
    ensemble_data4.Minute = 25
    ensemble_data4.Second = 39
    ensemble_data4.HSec = 10

    ensemble_data5 = EnsembleData.EnsembleData(19, 1)
    ensemble_data5.EnsembleNumber = 5
    ensemble_data5.NumBeams = 4
    ensemble_data5.NumBins = 10
    ensemble_data5.Year = 2019
    ensemble_data5.Month = 2
    ensemble_data5.Day = 19
    ensemble_data5.Hour = 10
    ensemble_data5.Minute = 26
    ensemble_data5.Second = 39
    ensemble_data5.HSec = 10

    ensemble_data6 = EnsembleData.EnsembleData(19, 1)
    ensemble_data6.EnsembleNumber = 6
    ensemble_data6.NumBeams = 1
    ensemble_data6.NumBins = 10
    ensemble_data6.Year = 2019
    ensemble_data6.Month = 2
    ensemble_data6.Day = 19
    ensemble_data6.Hour = 10
    ensemble_data6.Minute = 27
    ensemble_data6.Second = 39
    ensemble_data6.HSec = 10

    ensemble_data7 = EnsembleData.EnsembleData(19, 1)
    ensemble_data7.EnsembleNumber = 7
    ensemble_data7.NumBeams = 4
    ensemble_data7.NumBins = 10
    ensemble_data7.Year = 2019
    ensemble_data7.Month = 2
    ensemble_data7.Day = 19
    ensemble_data7.Hour = 10
    ensemble_data7.Minute = 28
    ensemble_data7.Second = 39
    ensemble_data7.HSec = 10

    range_track1 = RangeTracking.RangeTracking()
    range_track1.NumBeams = 4
    range_track1.Range.append(38.0)
    range_track1.Range.append(39.0)
    range_track1.Range.append(40.0)
    range_track1.Range.append(41.0)

    range_track2 = RangeTracking.RangeTracking()
    range_track2.NumBeams = 1
    range_track2.Range.append(37.0)

    range_track3 = RangeTracking.RangeTracking()
    range_track3.NumBeams = 4
    range_track3.Range.append(20.5)
    range_track3.Range.append(21.6)
    range_track3.Range.append(22.7)
    range_track3.Range.append(23.8)

    range_track4 = RangeTracking.RangeTracking()
    range_track4.NumBeams = 1
    range_track4.Range.append(25.3)

    range_track5 = RangeTracking.RangeTracking()
    range_track5.NumBeams = 4
    range_track5.Range.append(33.1)
    range_track5.Range.append(34.2)
    range_track5.Range.append(35.3)
    range_track5.Range.append(36.4)

    range_track6 = RangeTracking.RangeTracking()
    range_track6.NumBeams = 1
    range_track6.Range.append(34.9)

    range_track7 = RangeTracking.RangeTracking()
    range_track7.NumBeams = 4
    range_track7.Range.append(32.1)
    range_track7.Range.append(35.2)
    range_track7.Range.append(33.3)
    range_track7.Range.append(36.4)

    num_bins = 10
    num_beams = 4
    earth_vel1 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel1.Velocities[0][0] = -1.3
    earth_vel1.Velocities[0][1] = 0.65
    earth_vel1.Velocities[0][2] = -0.02
    earth_vel1.Velocities[0][3] = 0.1
    earth_vel1.Velocities[1][0] = -1.6
    earth_vel1.Velocities[1][1] = 0.56
    earth_vel1.Velocities[1][2] = -0.01
    earth_vel1.Velocities[1][3] = 0.08
    earth_vel1.Velocities[2][0] = -1.28
    earth_vel1.Velocities[2][1] = 0.36
    earth_vel1.Velocities[2][2] = -0.12
    earth_vel1.Velocities[2][3] = 0.13
    earth_vel1.Velocities[3][0] = -1.45
    earth_vel1.Velocities[3][1] = 0.25
    earth_vel1.Velocities[3][2] = -0.1
    earth_vel1.Velocities[3][3] = 0.11
    earth_vel1.Velocities[4][0] = -1.67
    earth_vel1.Velocities[4][1] = 0.67
    earth_vel1.Velocities[4][2] = -0.027
    earth_vel1.Velocities[4][3] = 0.17
    earth_vel1.Velocities[5][0] = -2.67
    earth_vel1.Velocities[5][1] = 2.67
    earth_vel1.Velocities[5][2] = -2.027
    earth_vel1.Velocities[5][3] = 2.17

    earth_vel3 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel3.Velocities[0][0] = -11.3
    earth_vel3.Velocities[0][1] = 1.65
    earth_vel3.Velocities[0][2] = -1.02
    earth_vel3.Velocities[0][3] = 1.1
    earth_vel3.Velocities[1][0] = -11.6
    earth_vel3.Velocities[1][1] = 1.56
    earth_vel3.Velocities[1][2] = -1.01
    earth_vel3.Velocities[1][3] = 1.08
    earth_vel3.Velocities[2][0] = -11.28
    earth_vel3.Velocities[2][1] = 1.36
    earth_vel3.Velocities[2][2] = -1.12
    earth_vel3.Velocities[2][3] = 1.13
    earth_vel3.Velocities[3][0] = -11.45
    earth_vel3.Velocities[3][1] = 1.25
    earth_vel3.Velocities[3][2] = -1.1
    earth_vel3.Velocities[3][3] = 1.11
    earth_vel3.Velocities[4][0] = -11.67
    earth_vel3.Velocities[4][1] = 1.67
    earth_vel3.Velocities[4][2] = -1.027
    earth_vel3.Velocities[4][3] = 1.17
    earth_vel3.Velocities[5][0] = -12.67
    earth_vel3.Velocities[5][1] = 2.67
    earth_vel3.Velocities[5][2] = -2.027
    earth_vel3.Velocities[5][3] = 2.17

    earth_vel5 = EarthVelocity.EarthVelocity(num_bins, num_beams)
    earth_vel5.Velocities[0][0] = -12.3
    earth_vel5.Velocities[0][1] = 2.65
    earth_vel5.Velocities[0][2] = -2.02
    earth_vel5.Velocities[0][3] = 2.1
    earth_vel5.Velocities[1][0] = -12.6
    earth_vel5.Velocities[1][1] = 2.56
    earth_vel5.Velocities[1][2] = -2.01
    earth_vel5.Velocities[1][3] = 2.08
    earth_vel5.Velocities[2][0] = -12.28
    earth_vel5.Velocities[2][1] = 2.36
    earth_vel5.Velocities[2][2] = -2.12
    earth_vel5.Velocities[2][3] = 2.13
    earth_vel5.Velocities[3][0] = -12.45
    earth_vel5.Velocities[3][1] = 2.25
    earth_vel5.Velocities[3][2] = -2.1
    earth_vel5.Velocities[3][3] = 2.11
    earth_vel5.Velocities[4][0] = -12.67
    earth_vel5.Velocities[4][1] = 2.67
    earth_vel5.Velocities[4][2] = -2.027
    earth_vel5.Velocities[4][3] = 2.17
    earth_vel5.Velocities[5][0] = -13.67
    earth_vel5.Velocities[5][1] = 3.67
    earth_vel5.Velocities[5][2] = -3.027
    earth_vel5.Velocities[5][3] = 3.17

    # Beam Velocity
    beam_vel1 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel1.Velocities[0][0] = -1.3
    beam_vel1.Velocities[0][1] = 0.65
    beam_vel1.Velocities[0][2] = -0.02
    beam_vel1.Velocities[0][3] = 0.1
    beam_vel1.Velocities[1][0] = -1.6
    beam_vel1.Velocities[1][1] = 0.56
    beam_vel1.Velocities[1][2] = -0.01
    beam_vel1.Velocities[1][3] = 0.08
    beam_vel1.Velocities[2][0] = -1.28
    beam_vel1.Velocities[2][1] = 0.36
    beam_vel1.Velocities[2][2] = -0.12
    beam_vel1.Velocities[2][3] = 0.13
    beam_vel1.Velocities[3][0] = -1.45
    beam_vel1.Velocities[3][1] = 0.25
    beam_vel1.Velocities[3][2] = -0.1
    beam_vel1.Velocities[3][3] = 0.11
    beam_vel1.Velocities[4][0] = -1.67
    beam_vel1.Velocities[4][1] = 0.67
    beam_vel1.Velocities[4][2] = -0.027
    beam_vel1.Velocities[4][3] = 0.17
    beam_vel1.Velocities[5][0] = -2.67
    beam_vel1.Velocities[5][1] = 2.67
    beam_vel1.Velocities[5][2] = -2.027
    beam_vel1.Velocities[5][3] = 2.17

    beam_vel2 = BeamVelocity.BeamVelocity(num_bins, 1)
    beam_vel2.Velocities[0][0] = -3.3
    beam_vel2.Velocities[1][0] = -3.6
    beam_vel2.Velocities[2][0] = -3.28
    beam_vel2.Velocities[3][0] = -3.45
    beam_vel2.Velocities[4][0] = -3.67
    beam_vel2.Velocities[5][0] = -3.67

    beam_vel3 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel3.Velocities[0][0] = -11.3
    beam_vel3.Velocities[0][1] = 1.65
    beam_vel3.Velocities[0][2] = -1.02
    beam_vel3.Velocities[0][3] = 1.1
    beam_vel3.Velocities[1][0] = -11.6
    beam_vel3.Velocities[1][1] = 1.56
    beam_vel3.Velocities[1][2] = -1.01
    beam_vel3.Velocities[1][3] = 1.08
    beam_vel3.Velocities[2][0] = -11.28
    beam_vel3.Velocities[2][1] = 1.36
    beam_vel3.Velocities[2][2] = -1.12
    beam_vel3.Velocities[2][3] = 1.13
    beam_vel3.Velocities[3][0] = -11.45
    beam_vel3.Velocities[3][1] = 1.25
    beam_vel3.Velocities[3][2] = -1.1
    beam_vel3.Velocities[3][3] = 1.11
    beam_vel3.Velocities[4][0] = -11.67
    beam_vel3.Velocities[4][1] = 1.67
    beam_vel3.Velocities[4][2] = -1.027
    beam_vel3.Velocities[4][3] = 1.17
    beam_vel3.Velocities[5][0] = -12.67
    beam_vel3.Velocities[5][1] = 2.67
    beam_vel3.Velocities[5][2] = -2.027
    beam_vel3.Velocities[5][3] = 2.17

    beam_vel4 = BeamVelocity.BeamVelocity(num_bins, 1)
    beam_vel4.Velocities[0][0] = -4.3
    beam_vel4.Velocities[1][0] = -4.6
    beam_vel4.Velocities[2][0] = -4.28
    beam_vel4.Velocities[3][0] = -4.45
    beam_vel4.Velocities[4][0] = -4.67
    beam_vel4.Velocities[5][0] = -4.67

    beam_vel5 = BeamVelocity.BeamVelocity(num_bins, num_beams)
    beam_vel5.Velocities[0][0] = -12.3
    beam_vel5.Velocities[0][1] = 2.65
    beam_vel5.Velocities[0][2] = -2.02
    beam_vel5.Velocities[0][3] = 2.1
    beam_vel5.Velocities[1][0] = -12.6
    beam_vel5.Velocities[1][1] = 2.56
    beam_vel5.Velocities[1][2] = -2.01
    beam_vel5.Velocities[1][3] = 2.08
    beam_vel5.Velocities[2][0] = -12.28
    beam_vel5.Velocities[2][1] = 2.36
    beam_vel5.Velocities[2][2] = -2.12
    beam_vel5.Velocities[2][3] = 2.13
    beam_vel5.Velocities[3][0] = -12.45
    beam_vel5.Velocities[3][1] = 2.25
    beam_vel5.Velocities[3][2] = -2.1
    beam_vel5.Velocities[3][3] = 2.11
    beam_vel5.Velocities[4][0] = -12.67
    beam_vel5.Velocities[4][1] = 2.67
    beam_vel5.Velocities[4][2] = -2.027
    beam_vel5.Velocities[4][3] = 2.17
    beam_vel5.Velocities[5][0] = -13.67
    beam_vel5.Velocities[5][1] = 3.67
    beam_vel5.Velocities[5][2] = -3.027
    beam_vel5.Velocities[5][3] = 3.17

    beam_vel6 = BeamVelocity.BeamVelocity(num_bins, 1)
    beam_vel6.Velocities[0][0] = -5.3
    beam_vel6.Velocities[1][0] = -5.6
    beam_vel6.Velocities[2][0] = -5.28
    beam_vel6.Velocities[3][0] = -5.45
    beam_vel6.Velocities[4][0] = -5.67
    beam_vel6.Velocities[5][0] = -5.67

    corr1 = CorrelationData.Correlation(num_bins, num_beams)
    corr1.Correlation[3][0] = 0.55
    corr1.Correlation[3][1] = 0.55
    corr1.Correlation[3][2] = 0.10
    corr1.Correlation[3][3] = 0.55
    corr1.Correlation[4][0] = 0.55
    corr1.Correlation[4][1] = 0.55
    corr1.Correlation[4][2] = 0.55
    corr1.Correlation[4][3] = 0.55
    corr1.Correlation[5][0] = 0.11
    corr1.Correlation[5][1] = 0.55
    corr1.Correlation[5][2] = 0.55
    corr1.Correlation[5][3] = 0.22

    corr2 = CorrelationData.Correlation(num_bins, 1)
    corr2.Correlation[3][0] = 0.55
    corr2.Correlation[4][0] = 0.55
    corr2.Correlation[5][0] = 0.11

    ensemble1 = Ensemble.Ensemble()
    ensemble1.AddAncillaryData(ancillary_data1)
    ensemble1.AddEnsembleData(ensemble_data1)
    ensemble1.AddRangeTracking(range_track1)
    ensemble1.AddEarthVelocity(earth_vel1)
    ensemble1.AddBeamVelocity(beam_vel1)
    ensemble1.AddCorrelation(corr1)

    ensemble2 = Ensemble.Ensemble()
    ensemble2.AddAncillaryData(ancillary_data2)
    ensemble2.AddEnsembleData(ensemble_data2)
    ensemble2.AddRangeTracking(range_track2)
    ensemble2.AddBeamVelocity(beam_vel2)
    ensemble2.AddCorrelation(corr2)

    ensemble3 = Ensemble.Ensemble()
    ensemble3.AddAncillaryData(ancillary_data3)
    ensemble3.AddEnsembleData(ensemble_data3)
    ensemble3.AddRangeTracking(range_track3)
    ensemble3.AddEarthVelocity(earth_vel3)
    ensemble3.AddBeamVelocity(beam_vel3)

    ensemble4 = Ensemble.Ensemble()
    ensemble4.AddAncillaryData(ancillary_data1)
    ensemble4.AddEnsembleData(ensemble_data4)
    ensemble4.AddRangeTracking(range_track4)
    ensemble4.AddBeamVelocity(beam_vel4)

    ensemble5 = Ensemble.Ensemble()
    ensemble5.AddAncillaryData(ancillary_data2)
    ensemble5.AddEnsembleData(ensemble_data5)
    ensemble5.AddRangeTracking(range_track5)
    ensemble5.AddEarthVelocity(earth_vel5)
    ensemble5.AddBeamVelocity(beam_vel5)

    ensemble6 = Ensemble.Ensemble()
    ensemble6.AddAncillaryData(ancillary_data3)
    ensemble6.AddEnsembleData(ensemble_data6)
    ensemble6.AddRangeTracking(range_track6)
    ensemble6.AddBeamVelocity(beam_vel6)

    ensemble7 = Ensemble.Ensemble()
    ensemble7.AddAncillaryData(ancillary_data3)
    ensemble7.AddEnsembleData(ensemble_data7)
    ensemble7.AddRangeTracking(range_track7)

    codec.add(ensemble1)
    codec.add(ensemble2)
    codec.add(ensemble3)
    codec.add(ensemble4)
    codec.add(ensemble5)
    codec.add(ensemble6)
    codec.add(ensemble7)


def waves_rcv_ens_Corr(self, file_name):

    assert True == os.path.isfile(file_name)

    # Read in the MATLAB file
    mat_data = sio.loadmat(file_name)

    # Lat and Lon
    assert 32.0 == mat_data['lat'][0][0]
    assert 118.0 == mat_data['lon'][0][0]

    # Wave Cell Depths
    assert 6.0 == mat_data['whv'][0][0]
    assert 7.0 == mat_data['whv'][0][1]
    assert 8.0 == mat_data['whv'][0][2]

    # First Ensemble Time
    assert 737475.4323958333 == mat_data['wft'][0][0]

    # Time between Ensembles
    assert 60.0 == mat_data['wdt'][0][0]

    # Pressure Sensor Height
    assert 30 == mat_data['whp'][0][0]

    # Heading
    assert 22.0 == mat_data['whg'][0][0]
    assert 24.0 == mat_data['whg'][1][0]
    assert 23.0 == mat_data['whg'][2][0]

    # Pitch
    assert 10.0 == mat_data['wph'][0][0]
    assert 14.0 == mat_data['wph'][1][0]
    assert 13.0 == mat_data['wph'][2][0]

    # Roll
    assert 1.0 == mat_data['wrl'][0][0]
    assert 4.0 == mat_data['wrl'][1][0]
    assert 3.0 == mat_data['wrl'][2][0]

    # Pressure
    assert 30.2 == pytest.approx(mat_data['wps'][0][0], 0.1)
    assert 33.2 == pytest.approx(mat_data['wps'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wps'][2][0], 0.1)

    # Water Temp
    assert 23.5 == pytest.approx(mat_data['wts'][0][0], 0.1)
    assert 26.5 == pytest.approx(mat_data['wts'][1][0], 0.1)
    assert 27.5 == pytest.approx(mat_data['wts'][2][0], 0.1)

    # Average Range and Pressure
    assert 37.64 == pytest.approx(mat_data['wah'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['wah'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['wah'][2][0], 0.1)

    # Range Tracking
    assert 38.0 == pytest.approx(mat_data['wr0'][0][0], 0.1)
    assert 20.5 == pytest.approx(mat_data['wr0'][1][0], 0.1)
    assert 33.1 == pytest.approx(mat_data['wr0'][2][0], 0.1)

    assert 39.0 == pytest.approx(mat_data['wr1'][0][0], 0.1)
    assert 21.6 == pytest.approx(mat_data['wr1'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wr1'][2][0], 0.1)

    assert 40.0 == pytest.approx(mat_data['wr2'][0][0], 0.1)
    assert 22.7 == pytest.approx(mat_data['wr2'][1][0], 0.1)
    assert 35.3 == pytest.approx(mat_data['wr2'][2][0], 0.1)

    assert 41.0 == pytest.approx(mat_data['wr3'][0][0], 0.1)
    assert 23.8 == pytest.approx(mat_data['wr3'][1][0], 0.1)
    assert 36.4 == pytest.approx(mat_data['wr3'][2][0], 0.1)

    # Selected Wave Height Source
    # Average height
    assert 37.64 == pytest.approx(mat_data['whs'][0][0], 0.1)
    assert 24.36 == pytest.approx(mat_data['whs'][1][0], 0.1)
    assert 34.64 == pytest.approx(mat_data['whs'][2][0], 0.1)

    # Vertical Beam Pressure
    assert 33.2 == pytest.approx(mat_data['wzp'][0][0], 0.1)
    assert 30.2 == pytest.approx(mat_data['wzp'][1][0], 0.1)
    assert 34.2 == pytest.approx(mat_data['wzp'][2][0], 0.1)

    # Vertical Beam Range Tracking
    assert 37.0 == pytest.approx(mat_data['wzr'][0][0], 0.1)
    assert 25.3 == pytest.approx(mat_data['wzr'][1][0], 0.1)
    assert 34.9 == pytest.approx(mat_data['wzr'][2][0], 0.1)

    # Earth East Velocity
    assert -1.45 == pytest.approx(mat_data['wus'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wus'][1][0], 0.1)
    assert -2.67 == pytest.approx(mat_data['wus'][2][0], 0.1)
    assert -11.45 == pytest.approx(mat_data['wus'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wus'][1][1], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][2][1], 0.1)
    assert -12.45 == pytest.approx(mat_data['wus'][0][2], 0.1)
    assert -12.67 == pytest.approx(mat_data['wus'][1][2], 0.1)
    assert -13.67 == pytest.approx(mat_data['wus'][2][2], 0.1)

    # Earth North Velocity
    assert 0.25 == pytest.approx(mat_data['wvs'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wvs'][1][0], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][2][0], 0.1)
    assert 1.25 == pytest.approx(mat_data['wvs'][0][1], 0.1)
    assert 1.67 == pytest.approx(mat_data['wvs'][1][1], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][2][1], 0.1)
    assert 2.25 == pytest.approx(mat_data['wvs'][0][2], 0.1)
    assert 2.67 == pytest.approx(mat_data['wvs'][1][2], 0.1)
    assert 3.67 == pytest.approx(mat_data['wvs'][2][2], 0.1)

    # Earth Vertical Velocity
    assert -0.1 == pytest.approx(mat_data['wzs'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wzs'][1][0], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][2][0], 0.1)
    assert -1.1 == pytest.approx(mat_data['wzs'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wzs'][1][1], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][2][1], 0.1)
    assert -2.1 == pytest.approx(mat_data['wzs'][0][2], 0.1)
    assert -2.027 == pytest.approx(mat_data['wzs'][1][2], 0.1)
    assert -3.027 == pytest.approx(mat_data['wzs'][2][2], 0.1)

    # Beam 0 Velocity
    assert -1.45 == pytest.approx(mat_data['wb0'][0][0], 0.1)
    assert -1.67 == pytest.approx(mat_data['wb0'][1][0], 0.1)
    assert 88.88 == pytest.approx(mat_data['wb0'][2][0], 0.1)
    assert -11.45 == pytest.approx(mat_data['wb0'][0][1], 0.1)
    assert -11.67 == pytest.approx(mat_data['wb0'][1][1], 0.1)
    assert -12.67 == pytest.approx(mat_data['wb0'][2][1], 0.1)
    assert -12.45 == pytest.approx(mat_data['wb0'][0][2], 0.1)
    assert -12.67 == pytest.approx(mat_data['wb0'][1][2], 0.1)
    assert -13.67 == pytest.approx(mat_data['wb0'][2][2], 0.1)

    # Beam 1 Velocity
    assert 0.25 == pytest.approx(mat_data['wb1'][0][0], 0.1)
    assert 0.67 == pytest.approx(mat_data['wb1'][1][0], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][2][0], 0.1)
    assert 1.25 == pytest.approx(mat_data['wb1'][0][1], 0.1)
    assert 1.67 == pytest.approx(mat_data['wb1'][1][1], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][2][1], 0.1)
    assert 2.25 == pytest.approx(mat_data['wb1'][0][2], 0.1)
    assert 2.67 == pytest.approx(mat_data['wb1'][1][2], 0.1)
    assert 3.67 == pytest.approx(mat_data['wb1'][2][2], 0.1)

    # Beam 3 Velocity
    assert 88.88 == pytest.approx(mat_data['wb2'][0][0], 0.1)
    assert -0.029 == pytest.approx(mat_data['wb2'][1][0], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][2][0], 0.1)
    assert -1.1 == pytest.approx(mat_data['wb2'][0][1], 0.1)
    assert -1.027 == pytest.approx(mat_data['wb2'][1][1], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][2][1], 0.1)
    assert -2.1 == pytest.approx(mat_data['wb2'][0][2], 0.1)
    assert -2.027 == pytest.approx(mat_data['wb2'][1][2], 0.1)
    assert -3.027 == pytest.approx(mat_data['wb2'][2][2], 0.1)

    # Beam 4 Velocity
    assert 0.11 == pytest.approx(mat_data['wb3'][0][0], 0.1)
    assert 0.17 == pytest.approx(mat_data['wb3'][1][0], 0.1)
    assert 88.88 == pytest.approx(mat_data['wb3'][2][0], 0.1)
    assert 1.11 == pytest.approx(mat_data['wb3'][0][1], 0.1)
    assert 1.17 == pytest.approx(mat_data['wb3'][1][1], 0.1)
    assert 2.17 == pytest.approx(mat_data['wb3'][2][1], 0.1)
    assert 2.11 == pytest.approx(mat_data['wb3'][0][2], 0.1)
    assert 2.17 == pytest.approx(mat_data['wb3'][1][2], 0.1)
    assert 3.17 == pytest.approx(mat_data['wb3'][2][2], 0.1)

    # Vertical Beam Velocity
    assert -3.45 == pytest.approx(mat_data['wz0'][0][0], 0.1)
    assert -3.67 == pytest.approx(mat_data['wz0'][1][0], 0.1)
    assert 88.88 == pytest.approx(mat_data['wz0'][2][0], 0.1)
    assert -4.45 == pytest.approx(mat_data['wz0'][0][1], 0.1)
    assert -4.67 == pytest.approx(mat_data['wz0'][1][1], 0.1)
    assert -4.67 == pytest.approx(mat_data['wz0'][2][1], 0.1)
    assert -5.45 == pytest.approx(mat_data['wz0'][0][2], 0.1)
    assert -5.67 == pytest.approx(mat_data['wz0'][1][2], 0.1)
    assert -5.67 == pytest.approx(mat_data['wz0'][2][2], 0.1)