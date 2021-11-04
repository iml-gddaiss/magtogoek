import pytest
import xarray as xr
from magtogoek.adcp.odf_exporter import make_odf
from magtogoek.adcp.process import _default_platform
from magtogoek.utils import json2dict

DATASET = xr.open_dataset("data/netcdf_test_files/test_netcdf.nc")
GLOBAL_ATTRS = json2dict("data/test_global_attributes.json")

P01_TO_GENEREIC_NAME = {
    "u": "LCEWAP01",
    "u_QC": "LCEWAP01_QC",
    "v": "LCNSAP01",
    "v_QC": "LCNSAP01_QC",
    "w": "LRZAAP01",
    "w_QC": "LRZAAP01_QC",
    "e": "LERRAP01",
}

SENSOR_METADATA = _default_platform()
SENSOR_METADATA.update(
    {
        "platform_name": "platform_name_test",
        "platform_type": "buoy_test",
        "description": "platform_description_test",
        "buoy_specs": {
            "type": "buoy_type_test",
            "model": "buoy_model_test",
            "height": "buoy_height_test",
            "diameter": "buoy_diameter_test",
            "weight": "buoy_weight_test",
            "description": "buoy_description_test",
        },
    }
)


def test_make():
    odf = make_odf(DATASET, SENSOR_METADATA, GLOBAL_ATTRS, P01_TO_GENEREIC_NAME)
    assert odf.data.shape == (40, 9)


@pytest.mark.parametrize(
    "platform_type, headers, cruise_platform",
    [
        ("mooring", ["instrument"], SENSOR_METADATA["platform_name"]),
        ("ship", ["instrument"], SENSOR_METADATA["platform_name"]),
        ("buoy", ["buoy_instrument", "buoy"], "Oceanographic Buoy"),
    ],
)
def test_platform_type(platform_type, headers, cruise_platform):
    SENSOR_METADATA["platform_type"] = platform_type
    odf = make_odf(DATASET, SENSOR_METADATA, GLOBAL_ATTRS, P01_TO_GENEREIC_NAME)
    for header in headers:
        assert header in odf.__dict__
        assert odf.cruise["platform"] == cruise_platform
    if platform_type == "buoy":
        assert odf.buoy["name"] == SENSOR_METADATA["platform_name"]
        for key, value in SENSOR_METADATA["buoy_specs"].items():
            assert odf.buoy[key] == value
