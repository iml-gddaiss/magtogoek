import pytest
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Ensemble.EnsembleData import EnsembleData
from rti_python.Ensemble.BeamVelocity import BeamVelocity
from rti_python.Ensemble.InstrumentVelocity import InstrumentVelocity
from rti_python.Ensemble.EarthVelocity import EarthVelocity
from rti_python.Post_Process.Average.AverageWaterColumn import AverageWaterColumn
from rti_python.Ensemble.AncillaryData import AncillaryData

def test_AWC_1ens():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 1.0
    instrVel.Velocities[0][1] = 2.0
    instrVel.Velocities[0][2] = 3.0
    instrVel.Velocities[0][3] = 4.0
    instrVel.Velocities[1][0] = 1.0
    instrVel.Velocities[1][1] = 2.0
    instrVel.Velocities[1][2] = 3.0
    instrVel.Velocities[1][3] = 4.0
    instrVel.Velocities[2][0] = 1.0
    instrVel.Velocities[2][1] = 2.0
    instrVel.Velocities[2][2] = 3.0
    instrVel.Velocities[2][3] = 4.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 1.0
    earthVel.Velocities[0][1] = 2.0
    earthVel.Velocities[0][2] = 3.0
    earthVel.Velocities[0][3] = 4.0
    earthVel.Velocities[1][0] = 1.0
    earthVel.Velocities[1][1] = 2.0
    earthVel.Velocities[1][2] = 3.0
    earthVel.Velocities[1][3] = 4.0
    earthVel.Velocities[2][0] = 1.0
    earthVel.Velocities[2][1] = 2.0
    earthVel.Velocities[2][2] = 3.0
    earthVel.Velocities[2][3] = 4.0
    ens.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    result = awc.average()

    # verify empty list
    assert result[0]
    assert result[1]
    assert result[2]

    # Beam Results
    assert result[4][0][0] == 1.0
    assert result[4][0][1] == 2.0
    assert result[4][0][2] == 3.0
    assert result[4][0][3] == 4.0

    # Instrument Results
    assert result[5][0][0] == 1.0
    assert result[5][0][1] == 2.0
    assert result[5][0][2] == 3.0
    assert result[5][0][3] == 4.0

    # Earth Results
    assert result[6][0][0] == 1.0
    assert result[6][0][1] == 2.0
    assert result[6][0][2] == 3.0
    assert result[6][0][3] == 4.0

def test_AWC_2ens():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 1.0
    instrVel.Velocities[0][1] = 2.0
    instrVel.Velocities[0][2] = 3.0
    instrVel.Velocities[0][3] = 4.0
    instrVel.Velocities[1][0] = 1.0
    instrVel.Velocities[1][1] = 2.0
    instrVel.Velocities[1][2] = 3.0
    instrVel.Velocities[1][3] = 4.0
    instrVel.Velocities[2][0] = 1.0
    instrVel.Velocities[2][1] = 2.0
    instrVel.Velocities[2][2] = 3.0
    instrVel.Velocities[2][3] = 4.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 1.0
    earthVel.Velocities[0][1] = 2.0
    earthVel.Velocities[0][2] = 3.0
    earthVel.Velocities[0][3] = 4.0
    earthVel.Velocities[1][0] = 1.0
    earthVel.Velocities[1][1] = 2.0
    earthVel.Velocities[1][2] = 3.0
    earthVel.Velocities[1][3] = 4.0
    earthVel.Velocities[2][0] = 1.0
    earthVel.Velocities[2][1] = 2.0
    earthVel.Velocities[2][2] = 3.0
    earthVel.Velocities[2][3] = 4.0
    ens.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    result = awc.average()

    # verify empty list
    assert result[0]
    assert result[1]
    assert result[2]

    # Beam Results
    assert result[4][0][0] == 1.0
    assert result[4][0][1] == 2.0
    assert result[4][0][2] == 3.0
    assert result[4][0][3] == 4.0

    # Instrument Results
    assert result[5][0][0] == 1.0
    assert result[5][0][1] == 2.0
    assert result[5][0][2] == 3.0
    assert result[5][0][3] == 4.0

    # Earth Results
    assert result[6][0][0] == 1.0
    assert result[6][0][1] == 2.0
    assert result[6][0][2] == 3.0
    assert result[6][0][3] == 4.0

def test_AWC_3ens():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 1.0
    instrVel.Velocities[0][1] = 2.0
    instrVel.Velocities[0][2] = 3.0
    instrVel.Velocities[0][3] = 4.0
    instrVel.Velocities[1][0] = 1.0
    instrVel.Velocities[1][1] = 2.0
    instrVel.Velocities[1][2] = 3.0
    instrVel.Velocities[1][3] = 4.0
    instrVel.Velocities[2][0] = 1.0
    instrVel.Velocities[2][1] = 2.0
    instrVel.Velocities[2][2] = 3.0
    instrVel.Velocities[2][3] = 4.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 1.0
    earthVel.Velocities[0][1] = 2.0
    earthVel.Velocities[0][2] = 3.0
    earthVel.Velocities[0][3] = 4.0
    earthVel.Velocities[1][0] = 1.0
    earthVel.Velocities[1][1] = 2.0
    earthVel.Velocities[1][2] = 3.0
    earthVel.Velocities[1][3] = 4.0
    earthVel.Velocities[2][0] = 1.0
    earthVel.Velocities[2][1] = 2.0
    earthVel.Velocities[2][2] = 3.0
    earthVel.Velocities[2][3] = 4.0
    ens.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    result = awc.average()

    # verify empty list
    assert result[0]
    assert result[1]
    assert result[2]

    # Beam Results
    assert result[4][0][0] == 1.0
    assert result[4][0][1] == 2.0
    assert result[4][0][2] == 3.0
    assert result[4][0][3] == 4.0

    # Instrument Results
    assert result[5][0][0] == 1.0
    assert result[5][0][1] == 2.0
    assert result[5][0][2] == 3.0
    assert result[5][0][3] == 4.0

    # Earth Results
    assert result[6][0][0] == 1.0
    assert result[6][0][1] == 2.0
    assert result[6][0][2] == 3.0
    assert result[6][0][3] == 4.0

def test_AWC_data():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 5.0
    instrVel.Velocities[0][1] = 6.0
    instrVel.Velocities[0][2] = 7.0
    instrVel.Velocities[0][3] = 8.0
    instrVel.Velocities[1][0] = 5.0
    instrVel.Velocities[1][1] = 6.0
    instrVel.Velocities[1][2] = 7.0
    instrVel.Velocities[1][3] = 8.0
    instrVel.Velocities[2][0] = 5.0
    instrVel.Velocities[2][1] = 6.0
    instrVel.Velocities[2][2] = 7.0
    instrVel.Velocities[2][3] = 8.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 9.0
    earthVel.Velocities[0][1] = 10.0
    earthVel.Velocities[0][2] = 11.0
    earthVel.Velocities[0][3] = 12.0
    earthVel.Velocities[1][0] = 9.0
    earthVel.Velocities[1][1] = 10.0
    earthVel.Velocities[1][2] = 11.0
    earthVel.Velocities[1][3] = 12.0
    earthVel.Velocities[2][0] = 9.0
    earthVel.Velocities[2][1] = 10.0
    earthVel.Velocities[2][2] = 11.0
    earthVel.Velocities[2][3] = 12.0
    ens.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    result = awc.average()

    # verify empty list
    assert result[0]
    assert result[1]
    assert result[2]

    # Beam Results
    assert result[4][0][0] == 1.0
    assert result[4][0][1] == 2.0
    assert result[4][0][2] == 3.0
    assert result[4][0][3] == 4.0

    # Instrument Results
    assert result[5][0][0] == 5.0
    assert result[5][0][1] == 6.0
    assert result[5][0][2] == 7.0
    assert result[5][0][3] == 8.0

    # Earth Results
    assert result[6][0][0] == 9.0
    assert result[6][0][1] == 10.0
    assert result[6][0][2] == 11.0
    assert result[6][0][3] == 12.0


def test_AWC_4ens():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 5.0
    instrVel.Velocities[0][1] = 6.0
    instrVel.Velocities[0][2] = 7.0
    instrVel.Velocities[0][3] = 8.0
    instrVel.Velocities[1][0] = 5.0
    instrVel.Velocities[1][1] = 6.0
    instrVel.Velocities[1][2] = 7.0
    instrVel.Velocities[1][3] = 8.0
    instrVel.Velocities[2][0] = 5.0
    instrVel.Velocities[2][1] = 6.0
    instrVel.Velocities[2][2] = 7.0
    instrVel.Velocities[2][3] = 8.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 9.0
    earthVel.Velocities[0][1] = 10.0
    earthVel.Velocities[0][2] = 11.0
    earthVel.Velocities[0][3] = 12.0
    earthVel.Velocities[1][0] = 9.0
    earthVel.Velocities[1][1] = 10.0
    earthVel.Velocities[1][2] = 11.0
    earthVel.Velocities[1][3] = 12.0
    earthVel.Velocities[2][0] = 9.0
    earthVel.Velocities[2][1] = 10.0
    earthVel.Velocities[2][2] = 11.0
    earthVel.Velocities[2][3] = 12.0
    ens.AddEarthVelocity(earthVel)

    ens1 = Ensemble()
    ens1DS = EnsembleData()
    ens1DS.SysFirmwareSubsystemCode = '3'
    ens1DS.SubsystemConfig = '1'
    ens1DS.NumBeams = 4
    ens1DS.NumBins = 3
    ens1.AddEnsembleData(ens1DS)

    beamVel1 = BeamVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    beamVel1.Velocities[0][0] = 1.0
    beamVel1.Velocities[0][1] = 2.0
    beamVel1.Velocities[0][2] = 3.0
    beamVel1.Velocities[0][3] = 4.0
    beamVel1.Velocities[1][0] = 1.0
    beamVel1.Velocities[1][1] = 2.0
    beamVel1.Velocities[1][2] = 3.0
    beamVel1.Velocities[1][3] = 4.0
    beamVel1.Velocities[2][0] = 1.0
    beamVel1.Velocities[2][1] = 2.0
    beamVel1.Velocities[2][2] = 3.0
    beamVel1.Velocities[2][3] = 4.0
    ens1.AddBeamVelocity(beamVel1)

    instrVel1 = InstrumentVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    instrVel1.Velocities[0][0] = 5.0
    instrVel1.Velocities[0][1] = 6.0
    instrVel1.Velocities[0][2] = 7.0
    instrVel1.Velocities[0][3] = 8.0
    instrVel1.Velocities[1][0] = 5.0
    instrVel1.Velocities[1][1] = 6.0
    instrVel1.Velocities[1][2] = 7.0
    instrVel1.Velocities[1][3] = 8.0
    instrVel1.Velocities[2][0] = 5.0
    instrVel1.Velocities[2][1] = 6.0
    instrVel1.Velocities[2][2] = 7.0
    instrVel1.Velocities[2][3] = 8.0
    ens1.AddInstrumentVelocity(instrVel1)

    earthVel1 = EarthVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    earthVel1.Velocities[0][0] = 9.0
    earthVel1.Velocities[0][1] = 10.0
    earthVel1.Velocities[0][2] = 11.0
    earthVel1.Velocities[0][3] = 12.0
    earthVel1.Velocities[1][0] = 9.0
    earthVel1.Velocities[1][1] = 10.0
    earthVel1.Velocities[1][2] = 11.0
    earthVel1.Velocities[1][3] = 12.0
    earthVel1.Velocities[2][0] = 9.0
    earthVel1.Velocities[2][1] = 10.0
    earthVel1.Velocities[2][2] = 11.0
    earthVel1.Velocities[2][3] = 12.0
    ens1.AddEarthVelocity(earthVel1)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens1)
    result = awc.average()

    # verify not empty list
    assert result[0]
    assert result[1]
    assert result[2]

    # Beam Results
    assert result[4][0][0] == 1.0
    assert result[4][0][1] == 2.0
    assert result[4][0][2] == 3.0
    assert result[4][0][3] == 4.0

    # Instrument Results
    assert result[5][0][0] == 5.0
    assert result[5][0][1] == 6.0
    assert result[5][0][2] == 7.0
    assert result[5][0][3] == 8.0

    # Earth Results
    assert result[6][0][0] == 9.0
    assert result[6][0][1] == 10.0
    assert result[6][0][2] == 11.0
    assert result[6][0][3] == 12.0


def test_AWC_4ens_new_data():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 5.0
    instrVel.Velocities[0][1] = 6.0
    instrVel.Velocities[0][2] = 7.0
    instrVel.Velocities[0][3] = 8.0
    instrVel.Velocities[1][0] = 5.0
    instrVel.Velocities[1][1] = 6.0
    instrVel.Velocities[1][2] = 7.0
    instrVel.Velocities[1][3] = 8.0
    instrVel.Velocities[2][0] = 5.0
    instrVel.Velocities[2][1] = 6.0
    instrVel.Velocities[2][2] = 7.0
    instrVel.Velocities[2][3] = 8.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 9.0
    earthVel.Velocities[0][1] = 10.0
    earthVel.Velocities[0][2] = 11.0
    earthVel.Velocities[0][3] = 12.0
    earthVel.Velocities[1][0] = 9.0
    earthVel.Velocities[1][1] = 10.0
    earthVel.Velocities[1][2] = 11.0
    earthVel.Velocities[1][3] = 12.0
    earthVel.Velocities[2][0] = 9.0
    earthVel.Velocities[2][1] = 10.0
    earthVel.Velocities[2][2] = 11.0
    earthVel.Velocities[2][3] = 12.0
    ens.AddEarthVelocity(earthVel)

    ens1 = Ensemble()
    ens1DS = EnsembleData()
    ens1DS.SysFirmwareSubsystemCode = '3'
    ens1DS.SubsystemConfig = '1'
    ens1DS.NumBeams = 4
    ens1DS.NumBins = 3
    ens1.AddEnsembleData(ens1DS)

    beamVel1 = BeamVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    beamVel1.Velocities[0][0] = 11.0
    beamVel1.Velocities[0][1] = 21.0
    beamVel1.Velocities[0][2] = 31.0
    beamVel1.Velocities[0][3] = 41.0
    beamVel1.Velocities[1][0] = 11.0
    beamVel1.Velocities[1][1] = 21.0
    beamVel1.Velocities[1][2] = 31.0
    beamVel1.Velocities[1][3] = 41.0
    beamVel1.Velocities[2][0] = 11.0
    beamVel1.Velocities[2][1] = 21.0
    beamVel1.Velocities[2][2] = 31.0
    beamVel1.Velocities[2][3] = 41.0
    ens1.AddBeamVelocity(beamVel1)

    instrVel1 = InstrumentVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    instrVel1.Velocities[0][0] = 51.0
    instrVel1.Velocities[0][1] = 61.0
    instrVel1.Velocities[0][2] = 71.0
    instrVel1.Velocities[0][3] = 81.0
    instrVel1.Velocities[1][0] = 51.0
    instrVel1.Velocities[1][1] = 61.0
    instrVel1.Velocities[1][2] = 71.0
    instrVel1.Velocities[1][3] = 81.0
    instrVel1.Velocities[2][0] = 51.0
    instrVel1.Velocities[2][1] = 61.0
    instrVel1.Velocities[2][2] = 71.0
    instrVel1.Velocities[2][3] = 81.0
    ens1.AddInstrumentVelocity(instrVel1)

    earthVel1 = EarthVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    earthVel1.Velocities[0][0] = 91.0
    earthVel1.Velocities[0][1] = 101.0
    earthVel1.Velocities[0][2] = 111.0
    earthVel1.Velocities[0][3] = 121.0
    earthVel1.Velocities[1][0] = 91.0
    earthVel1.Velocities[1][1] = 101.0
    earthVel1.Velocities[1][2] = 111.0
    earthVel1.Velocities[1][3] = 121.0
    earthVel1.Velocities[2][0] = 91.0
    earthVel1.Velocities[2][1] = 101.0
    earthVel1.Velocities[2][2] = 111.0
    earthVel1.Velocities[2][3] = 121.0
    ens1.AddEarthVelocity(earthVel1)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens1)
    result = awc.average()

    # verify not empty list
    assert result[0]
    assert result[1]
    assert result[2]

    # Beam Results
    assert result[4][0][0] == pytest.approx(4.33, 0.01)
    assert result[4][0][1] == pytest.approx(8.33, 0.01)
    assert result[4][0][2] == pytest.approx(12.33, 0.01)
    assert result[4][0][3] == pytest.approx(16.33, 0.01)

    # Instrument Results
    assert result[5][0][0] == pytest.approx(20.3, 0.01)
    assert result[5][0][1] == pytest.approx(24.3, 0.01)
    assert result[5][0][2] == pytest.approx(28.3, 0.01)
    assert result[5][0][3] == pytest.approx(32.3, 0.01)

    # Earth Results
    assert result[6][0][0] == pytest.approx(36.3, 0.01)
    assert result[6][0][1] == pytest.approx(40.3, 0.01)
    assert result[6][0][2] == pytest.approx(44.3, 0.01)
    assert result[6][0][3] == pytest.approx(48.3, 0.01)


def test_AWC_change_beam():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 5.0
    instrVel.Velocities[0][1] = 6.0
    instrVel.Velocities[0][2] = 7.0
    instrVel.Velocities[0][3] = 8.0
    instrVel.Velocities[1][0] = 5.0
    instrVel.Velocities[1][1] = 6.0
    instrVel.Velocities[1][2] = 7.0
    instrVel.Velocities[1][3] = 8.0
    instrVel.Velocities[2][0] = 5.0
    instrVel.Velocities[2][1] = 6.0
    instrVel.Velocities[2][2] = 7.0
    instrVel.Velocities[2][3] = 8.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 9.0
    earthVel.Velocities[0][1] = 10.0
    earthVel.Velocities[0][2] = 11.0
    earthVel.Velocities[0][3] = 12.0
    earthVel.Velocities[1][0] = 9.0
    earthVel.Velocities[1][1] = 10.0
    earthVel.Velocities[1][2] = 11.0
    earthVel.Velocities[1][3] = 12.0
    earthVel.Velocities[2][0] = 9.0
    earthVel.Velocities[2][1] = 10.0
    earthVel.Velocities[2][2] = 11.0
    earthVel.Velocities[2][3] = 12.0
    ens.AddEarthVelocity(earthVel)

    ens1 = Ensemble()
    ens1DS = EnsembleData()
    ens1DS.SysFirmwareSubsystemCode = '3'
    ens1DS.SubsystemConfig = '1'
    ens1DS.NumBeams = 1
    ens1DS.NumBins = 3
    ens1.AddEnsembleData(ens1DS)

    beamVel1 = BeamVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    beamVel1.Velocities[0][0] = 11.0
    beamVel1.Velocities[1][0] = 11.0
    beamVel1.Velocities[2][0] = 11.0
    ens1.AddBeamVelocity(beamVel1)

    instrVel1 = InstrumentVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    instrVel1.Velocities[0][0] = 51.0
    instrVel1.Velocities[1][0] = 51.0
    instrVel1.Velocities[2][0] = 51.0
    ens1.AddInstrumentVelocity(instrVel1)

    earthVel1 = EarthVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    earthVel1.Velocities[0][0] = 91.0
    earthVel1.Velocities[1][0] = 91.0
    earthVel1.Velocities[2][0] = 91.0
    ens1.AddEarthVelocity(earthVel1)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens1)
    result = awc.average()

    # verify empty list
    assert not result[4]
    assert not result[5]
    assert not result[6]


def test_AWC_change_bin():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 5.0
    instrVel.Velocities[0][1] = 6.0
    instrVel.Velocities[0][2] = 7.0
    instrVel.Velocities[0][3] = 8.0
    instrVel.Velocities[1][0] = 5.0
    instrVel.Velocities[1][1] = 6.0
    instrVel.Velocities[1][2] = 7.0
    instrVel.Velocities[1][3] = 8.0
    instrVel.Velocities[2][0] = 5.0
    instrVel.Velocities[2][1] = 6.0
    instrVel.Velocities[2][2] = 7.0
    instrVel.Velocities[2][3] = 8.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 9.0
    earthVel.Velocities[0][1] = 10.0
    earthVel.Velocities[0][2] = 11.0
    earthVel.Velocities[0][3] = 12.0
    earthVel.Velocities[1][0] = 9.0
    earthVel.Velocities[1][1] = 10.0
    earthVel.Velocities[1][2] = 11.0
    earthVel.Velocities[1][3] = 12.0
    earthVel.Velocities[2][0] = 9.0
    earthVel.Velocities[2][1] = 10.0
    earthVel.Velocities[2][2] = 11.0
    earthVel.Velocities[2][3] = 12.0
    ens.AddEarthVelocity(earthVel)

    ens1 = Ensemble()
    ens1DS = EnsembleData()
    ens1DS.SysFirmwareSubsystemCode = '3'
    ens1DS.SubsystemConfig = '1'
    ens1DS.NumBeams = 4
    ens1DS.NumBins = 2
    ens1.AddEnsembleData(ens1DS)

    beamVel = BeamVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    ens1.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    instrVel.Velocities[0][0] = 5.0
    instrVel.Velocities[0][1] = 6.0
    instrVel.Velocities[0][2] = 7.0
    instrVel.Velocities[0][3] = 8.0
    instrVel.Velocities[1][0] = 5.0
    instrVel.Velocities[1][1] = 6.0
    instrVel.Velocities[1][2] = 7.0
    instrVel.Velocities[1][3] = 8.0
    ens1.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    earthVel.Velocities[0][0] = 9.0
    earthVel.Velocities[0][1] = 10.0
    earthVel.Velocities[0][2] = 11.0
    earthVel.Velocities[0][3] = 12.0
    earthVel.Velocities[1][0] = 9.0
    earthVel.Velocities[1][1] = 10.0
    earthVel.Velocities[1][2] = 11.0
    earthVel.Velocities[1][3] = 12.0
    ens1.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens1)
    result = awc.average()

    # verify empty list
    assert not result[4]
    assert not result[5]
    assert not result[6]


def test_AWC_change_ss_code():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 5.0
    instrVel.Velocities[0][1] = 6.0
    instrVel.Velocities[0][2] = 7.0
    instrVel.Velocities[0][3] = 8.0
    instrVel.Velocities[1][0] = 5.0
    instrVel.Velocities[1][1] = 6.0
    instrVel.Velocities[1][2] = 7.0
    instrVel.Velocities[1][3] = 8.0
    instrVel.Velocities[2][0] = 5.0
    instrVel.Velocities[2][1] = 6.0
    instrVel.Velocities[2][2] = 7.0
    instrVel.Velocities[2][3] = 8.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 9.0
    earthVel.Velocities[0][1] = 10.0
    earthVel.Velocities[0][2] = 11.0
    earthVel.Velocities[0][3] = 12.0
    earthVel.Velocities[1][0] = 9.0
    earthVel.Velocities[1][1] = 10.0
    earthVel.Velocities[1][2] = 11.0
    earthVel.Velocities[1][3] = 12.0
    earthVel.Velocities[2][0] = 9.0
    earthVel.Velocities[2][1] = 10.0
    earthVel.Velocities[2][2] = 11.0
    earthVel.Velocities[2][3] = 12.0
    ens.AddEarthVelocity(earthVel)

    ens1 = Ensemble()
    ens1DS = EnsembleData()
    ens1DS.SysFirmwareSubsystemCode = '3'
    ens1DS.SubsystemConfig = '2'
    ens1DS.NumBeams = 4
    ens1DS.NumBins = 3
    ens1.AddEnsembleData(ens1DS)

    beamVel1 = BeamVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    beamVel1.Velocities[0][0] = 11.0
    beamVel1.Velocities[0][1] = 21.0
    beamVel1.Velocities[0][2] = 31.0
    beamVel1.Velocities[0][3] = 41.0
    beamVel1.Velocities[1][0] = 11.0
    beamVel1.Velocities[1][1] = 21.0
    beamVel1.Velocities[1][2] = 31.0
    beamVel1.Velocities[1][3] = 41.0
    beamVel1.Velocities[2][0] = 11.0
    beamVel1.Velocities[2][1] = 21.0
    beamVel1.Velocities[2][2] = 31.0
    beamVel1.Velocities[2][3] = 41.0
    ens1.AddBeamVelocity(beamVel1)

    instrVel1 = InstrumentVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    instrVel1.Velocities[0][0] = 51.0
    instrVel1.Velocities[0][1] = 61.0
    instrVel1.Velocities[0][2] = 71.0
    instrVel1.Velocities[0][3] = 81.0
    instrVel1.Velocities[1][0] = 51.0
    instrVel1.Velocities[1][1] = 61.0
    instrVel1.Velocities[1][2] = 71.0
    instrVel1.Velocities[1][3] = 81.0
    instrVel1.Velocities[2][0] = 51.0
    instrVel1.Velocities[2][1] = 61.0
    instrVel1.Velocities[2][2] = 71.0
    instrVel1.Velocities[2][3] = 81.0
    ens1.AddInstrumentVelocity(instrVel1)

    earthVel1 = EarthVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    earthVel1.Velocities[0][0] = 91.0
    earthVel1.Velocities[0][1] = 101.0
    earthVel1.Velocities[0][2] = 111.0
    earthVel1.Velocities[0][3] = 121.0
    earthVel1.Velocities[1][0] = 91.0
    earthVel1.Velocities[1][1] = 101.0
    earthVel1.Velocities[1][2] = 111.0
    earthVel1.Velocities[1][3] = 121.0
    earthVel1.Velocities[2][0] = 91.0
    earthVel1.Velocities[2][1] = 101.0
    earthVel1.Velocities[2][2] = 111.0
    earthVel1.Velocities[2][3] = 121.0
    ens1.AddEarthVelocity(earthVel1)

    ens.EarthVelocity.generate_velocity_vectors()
    ens1.EarthVelocity.generate_velocity_vectors()


    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens1)
    result = awc.average()

    assert 18 == len(result)

    # verify not empty list
    assert result[4]
    assert result[5]
    assert result[6]

    # Beam Results
    assert result[4][0][0] == 1.0
    assert result[4][0][1] == 2.0
    assert result[4][0][2] == 3.0
    assert result[4][0][3] == 4.0

    # Instrument Results
    assert result[5][0][0] == 5.0
    assert result[5][0][1] == 6.0
    assert result[5][0][2] == 7.0
    assert result[5][0][3] == 8.0

    # Earth Results
    assert result[6][0][0] == 9.0
    assert result[6][0][1] == 10.0
    assert result[6][0][2] == 11.0
    assert result[6][0][3] == 12.0

    # Magnitude
    assert result[7][0] == pytest.approx(17.378, 0.1)
    assert result[7][1] == pytest.approx(17.378, 0.1)
    assert result[7][2] == pytest.approx(17.378, 0.1)

    # Direction
    assert result[8][0] == pytest.approx(41.98, 0.1)
    assert result[8][1] == pytest.approx(41.98, 0.1)
    assert result[8][2] == pytest.approx(41.98, 0.1)


def test_AWC_change_ss_config():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 5.0
    instrVel.Velocities[0][1] = 6.0
    instrVel.Velocities[0][2] = 7.0
    instrVel.Velocities[0][3] = 8.0
    instrVel.Velocities[1][0] = 5.0
    instrVel.Velocities[1][1] = 6.0
    instrVel.Velocities[1][2] = 7.0
    instrVel.Velocities[1][3] = 8.0
    instrVel.Velocities[2][0] = 5.0
    instrVel.Velocities[2][1] = 6.0
    instrVel.Velocities[2][2] = 7.0
    instrVel.Velocities[2][3] = 8.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 9.0
    earthVel.Velocities[0][1] = 10.0
    earthVel.Velocities[0][2] = 11.0
    earthVel.Velocities[0][3] = 12.0
    earthVel.Velocities[1][0] = 9.0
    earthVel.Velocities[1][1] = 10.0
    earthVel.Velocities[1][2] = 11.0
    earthVel.Velocities[1][3] = 12.0
    earthVel.Velocities[2][0] = 9.0
    earthVel.Velocities[2][1] = 10.0
    earthVel.Velocities[2][2] = 11.0
    earthVel.Velocities[2][3] = 12.0
    ens.AddEarthVelocity(earthVel)

    ens1 = Ensemble()
    ens1DS = EnsembleData()
    ens1DS.SysFirmwareSubsystemCode = '4'
    ens1DS.SubsystemConfig = '1'
    ens1DS.NumBeams = 4
    ens1DS.NumBins = 3
    ens1.AddEnsembleData(ens1DS)

    beamVel1 = BeamVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    beamVel1.Velocities[0][0] = 11.0
    beamVel1.Velocities[0][1] = 21.0
    beamVel1.Velocities[0][2] = 31.0
    beamVel1.Velocities[0][3] = 41.0
    beamVel1.Velocities[1][0] = 11.0
    beamVel1.Velocities[1][1] = 21.0
    beamVel1.Velocities[1][2] = 31.0
    beamVel1.Velocities[1][3] = 41.0
    beamVel1.Velocities[2][0] = 11.0
    beamVel1.Velocities[2][1] = 21.0
    beamVel1.Velocities[2][2] = 31.0
    beamVel1.Velocities[2][3] = 41.0
    ens1.AddBeamVelocity(beamVel1)

    instrVel1 = InstrumentVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    instrVel1.Velocities[0][0] = 51.0
    instrVel1.Velocities[0][1] = 61.0
    instrVel1.Velocities[0][2] = 71.0
    instrVel1.Velocities[0][3] = 81.0
    instrVel1.Velocities[1][0] = 51.0
    instrVel1.Velocities[1][1] = 61.0
    instrVel1.Velocities[1][2] = 71.0
    instrVel1.Velocities[1][3] = 81.0
    instrVel1.Velocities[2][0] = 51.0
    instrVel1.Velocities[2][1] = 61.0
    instrVel1.Velocities[2][2] = 71.0
    instrVel1.Velocities[2][3] = 81.0
    ens1.AddInstrumentVelocity(instrVel1)

    earthVel1 = EarthVelocity(ens1DS.NumBins, ens1DS.NumBeams)
    earthVel1.Velocities[0][0] = 91.0
    earthVel1.Velocities[0][1] = 101.0
    earthVel1.Velocities[0][2] = 111.0
    earthVel1.Velocities[0][3] = 121.0
    earthVel1.Velocities[1][0] = 91.0
    earthVel1.Velocities[1][1] = 101.0
    earthVel1.Velocities[1][2] = 111.0
    earthVel1.Velocities[1][3] = 121.0
    earthVel1.Velocities[2][0] = 91.0
    earthVel1.Velocities[2][1] = 101.0
    earthVel1.Velocities[2][2] = 111.0
    earthVel1.Velocities[2][3] = 121.0
    ens1.AddEarthVelocity(earthVel1)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens1)
    result = awc.average()

    # verify not empty list
    assert result[AverageWaterColumn.INDEX_BEAM]
    assert result[AverageWaterColumn.INDEX_INSTRUMENT]
    assert result[AverageWaterColumn.INDEX_EARTH]

    # Beam Results
    assert result[4][0][0] == 1.0
    assert result[4][0][1] == 2.0
    assert result[4][0][2] == 3.0
    assert result[4][0][3] == 4.0

    # Instrument Results
    assert result[5][0][0] == 5.0
    assert result[5][0][1] == 6.0
    assert result[5][0][2] == 7.0
    assert result[5][0][3] == 8.0

    # Earth Results
    assert result[6][0][0] == 9.0
    assert result[6][0][1] == 10.0
    assert result[6][0][2] == 11.0
    assert result[6][0][3] == 12.0


def test_AWC_mag_dir():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ens.AddEnsembleData(ensDS)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 1.0
    instrVel.Velocities[0][1] = 2.0
    instrVel.Velocities[0][2] = 3.0
    instrVel.Velocities[0][3] = 4.0
    instrVel.Velocities[1][0] = 1.0
    instrVel.Velocities[1][1] = 2.0
    instrVel.Velocities[1][2] = 3.0
    instrVel.Velocities[1][3] = 4.0
    instrVel.Velocities[2][0] = 1.0
    instrVel.Velocities[2][1] = 2.0
    instrVel.Velocities[2][2] = 3.0
    instrVel.Velocities[2][3] = 4.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 1.0
    earthVel.Velocities[0][1] = 2.0
    earthVel.Velocities[0][2] = 3.0
    earthVel.Velocities[0][3] = 4.0
    earthVel.Velocities[1][0] = 1.0
    earthVel.Velocities[1][1] = 2.0
    earthVel.Velocities[1][2] = 3.0
    earthVel.Velocities[1][3] = 4.0
    earthVel.Velocities[2][0] = 1.0
    earthVel.Velocities[2][1] = 2.0
    earthVel.Velocities[2][2] = 3.0
    earthVel.Velocities[2][3] = 4.0
    earthVel.generate_velocity_vectors()
    ens.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    result = awc.average()

    # verify empty list
    assert result[AverageWaterColumn.INDEX_BEAM]
    assert result[AverageWaterColumn.INDEX_INSTRUMENT]
    assert result[AverageWaterColumn.INDEX_EARTH]
    assert result[AverageWaterColumn.INDEX_MAG]
    assert result[AverageWaterColumn.INDEX_DIR]

    # Beam Results
    assert result[4][0][0] == 1.0
    assert result[4][0][1] == 2.0
    assert result[4][0][2] == 3.0
    assert result[4][0][3] == 4.0

    # Instrument Results
    assert result[5][0][0] == 1.0
    assert result[5][0][1] == 2.0
    assert result[5][0][2] == 3.0
    assert result[5][0][3] == 4.0

    # Earth Results
    assert result[6][0][0] == 1.0
    assert result[6][0][1] == 2.0
    assert result[6][0][2] == 3.0
    assert result[6][0][3] == 4.0

    # Mag Results
    assert result[AverageWaterColumn.INDEX_MAG][0] == pytest.approx(3.741, 0.01)
    assert result[AverageWaterColumn.INDEX_MAG][1] == pytest.approx(3.741, 0.01)
    assert result[AverageWaterColumn.INDEX_MAG][2] == pytest.approx(3.741, 0.01)

    # Dir Result
    assert result[AverageWaterColumn.INDEX_DIR][0] == pytest.approx(26.5650, 0.01)
    assert result[AverageWaterColumn.INDEX_DIR][1] == pytest.approx(26.5650, 0.01)
    assert result[AverageWaterColumn.INDEX_DIR][2] == pytest.approx(26.5650, 0.01)

    # Pressure and Transducer Depth
    assert not result[AverageWaterColumn.INDEX_PRESSURE]
    assert not result[AverageWaterColumn.INDEX_XDCR_DEPTH]


def test_AWC_pressure_xdcr_depth():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ensDS.Year = 2019
    ensDS.Month = 3
    ensDS.Day = 12
    ensDS.Hour = 14
    ensDS.Minute = 33
    ensDS.Second = 45
    ensDS.HSec = 34
    ens.AddEnsembleData(ensDS)

    anc = AncillaryData()
    anc.Pressure = 2.6345
    anc.TransducerDepth = 26.354
    ens.AddAncillaryData(anc)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 1.0
    instrVel.Velocities[0][1] = 2.0
    instrVel.Velocities[0][2] = 3.0
    instrVel.Velocities[0][3] = 4.0
    instrVel.Velocities[1][0] = 1.0
    instrVel.Velocities[1][1] = 2.0
    instrVel.Velocities[1][2] = 3.0
    instrVel.Velocities[1][3] = 4.0
    instrVel.Velocities[2][0] = 1.0
    instrVel.Velocities[2][1] = 2.0
    instrVel.Velocities[2][2] = 3.0
    instrVel.Velocities[2][3] = 4.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 1.0
    earthVel.Velocities[0][1] = 2.0
    earthVel.Velocities[0][2] = 3.0
    earthVel.Velocities[0][3] = 4.0
    earthVel.Velocities[1][0] = 1.0
    earthVel.Velocities[1][1] = 2.0
    earthVel.Velocities[1][2] = 3.0
    earthVel.Velocities[1][3] = 4.0
    earthVel.Velocities[2][0] = 1.0
    earthVel.Velocities[2][1] = 2.0
    earthVel.Velocities[2][2] = 3.0
    earthVel.Velocities[2][3] = 4.0
    earthVel.generate_velocity_vectors()
    ens.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    result = awc.average()

    # verify empty list
    assert result[AverageWaterColumn.INDEX_BEAM]
    assert result[AverageWaterColumn.INDEX_INSTRUMENT]
    assert result[AverageWaterColumn.INDEX_EARTH]
    assert result[AverageWaterColumn.INDEX_MAG]
    assert result[AverageWaterColumn.INDEX_DIR]

    # Beam Results
    assert result[AverageWaterColumn.INDEX_BEAM][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][3] == 4.0

    # Instrument Results
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][3] == 4.0

    # Earth Results
    assert result[AverageWaterColumn.INDEX_EARTH][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][3] == 4.0

    # Mag Results
    assert result[AverageWaterColumn.INDEX_MAG][0] == pytest.approx(3.741, 0.01)
    assert result[AverageWaterColumn.INDEX_MAG][1] == pytest.approx(3.741, 0.01)
    assert result[AverageWaterColumn.INDEX_MAG][2] == pytest.approx(3.741, 0.01)

    # Dir Result
    assert result[AverageWaterColumn.INDEX_DIR][0] == pytest.approx(26.5650, 0.01)
    assert result[AverageWaterColumn.INDEX_DIR][1] == pytest.approx(26.5650, 0.01)
    assert result[AverageWaterColumn.INDEX_DIR][2] == pytest.approx(26.5650, 0.01)

    # Pressure
    assert result[AverageWaterColumn.INDEX_PRESSURE][0] == pytest.approx(2.6345, 0.01)

    # Transducer Depth
    assert result[AverageWaterColumn.INDEX_XDCR_DEPTH][0] == pytest.approx(26.354, 0.01)


def test_AWC_time():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ensDS.Year = 2019
    ensDS.Month = 3
    ensDS.Day = 12
    ensDS.Hour = 14
    ensDS.Minute = 33
    ensDS.Second = 45
    ensDS.HSec = 34
    ens.AddEnsembleData(ensDS)

    anc = AncillaryData()
    anc.Pressure = 2.6345
    anc.TransducerDepth = 26.354
    ens.AddAncillaryData(anc)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 1.0
    instrVel.Velocities[0][1] = 2.0
    instrVel.Velocities[0][2] = 3.0
    instrVel.Velocities[0][3] = 4.0
    instrVel.Velocities[1][0] = 1.0
    instrVel.Velocities[1][1] = 2.0
    instrVel.Velocities[1][2] = 3.0
    instrVel.Velocities[1][3] = 4.0
    instrVel.Velocities[2][0] = 1.0
    instrVel.Velocities[2][1] = 2.0
    instrVel.Velocities[2][2] = 3.0
    instrVel.Velocities[2][3] = 4.0
    ens.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 1.0
    earthVel.Velocities[0][1] = 2.0
    earthVel.Velocities[0][2] = 3.0
    earthVel.Velocities[0][3] = 4.0
    earthVel.Velocities[1][0] = 1.0
    earthVel.Velocities[1][1] = 2.0
    earthVel.Velocities[1][2] = 3.0
    earthVel.Velocities[1][3] = 4.0
    earthVel.Velocities[2][0] = 1.0
    earthVel.Velocities[2][1] = 2.0
    earthVel.Velocities[2][2] = 3.0
    earthVel.Velocities[2][3] = 4.0
    earthVel.generate_velocity_vectors()
    ens.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens)
    result = awc.average()

    # verify empty list
    assert result[AverageWaterColumn.INDEX_BEAM]
    assert result[AverageWaterColumn.INDEX_INSTRUMENT]
    assert result[AverageWaterColumn.INDEX_EARTH]
    assert result[AverageWaterColumn.INDEX_MAG]
    assert result[AverageWaterColumn.INDEX_DIR]

    # Beam Results
    assert result[AverageWaterColumn.INDEX_BEAM][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][3] == 4.0

    # Instrument Results
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][3] == 4.0

    # Earth Results
    assert result[AverageWaterColumn.INDEX_EARTH][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][3] == 4.0

    # Mag Results
    assert result[AverageWaterColumn.INDEX_MAG][0] == pytest.approx(3.741, 0.01)
    assert result[AverageWaterColumn.INDEX_MAG][1] == pytest.approx(3.741, 0.01)
    assert result[AverageWaterColumn.INDEX_MAG][2] == pytest.approx(3.741, 0.01)

    # Dir Result
    assert result[AverageWaterColumn.INDEX_DIR][0] == pytest.approx(26.5650, 0.01)
    assert result[AverageWaterColumn.INDEX_DIR][1] == pytest.approx(26.5650, 0.01)
    assert result[AverageWaterColumn.INDEX_DIR][2] == pytest.approx(26.5650, 0.01)

    # Pressure
    assert result[AverageWaterColumn.INDEX_PRESSURE][0] == pytest.approx(2.6345, 0.01)

    # Transducer Depth
    assert result[AverageWaterColumn.INDEX_XDCR_DEPTH][0] == pytest.approx(26.354, 0.01)

    # First Time
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].year == pytest.approx(2019, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].month == pytest.approx(3, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].day == pytest.approx(12, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].hour == pytest.approx(14, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].minute == pytest.approx(33, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].second == pytest.approx(45, 0.1)

    # Last Time
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].year == pytest.approx(2019, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].month == pytest.approx(3, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].day == pytest.approx(12, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].hour == pytest.approx(14, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].minute == pytest.approx(33, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].second == pytest.approx(45, 0.1)


def test_AWC_last_time():

    ens = Ensemble()
    ensDS = EnsembleData()
    ensDS.SysFirmwareSubsystemCode = '3'
    ensDS.SubsystemConfig = '1'
    ensDS.NumBeams = 4
    ensDS.NumBins = 3
    ensDS.Year = 2019
    ensDS.Month = 3
    ensDS.Day = 12
    ensDS.Hour = 14
    ensDS.Minute = 33
    ensDS.Second = 45
    ensDS.HSec = 34
    ens.AddEnsembleData(ensDS)

    ens2 = Ensemble()
    ensDS1 = EnsembleData()
    ensDS1.SysFirmwareSubsystemCode = '3'
    ensDS1.SubsystemConfig = '1'
    ensDS1.NumBeams = 4
    ensDS1.NumBins = 3
    ensDS1.Year = 2019
    ensDS1.Month = 3
    ensDS1.Day = 12
    ensDS1.Hour = 15
    ensDS1.Minute = 33
    ensDS1.Second = 45
    ensDS1.HSec = 34
    ens2.AddEnsembleData(ensDS)

    anc = AncillaryData()
    anc.Pressure = 2.6345
    anc.TransducerDepth = 26.354
    ens.AddAncillaryData(anc)
    ens2.AddAncillaryData(anc)

    beamVel = BeamVelocity(ensDS.NumBins, ensDS.NumBeams)
    beamVel.Velocities[0][0] = 1.0
    beamVel.Velocities[0][1] = 2.0
    beamVel.Velocities[0][2] = 3.0
    beamVel.Velocities[0][3] = 4.0
    beamVel.Velocities[1][0] = 1.0
    beamVel.Velocities[1][1] = 2.0
    beamVel.Velocities[1][2] = 3.0
    beamVel.Velocities[1][3] = 4.0
    beamVel.Velocities[2][0] = 1.0
    beamVel.Velocities[2][1] = 2.0
    beamVel.Velocities[2][2] = 3.0
    beamVel.Velocities[2][3] = 4.0
    ens.AddBeamVelocity(beamVel)
    ens2.AddBeamVelocity(beamVel)

    instrVel = InstrumentVelocity(ensDS.NumBins, ensDS.NumBeams)
    instrVel.Velocities[0][0] = 1.0
    instrVel.Velocities[0][1] = 2.0
    instrVel.Velocities[0][2] = 3.0
    instrVel.Velocities[0][3] = 4.0
    instrVel.Velocities[1][0] = 1.0
    instrVel.Velocities[1][1] = 2.0
    instrVel.Velocities[1][2] = 3.0
    instrVel.Velocities[1][3] = 4.0
    instrVel.Velocities[2][0] = 1.0
    instrVel.Velocities[2][1] = 2.0
    instrVel.Velocities[2][2] = 3.0
    instrVel.Velocities[2][3] = 4.0
    ens.AddInstrumentVelocity(instrVel)
    ens2.AddInstrumentVelocity(instrVel)

    earthVel = EarthVelocity(ensDS.NumBins, ensDS.NumBeams)
    earthVel.Velocities[0][0] = 1.0
    earthVel.Velocities[0][1] = 2.0
    earthVel.Velocities[0][2] = 3.0
    earthVel.Velocities[0][3] = 4.0
    earthVel.Velocities[1][0] = 1.0
    earthVel.Velocities[1][1] = 2.0
    earthVel.Velocities[1][2] = 3.0
    earthVel.Velocities[1][3] = 4.0
    earthVel.Velocities[2][0] = 1.0
    earthVel.Velocities[2][1] = 2.0
    earthVel.Velocities[2][2] = 3.0
    earthVel.Velocities[2][3] = 4.0
    earthVel.generate_velocity_vectors()
    ens.AddEarthVelocity(earthVel)
    ens2.AddEarthVelocity(earthVel)

    awc = AverageWaterColumn(3, '3', '1')
    awc.add_ens(ens)
    awc.add_ens(ens)
    awc.add_ens(ens2)
    result = awc.average()

    # verify empty list
    assert result[AverageWaterColumn.INDEX_BEAM]
    assert result[AverageWaterColumn.INDEX_INSTRUMENT]
    assert result[AverageWaterColumn.INDEX_EARTH]
    assert result[AverageWaterColumn.INDEX_MAG]
    assert result[AverageWaterColumn.INDEX_DIR]

    # Beam Results
    assert result[AverageWaterColumn.INDEX_BEAM][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_BEAM][0][3] == 4.0

    # Instrument Results
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_INSTRUMENT][0][3] == 4.0

    # Earth Results
    assert result[AverageWaterColumn.INDEX_EARTH][0][0] == 1.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][1] == 2.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][2] == 3.0
    assert result[AverageWaterColumn.INDEX_EARTH][0][3] == 4.0

    # Mag Results
    assert result[AverageWaterColumn.INDEX_MAG][0] == pytest.approx(3.741, 0.01)
    assert result[AverageWaterColumn.INDEX_MAG][1] == pytest.approx(3.741, 0.01)
    assert result[AverageWaterColumn.INDEX_MAG][2] == pytest.approx(3.741, 0.01)

    # Dir Result
    assert result[AverageWaterColumn.INDEX_DIR][0] == pytest.approx(26.5650, 0.01)
    assert result[AverageWaterColumn.INDEX_DIR][1] == pytest.approx(26.5650, 0.01)
    assert result[AverageWaterColumn.INDEX_DIR][2] == pytest.approx(26.5650, 0.01)

    # Pressure
    assert result[AverageWaterColumn.INDEX_PRESSURE][0] == pytest.approx(2.6345, 0.01)

    # Transducer Depth
    assert result[AverageWaterColumn.INDEX_XDCR_DEPTH][0] == pytest.approx(26.354, 0.01)

    # First Time
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].year == pytest.approx(2019, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].month == pytest.approx(3, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].day == pytest.approx(12, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].hour == pytest.approx(14, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].minute == pytest.approx(33, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].second == pytest.approx(45, 0.1)

    # Last Time
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].year == pytest.approx(2019, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].month == pytest.approx(3, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].day == pytest.approx(12, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].hour == pytest.approx(15, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].minute == pytest.approx(33, 0.1)
    assert result[AverageWaterColumn.INDEX_FIRST_TIME].second == pytest.approx(45, 0.1)
