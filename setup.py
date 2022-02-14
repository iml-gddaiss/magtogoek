import os
from setuptools import find_packages, setup

from magtogoek.version import VERSION

def read_file(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="magtogoek",
    version=VERSION,
    author="JeromeJGuay,",
    author_email="jerome.guay@dfo-mpo.gc.ca",
    description="""Magtogoek is a Linux python package and command line application (CLI) for processing ocean data. At the moment, only Accoustisc Doopler Current Profiler (ADCP) data can be processed. This package is developped by the Scientific Advice, Information and Support Branch at the Fisheries and Ocean Canada Maurice-Lamontagne Institute.""",
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    url="https://github.com/JeromeJGuay/magtogoek",
    install_requires=[
        "pytest==6.2.3",
        "xarray==0.21.1",
        "matplotlib>=3.5.0",
        "scipy>=1.7.0",
        "numpy",
        "pandas",
        "netCDF4~=1.5.8",
        "pathlib~=1.0.1",
        "nptyping~=1.4.4",
        "datetime==4.3",
        "configparser==5.0.2",
        "pathlib==1.0.1",
        "click==7.1.2",
        "tqdm>=4.59.0",
        "pygeodesy==21.8.12",
        "gpxpy==1.4.2",
        "pynmea2==1.18.0",
        "cmocean~=2.0",
        "obsub==0.2",
        "crc16==0.1.1",
        "pyqt5",
        "pycurrents @ hg+https://currents.soest.hawaii.edu/hgstage/pycurrents",
    ],
    packages=find_packages(),
    package_data={"": ["*.json"], "magtogoek/test": ["files/*.*"]},
    include_package_data=True,
    classifiers=["Programming Language :: Python :: 3"],
    python_requires="~=3.8",
    entry_points={"console_scripts": ["mtgk=magtogoek.app:magtogoek", ]},
)
