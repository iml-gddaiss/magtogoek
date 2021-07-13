"""
module to map xarray dataset to Odf
"""
import xarray as xr
from magtogoek.odf_format import Odf

# Add a int suffix (_01) to parameter codes increasing with each new parameter of the same type.
# - dtype : sing or doub
# Missing Metadata are in the magtogoek/files/odf_parameter.json.
# - name
# - units
# - print_field_value
# - print_decimal_value
TIME_TYPE = "SYTM"
TIME_FILL_VALUE = "17-NOV-1858 00:00:00.00"

odf = Odf()


def _nc_to_odf_cruise_header(odf, dataset):
    """
    All in the cruise section
    """
    for key in odf.cruise:
        pass


A = dict(
    country_institue_code=0,
    cruise_number=0,
    cruise_name=0,
    organization=0,
    chief_scientist=0,
    start_date=0,
    end_date=0,
    envent_number=0,
)

B = dict(
    country_institute_code="",
    cruise_number="",
    organization="",
    chief_scientist="",
    start_date="",
    end_date="",
    platform="",
    cruise_name="",
    cruise_description="",
)
