"""
Sub-Package for meteoce data processing.
"""
SENSOR_TYPES = [
    'co2a',  # co2 atm
    'wave',
    'meteo',  # atm_{humidity, temperature, pressure}
    'wind',
    'debit',  # water current. NOT LOADED as of feb 2023
    'vemco'  # Receptor for tags. NOT LOADED as of feb 2023
]