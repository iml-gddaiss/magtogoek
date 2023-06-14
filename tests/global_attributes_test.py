import pytest
import xarray as xr
from magtogoek.process_common import BaseProcessConfig, add_global_attributes, add_platform_metadata_to_dataset
from magtogoek.platforms import default_platform_metadata

STANDARD_GLOBAL_ATTRIBUTES = {
    "featureType": "timeSeriesProfile",
}

CONFIG_DICT = {
    "HEADER": {"process": "adcp", "platform_type": ""},
    "INPUT": {
        "input_files": [""],
    },
    "OUTPUT": {"force_platform_metadata": False}, # test true False
    "PROJECT": {"project": "project_attr"},
    "CRUISE": {"cruise": "cruise_attr"},
    "GLOBAL_ATTRIBUTES": {
        "_global": "global_attr",
        'sounding': 111,
        'longitude': 111,
        'latitude': 111,
    },
}

PCONFIG = BaseProcessConfig(config_dict=CONFIG_DICT)
PCONFIG.platform_metadata = default_platform_metadata("buoy", "test_instrument", "adcp")

PCONFIG.platform_metadata.platform.platform_name = 'test_platform_name'
PCONFIG.platform_metadata.platform.platform_model = 'test_platform_model'
PCONFIG.platform_metadata.platform.sounding = 333
PCONFIG.platform_metadata.platform.longitude = 666
PCONFIG.platform_metadata.platform.latitude = 999
PCONFIG.platform_metadata.platform.description = 'test_platform_description'


EXPECTED_GLOBAL_ATTRIBUTES = {
    "basic": {
            "featureType": "timeSeriesProfile",
            'platform': 'test_platform_name',
            'platform_model': 'test_platform_model',
            'sounding': 111,
            'longitude': 111,
            'latitude': 111,
            'platform_description': 'test_platform_description',

            'data_type': "madcp",
            'data_subtype': "BUOY",

            "source": "test_source",
            "project": "project_attr",
            "cruise": "cruise_attr",
            "_global": "global_attr",
    },
    'force_platform': {
            "featureType": "timeSeriesProfile",
            'platform': 'test_platform_name',
            'platform_model': 'test_platform_model',
            'sounding': 333,
            'longitude': 666,
            'latitude': 999,
            'platform_description': 'test_platform_description',

            'data_type': "adcp",
            'data_subtype': "SHIPBORNE",

            "source": "ship",
            "project": "project_attr",
            "cruise": "cruise_attr",
            "_global": "global_attr",
    }
}


@pytest.mark.parametrize(
    "platform_type, source, force_platform_metadata, global_attrs",
    [
        ("buoy", "test_source", False, EXPECTED_GLOBAL_ATTRIBUTES['basic']),
        ("ship", "", True, EXPECTED_GLOBAL_ATTRIBUTES['force_platform']),
    ],
)
def test_global_attributes(platform_type, source, force_platform_metadata, global_attrs):
    PCONFIG.platform_type = platform_type
    PCONFIG.global_attributes['source'] = source
    PCONFIG.force_platform_metadata = force_platform_metadata

    dataset = xr.Dataset()
    add_global_attributes(dataset, PCONFIG, STANDARD_GLOBAL_ATTRIBUTES)
    add_platform_metadata_to_dataset(dataset=dataset, pconfig=PCONFIG)

    assert dataset.attrs == global_attrs
