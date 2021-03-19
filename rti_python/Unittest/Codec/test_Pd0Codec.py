import pytest
from rti_python.Codecs.Pd0Codec import Pd0Codec


def pd0_ens_event(sender, ens):
    print(ens)


def test_pd0_decode():
    # PD0 File Path
    file_path = "C:\\RTI_Capture\\Imperal Valley_20170816_094228_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0"

    pd0 = Pd0Codec()
    pd0.ensemble_event += pd0_ens_event
    ens_count, ens_error = pd0.decode(file_path)

    assert ens_count == 579



