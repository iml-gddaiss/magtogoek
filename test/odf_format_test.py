import pytest
import os
from magtogoek.odf_format import Odf, convert_odf_to_nc
from magtogoek.utils import json2dict

odf_dict = json2dict("data/odf_test_files/odf_read_test_expected_dict.json")
TEST_FILE = "data/odf_test_files/MADCP_BOUEE2019_RIMOUSKI_553_VEL.ODF"


@pytest.fixture
def odf():
    return Odf().read(TEST_FILE)


def test_reading_header(odf):
    odf.__dict__.pop("data")

    assert odf.__dict__ == odf_dict


def test_reading_data(odf):
    data = odf.data

    assert len(data) == 549660
    assert data.loc[0].SYTM_01 == "10-MAY-2019 19:30:00.00"
    assert data.loc[0].DEPH_01 == 10.47
    assert data.loc[0].EWCT_01 == 0.0615
    assert data.loc[0].QQQQ_01 == 3
    assert data.loc[0].NSCT_01 == 0.0002
    assert data.loc[0].QQQQ_02 == 3
    assert data.loc[0].VCSP_01 == -0.0029
    assert data.loc[0].QQQQ_03 == 3
    assert data.loc[0].ERRV_01 == -0.0122


def test_converting_odf2nc(odf):
    out_filename = 'convert_odf2nc_test.nc'
    try:
        convert_odf_to_nc(
            input_files=TEST_FILE,
            output_name=out_filename,
            dims=("DEPH_01", "SYTM_01"),
            time="SYTM_01"
        )
        os.remove(out_filename)
    except Exception as exc:
        assert False, f'Exception raised {exc}'

