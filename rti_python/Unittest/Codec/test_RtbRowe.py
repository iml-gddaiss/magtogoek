import pytest
from rti_python.Codecs.RtbRowe import RtbRowe


def test_count():
    file_path = r"RTI_20191101112241_00857.bin"
    count = RtbRowe.count_ensembles(file_path=file_path)
    assert count == 233

    file_path = r"B0000005.ens"
    count = RtbRowe.count_ensembles(file_path=file_path)
    assert count == 30

    file_path = r"B0000086_SUB.ENS"
    count = RtbRowe.count_ensembles(file_path=file_path)
    assert count == 238


def test_file_info():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path)
    ens_count, num_beams, num_bins = rowe.get_file_info(file_path=file_path)
    assert ens_count == 233
    assert num_beams == 4
    assert num_bins == 50

    file_path = r"B0000005.ens"
    rowe = RtbRowe(file_path=file_path)
    ens_count, num_beams, num_bins = rowe.get_file_info(file_path=file_path)
    assert ens_count == 30
    assert num_beams == 4
    assert num_bins == 80

    file_path = r"B0000086_SUB.ENS"
    rowe = RtbRowe(file_path=file_path)
    ens_count, num_beams, num_bins = rowe.get_file_info(file_path=file_path)
    assert ens_count == 251
    assert num_beams == 4
    assert num_bins == 20


def test_init():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path)
    assert len(rowe.Cfg.num_bins) == 233
    assert len(rowe.Cfg.num_beams) == 233
    assert len(rowe.Cfg.bt_lag_length) == 233
    assert len(rowe.Cfg.wp_nce) == 233
    assert len(rowe.Cfg.bt_actual_ping_count) == 233
    assert len(rowe.Cfg.wp_transmit_bandwidth) == 233
    assert len(rowe.Cfg.wp_system_freq_hz) == 233
    assert len(rowe.Cfg.wp_samples_per_second) == 233
    assert len(rowe.Cfg.wp_repeat_n) == 233
    assert len(rowe.Cfg.wp_receive_bandwidth) == 233
    assert len(rowe.Cfg.wp_lag_samples) == 233
    assert len(rowe.Cfg.wp_lag_length) == 233
    assert len(rowe.Cfg.wp_cpce) == 233
    assert len(rowe.Cfg.wp_broadband) == 233
    assert len(rowe.Cfg.wp_beam_mux) == 233
    assert len(rowe.Cfg.subsystem_config) == 233
    assert len(rowe.Cfg.subsystem_code) == 233
    assert len(rowe.Cfg.status) == 233
    assert len(rowe.Cfg.speed_of_sound) == 233
    assert len(rowe.Cfg.serial_num) == 233
    assert len(rowe.Cfg.second) == 233
    assert len(rowe.Cfg.salinity) == 233
    assert len(rowe.Cfg.month) == 233
    assert len(rowe.Cfg.minute) == 233
    assert len(rowe.Cfg.last_ping_time) == 233
    assert len(rowe.Cfg.hsec) == 233
    assert len(rowe.Cfg.hour) == 233
    assert len(rowe.Cfg.first_ping_time) == 233
    assert len(rowe.Cfg.firm_rev) == 233
    assert len(rowe.Cfg.firm_minor) == 233
    assert len(rowe.Cfg.firm_major) == 233
    assert len(rowe.Cfg.desired_ping_count) == 233
    assert len(rowe.Cfg.bt_system_freq_hz) == 233
    assert len(rowe.Cfg.bt_status) == 233
    assert len(rowe.Cfg.bt_speed_of_sound) == 233
    assert len(rowe.Cfg.bt_samples_per_second) == 233
    assert len(rowe.Cfg.bt_repeat_n) == 233
    assert len(rowe.Cfg.bt_num_beams) == 233
    assert len(rowe.Cfg.bt_nce) == 233
    assert len(rowe.Cfg.bt_narrowband) == 233
    assert len(rowe.Cfg.bt_last_ping_time) == 233
    assert len(rowe.Cfg.bt_first_ping_time) == 233
    assert len(rowe.Cfg.wp_nce) == 233
    assert len(rowe.Cfg.year) == 233
    assert len(rowe.Cfg.day) == 233
    assert len(rowe.Cfg.current_system) == 233
    assert len(rowe.Cfg.status_2) == 233
    assert len(rowe.Cfg.burst_index) == 233

    assert len(rowe.Sensor.heading) == 233
    assert len(rowe.Sensor.raw_mag_field_strength3) == 233
    assert len(rowe.Sensor.raw_mag_field_strength2) == 233
    assert len(rowe.Sensor.raw_mag_field_strength) == 233
    assert len(rowe.Sensor.vertical_gravity_vec) == 233
    assert len(rowe.Sensor.roll_gravity_vec) == 233
    assert len(rowe.Sensor.roll) == 233
    assert len(rowe.Sensor.pitch_gravity_vec) == 233
    assert len(rowe.Sensor.pitch) == 233
    assert len(rowe.Sensor.bt_salinity) == 233
    assert len(rowe.Sensor.bt_roll) == 233
    assert len(rowe.Sensor.bt_pitch) == 233
    assert len(rowe.Sensor.bt_heading) == 233
    assert len(rowe.Sensor.voltage) == 233
    assert len(rowe.Sensor.bt_transducer_depth) == 233
    assert len(rowe.Sensor.bt_pressure) == 233
    assert len(rowe.Sensor.transducer_depth) == 233
    assert len(rowe.Sensor.pressure) == 233
    assert len(rowe.Sensor.bt_water_temp) == 233
    assert len(rowe.Sensor.bt_system_temp) == 233
    assert len(rowe.Sensor.system_temp) == 233
    assert len(rowe.Sensor.water_temp) == 233
    assert len(rowe.Sensor.xmt_voltage) == 233
    assert len(rowe.Sensor.transmit_boost_neg_volt) == 233
    assert len(rowe.Sensor.hs1_temp) == 233
    assert len(rowe.Sensor.hs2_temp) == 233
    assert len(rowe.Sensor.rcv1_temp) == 233
    assert len(rowe.Sensor.rcv2_temp) == 233
    assert len(rowe.Sensor.vinf) == 233
    assert len(rowe.Sensor.vg) == 233
    assert len(rowe.Sensor.vt) == 233
    assert len(rowe.Sensor.vtl) == 233
    assert len(rowe.Sensor.d3v3) == 233
    assert len(rowe.Sensor.bt_hs1_temp) == 233
    assert len(rowe.Sensor.bt_hs2_temp) == 233
    assert len(rowe.Sensor.bt_rcv1_temp) == 233
    assert len(rowe.Sensor.bt_rcv2_temp) == 233
    assert len(rowe.Sensor.bt_vinf) == 233
    assert len(rowe.Sensor.bt_vg) == 233
    assert len(rowe.Sensor.bt_vt) == 233
    assert len(rowe.Sensor.bt_vtl) == 233
    assert len(rowe.Sensor.bt_d3v3) == 233
    assert len(rowe.Sensor.bt_sounder_range) == 233
    assert len(rowe.Sensor.bt_sounder_snr) == 233
    assert len(rowe.Sensor.bt_sounder_amp) == 233

    assert len(rowe.Rt.pings) == 0
    assert len(rowe.Rt.amp) == 0
    assert len(rowe.Rt.corr) == 0
    assert len(rowe.Rt.depth) == 0
    assert len(rowe.Rt.earth_vel) == 0
    assert len(rowe.Rt.instr_vel) == 0
    assert len(rowe.Rt.beam_vel) == 0
    assert len(rowe.Rt.snr) == 0

    assert len(rowe.Bt.depth) == 233               # NAN data
    assert len(rowe.Bt.snr) == 233
    assert len(rowe.Bt.beam_vel) == 233
    assert len(rowe.Bt.instr_vel) == 233
    assert len(rowe.Bt.earth_vel) == 233
    assert len(rowe.Bt.corr) == 233
    assert len(rowe.Bt.amp) == 233
    assert len(rowe.Bt.pulse_coh_corr) == 233
    assert len(rowe.Bt.pulse_coh_noise) == 233
    assert len(rowe.Bt.pulse_coh_vel) == 233
    assert len(rowe.Bt.pulse_coh_amp) == 233
    assert len(rowe.Bt.pulse_coh_snr) == 233
    assert len(rowe.Bt.earth_good) == 233
    assert len(rowe.Bt.instr_good) == 233
    assert len(rowe.Bt.beam_good) == 233

    assert len(rowe.GdE.pings) == 233
    assert len(rowe.GdB.pings) == 233
    assert len(rowe.Corr.corr) == 233
    assert len(rowe.Amp.amp) == 233
    assert len(rowe.EarthVel.vel) == 233
    assert len(rowe.InstrVel.vel) == 233
    assert len(rowe.BeamVel.vel) == 233

    assert len(rowe.Nmea.gga) == 233
    assert len(rowe.Nmea.heading) == 233
    assert len(rowe.Nmea.rel_true_north) == 233
    assert len(rowe.Nmea.hdt_header) == 233
    assert len(rowe.Nmea.alt_unit) == 233
    assert len(rowe.Nmea.hdt) == 233
    assert len(rowe.Nmea.mode_indicator) == 233
    assert len(rowe.Nmea.kph_indicator) == 233
    assert len(rowe.Nmea.speed_kph) == 233
    assert len(rowe.Nmea.knots_indicator) == 233
    assert len(rowe.Nmea.speed_knots) == 233
    assert len(rowe.Nmea.mag_indicator) == 233
    assert len(rowe.Nmea.course_mag) == 233
    assert len(rowe.Nmea.true_indicator) == 233
    assert len(rowe.Nmea.course_true) == 233
    assert len(rowe.Nmea.vtg_header) == 233
    assert len(rowe.Nmea.vtg) == 233
    assert len(rowe.Nmea.hdt_header) == 233
    assert len(rowe.Nmea.lat_ref) == 233
    assert len(rowe.Nmea.lon_ref) == 233
    assert len(rowe.Nmea.ref_stat_id) == 0
    assert len(rowe.Nmea.num_sats) == 233
    assert len(rowe.Nmea.lon_deg) == 233
    assert len(rowe.Nmea.dbt) == 233
    assert len(rowe.Nmea.gsa) == 233
    assert len(rowe.Nmea.corr_qual) == 233
    assert len(rowe.Nmea.geoid) == 233
    assert len(rowe.Nmea.geoid_unit) == 233
    assert len(rowe.Nmea.gga_delta_time) == 0
    assert len(rowe.Nmea.gga_header) == 233
    assert len(rowe.Nmea.hdop) == 233
    assert len(rowe.Nmea.lat_deg) == 233
    assert len(rowe.Nmea.utc) == 233
    assert len(rowe.Nmea.vtg_delta_time) == 0
    assert len(rowe.Nmea.alt) == 233

    assert len(rowe.AutoMode) == 0
    #assert len(rowe.Gps) == 0
    #assert len(rowe.Gps2) == 0
    #assert len(rowe.Surface) == 0
    #assert len(rowe.Wt) == 0


def test_init_1():
    file_path = r"B0000005.ens"
    rowe = RtbRowe(file_path=file_path)
    assert len(rowe.Cfg.num_bins) == 30
    assert len(rowe.Cfg.num_beams) == 30
    assert len(rowe.Cfg.bt_lag_length) == 30
    assert len(rowe.Cfg.wp_nce) == 30
    assert len(rowe.Cfg.bt_actual_ping_count) == 30
    assert len(rowe.Cfg.wp_transmit_bandwidth) == 30
    assert len(rowe.Cfg.wp_system_freq_hz) == 30
    assert len(rowe.Cfg.wp_samples_per_second) == 30
    assert len(rowe.Cfg.wp_repeat_n) == 30
    assert len(rowe.Cfg.wp_receive_bandwidth) == 30
    assert len(rowe.Cfg.wp_lag_samples) == 30
    assert len(rowe.Cfg.wp_lag_length) == 30
    assert len(rowe.Cfg.wp_cpce) == 30
    assert len(rowe.Cfg.wp_broadband) == 30
    assert len(rowe.Cfg.wp_beam_mux) == 30
    assert len(rowe.Cfg.subsystem_config) == 30
    assert len(rowe.Cfg.subsystem_code) == 30
    assert len(rowe.Cfg.status) == 30
    assert len(rowe.Cfg.speed_of_sound) == 30
    assert len(rowe.Cfg.serial_num) == 30
    assert len(rowe.Cfg.second) == 30
    assert len(rowe.Cfg.salinity) == 30
    assert len(rowe.Cfg.month) == 30
    assert len(rowe.Cfg.minute) == 30
    assert len(rowe.Cfg.last_ping_time) == 30
    assert len(rowe.Cfg.hsec) == 30
    assert len(rowe.Cfg.hour) == 30
    assert len(rowe.Cfg.first_ping_time) == 30
    assert len(rowe.Cfg.firm_rev) == 30
    assert len(rowe.Cfg.firm_minor) == 30
    assert len(rowe.Cfg.firm_major) == 30
    assert len(rowe.Cfg.desired_ping_count) == 30
    assert len(rowe.Cfg.bt_system_freq_hz) == 30
    assert len(rowe.Cfg.bt_status) == 30
    assert len(rowe.Cfg.bt_speed_of_sound) == 30
    assert len(rowe.Cfg.bt_samples_per_second) == 30
    assert len(rowe.Cfg.bt_repeat_n) == 30
    assert len(rowe.Cfg.bt_num_beams) == 30
    assert len(rowe.Cfg.bt_nce) == 30
    assert len(rowe.Cfg.bt_narrowband) == 30
    assert len(rowe.Cfg.bt_last_ping_time) == 30
    assert len(rowe.Cfg.bt_first_ping_time) == 30
    assert len(rowe.Cfg.wp_nce) == 30
    assert len(rowe.Cfg.year) == 30
    assert len(rowe.Cfg.day) == 30

    assert len(rowe.Sensor.heading) == 30
    assert len(rowe.Sensor.raw_mag_field_strength3) == 30
    assert len(rowe.Sensor.raw_mag_field_strength2) == 30
    assert len(rowe.Sensor.raw_mag_field_strength) == 30
    assert len(rowe.Sensor.vertical_gravity_vec) == 30
    assert len(rowe.Sensor.roll_gravity_vec) == 30
    assert len(rowe.Sensor.roll) == 30
    assert len(rowe.Sensor.pitch_gravity_vec) == 30
    assert len(rowe.Sensor.pitch) == 30
    assert len(rowe.Sensor.bt_salinity) == 30
    assert len(rowe.Sensor.bt_roll) == 30
    assert len(rowe.Sensor.bt_pitch) == 30
    assert len(rowe.Sensor.bt_heading) == 30
    assert len(rowe.Sensor.voltage) == 30
    assert len(rowe.Sensor.bt_transducer_depth) == 30
    assert len(rowe.Sensor.bt_pressure) == 30
    assert len(rowe.Sensor.transducer_depth) == 30
    assert len(rowe.Sensor.pressure) == 30
    assert len(rowe.Sensor.bt_water_temp) == 30
    assert len(rowe.Sensor.bt_system_temp) == 30
    assert len(rowe.Sensor.system_temp) == 30
    assert len(rowe.Sensor.water_temp) == 30
    assert len(rowe.Sensor.xmt_voltage) == 30
    assert len(rowe.Sensor.transmit_boost_neg_volt) == 30

    assert len(rowe.Rt.pings) == 30
    assert len(rowe.Rt.amp) == 30
    assert len(rowe.Rt.corr) == 30
    assert len(rowe.Rt.depth) == 30
    assert len(rowe.Rt.earth_vel) == 30
    assert len(rowe.Rt.instr_vel) == 30
    assert len(rowe.Rt.beam_vel) == 30
    assert len(rowe.Rt.snr) == 30

    assert len(rowe.Bt.depth) == 30               # NAN data
    assert len(rowe.Bt.snr) == 30
    assert len(rowe.Bt.beam_vel) == 30
    assert len(rowe.Bt.instr_vel) == 30
    assert len(rowe.Bt.earth_vel) == 30
    assert len(rowe.Bt.corr) == 30
    assert len(rowe.Bt.amp) == 30
    assert len(rowe.Bt.pulse_coh_corr) == 30
    assert len(rowe.Bt.pulse_coh_noise) == 30
    assert len(rowe.Bt.pulse_coh_vel) == 30
    assert len(rowe.Bt.pulse_coh_amp) == 30
    assert len(rowe.Bt.pulse_coh_snr) == 30
    assert len(rowe.Bt.earth_good) == 30
    assert len(rowe.Bt.instr_good) == 30
    assert len(rowe.Bt.beam_good) == 30

    assert len(rowe.GdE.pings) == 30
    assert len(rowe.GdB.pings) == 30
    assert len(rowe.Corr.corr) == 30
    assert len(rowe.Amp.amp) == 30
    assert len(rowe.EarthVel.vel) == 30
    assert len(rowe.InstrVel.vel) == 30
    assert len(rowe.BeamVel.vel) == 30

    assert len(rowe.Nmea.gga) == 0
    assert len(rowe.Nmea.heading) == 0
    assert len(rowe.Nmea.rel_true_north) == 0
    assert len(rowe.Nmea.hdt_header) == 0
    assert len(rowe.Nmea.alt_unit) == 0
    assert len(rowe.Nmea.hdt) == 0
    assert len(rowe.Nmea.mode_indicator) == 0
    assert len(rowe.Nmea.kph_indicator) == 0
    assert len(rowe.Nmea.speed_kph) == 0
    assert len(rowe.Nmea.knots_indicator) == 0
    assert len(rowe.Nmea.speed_knots) == 0
    assert len(rowe.Nmea.mag_indicator) == 0
    assert len(rowe.Nmea.course_mag) == 0
    assert len(rowe.Nmea.true_indicator) == 0
    assert len(rowe.Nmea.course_true) == 0
    assert len(rowe.Nmea.vtg_header) == 0
    assert len(rowe.Nmea.vtg) == 0
    assert len(rowe.Nmea.hdt_header) == 0
    assert len(rowe.Nmea.lat_ref) == 0
    assert len(rowe.Nmea.lon_ref) == 0
    assert len(rowe.Nmea.ref_stat_id) == 0
    assert len(rowe.Nmea.num_sats) == 0
    assert len(rowe.Nmea.lon_deg) == 0
    assert len(rowe.Nmea.dbt) == 0
    assert len(rowe.Nmea.gsa) == 0
    assert len(rowe.Nmea.corr_qual) == 0
    assert len(rowe.Nmea.geoid) == 0
    assert len(rowe.Nmea.geoid_unit) == 0
    assert len(rowe.Nmea.gga_delta_time) == 0
    assert len(rowe.Nmea.gga_header) == 0
    assert len(rowe.Nmea.hdop) == 0
    assert len(rowe.Nmea.lat_deg) == 0
    assert len(rowe.Nmea.utc) == 0
    assert len(rowe.Nmea.vtg_delta_time) == 0
    assert len(rowe.Nmea.alt) == 0

    assert len(rowe.AutoMode) == 0
    #assert len(rowe.Gps) == 0
    #assert len(rowe.Gps2) == 0
    #assert len(rowe.Surface) == 0
    #assert len(rowe.Wt) == 0


def test_init_2():
    file_path = r"B0000086_SUB.ENS"
    rowe = RtbRowe(file_path=file_path)
    assert len(rowe.Cfg) == 502
    assert len(rowe.Rt) == 502
    assert len(rowe.GdE) == 251
    assert len(rowe.Bt) == 502              # NAN data
    assert len(rowe.GdB) == 502
    assert len(rowe.Corr) == 502
    assert len(rowe.Amp) == 502
    assert len(rowe.EarthVel) == 251
    assert len(rowe.InstrVel) == 251
    assert len(rowe.BeamVel) == 502
    assert len(rowe.Sensor) == 502
    assert len(rowe.Nmea) == 0
    assert len(rowe.AutoMode) == 0
    assert len(rowe.Gps) == 0
    assert len(rowe.Gps2) == 0
    assert len(rowe.Surface) == 0
    assert len(rowe.Wt) == 0


def test_init_varying_bin():
    file_path = r"A0000004_varying_bin.ens"
    rowe = RtbRowe(file_path=file_path)
    assert len(rowe.Cfg.num_bins) == 267
    assert len(rowe.Cfg.num_beams) == 267
    assert len(rowe.Cfg.bt_lag_length) == 267
    assert len(rowe.Cfg.wp_nce) == 267
    assert len(rowe.Cfg.bt_actual_ping_count) == 267
    assert len(rowe.Cfg.wp_transmit_bandwidth) == 267
    assert len(rowe.Cfg.wp_system_freq_hz) == 267
    assert len(rowe.Cfg.wp_samples_per_second) == 267
    assert len(rowe.Cfg.wp_repeat_n) == 267
    assert len(rowe.Cfg.wp_receive_bandwidth) == 267
    assert len(rowe.Cfg.wp_lag_samples) == 267
    assert len(rowe.Cfg.wp_lag_length) == 267
    assert len(rowe.Cfg.wp_cpce) == 267
    assert len(rowe.Cfg.wp_broadband) == 267
    assert len(rowe.Cfg.wp_beam_mux) == 267
    assert len(rowe.Cfg.subsystem_config) == 267
    assert len(rowe.Cfg.subsystem_code) == 267
    assert len(rowe.Cfg.status) == 267
    assert len(rowe.Cfg.speed_of_sound) == 267
    assert len(rowe.Cfg.serial_num) == 267
    assert len(rowe.Cfg.second) == 267
    assert len(rowe.Cfg.salinity) == 267
    assert len(rowe.Cfg.month) == 267
    assert len(rowe.Cfg.minute) == 267
    assert len(rowe.Cfg.last_ping_time) == 267
    assert len(rowe.Cfg.hsec) == 267
    assert len(rowe.Cfg.hour) == 267
    assert len(rowe.Cfg.first_ping_time) == 267
    assert len(rowe.Cfg.firm_rev) == 267
    assert len(rowe.Cfg.firm_minor) == 267
    assert len(rowe.Cfg.firm_major) == 267
    assert len(rowe.Cfg.desired_ping_count) == 267
    assert len(rowe.Cfg.bt_system_freq_hz) == 267
    assert len(rowe.Cfg.bt_status) == 267
    assert len(rowe.Cfg.bt_speed_of_sound) == 267
    assert len(rowe.Cfg.bt_samples_per_second) == 267
    assert len(rowe.Cfg.bt_repeat_n) == 267
    assert len(rowe.Cfg.bt_num_beams) == 267
    assert len(rowe.Cfg.bt_nce) == 267
    assert len(rowe.Cfg.bt_narrowband) == 267
    assert len(rowe.Cfg.bt_last_ping_time) == 267
    assert len(rowe.Cfg.bt_first_ping_time) == 267
    assert len(rowe.Cfg.wp_nce) == 267
    assert len(rowe.Cfg.year) == 267
    assert len(rowe.Cfg.day) == 267
    assert len(rowe.Cfg.current_system) == 267
    assert len(rowe.Cfg.status_2) == 267
    assert len(rowe.Cfg.burst_index) == 267

    assert len(rowe.Sensor.heading) == 267
    assert len(rowe.Sensor.raw_mag_field_strength3) == 267
    assert len(rowe.Sensor.raw_mag_field_strength2) == 267
    assert len(rowe.Sensor.raw_mag_field_strength) == 267
    assert len(rowe.Sensor.vertical_gravity_vec) == 267
    assert len(rowe.Sensor.roll_gravity_vec) == 267
    assert len(rowe.Sensor.roll) == 267
    assert len(rowe.Sensor.pitch_gravity_vec) == 267
    assert len(rowe.Sensor.pitch) == 267
    assert len(rowe.Sensor.bt_salinity) == 267
    assert len(rowe.Sensor.bt_roll) == 267
    assert len(rowe.Sensor.bt_pitch) == 267
    assert len(rowe.Sensor.bt_heading) == 267
    assert len(rowe.Sensor.voltage) == 267
    assert len(rowe.Sensor.bt_transducer_depth) == 267
    assert len(rowe.Sensor.bt_pressure) == 267
    assert len(rowe.Sensor.transducer_depth) == 267
    assert len(rowe.Sensor.pressure) == 267
    assert len(rowe.Sensor.bt_water_temp) == 267
    assert len(rowe.Sensor.bt_system_temp) == 267
    assert len(rowe.Sensor.system_temp) == 267
    assert len(rowe.Sensor.water_temp) == 267
    assert len(rowe.Sensor.xmt_voltage) == 267
    assert len(rowe.Sensor.transmit_boost_neg_volt) == 267
    assert len(rowe.Sensor.hs1_temp) == 267
    assert len(rowe.Sensor.hs2_temp) == 267
    assert len(rowe.Sensor.rcv1_temp) == 267
    assert len(rowe.Sensor.rcv2_temp) == 267
    assert len(rowe.Sensor.vinf) == 267
    assert len(rowe.Sensor.vg) == 267
    assert len(rowe.Sensor.vt) == 267
    assert len(rowe.Sensor.vtl) == 267
    assert len(rowe.Sensor.d3v3) == 267
    assert len(rowe.Sensor.bt_hs1_temp) == 267
    assert len(rowe.Sensor.bt_hs2_temp) == 267
    assert len(rowe.Sensor.bt_rcv1_temp) == 267
    assert len(rowe.Sensor.bt_rcv2_temp) == 267
    assert len(rowe.Sensor.bt_vinf) == 267
    assert len(rowe.Sensor.bt_vg) == 267
    assert len(rowe.Sensor.bt_vt) == 267
    assert len(rowe.Sensor.bt_vtl) == 267
    assert len(rowe.Sensor.bt_d3v3) == 267
    assert len(rowe.Sensor.bt_sounder_range) == 267
    assert len(rowe.Sensor.bt_sounder_snr) == 267
    assert len(rowe.Sensor.bt_sounder_amp) == 267

    assert len(rowe.Rt.pings) == 0
    assert len(rowe.Rt.amp) == 0
    assert len(rowe.Rt.corr) == 0
    assert len(rowe.Rt.depth) == 0
    assert len(rowe.Rt.earth_vel) == 0
    assert len(rowe.Rt.instr_vel) == 0
    assert len(rowe.Rt.beam_vel) == 0
    assert len(rowe.Rt.snr) == 0

    assert len(rowe.Bt.depth) == 267               # NAN data
    assert len(rowe.Bt.snr) == 267
    assert len(rowe.Bt.beam_vel) == 267
    assert len(rowe.Bt.instr_vel) == 267
    assert len(rowe.Bt.earth_vel) == 267
    assert len(rowe.Bt.corr) == 267
    assert len(rowe.Bt.amp) == 267
    assert len(rowe.Bt.pulse_coh_corr) == 267
    assert len(rowe.Bt.pulse_coh_noise) == 267
    assert len(rowe.Bt.pulse_coh_vel) == 267
    assert len(rowe.Bt.pulse_coh_amp) == 267
    assert len(rowe.Bt.pulse_coh_snr) == 267
    assert len(rowe.Bt.earth_good) == 267
    assert len(rowe.Bt.instr_good) == 267
    assert len(rowe.Bt.beam_good) == 267

    assert len(rowe.GdE.pings) == 0
    assert len(rowe.GdB.pings) == 0

    assert len(rowe.Corr.corr) == 267
    assert len(rowe.Amp.amp) == 267
    assert len(rowe.EarthVel.vel) == 267
    assert len(rowe.InstrVel.vel) == 267
    assert len(rowe.BeamVel.vel) == 267

    assert len(rowe.Nmea.gga) == 267
    assert len(rowe.Nmea.heading) == 267
    assert len(rowe.Nmea.rel_true_north) == 267
    assert len(rowe.Nmea.hdt_header) == 267
    assert len(rowe.Nmea.alt_unit) == 267
    assert len(rowe.Nmea.hdt) == 267
    assert len(rowe.Nmea.mode_indicator) == 267
    assert len(rowe.Nmea.kph_indicator) == 267
    assert len(rowe.Nmea.speed_kph) == 267
    assert len(rowe.Nmea.knots_indicator) == 267
    assert len(rowe.Nmea.speed_knots) == 267
    assert len(rowe.Nmea.mag_indicator) == 267
    assert len(rowe.Nmea.course_mag) == 267
    assert len(rowe.Nmea.true_indicator) == 267
    assert len(rowe.Nmea.course_true) == 267
    assert len(rowe.Nmea.vtg_header) == 267
    assert len(rowe.Nmea.vtg) == 267
    assert len(rowe.Nmea.hdt_header) == 267
    assert len(rowe.Nmea.lat_ref) == 267
    assert len(rowe.Nmea.lon_ref) == 267
    assert len(rowe.Nmea.ref_stat_id) == 0
    assert len(rowe.Nmea.num_sats) == 267
    assert len(rowe.Nmea.lon_deg) == 267
    assert len(rowe.Nmea.dbt) == 267
    assert len(rowe.Nmea.gsa) == 267
    assert len(rowe.Nmea.corr_qual) == 267
    assert len(rowe.Nmea.geoid) == 267
    assert len(rowe.Nmea.geoid_unit) == 267
    assert len(rowe.Nmea.gga_delta_time) == 0
    assert len(rowe.Nmea.gga_header) == 267
    assert len(rowe.Nmea.hdop) == 267
    assert len(rowe.Nmea.lat_deg) == 267
    assert len(rowe.Nmea.utc) == 267
    assert len(rowe.Nmea.vtg_delta_time) == 0
    assert len(rowe.Nmea.alt) == 267

    assert len(rowe.AutoMode) == 0
    #assert len(rowe.Gps) == 0
    #assert len(rowe.Gps2) == 0
    #assert len(rowe.Surface) == 0
    #assert len(rowe.Wt) == 0

    assert len(rowe.River_BT.bt_noise_amp_fp) == 267
    assert len(rowe.River_BT.bt_corr) == 267
    assert len(rowe.River_BT.beam_n) == 267
    assert len(rowe.River_BT.vel) == 267
    assert len(rowe.River_BT.bt_amp) == 267
    assert len(rowe.River_BT.bt_noise_amp_bp) == 267
    assert len(rowe.River_BT.bt_snr) == 267
    assert len(rowe.River_BT.bt_range) == 267
    assert len(rowe.River_BT.system_freq_hz) == 267
    assert len(rowe.River_BT.samples_per_sec) == 267
    assert len(rowe.River_BT.speed_of_sound) == 267
    assert len(rowe.River_BT.depth) == 267
    assert len(rowe.River_BT.pressure) == 267
    assert len(rowe.River_BT.salinity) == 267
    assert len(rowe.River_BT.backplane_temp) == 267
    assert len(rowe.River_BT.water_temp) == 267
    assert len(rowe.River_BT.pitch) == 267
    assert len(rowe.River_BT.heading) == 267
    assert len(rowe.River_BT.ping_sec) == 267
    assert len(rowe.River_BT.beam_mux) == 267
    assert len(rowe.River_BT.cpce) == 267
    assert len(rowe.River_BT.repeats_n) == 267
    assert len(rowe.River_BT.beams) == 267
    assert len(rowe.River_BT.ping_count) == 267
    assert len(rowe.River_BT.num_subsystems) == 267
    assert len(rowe.River_BT.roll) == 267
    assert len(rowe.River_BT.status) == 267
    assert len(rowe.River_BT.bb) == 267
    assert len(rowe.River_BT.gp) == 267
    assert len(rowe.River_BT.gr) == 267
    assert len(rowe.River_BT.gz) == 267
    assert len(rowe.River_BT.ll) == 267
    assert len(rowe.River_BT.mx) == 267
    assert len(rowe.River_BT.my) == 267
    assert len(rowe.River_BT.mz) == 267
    assert len(rowe.River_BT.nb) == 267
    assert len(rowe.River_BT.nce) == 267
    assert len(rowe.River_BT.roll[-1]) == rowe.River_BT.num_subsystems[-1]


def test_pd0():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=True)
    assert len(rowe.Cfg) == 233
    assert len(rowe.Rt) == 0
    assert len(rowe.GdE) == 233
    assert len(rowe.Bt) == 233
    assert len(rowe.GdB) == 233
    assert len(rowe.Corr) == 233
    assert len(rowe.Amp) == 233
    assert len(rowe.EarthVel) == 233
    assert len(rowe.InstrVel) == 233
    assert len(rowe.BeamVel) == 233
    assert len(rowe.Sensor) == 233
    assert len(rowe.Nmea) == 233
    assert len(rowe.AutoMode) == 0
    assert len(rowe.Gps) == 0
    assert len(rowe.Gps2) == 0
    assert len(rowe.Surface) == 0
    assert len(rowe.Wt) == 0


def test_cfg():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path)
    assert rowe.Cfg[-1].ens_num == 267
    assert rowe.Cfg[-1].actual_ping_count == 1
    assert rowe.Cfg[-1].bin_size == 1.0
    assert rowe.Cfg[-1].blank == pytest.approx(1.5, 0.1)
    assert rowe.Cfg[-1].bt_actual_ping_count == 1
    assert rowe.Cfg[-1].bt_beam_mux == 2.0
    assert rowe.Cfg[-1].bt_broadband == 7.0
    assert rowe.Cfg[-1].bt_cpce == 10604
    assert rowe.Cfg[-1].bt_first_ping_time == 267
    assert rowe.Cfg[-1].bt_lag_length == 0.0
    assert rowe.Cfg[-1].bt_last_ping_time == 267
    assert rowe.Cfg[-1].bt_lag_length == 0.0
    assert rowe.Cfg[-1].bt_narrowband == 20
    assert rowe.Cfg[-1].bt_nce == 1.0
    assert rowe.Cfg[-1].bt_num_beams == 4
    assert rowe.Cfg[-1].bt_repeat_n == 1.0
    assert rowe.Cfg[-1].bt_samples_per_second == 96000
    assert rowe.Cfg[-1].bt_speed_of_sound == pytest.approx(1484.20, 0.1)
    assert rowe.Cfg[-1].bt_status == 16
    assert rowe.Cfg[-1].bt_system_freq_hz == 1152000
    assert rowe.Cfg[-1].day == 1
    assert rowe.Cfg[-1].desired_ping_count == 1
    assert rowe.Cfg[-1].firm_major == 0
    assert rowe.Cfg[-1].firm_minor == 2
    assert rowe.Cfg[-1].firm_rev == 133
    assert rowe.Cfg[-1].first_ping_time == pytest.approx(267.519, 0.001)
    assert rowe.Cfg[-1].hour == 11
    assert rowe.Cfg[-1].hsec == 0
    assert rowe.Cfg[-1].last_ping_time == pytest.approx(267.5199, 0.001)
    assert rowe.Cfg[-1].minute == 26
    assert rowe.Cfg[-1].month == 11
    assert rowe.Cfg[-1].num_beams == 4
    assert rowe.Cfg[-1].salinity == 0.0
    assert rowe.Cfg[-1].second == 26
    assert rowe.Cfg[-1].serial_num == '01200000000000000000000000000857'
    assert rowe.Cfg[-1].speed_of_sound == pytest.approx(1484.1315, 0.01)
    assert rowe.Cfg[-1].status == 0
    assert rowe.Cfg[-1].subsystem_code == '2'
    assert rowe.Cfg[-1].subsystem_config == 0
    assert rowe.Cfg[-1].wp_beam_mux == 2.0
    assert rowe.Cfg[-1].wp_broadband == 1.0
    assert rowe.Cfg[-1].wp_cpce == 12.0
    assert rowe.Cfg[-1].wp_lag_length == pytest.approx(0.20, 0.01)
    assert rowe.Cfg[-1].wp_lag_samples == 28
    assert rowe.Cfg[-1].wp_nce == 28
    assert rowe.Cfg[-1].wp_receive_bandwidth == 0.0
    assert rowe.Cfg[-1].wp_repeat_n == 5.0
    assert rowe.Cfg[-1].wp_samples_per_second == 96000
    assert rowe.Cfg[-1].wp_system_freq_hz == 1152000
    assert rowe.Cfg[-1].wp_transmit_bandwidth == 0.0
    assert rowe.Cfg[-1].year == 2019


def test_cfg_pd0():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=True)
    assert rowe.Cfg[-1].ens_num == 267
    assert rowe.Cfg[-1].actual_ping_count == 1
    assert rowe.Cfg[-1].bin_size == 1.0
    assert rowe.Cfg[-1].blank == pytest.approx(1.5, 0.1)
    assert rowe.Cfg[-1].bt_actual_ping_count == 1
    assert rowe.Cfg[-1].bt_beam_mux == 2.0
    assert rowe.Cfg[-1].bt_broadband == 7.0
    assert rowe.Cfg[-1].bt_cpce == 10604
    assert rowe.Cfg[-1].bt_first_ping_time == 267
    assert rowe.Cfg[-1].bt_lag_length == 0.0
    assert rowe.Cfg[-1].bt_last_ping_time == 267
    assert rowe.Cfg[-1].bt_lag_length == 0.0
    assert rowe.Cfg[-1].bt_narrowband == 20
    assert rowe.Cfg[-1].bt_nce == 1.0
    assert rowe.Cfg[-1].bt_num_beams == 4
    assert rowe.Cfg[-1].bt_repeat_n == 1.0
    assert rowe.Cfg[-1].bt_samples_per_second == 96000
    assert rowe.Cfg[-1].bt_speed_of_sound == pytest.approx(1484.20, 0.1)
    assert rowe.Cfg[-1].bt_status == 16
    assert rowe.Cfg[-1].bt_system_freq_hz == 1152000
    assert rowe.Cfg[-1].day == 1
    assert rowe.Cfg[-1].desired_ping_count == 1
    assert rowe.Cfg[-1].firm_major == 0
    assert rowe.Cfg[-1].firm_minor == 2
    assert rowe.Cfg[-1].firm_rev == 133
    assert rowe.Cfg[-1].first_ping_time == pytest.approx(267.519, 0.001)
    assert rowe.Cfg[-1].hour == 11
    assert rowe.Cfg[-1].hsec == 0
    assert rowe.Cfg[-1].last_ping_time == pytest.approx(267.5199, 0.001)
    assert rowe.Cfg[-1].minute == 26
    assert rowe.Cfg[-1].month == 11
    assert rowe.Cfg[-1].num_beams == 4
    assert rowe.Cfg[-1].salinity == 0.0
    assert rowe.Cfg[-1].second == 26
    assert rowe.Cfg[-1].serial_num == '01200000000000000000000000000857'
    assert rowe.Cfg[-1].speed_of_sound == pytest.approx(1484.1315, 0.01)
    assert rowe.Cfg[-1].status == 0
    assert rowe.Cfg[-1].subsystem_code == '2'
    assert rowe.Cfg[-1].subsystem_config == 0
    assert rowe.Cfg[-1].wp_beam_mux == 2.0
    assert rowe.Cfg[-1].wp_broadband == 1.0
    assert rowe.Cfg[-1].wp_cpce == 12.0
    assert rowe.Cfg[-1].wp_lag_length == pytest.approx(0.20, 0.01)
    assert rowe.Cfg[-1].wp_lag_samples == 28
    assert rowe.Cfg[-1].wp_nce == 28
    assert rowe.Cfg[-1].wp_receive_bandwidth == 0.0
    assert rowe.Cfg[-1].wp_repeat_n == 5.0
    assert rowe.Cfg[-1].wp_samples_per_second == 96000
    assert rowe.Cfg[-1].wp_system_freq_hz == 1152000
    assert rowe.Cfg[-1].wp_transmit_bandwidth == 0.0
    assert rowe.Cfg[-1].year == 19


def test_sensor():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=False)
    assert rowe.Sensor[-1].heading == pytest.approx(153.944, 0.01)
    assert rowe.Sensor[-1].pitch == pytest.approx(0.719, 0.01)
    assert rowe.Sensor[-1].roll == pytest.approx(-179.036, 0.001)
    assert rowe.Sensor[-1].water_temp == pytest.approx(20.819, 0.001)
    assert rowe.Sensor[-1].bt_water_temp == pytest.approx(20.843, 0.001)
    assert rowe.Sensor[-1].system_temp == pytest.approx(28.392, 0.001)
    assert rowe.Sensor[-1].bt_system_temp == pytest.approx(28.392, 0.001)
    assert rowe.Sensor[-1].pressure == pytest.approx(0.0, 0.001)
    assert rowe.Sensor[-1].transducer_depth == pytest.approx(0.0, 0.001)
    assert rowe.Sensor[-1].bt_pressure == pytest.approx(0.0, 0.001)
    assert rowe.Sensor[-1].bt_transducer_depth == pytest.approx(0.0, 0.001)
    assert rowe.Sensor[-1].voltage == pytest.approx(24.393, 0.001)
    assert rowe.Sensor[-1].xmt_voltage == pytest.approx(17.8573, 0.01)
    assert rowe.Sensor[-1].transmit_boost_neg_volt == pytest.approx(-18.044, 0.01)
    assert rowe.Sensor[-1].bt_heading == pytest.approx(150.721, 0.01)
    assert rowe.Sensor[-1].bt_pitch == pytest.approx(2.836, 0.01)
    assert rowe.Sensor[-1].bt_roll == pytest.approx(-179.222, 0.01)
    assert rowe.Sensor[-1].bt_salinity == pytest.approx(0.0, 0.01)
    assert rowe.Sensor[-1].raw_mag_field_strength == pytest.approx(-13.992, 0.01)
    assert rowe.Sensor[-1].raw_mag_field_strength2 == pytest.approx(6.1815, 0.01)
    assert rowe.Sensor[-1].raw_mag_field_strength3 == pytest.approx(-24.865, 0.01)
    assert rowe.Sensor[-1].pitch_gravity_vec == pytest.approx(-0.01237, 0.01)
    assert rowe.Sensor[-1].roll_gravity_vec == pytest.approx(-0.0165, 0.01)
    assert rowe.Sensor[-1].vertical_gravity_vec == pytest.approx(-0.9862, 0.01)


def test_sensor_pd0():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=True)
    assert rowe.Sensor[-1].heading == pytest.approx(153.944, 0.01)
    assert rowe.Sensor[-1].pitch == pytest.approx(0.719, 0.01)
    assert rowe.Sensor[-1].roll == pytest.approx(0.963, 0.001)
    assert rowe.Sensor[-1].water_temp == pytest.approx(20.819, 0.001)
    assert rowe.Sensor[-1].bt_water_temp == pytest.approx(20.843, 0.001)
    assert rowe.Sensor[-1].system_temp == pytest.approx(28.392, 0.001)
    assert rowe.Sensor[-1].bt_system_temp == pytest.approx(28.392, 0.001)
    assert rowe.Sensor[-1].pressure == pytest.approx(0.0, 0.001)
    assert rowe.Sensor[-1].transducer_depth == pytest.approx(0.0, 0.001)
    assert rowe.Sensor[-1].bt_pressure == pytest.approx(0.0, 0.001)
    assert rowe.Sensor[-1].bt_transducer_depth == pytest.approx(0.0, 0.001)
    assert rowe.Sensor[-1].voltage == pytest.approx(24.393, 0.001)
    assert rowe.Sensor[-1].xmt_voltage == pytest.approx(17.8573, 0.01)
    assert rowe.Sensor[-1].transmit_boost_neg_volt == pytest.approx(-18.044, 0.01)
    assert rowe.Sensor[-1].bt_heading == pytest.approx(150.721, 0.01)
    assert rowe.Sensor[-1].bt_pitch == pytest.approx(2.836, 0.01)
    assert rowe.Sensor[-1].bt_roll == pytest.approx(0.778, 0.01)
    assert rowe.Sensor[-1].bt_salinity == pytest.approx(0.0, 0.01)
    assert rowe.Sensor[-1].raw_mag_field_strength == pytest.approx(-13.992, 0.01)
    assert rowe.Sensor[-1].raw_mag_field_strength2 == pytest.approx(6.1815, 0.01)
    assert rowe.Sensor[-1].raw_mag_field_strength3 == pytest.approx(-24.865, 0.01)
    assert rowe.Sensor[-1].pitch_gravity_vec == pytest.approx(-0.01237, 0.01)
    assert rowe.Sensor[-1].roll_gravity_vec == pytest.approx(-0.0165, 0.01)
    assert rowe.Sensor[-1].vertical_gravity_vec == pytest.approx(-0.9862, 0.01)


def test_beam_vel():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=False)
    assert rowe.BeamVel[-1].vel[0][0] == pytest.approx(0.008, abs=0.001)
    assert rowe.BeamVel[-1].vel[1][0] == pytest.approx(-0.006, abs=0.001)
    assert rowe.BeamVel[-1].vel[2][0] == pytest.approx(-0.487, abs=0.001)
    assert rowe.BeamVel[-1].vel[3][0] == pytest.approx(0.481, abs=0.001)

    assert rowe.BeamVel[-1].vel[0][21] == pytest.approx(0.037, abs=0.001)
    assert rowe.BeamVel[-1].vel[1][21] == pytest.approx(88.888, 0.01)
    assert rowe.BeamVel[-1].vel[2][21] == pytest.approx(88.888, 0.01)
    assert rowe.BeamVel[-1].vel[3][21] == pytest.approx(88.888, 0.01)

    assert rowe.BeamVel[-1].vel[0][22] == pytest.approx(88.888, 0.01)
    assert rowe.BeamVel[-1].vel[1][22] == pytest.approx(88.888, 0.01)
    assert rowe.BeamVel[-1].vel[2][22] == pytest.approx(88.888, 0.01)
    assert rowe.BeamVel[-1].vel[3][22] == pytest.approx(88.888, 0.01)

    assert rowe.BeamVel[-1].vel[0][49] == pytest.approx(88.888, 0.01)
    assert rowe.BeamVel[-1].vel[1][49] == pytest.approx(88.888, 0.01)
    assert rowe.BeamVel[-1].vel[2][49] == pytest.approx(88.888, 0.01)
    assert rowe.BeamVel[-1].vel[3][49] == pytest.approx(88.888, 0.01)


def test_beam_vel_pd0():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=True)
    assert rowe.BeamVel[-1].vel[3][0] == round(0.008 * 1000.0)
    assert rowe.BeamVel[-1].vel[2][0] == round(-0.006 * 1000.0)
    assert rowe.BeamVel[-1].vel[0][0] == round(-0.487 * 1000.0)
    assert rowe.BeamVel[-1].vel[1][0] == round(0.481 * 1000.0)

    assert rowe.BeamVel[-1].vel[3][21] == round(0.037 * 1000.0)
    assert rowe.BeamVel[-1].vel[2][21] == -32768
    assert rowe.BeamVel[-1].vel[0][21] == -32768
    assert rowe.BeamVel[-1].vel[1][21] == -32768

    assert rowe.BeamVel[-1].vel[3][22] == -32768
    assert rowe.BeamVel[-1].vel[2][22] == -32768
    assert rowe.BeamVel[-1].vel[0][22] == -32768
    assert rowe.BeamVel[-1].vel[1][22] == -32768

    assert rowe.BeamVel[-1].vel[3][49] == -32768
    assert rowe.BeamVel[-1].vel[2][49] == -32768
    assert rowe.BeamVel[-1].vel[0][49] == -32768
    assert rowe.BeamVel[-1].vel[1][49] == -32768


def test_instrument_vel():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=False)
    assert rowe.InstrVel[-1].vel[0][0] == pytest.approx(-0.020, abs=0.001)
    assert rowe.InstrVel[-1].vel[1][0] == pytest.approx(1.416, abs=0.001)
    assert rowe.InstrVel[-1].vel[2][0] == pytest.approx(0.001, abs=0.001)
    assert rowe.InstrVel[-1].vel[3][0] == pytest.approx(0.002, abs=0.001)

    assert rowe.InstrVel[-1].vel[0][21] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[1][21] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[2][21] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[3][21] == pytest.approx(88.888, 0.01)

    assert rowe.InstrVel[-1].vel[0][22] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[1][22] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[2][22] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[3][22] == pytest.approx(88.888, 0.01)

    assert rowe.InstrVel[-1].vel[0][49] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[1][49] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[2][49] == pytest.approx(88.888, 0.01)
    assert rowe.InstrVel[-1].vel[3][49] == pytest.approx(88.888, 0.01)


def test_instrument_vel_pd0():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=True)
    assert rowe.InstrVel[-1].vel[1][0] == round(-0.020 * 1000.0)
    assert rowe.InstrVel[-1].vel[0][0] == round(1.416 * 1000.0)
    assert rowe.InstrVel[-1].vel[2][0] == round(0.001 * 1000.0) * -1
    assert rowe.InstrVel[-1].vel[3][0] == round(0.002 * 1000.0)

    assert rowe.InstrVel[-1].vel[1][21] == -32768
    assert rowe.InstrVel[-1].vel[0][21] == -32768
    assert rowe.InstrVel[-1].vel[2][21] == -32768
    assert rowe.InstrVel[-1].vel[3][21] == -32768

    assert rowe.InstrVel[-1].vel[1][22] == -32768
    assert rowe.InstrVel[-1].vel[0][22] == -32768
    assert rowe.InstrVel[-1].vel[2][22] == -32768
    assert rowe.InstrVel[-1].vel[3][22] == -32768

    assert rowe.InstrVel[-1].vel[1][49] == -32768
    assert rowe.InstrVel[-1].vel[0][49] == -32768
    assert rowe.InstrVel[-1].vel[2][49] == -32768
    assert rowe.InstrVel[-1].vel[3][49] == -32768


def test_earth_vel():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=False)
    assert rowe.EarthVel[-1].vel[0][0] == pytest.approx(-1.281, abs=0.001)
    assert rowe.EarthVel[-1].vel[1][0] == pytest.approx(-0.604, abs=0.001)
    assert rowe.EarthVel[-1].vel[2][0] == pytest.approx(-0.025, abs=0.001)
    assert rowe.EarthVel[-1].vel[3][0] == pytest.approx(0.002, abs=0.001)

    assert rowe.EarthVel[-1].vel[0][21] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[1][21] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[2][21] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[3][21] == pytest.approx(88.888, 0.01)

    assert rowe.EarthVel[-1].vel[0][22] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[1][22] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[2][22] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[3][22] == pytest.approx(88.888, 0.01)

    assert rowe.EarthVel[-1].vel[0][49] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[1][49] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[2][49] == pytest.approx(88.888, 0.01)
    assert rowe.EarthVel[-1].vel[3][49] == pytest.approx(88.888, 0.01)


def test_earth_vel_pd0():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=True)
    assert rowe.EarthVel[-1].vel[0][0] == round(-1.281 * 1000.0)
    assert rowe.EarthVel[-1].vel[1][0] == round(-0.604 * 1000.0)
    assert rowe.EarthVel[-1].vel[2][0] == round(-0.025 * 1000.0)
    assert rowe.EarthVel[-1].vel[3][0] == round(0.002 * 1000.0)

    assert rowe.EarthVel[-1].vel[0][21] == -32768
    assert rowe.EarthVel[-1].vel[1][21] == -32768
    assert rowe.EarthVel[-1].vel[2][21] == -32768
    assert rowe.EarthVel[-1].vel[3][21] == -32768

    assert rowe.EarthVel[-1].vel[0][22] == -32768
    assert rowe.EarthVel[-1].vel[1][22] == -32768
    assert rowe.EarthVel[-1].vel[2][22] == -32768
    assert rowe.EarthVel[-1].vel[3][22] == -32768

    assert rowe.EarthVel[-1].vel[0][49] == -32768
    assert rowe.EarthVel[-1].vel[1][49] == -32768
    assert rowe.EarthVel[-1].vel[2][49] == -32768
    assert rowe.EarthVel[-1].vel[3][49] == -32768


def test_bt():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=False)
    assert rowe.Bt[-1].range[0] == pytest.approx(21.828, abs=0.001)
    assert rowe.Bt[-1].range[1] == pytest.approx(20.695, abs=0.001)
    assert rowe.Bt[-1].range[2] == pytest.approx(21.828, abs=0.001)
    assert rowe.Bt[-1].range[3] == pytest.approx(20.695, abs=0.001)

    assert rowe.Bt[-1].beam_vel[0] == pytest.approx(0.058, abs=0.001)
    assert rowe.Bt[-1].beam_vel[1] == pytest.approx(-0.004, abs=0.001)
    assert rowe.Bt[-1].beam_vel[2] == pytest.approx(-0.419, abs=0.001)
    assert rowe.Bt[-1].beam_vel[3] == pytest.approx(0.485, abs=0.001)

    assert rowe.Bt[-1].instr_vel[0] == pytest.approx(0.091, abs=0.001)
    assert rowe.Bt[-1].instr_vel[1] == pytest.approx(-1.321, abs=0.001)
    assert rowe.Bt[-1].instr_vel[2] == pytest.approx(0.032, abs=0.001)
    assert rowe.Bt[-1].instr_vel[3] == pytest.approx(-0.003, abs=0.001)

    assert rowe.Bt[-1].earth_vel[0] == pytest.approx(1.208, abs=0.001)
    assert rowe.Bt[-1].earth_vel[1] == pytest.approx(0.543, abs=0.001)
    assert rowe.Bt[-1].earth_vel[2] == pytest.approx(-0.010, abs=0.001)
    assert rowe.Bt[-1].earth_vel[3] == pytest.approx(-0.003, abs=0.001)

    assert rowe.Bt[-1].snr[0] == pytest.approx(60.4, abs=0.1)
    assert rowe.Bt[-1].snr[1] == pytest.approx(52.9, abs=0.1)
    assert rowe.Bt[-1].snr[2] == pytest.approx(61.4, abs=0.1)
    assert rowe.Bt[-1].snr[3] == pytest.approx(61.9, abs=0.1)

    assert rowe.Bt[-1].amp[0] == pytest.approx(79.2, abs=0.1)
    assert rowe.Bt[-1].amp[1] == pytest.approx(70.0, abs=0.1)
    assert rowe.Bt[-1].amp[2] == pytest.approx(74.8, abs=0.1)
    assert rowe.Bt[-1].amp[3] == pytest.approx(79.5, abs=0.1)

    assert rowe.Bt[-1].corr[0] == pytest.approx(1.0, abs=0.1)
    assert rowe.Bt[-1].corr[1] == pytest.approx(1.0, abs=0.1)
    assert rowe.Bt[-1].corr[2] == pytest.approx(1.0, abs=0.1)
    assert rowe.Bt[-1].corr[3] == pytest.approx(1.0, abs=0.1)

    assert rowe.Bt[-1].beam_good[0] == 1
    assert rowe.Bt[-1].beam_good[1] == 1
    assert rowe.Bt[-1].beam_good[2] == 1
    assert rowe.Bt[-1].beam_good[3] == 1

    assert rowe.Bt[-1].instr_good[0] == 1
    assert rowe.Bt[-1].instr_good[1] == 1
    assert rowe.Bt[-1].instr_good[2] == 1
    assert rowe.Bt[-1].instr_good[3] == 1

    assert rowe.Bt[-1].earth_good[0] == 1
    assert rowe.Bt[-1].earth_good[1] == 1
    assert rowe.Bt[-1].earth_good[2] == 1
    assert rowe.Bt[-1].earth_good[3] == 1


def test_bt_pd0():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=True)
    assert rowe.Bt[-1].range[3] == round(21.828 * 100.0)
    assert rowe.Bt[-1].range[2] == round(20.695 * 100.0)
    assert rowe.Bt[-1].range[0] == round(21.828 * 100.0)
    assert rowe.Bt[-1].range[1] == round(20.695 * 100.0)

    assert rowe.Bt[-1].beam_vel[3] == round(0.058 * -1000.0)
    assert rowe.Bt[-1].beam_vel[2] == round(-0.004 * -1000.0)
    assert rowe.Bt[-1].beam_vel[0] == round(-0.419 * -1000.0)
    assert rowe.Bt[-1].beam_vel[1] == round(0.485 * -1000.0)

    assert rowe.Bt[-1].instr_vel[1] == round(0.091 * -1000.0)
    assert rowe.Bt[-1].instr_vel[0] == round(-1.321 * -1000.0)
    assert rowe.Bt[-1].instr_vel[2] == round(0.032 * 1000.0)
    assert rowe.Bt[-1].instr_vel[3] == round(-0.003 * -1000.0)

    assert rowe.Bt[-1].earth_vel[0] == round(1.208 * -1000.0)
    assert rowe.Bt[-1].earth_vel[1] == round(0.543 * -1000.0)
    assert rowe.Bt[-1].earth_vel[2] == round(-0.010 * -1000.0)
    assert rowe.Bt[-1].earth_vel[3] == round(-0.003 * -1000.0)

    assert rowe.Bt[-1].snr[3] == round(60.4 * 2.0)
    assert rowe.Bt[-1].snr[2] == round(52.9 * 2.0)
    assert rowe.Bt[-1].snr[0] == round(61.4 * 2.0)
    assert rowe.Bt[-1].snr[1] == round(61.9 * 2.0)

    assert rowe.Bt[-1].amp[3] == round(79.2 * 2.0)
    assert rowe.Bt[-1].amp[2] == round(70.0 * 2.0)
    assert rowe.Bt[-1].amp[0] == round(74.8 * 2.0)
    assert rowe.Bt[-1].amp[1] == round(79.5 * 2.0)

    assert rowe.Bt[-1].corr[3] == round(1.0 * 255)
    assert rowe.Bt[-1].corr[2] == round(1.0 * 255)
    assert rowe.Bt[-1].corr[0] == round(1.0 * 255)
    assert rowe.Bt[-1].corr[1] == round(1.0 * 255)

    assert rowe.Bt[-1].beam_good[3] == 1 * 100
    assert rowe.Bt[-1].beam_good[2] == 1 * 100
    assert rowe.Bt[-1].beam_good[0] == 1 * 100
    assert rowe.Bt[-1].beam_good[1] == 1 * 100

    assert rowe.Bt[-1].instr_good[1] == 1 * 100
    assert rowe.Bt[-1].instr_good[0] == 1 * 100
    assert rowe.Bt[-1].instr_good[2] == 1 * 100
    assert rowe.Bt[-1].instr_good[3] == 1 * 100

    assert rowe.Bt[-1].earth_good[0] == 1 * 100
    assert rowe.Bt[-1].earth_good[1] == 1 * 100
    assert rowe.Bt[-1].earth_good[2] == 1 * 100
    assert rowe.Bt[-1].earth_good[3] == 1 * 100


def test_rt():
    file_path = r"B0000086_SUB.ens"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=False)
    assert rowe.Rt[-2].range[0] == pytest.approx(1.645, abs=0.001)
    assert rowe.Rt[-2].range[1] == pytest.approx(2.221, abs=0.001)
    assert rowe.Rt[-2].range[2] == pytest.approx(1.727, abs=0.001)
    assert rowe.Rt[-2].range[3] == pytest.approx(2.102, abs=0.001)

    assert len(rowe.Rt[-1].range) == 1
    assert rowe.Rt[-1].range[0] == pytest.approx(1.617, abs=0.001)
    assert rowe.Rt[-1].snr[0] == pytest.approx(26.91, abs=0.01)
    assert rowe.Rt[-1].pings[0] == pytest.approx(1, abs=0.001)
    assert rowe.Rt[-1].amp[0] == pytest.approx(111.4, abs=0.1)
    assert rowe.Rt[-1].corr[0] == pytest.approx(1.00, abs=0.01)

    assert rowe.Rt[-2].beam_vel[0] == pytest.approx(-0.12, abs=0.01)
    assert rowe.Rt[-2].beam_vel[1] == pytest.approx(88.888, abs=0.001)
    assert rowe.Rt[-2].beam_vel[2] == pytest.approx(88.888, abs=0.001)
    assert rowe.Rt[-2].beam_vel[3] == pytest.approx(88.888, abs=0.001)

    assert rowe.Rt[-2].instr_vel[0] == pytest.approx(88.888, abs=0.001)
    assert rowe.Rt[-2].instr_vel[1] == pytest.approx(88.888, abs=0.001)
    assert rowe.Rt[-2].instr_vel[2] == pytest.approx(88.888, abs=0.001)
    assert rowe.Rt[-2].instr_vel[3] == pytest.approx(88.888, abs=0.001)

    assert rowe.Rt[-2].earth_vel[0] == pytest.approx(88.888, abs=0.001)
    assert rowe.Rt[-2].earth_vel[1] == pytest.approx(88.888, abs=0.001)
    assert rowe.Rt[-2].earth_vel[2] == pytest.approx(88.888, abs=0.001)
    assert rowe.Rt[-2].earth_vel[3] == pytest.approx(88.888, abs=0.001)

    assert rowe.Rt[-2].snr[0] == pytest.approx(32.01, abs=0.1)
    assert rowe.Rt[-2].snr[1] == pytest.approx(-189.35, abs=0.1)
    assert rowe.Rt[-2].snr[2] == pytest.approx(12.31, abs=0.1)
    assert rowe.Rt[-2].snr[3] == pytest.approx(-186.99, abs=0.1)

    assert rowe.Rt[-2].amp[0] == pytest.approx(81.6, abs=0.1)
    assert rowe.Rt[-2].amp[1] == pytest.approx(-14.0, abs=0.1)
    assert rowe.Rt[-2].amp[2] == pytest.approx(93.1, abs=0.1)
    assert rowe.Rt[-2].amp[3] == pytest.approx(-14.0, abs=0.1)

    assert rowe.Rt[-2].corr[0] == pytest.approx(0.97, abs=0.1)
    assert rowe.Rt[-2].corr[1] == pytest.approx(0.49, abs=0.1)
    assert rowe.Rt[-2].corr[2] == pytest.approx(0.96, abs=0.1)
    assert rowe.Rt[-2].corr[3] == pytest.approx(0.51, abs=0.1)

    assert rowe.Rt[-2].pings[0] == 1
    assert rowe.Rt[-2].pings[1] == 1
    assert rowe.Rt[-2].pings[2] == 1
    assert rowe.Rt[-2].pings[3] == 1


def test_nmea():
    file_path = r"RTI_20191101112241_00857.bin"
    rowe = RtbRowe(file_path=file_path, use_pd0_format=False)
    assert rowe.Nmea[-1].heading == pytest.approx(73.05, abs=0.01)
    assert rowe.Nmea[-1].speed_knots == pytest.approx(2.64, abs=0.01)
    assert rowe.Nmea[-1].speed_kph == pytest.approx(4.9, abs=0.01)
    assert rowe.Nmea[-1].lon_deg == pytest.approx(117.0986, abs=0.01)
    assert rowe.Nmea[-1].lat_deg == pytest.approx(32.915, abs=0.01)
    assert rowe.Nmea[-1].num_sats == pytest.approx(9.0, abs=0.01)
    assert rowe.Nmea[-1].rel_true_north == 'T'
    assert rowe.Nmea[-1].ref_stat_id == pytest.approx(0.0, abs=0.01)
    assert rowe.Nmea[-1].mag_indicator == 'M'
    assert rowe.Nmea[-1].lon_ref == 'W'
    assert rowe.Nmea[-1].lat_ref == 'N'
    assert rowe.Nmea[-1].mode_indicator == 'D'

