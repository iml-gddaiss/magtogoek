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
    "PROJECT": {"project": "project_attr"},
    "CRUISE": {"cruise": "cruise_attr"},
    "GLOBAL_ATTRIBUTES": {
        "_global": "global_attr",
        'sounding': 111,
        'longitude': 111,
        'latitude': 111,
    },
}

DEFAULT_METADATA = default_platform_metadata("buoy", "test_instrument", "adcp")

DEFAULT_METADATA.platform.platform_name = 'test_platform_name'
DEFAULT_METADATA.platform.platform_model = 'test_platform_model'
DEFAULT_METADATA.platform.sounding = 333
DEFAULT_METADATA.platform.longitude = 666
DEFAULT_METADATA.platform.latitude = 999
DEFAULT_METADATA.platform.description = 'test_platform_description'


EXPECTED_GLOBAL_ATTRIBUTES = {
    "standard": {
        "featureType": "timeSeriesProfile",
        'platform': 'test_platform_name',
        'platform_model': 'test_platform_model',
        'platform_description': 'test_platform_description',
        "project": "project_attr",
        "cruise": "cruise_attr",
        "_global": "global_attr",
        "data_type": "madcp",
        "data_subtype": "BUOY",
        "source": "buoy",
        'sounding': 111,
        'longitude': 111,
        'latitude': 111,
    },
    "platform_type": {
        "data_type": "adcp",
        "data_subtype": "SHIPBORNE",
        "source": "ship",
    },
    "source": {
        "source": "test_source"
    },
    'force_platform': {
            'sounding': 333,
            'longitude': 666,
            'latitude': 999,
    }
}


@pytest.mark.parametrize(
    "platform_type, source, force_platform_metadata, expected_key",
    [
        ("ship", None, False, "platform_type"),
        (None, "test_source", False, "source"),
        (None, None, True, "force_platform"),

    ],
)
def test_global_attributes(platform_type, source, force_platform_metadata, expected_key):
    pconfig = BaseProcessConfig(config_dict=CONFIG_DICT)
    pconfig.platform_metadata = DEFAULT_METADATA
    pconfig.platform_type = pconfig.platform_metadata.platform.platform_type
    
    if platform_type is not None:
        pconfig.platform_type = platform_type

    if source is not None:
        pconfig.global_attributes['source'] = source

    pconfig.force_platform_metadata = force_platform_metadata

    dataset = xr.Dataset()
    add_global_attributes(dataset, pconfig, STANDARD_GLOBAL_ATTRIBUTES)
    add_platform_metadata_to_dataset(dataset=dataset, pconfig=pconfig)

    global_attrs = {**EXPECTED_GLOBAL_ATTRIBUTES['standard']}
    global_attrs.update(EXPECTED_GLOBAL_ATTRIBUTES[expected_key])
    assert dataset.attrs == global_attrs
