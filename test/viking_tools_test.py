import numpy as np
from magtogoek.viking.tools import pHEXT_from_vFET


def test_pHEXT_from_vFET():
    """
    Test value from Seabird documentations
    Notes
    -----
    Sea-Bird Scientific, Technical Note on Calculating pH, Application Note 99
    """
    ph_ext = np.array([7.8454])
    temp = np.array([15.8735])
    psal = np.array([36.817])
    volt = np.array([-0.965858])
    k0 = -1.429278
    k2 = -1.142026*10**(-3)

    assert ph_ext[0] == np.round(pHEXT_from_vFET(temp=temp, psal=psal, volt=volt, k0=k0, k2=k2)[0], 4)