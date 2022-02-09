from setuptools import find_packages, setup

from magtogoek.version import VERSION

with open("README.md", "r") as f:
    long_description = f.read()


setup(
    name="magtogoek",
    version=VERSION,
    author="JeromeJGuay,",
    author_email="jerome.guay@dfo-mpo.gc.ca",
    description="""Magtogoek is a Linux python package and command line application (CLI) for processing ocean data. At the moment, only Accoustisc Doopler Current Profiler (ADCP) data can be processed. This package is developped by the Scientific Advice, Information and Support Branch at the Fisheries and Ocean Canada Maurice-Lamontagne Institute.""",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/JeromeJGuay/magtogoek",
    install_requires=[
        "numpy >=1.20.0, <1.22.2",
        "xarray",
        "pandas",
        "dask",
        "back",
        "datetime",
        "netCDF4",
        "scipy",
        "matplotlib == 3.5",
        "typing",
        "nptyping",
        "click >=7, <8",
        "configparser >= 5.0.2 ",
        "tqdm",
        "pathlib",
        "pynmea2",
        "obsub",
        "pygeodesy",
        "crc16",
        "gpxpy",
        "cmocean",
        "pycurrents @ hg+https://currents.soest.hawaii.edu/hgstage/pycurrents",
    ],
    packages=find_packages(),
    package_data={"": ["*.json"], "magtogoek/test": ["files/*.*"]},
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
    python_requires="~=3.7",
    entry_points={"console_scripts": ["mtgk=magtogoek.app:magtogoek",]},
)
