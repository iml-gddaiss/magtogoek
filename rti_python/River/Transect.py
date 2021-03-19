

class Transect:

    VERSION = 1.0

    def __init__(self, index):

        self.transect_index = index
        self.site_name = ""
        #self.station_name = ""
        self.station_number = ""
        self.location = ""
        self.party = ""
        self.boat = ""
        self.measurement_number = ""
        self.comments = ""
        self.xdcr_depth = 0.0
        self.screening_distance = 0.0
        self.salinity = 0.0
        self.magnetic_declination = 0.0
        self.track_reference = ""
        self.depth_reference = ""
        self.coordinate_system = ""
        self.station_info = ""
        self.cross_section_loc = ""
        self.drafts = ""
        self.measured_water_temp = ""
        self.start_edge = ""
        self.rated_discharge = ""
        self.measurement_quality = ""
        self.auto_edge_profile = ""
        self.show_edge_dialog = True
        self.top_fit_type = ""
        self.top_use_cells = ""
        self.bottom_fit_type = ""
        self.bottom_use_cells = ""
        self.rated_discharge = 0.0
        self.measurement_quality = ""
        self.previous_set_time = None
        self.left_edge_shape = ""
        self.right_edge_shape = ""
        self.left_edge_distance = 0.0
        self.right_edge_distance = 0.0
        self.manual_speed_of_sound = 0.0
        self.transect_identification = ""
        self.time_of_day_start_transect = ""
        self.elasped_time = 0.0
        self.mean_vel_boat = 0.0
        self.mean_vel_water = 0.0
        self.total_width = 0.0
        self.sys_test_result = ""
        self.list_ens = []
        self.bottom_extrap = 0.0
        self.top_extrap = 0.0
        self.left_extrap = 0.0
        self.right_extrap = 0.0
        self.q_bottom = 0.0
        self.q_top = 0.0
        self.q_right = 0.0
        self.q_left = 0.0
        self.total_discharge = 0.0
        self.start_ens_index = 0
        self.stop_ens_index = 0
        self.start_datetime = None
        self.stop_datetime = None

    def get_name(self) -> str:
        return "Transect_" + str(self.transect_index)


