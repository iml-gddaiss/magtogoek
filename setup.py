from setuptools import find_packages, setup

with open("README.md", "r") as f:
    long_description = f.read()
with open("version.txt", "r") as f:
    version = f.read()[:-1]


setup(
    name="magtogoek",
    version=version,
    author="JeromeJGuay,",
    author_email="jerome.guay@dfo-mpo.gc.ca",
    description="""
    This package aim to process ocean data from the different instruments.
    Magtogoek is the Algonquin name for the Saint-Lawrence River which mean
    'the path that walks.'""",
    long_description="",
    long_description_content_type="text/markdown",
    url="https://github.com/JeromeJGuay/magtogoek",
    install_requires=[
        "numpy",
        "xarray",
        "pandas",
        "datetime",
        "netCDF4",
        "scipy",
        "matplotlib",
        "typing",
        "nptyping",
        "click",
        "configparser",
        "tqdm",
        "path",
        "pynmea2",
        "obsub",
        "pygeodesy",
        "crc16",
    ],
    packages=find_packages(),
    package_data={"magtogoek": ["*.geojson"]},
    classifiers=["Programming Language :: Python :: 3"],
    python_requires="~=3.7",
    entry_points={
        "console_scripts": [
            "mtgk=magtogoek.app:magtogoek",
        ]
    },
)
