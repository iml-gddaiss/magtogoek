from magtogoek.platforms import load_platform_metadata

FILENAME = "files/iml_platforms.json"

def test_load_platform_metadata():
    load_platform_metadata(platform_file=FILENAME, platform_id="IML6_2017")
    assert True