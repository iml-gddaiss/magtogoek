import pytest
import xarray as xr
from magtogoek.adcp.odf_exporter import make_odf
from magtogoek.platforms import PlatformMetadata, Platform, BuoySpecifications, InstrumentMetadata
from magtogoek.utils import json2dict

DATASET = xr.open_dataset("data/odf_test_files/odf_adcp_test_dataset.nc")
GLOBAL_ATTRS = json2dict("data/odf_test_global_attributes.json") # FIXME not used ?
P01_TO_GENERIC_NAME = {
    "u": "LCEWAP01",
    "u_QC": "LCEWAP01_QC",
    "v": "LCNSAP01",
    "v_QC": "LCNSAP01_QC",
    "w": "LRZAAP01",
    "w_QC": "LRZAAP01_QC",
    "e": "LERRAP01",
}
GENERIC_VARIABLES_NAME = [var for var in DATASET.variables]

DATASET.attrs.update({'flag_reference': '', 'flag_values': '', 'flag_meanings': ''})

PLATFORM_METADATA = PlatformMetadata(
    platform=Platform(platform_name='platform_name_test', description='platform_description_test'),
    buoy_specs=BuoySpecifications(
        type="buoy_type_test",
        model="buoy_model_test",
        height="buoy_height_test",
        diameter="buoy_diameter_test",
        weight="buoy_weight_test",
        description="buoy_description_test"
    )
)
PLATFORM_METADATA.add_instrument(instrument_id='ADCP_01', instrument_meta={'adcp_sensor_id': 'ADCP_01', 'sensor_type': 'adcp', 'sensors': {}})


def test_make():
    odf = make_odf(
        dataset=DATASET,
        platform_metadata=PLATFORM_METADATA,
        adcp_id='ADCP_01',
        global_attributes=GLOBAL_ATTRS,
        p01_codes_map=P01_TO_GENERIC_NAME
    )
    assert odf.data.shape == (40, 9)


@pytest.mark.parametrize(
    "platform_type, headers, cruise_platform",
    [
        ("mooring", ["instrument"], PLATFORM_METADATA.platform.platform_name),
        ("ship", ["instrument"], PLATFORM_METADATA.platform.platform_name),
        ("buoy", ["buoy_instrument", "buoy"], "Oceanographic Buoy"),
    ],
)
def test_platform_type(platform_type, headers, cruise_platform):
    PLATFORM_METADATA.platform.platform_type = platform_type
    odf = make_odf(dataset=DATASET,
                   platform_metadata=PLATFORM_METADATA,
                   adcp_id='ADCP_01',
                   global_attributes=GLOBAL_ATTRS,
                   p01_codes_map=P01_TO_GENERIC_NAME,
                   use_bodc_name=True,
                   event_qualifier2='VEL',
                   output_path=None,
                   )
    assert odf.cruise["platform"] == cruise_platform

    for header in headers:
        assert header in odf.__dict__

    if platform_type == "buoy":
        assert odf.buoy["name"] == PLATFORM_METADATA.platform.platform_name
        for key, value in PLATFORM_METADATA.buoy_specs.__dict__.items():
            assert odf.buoy[key] == value
