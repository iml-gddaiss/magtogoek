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

GENERIC_PARAMETERS = [
    'time',
    'mean_wind_speed',
    'max_wind_speed',
    'mean_wind_direction',
    'max_wind_direction',
    'atm_temperature',
    'atm_humidity',
    'atm_pressure',
    'wave_mean_height',
    'wave_maximal_height',
    'wave_period',
    'wave_direction',
    'temperature',
    'conductivity',
    'salinity',
    'density',
    'dissolved_oxygen',
    'ph',
    'par',
    'fluorescence',
    'chlorophyll',
    'fdom',
    'co2_a',
    'co2_w',
    'u',
    'v',
    'w',
    'e',
    'pg',
    'pg1',
    'pg2',
    'pg3',
    'pg4',
    'corr1',
    'corr2',
    'corr3',
    'corr4',
    'amp1',
    'amp2',
    'amp3',
    'amp4',
    'bt_u',
    'bt_v',
    'bt_w',
    'bt_e',
    'lon',
    'lat',
    'heading',
    'roll_',
    'pitch',
    'roll_std',
    'pitch_std',
    'u_ship',
    'v_ship'
]