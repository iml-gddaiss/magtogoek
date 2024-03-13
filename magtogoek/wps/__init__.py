"""
WPS: Water Property Sensor

Sub-Package for Water Property Sensor processing: CTD, pH, oxygen, Nitrate, etc.

"""

SENSOR_TYPES =[
    'ct',  # Conductivity Temperature
    'ctd',  # Conductivity Temperature Depth
    'ctdo',  # Conductivity Temperature Depth Oxygen
    'doxy',  # only oxygen # RINKO maybe
    'nitrate', # e.g. SUNA
    'ph',  # pH
    'par',  # Photo-Active Radiation
    'eco',  # Eco-Triplet Chloro, FDOM Fluorescence
    'pco2',  # co2 water
]