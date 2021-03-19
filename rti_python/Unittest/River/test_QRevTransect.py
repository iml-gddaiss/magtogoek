import os
from rti_python.River.QRevTransect import RTTtransect


def test_constructor():
    transect = RTTtransect()

    assert transect.Checked
    assert len(transect.Files) == 0
    assert len(transect.Notes) == 0


def test_unchecked():
    transect = RTTtransect()
    transect.Checked = False

    assert not transect.Checked
    assert len(transect.Files) == 0


def test_add_transect():
    transect = RTTtransect()
    file_name = 'Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0'

    # Add the transect file to the transect
    transect.add_transect_file(file_name)

    assert transect.Checked
    assert len(transect.Files) == 1
    assert transect.Files[0] == 'Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0'


def test_add_transect_unchecked():
    transect = RTTtransect()
    file_name = 'Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0'

    # Add the transect file to the transect
    transect.add_transect_file(file_name)
    transect.Checked = 0

    assert transect.Checked == 0
    assert len(transect.Files) == 1
    assert transect.Files[0] == 'Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0'


def test_add_transect_multiple_files():
    transect = RTTtransect()
    file_name1 = 'Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0'
    file_name2 = 'Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0_1.pd0'

    # Add the transect file to the transect
    transect.add_transect_file(file_name1)
    transect.add_transect_file(file_name2)

    assert transect.Checked
    assert len(transect.Files) == 2
    assert transect.Files[0] == 'Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0'
    assert transect.Files[1] == 'Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0_1.pd0'


