import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

version = "0.0.1"

setuptools.setup(
    name="magtogoek",
    version=version,
    author="JeromeJGuay,",
    author_email="jerome.guay@dfo-mpo.gc.ca",
    description="""
    This package aim to process ocean data from the different instruments.
    Magtogoek is the Algonquin name for the Saint-Lawrence River which mean
    'the path that walks.'""",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/JeromeJGuay/magtogoek",
    install_requires=[
        "numpy",
        "xarray",
        "pandas",
        # "datetime",
        #'gsw',
        "netCDF4",
        #'scipy',
        "matplotlib",
        #'shapely',
        "typing",
        "nptyping",
        "click",
    ],
    packages=setuptools.find_packages(),
    package_data={"Magtogoek": ["*.geojson"]},
    classifiers=["Programming Language :: Python :: 3"],
    python_requires="~=3.7",
    entry_points={
        "console_scripts": [
            "mtgk=magtogoek.bin.magtogoek_command:magtogoek",
            # "magtogoek_config_adcp=magtogoek.bin.config_command:magtogoek_config_adcp",
        ]
    },
)
