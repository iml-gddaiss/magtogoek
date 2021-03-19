import pytest
from rti_python.River.Transect import Transect


def test_constructor():
    transect = Transect(33)
    assert transect.transect_index == 33


def test_get_name():
    transect = Transect(33)
    transect_name = transect.get_name()

    assert transect_name == "Transect_33"
