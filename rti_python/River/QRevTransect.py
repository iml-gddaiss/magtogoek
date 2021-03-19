import json


class RTTtransect(object):
    """
    This to reproduce a MMTtransect object used in QRev.
    The MMTtransect is populated using an MMT file.
    This object is populated using the software or a file.
    """

    VERSION = 1.0

    def __init__(self):
        # Set if this transect is checked to be used or unchecked
        self.Checked = 1

        # List of all files in the transect
        # A transect can contain more than 1 file based on max file size
        """
        {
            'Path': '',             # Full filename of transect including path
            'File': '',             # Filename of transect
            'Number': 0,            # Transect number assigned
        }
        """
        self.Files = []

        # Create Note classes for each file associated with transect
        """
        {
            'NoteFileNo': 0,        # Transect number associated with the note
            'NoteDate': '',         # Date note was entered
            'NoteText': '',         # Text of note
        }
        """
        self.Notes = []

        self.field_config = {
            'Fixed_Commands': [],
            'Wizard_Commands': [],
            'User_Commands': [],
            'Fixed_Commands_RiverQ': [],
            'DS_Use_Process': 0,                # Use Depth Sounder In Processing
            'DS_Transducer_Depth': 0.0,
            'DS_Transducer_Offset': 0.0,
            'DS_Cor_Spd_Sound': 0,              # Depth Sounder Correct Speed of Sound
            'DS_Scale_Factor': 0.0,
            'Ext_Heading_Offset': 0.0,          # External Heading Configuration
            'Ext_Heading_Use': False,           # Use External Heading
            'GPS_Time_Delay': '',
            'Q_Top_Method': 0.0,                # Top Discharge Estimate
            'Q_Bottom_Method': 0.0,             # Bottom Discharge Estimate
            'Q_Power_Curve_Coeff': 0.0,         # Power Curve Coef
            'Q_Cut_Top_Bins': 0.0,              # Cut Top Bins
            'Q_Bins_Above_Sidelobe': 0.0,       # Cut Bins Above Sidelobe
            'Q_Left_Edge_Type': 0.0,            # River Left Edge Type
            'Q_Left_Edge_Coeff': 0.0,           # Left Edge Slope Coeff
            'Q_Right_Edge_Type': 0.0,           # River Right Edge Type
            'Q_Right_Edge_Coeff': 0.0,          # Right Edge Slope Coeff
            'Q_Shore_Pings_Avg': 0.0,           # Shore Pings Avg
            'Edge_Begin_Shore_Distance': 0.0,
            'Edge_Begin_Left_Bank': 1,
            'Edge_End_Shore_Distance': 0.0,
            'Offsets_Transducer_Depth': 0.0,
            'Offsets_Magnetic_Variation': 0.0,
            'Offsets_Heading_Offset': 0.0,
            'Offsets_One_Cycle_K': 0.0,
            'Offsets_One_Cycle_Offset': 0.0,
            'Offsets_Two_Cycle_K': 0.0,
            'Offsets_Two_Cycle_Offset': 0.0,
            'Proc_Speed_of_Sound_Correction': 0,
            'Proc_Salinity': 0.0,
            'Proc_Fixed_Speed_Of_Sound': 1500,
            'Proc_Mark_Below_Bottom_Bad': 1,
            'Proc_Mark_Below_Sidelobe_Bad': 1,
            'Proc_Screen_Depth': 0,
            'Proc_Screen_BT_Depth': 0,
            'Proc_Use_Weighted_Mean': 0,
            'Proc_Use_Weighted_Mean_Depth': 0,
            'Proc_Backscatter_Type': 0,
            'Proc_Intensity_Scale': 0.43,
            'Proc_Absorption': 0.139,
            'Proc_Projection_Angle': 0.0,
            'Proc_River_Depth_Source': 4,
            'Proc_Cross_Area_Type': 2,
            'Proc_Use_3_Beam_BT': 1,
            'Proc_Use_3_Beam_WT': 1,
            'Proc_BT_Error_Vel_Threshold': 0.1,
            'Proc_WT_Error_Velocity_Threshold': 10.0,
            'Proc_BT_Up_Vel_Threshold': 10.0,
            'Proc_WT_Up_Vel_Threshold': 10.0,
            'Proc_Fish_Intensity_Threshold': 255,
            'Proc_Near_Zone_Distance': 2.1,
            'Rec_Filename_Prefix': '',
            'Rec_Output_Directory': '',
            'Rec_Root_Directory': None,
            'Rec_MeasNmb': '',
            'Rec_GPS': 'NO',
            'Rec_DS': 'NO',
            'Rec_EH': 'NO',
            'Rec_ASCII_Output': 'NO',
            'Rec_Max_File_Size': 0.0,
            'Rec_Next_Transect_Number': 0.0,
            'Rec_Add_Date_Time': 0.0,
            'Rec_Use_Delimiter': 1,
            'Rec_Delimiter': '',
            'Rec_Prefix': '',
            'Rec_Use_MeasNmb': 'YES',
            'Rec_Use_TransectNmb': 'YES',
            'Rec_Use_SequenceNmb': 'NO',
            'Wiz_ADCP_Type': 0.0,
            'Wiz_Firmware': 0.0,
            'Wiz_Use_Ext_Heading': 'NO',
            'Wiz_Use_GPS': 'NO',
            'Wiz_Use_DS': 'NO',
            'Wiz_Max_Water_Depth': 0.0,
            'Wiz_Max_Water_Speed': 0.0,
            'Wiz_Max_Boat_Space': 0.0,
            'Wiz_Material': 0.0,
            'Wiz_Water_Mode': 0.0,
            'Wiz_Bottom_Mode': 0.0,
            'Wiz_Beam_Angle': 0.0,
            'Wiz_Pressure_Sensor': 0.0,
            'Wiz_Water_Mode_13': 0.0,
            'Wiz_StreamPro_Default': 0.0,
            'Wiz_StreamPro_Bin_Size': 0.0,
            'Wiz_StreamPro_Bin_Number': 0.0,
            'Wiz_Use_GPS_Internal': 'NO',
            'Wiz_Internal_GPS_Baud_Rate_Index': 0.0,
        }

        self.active_config = {
            'Fixed_Commands': [],
            'Wizard_Commands': [],
            'User_Commands': [],
            'Fixed_Commands_RiverQ': [],
            'DS_Use_Process': 0,                # Use Depth Sounder In Processing
            'DS_Transducer_Depth': 0.0,
            'DS_Transducer_Offset': 0.0,
            'DS_Cor_Spd_Sound': 0,              # Depth Sounder Correct Speed of Sound
            'DS_Scale_Factor': 0.0,
            'Ext_Heading_Offset': 0.0,          # External Heading Configuration
            'Ext_Heading_Use': False,           # Use External Heading
            'GPS_Time_Delay': '',
            'Q_Top_Method': 0.0,                # Top Discharge Estimate
            'Q_Bottom_Method': 0.0,             # Bottom Discharge Estimate
            'Q_Power_Curve_Coeff': 0.0,         # Power Curve Coef
            'Q_Cut_Top_Bins': 0.0,              # Cut Top Bins
            'Q_Bins_Above_Sidelobe': 0.0,       # Cut Bins Above Sidelobe
            'Q_Left_Edge_Type': 0.0,            # River Left Edge Type
            'Q_Left_Edge_Coeff': 0.0,           # Left Edge Slope Coeff
            'Q_Right_Edge_Type': 0.0,           # River Right Edge Type
            'Q_Right_Edge_Coeff': 0.0,          # Right Edge Slope Coeff
            'Q_Shore_Pings_Avg': 0.0,           # Shore Pings Avg
            'Edge_Begin_Shore_Distance': 0.0,
            'Edge_Begin_Left_Bank': 1,
            'Edge_End_Shore_Distance': 0.0,
            'Offsets_Transducer_Depth': 0.0,
            'Offsets_Magnetic_Variation': 0.0,
            'Offsets_Heading_Offset': 0.0,
            'Offsets_One_Cycle_K': 0.0,
            'Offsets_One_Cycle_Offset': 0.0,
            'Offsets_Two_Cycle_K': 0.0,
            'Offsets_Two_Cycle_Offset': 0.0,
            'Proc_Speed_of_Sound_Correction': 0,
            'Proc_Salinity': 0.0,
            'Proc_Fixed_Speed_Of_Sound': 1500,
            'Proc_Mark_Below_Bottom_Bad': 1,
            'Proc_Mark_Below_Sidelobe_Bad': 1,
            'Proc_Screen_Depth': 0,
            'Proc_Screen_BT_Depth': 0,
            'Proc_Use_Weighted_Mean': 0,
            'Proc_Use_Weighted_Mean_Depth': 0,
            'Proc_Backscatter_Type': 0,
            'Proc_Intensity_Scale': 0.43,
            'Proc_Absorption': 0.139,
            'Proc_Projection_Angle': 0.0,
            'Proc_River_Depth_Source': 4,
            'Proc_Cross_Area_Type': 2,
            'Proc_Use_3_Beam_BT': 1,
            'Proc_Use_3_Beam_WT': 1,
            'Proc_BT_Error_Vel_Threshold': 0.1,
            'Proc_WT_Error_Velocity_Threshold': 10.0,
            'Proc_BT_Up_Vel_Threshold': 10.0,
            'Proc_WT_Up_Vel_Threshold': 10.0,
            'Proc_Fish_Intensity_Threshold': 255,
            'Proc_Near_Zone_Distance': 2.1,
            'Rec_Filename_Prefix': '',
            'Rec_Output_Directory': '',
            'Rec_Root_Directory': None,
            'Rec_MeasNmb': '',
            'Rec_GPS': 'NO',
            'Rec_DS': 'NO',
            'Rec_EH': 'NO',
            'Rec_ASCII_Output': 'NO',
            'Rec_Max_File_Size': 0.0,
            'Rec_Next_Transect_Number': 0.0,
            'Rec_Add_Date_Time': 0.0,
            'Rec_Use_Delimiter': 1,
            'Rec_Delimiter': '',
            'Rec_Prefix': '',
            'Rec_Use_MeasNmb': 'YES',
            'Rec_Use_TransectNmb': 'YES',
            'Rec_Use_SequenceNmb': 'NO',
            'Wiz_ADCP_Type': 0.0,
            'Wiz_Firmware': 0.0,
            'Wiz_Use_Ext_Heading': 'NO',
            'Wiz_Use_GPS': 'NO',
            'Wiz_Use_DS': 'NO',
            'Wiz_Max_Water_Depth': 0.0,
            'Wiz_Max_Water_Speed': 0.0,
            'Wiz_Max_Boat_Space': 0.0,
            'Wiz_Material': 0.0,
            'Wiz_Water_Mode': 0.0,
            'Wiz_Bottom_Mode': 0.0,
            'Wiz_Beam_Angle': 0.0,
            'Wiz_Pressure_Sensor': 0.0,
            'Wiz_Water_Mode_13': 0.0,
            'Wiz_StreamPro_Default': 0.0,
            'Wiz_StreamPro_Bin_Size': 0.0,
            'Wiz_StreamPro_Bin_Number': 0.0,
            'Wiz_Use_GPS_Internal': 'NO',
            'Wiz_Internal_GPS_Baud_Rate_Index': 0.0,
        }

        self.moving_bed_type = None

    def add_transect_file(self, file_name: str):
        """
        Add transect files to the list.
        Each transect can contain more than 1 file, based on the file size limit, so the file names is a list.

        :param file_name for the transect.
        """
        # Create a transect dict
        #transect = {
        #    'Path': file_path,
        #    'File': file_name,
        #    'Number': index,
        #}

        # Add the transect to the file
        self.Files.append(file_name)

    def to_dict(self):
        """
        Convert this object to a dictionary.
        This is used to write the data to a
        JSON file.
        """
        transect_json = {
            "Checked": self.Checked,
            "Files": self.Files,
            "Notes": self.Notes,
            "field_config": self.field_config,
            "active_config": self.active_config,
            "moving_bed_type": self.moving_bed_type,
        }

        return transect_json

    def parse_config(self, json_dict):
        """
        Convert the JSON dictionary read from the
        JSON to create a Transect object
        """
        self.Checked = json_dict['Checked']
        self.Files = json_dict['Files']
        self.Notes = json_dict['Notes']
        self.field_config = json_dict['field_config']
        self.active_config = json_dict['active_config']
        self.moving_bed_type = json_dict['moving_bed_type']


"""
<Transect Type="5" Checked="1" Status="0" SelectAll="1" First="0" Last="0" Error="0">
    <File PathName="C:\RTI_Capture\imperial\Imperal Valley_20170816_095301\Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0" Type="6" TransectNmb="0">Imperal Valley_20170816_095301_0_1.2 MHz 4 beam 20 degree piston_pd0.pd0</File>
    <Configuration Type="7" Checked="0" Status="-1" Error="0">
       <Commands>
          <Fixed_Commands Status="-1">
             <Command_0>CR1</Command_0>
             <Command_1>CF11110</Command_1>
             <Command_2>BA30</Command_2>
             <Command_3>BC220</Command_3>
             <Command_4>BE100</Command_4>
             <Command_5>BP1</Command_5>
             <Command_6>BR2</Command_6>
             <Command_7>ES0</Command_7>
             <Command_8>EX10111</Command_8>
             <Command_9>TE00000000</Command_9>
             <Command_10>TP000020</Command_10>
             <Command_11>WA50</Command_11>
             <Command_12>WE1500</Command_12>
             <Command_13>WF50</Command_13>
             <Command_14>WM1</Command_14>
             <Command_15>WN50</Command_15>
             <Command_16>WP1</Command_16>
             <Command_17>WS50</Command_17>
             <Command_18>WV170</Command_18>
             <Command_19>WZ005</Command_19>
             <Command_20>&amp;R20</Command_20>
          </Fixed_Commands>
          <Fixed_Commands_StreamPro Status="-1">
             <Command_0>CR1</Command_0>
             <Command_1>TS</Command_1>
             <Command_2>WF3</Command_2>
             <Command_3>WN20</Command_3>
             <Command_4>WS10</Command_4>
             <Command_5>WM12</Command_5>
          </Fixed_Commands_StreamPro>
          <Wizard_Commands Status="-1" />
          <User_Commands Status="-1" />
          <Fixed_Commands_RiverRay Status="-1">
             <Command_0>CR1</Command_0>
          </Fixed_Commands_RiverRay>
          <Fixed_Commands_RiverPro Status="-1">
             <Command_0>CR1</Command_0>
          </Fixed_Commands_RiverPro>
          <Fixed_Commands_SentinelV_RT Status="-1">
             <Command_0>CR1</Command_0>
             <Command_1>TP000100</Command_1>
             <Command_2>WP1</Command_2>
             <Command_3>BP1</Command_3>
             <Command_4>EX00111</Command_4>
          </Fixed_Commands_SentinelV_RT>
       </Commands>
       <Depth_Sounder>
          <Depth_Sounder_Transducer_Depth Status="-1">0.000000</Depth_Sounder_Transducer_Depth>
          <Depth_Sounder_Transducer_Offset Status="-1">0.000000</Depth_Sounder_Transducer_Offset>
          <Depth_Sounder_Correct_Speed_of_Sound Status="-1">NO</Depth_Sounder_Correct_Speed_of_Sound>
          <Depth_Sounder_Scale_Factor Status="-1">1.000000</Depth_Sounder_Scale_Factor>
       </Depth_Sounder>
       <Ext_Heading>
          <Offset Status="-1">0.000000</Offset>
          <Use_Ext_Heading Status="-1">NO</Use_Ext_Heading>
       </Ext_Heading>
       <GPS>
          <Time_Delay Status="-1">0.000000</Time_Delay>
          <OffsetX Status="-1">0.000000</OffsetX>
          <OffsetY Status="-1">0.000000</OffsetY>
       </GPS>
       <Discharge>
          <Top_Discharge_Estimate Status="-1">0</Top_Discharge_Estimate>
          <Bottom_Discharge_Estimate Status="-1">0</Bottom_Discharge_Estimate>
          <Power_Curve_Coef Status="-1">0.166700</Power_Curve_Coef>
          <Cut_Top_Bins Status="-1">0</Cut_Top_Bins>
          <Cut_Bins_Above_Sidelobe Status="-1">0</Cut_Bins_Above_Sidelobe>
          <River_Left_Edge_Type Status="-1">0</River_Left_Edge_Type>
          <Left_Edge_Slope_Coeff Status="-1">0.500000</Left_Edge_Slope_Coeff>
          <River_Right_Edge_Type Status="-1">0</River_Right_Edge_Type>
          <Right_Edge_Slope_Coeff Status="-1">0.500000</Right_Edge_Slope_Coeff>
          <Shore_Pings_Avg Status="-1">10</Shore_Pings_Avg>
       </Discharge>
       <Edge_Estimates>
          <Begin_Shore_Distance Status="-1">0.000000</Begin_Shore_Distance>
          <Begin_Left_Bank Status="-1">YES</Begin_Left_Bank>
          <End_Shore_Distance Status="-1">0.000000</End_Shore_Distance>
       </Edge_Estimates>
       <Offsets>
          <ADCP_Transducer_Depth Status="-1">0.000000</ADCP_Transducer_Depth>
          <Magnetic_Variation Status="-1">0.000000</Magnetic_Variation>
          <Heading_Offset Status="-1">0.000000</Heading_Offset>
          <One_Cycle_K Status="-1">0.000000</One_Cycle_K>
          <One_Cycle_Offset Status="-1">0.000000</One_Cycle_Offset>
          <Two_Cycle_K Status="-1">0.000000</Two_Cycle_K>
          <Two_Cycle_Offset Status="-1">0.000000</Two_Cycle_Offset>
       </Offsets>
       <Processing>
          <Speed_of_Sound_Correction Status="-1">0</Speed_of_Sound_Correction>
          <Salinity Status="-1">0.000000</Salinity>
          <Fixed_Speed_Of_Sound Status="-1">1500</Fixed_Speed_Of_Sound>
          <Mark_Below_Botom_Bad Status="-1">YES</Mark_Below_Botom_Bad>
          <Mark_Below_Sidelobe_Bad Status="-1">YES</Mark_Below_Sidelobe_Bad>
          <Screen_Depth Status="-1">NO</Screen_Depth>
          <Screen_BT_Depth Status="-1">NO</Screen_BT_Depth>
          <Use_Weighted_Mean_Depth Status="-1">NO</Use_Weighted_Mean_Depth>
          <Backscatter_Type Status="-1">0</Backscatter_Type>
          <Intensity_Scale Status="-1">0.430000</Intensity_Scale>
          <Absorption Status="-1">0.139000</Absorption>
          <Projection_Angle Status="-1">0.000000</Projection_Angle>
          <River_Depth_Source Status="-1">4</River_Depth_Source>
          <Cross_Area_Type Status="-1">2</Cross_Area_Type>
          <Use_3_Beam_Solution_For_BT Status="-1">YES</Use_3_Beam_Solution_For_BT>
          <Use_3_Beam_Solution_For_WT Status="-1">YES</Use_3_Beam_Solution_For_WT>
          <BT_Error_Velocity_Threshold Status="-1">0.100000</BT_Error_Velocity_Threshold>
          <WT_Error_Velocity_Threshold Status="-1">10.000000</WT_Error_Velocity_Threshold>
          <BT_Up_Velocity_Threshold Status="-1">10.000000</BT_Up_Velocity_Threshold>
          <WT_Up_Velocity_Threshold Status="-1">10.000000</WT_Up_Velocity_Threshold>
          <Fish_Intensity_Threshold Status="-1">255</Fish_Intensity_Threshold>
          <Near_Zone_Distance Status="-1">2.100000</Near_Zone_Distance>
       </Processing>
       <Recording>
          <Filename_Prefix Status="-1">Imperal Valley</Filename_Prefix>
          <Output_Directory Status="-1">C:\RTI_Capture\imperial\Imperal Valley_20170816_095301</Output_Directory>
          <Root_Directory Status="-1" />
          <MeasurmentNmb />
          <GPS_Recording Status="-1">NO</GPS_Recording>
          <DS_Recording Status="-1">NO</DS_Recording>
          <EH_Recording Status="-1">NO</EH_Recording>
          <ASCII_Output_Recording Status="-1">NO</ASCII_Output_Recording>
          <Maximum_File_Size Status="-1">0</Maximum_File_Size>
          <Next_Transect_Number Status="-1">0</Next_Transect_Number>
          <Add_Date_Time Status="-1">0</Add_Date_Time>
          <Use_Delimiter Status="-1">1</Use_Delimiter>
          <Custom_Delimiter Status="-1">_</Custom_Delimiter>
          <Use_Prefix Status="-1">YES</Use_Prefix>
          <Use_MeasurementNmb Status="-1">YES</Use_MeasurementNmb>
          <Use_TransectNmb Status="-1">YES</Use_TransectNmb>
          <Use_SequenceNmb Status="-1">NO</Use_SequenceNmb>
          <Add_Lat_Long Status="-1">NO</Add_Lat_Long>
       </Recording>
       <Wizard_Info>
          <ADCP_Type>1</ADCP_Type>
          <ADCP_FW_Version>0.00</ADCP_FW_Version>
          <Use_Ext_Heading>NO</Use_Ext_Heading>
          <Use_VerticalBeam_Profile>NO</Use_VerticalBeam_Profile>
          <Use_Integrated_Heading>NO</Use_Integrated_Heading>
          <Use_GPS>NO</Use_GPS>
          <Use_GPS_Internal>NO</Use_GPS_Internal>
          <Internal_GPS_Baud_Rate_Index>4</Internal_GPS_Baud_Rate_Index>
          <Use_Depth_Sounder>NO</Use_Depth_Sounder>
          <Max_Water_Depth>5.000000</Max_Water_Depth>
          <Max_Water_Speed>0.500000</Max_Water_Speed>
          <Max_Boat_Speed>0.500000</Max_Boat_Speed>
          <Material>2</Material>
          <Water_Mode>0</Water_Mode>
          <Bottom_Mode>0</Bottom_Mode>
          <Beam_Angle>20</Beam_Angle>
          <Pressure_Sensor>NO</Pressure_Sensor>
          <Water_Mode_13_Avail>0</Water_Mode_13_Avail>
          <Use_StreamPro_Def_Cfg>1</Use_StreamPro_Def_Cfg>
          <StreamPro_Bin_Size>0.000000</StreamPro_Bin_Size>
          <StreamPro_Bin_Num>0</StreamPro_Bin_Num>
       </Wizard_Info>
       <DMFilter>
          <Enable_Error_Velocity_Filter>NO</Enable_Error_Velocity_Filter>
          <Error_Velocity_Multiplier>4.000000</Error_Velocity_Multiplier>
          <Enable_Depth_Filter>NO</Enable_Depth_Filter>
          <Depth_Filter_Width>20</Depth_Filter_Width>
          <Depth_Filter_Half_Width>10</Depth_Filter_Half_Width>
          <Depth_Filter_Multiplier>15.000000</Depth_Filter_Multiplier>
          <Depth_Filter_Cycles>3</Depth_Filter_Cycles>
          <Enable_Boat_Velocity_Filter>NO</Enable_Boat_Velocity_Filter>
          <Boat_Velocity_Filter_Width>10</Boat_Velocity_Filter_Width>
          <Boat_Velocity_Filter_Half_Width>10</Boat_Velocity_Filter_Half_Width>
          <Boat_Velocity_Filter_Multiplier>9.000000</Boat_Velocity_Filter_Multiplier>
          <Boat_Velocity_Filter_Cycles>3</Boat_Velocity_Filter_Cycles>
          <Enable_Filter_Expert_Mode>NO</Enable_Filter_Expert_Mode>
       </DMFilter>
    </Configuration>
    <Configuration Type="7" Checked="1" Status="0" Error="0">
       <Commands>
          <Fixed_Commands Status="-1">
             <Command_0>CR1</Command_0>
             <Command_1>CF11110</Command_1>
             <Command_2>BA30</Command_2>
             <Command_3>BC220</Command_3>
             <Command_4>BE100</Command_4>
             <Command_5>BP1</Command_5>
             <Command_6>BR2</Command_6>
             <Command_7>ES0</Command_7>
             <Command_8>EX10111</Command_8>
             <Command_9>TE00000000</Command_9>
             <Command_10>TP000020</Command_10>
             <Command_11>WA50</Command_11>
             <Command_12>WE1500</Command_12>
             <Command_13>WF50</Command_13>
             <Command_14>WM1</Command_14>
             <Command_15>WN50</Command_15>
             <Command_16>WP1</Command_16>
             <Command_17>WS50</Command_17>
             <Command_18>WV170</Command_18>
             <Command_19>WZ005</Command_19>
             <Command_20>&amp;R20</Command_20>
          </Fixed_Commands>
          <Fixed_Commands_StreamPro Status="-1">
             <Command_0>CR1</Command_0>
             <Command_1>TS</Command_1>
             <Command_2>WF3</Command_2>
             <Command_3>WN20</Command_3>
             <Command_4>WS10</Command_4>
             <Command_5>WM12</Command_5>
          </Fixed_Commands_StreamPro>
          <Wizard_Commands Status="-1" />
          <User_Commands Status="-1" />
          <Fixed_Commands_RiverRay Status="-1">
             <Command_0>CR1</Command_0>
          </Fixed_Commands_RiverRay>
          <Fixed_Commands_RiverPro Status="-1">
             <Command_0>CR1</Command_0>
          </Fixed_Commands_RiverPro>
          <Fixed_Commands_SentinelV_RT Status="-1">
             <Command_0>CR1</Command_0>
             <Command_1>TP000100</Command_1>
             <Command_2>WP1</Command_2>
             <Command_3>BP1</Command_3>
             <Command_4>EX00111</Command_4>
          </Fixed_Commands_SentinelV_RT>
       </Commands>
       <Depth_Sounder>
          <Depth_Sounder_Transducer_Depth Status="0">0.000000</Depth_Sounder_Transducer_Depth>
          <Depth_Sounder_Transducer_Offset Status="0">0.000000</Depth_Sounder_Transducer_Offset>
          <Depth_Sounder_Correct_Speed_of_Sound Status="0">NO</Depth_Sounder_Correct_Speed_of_Sound>
          <Depth_Sounder_Scale_Factor Status="0">1.000000</Depth_Sounder_Scale_Factor>
       </Depth_Sounder>
       <Ext_Heading>
          <Offset Status="0">0.000000</Offset>
          <Use_Ext_Heading Status="0">NO</Use_Ext_Heading>
       </Ext_Heading>
       <GPS>
          <Time_Delay Status="0">0.000000</Time_Delay>
          <OffsetX Status="0">0.000000</OffsetX>
          <OffsetY Status="0">0.000000</OffsetY>
       </GPS>
       <Discharge>
          <Top_Discharge_Estimate Status="0">0</Top_Discharge_Estimate>
          <Bottom_Discharge_Estimate Status="0">0</Bottom_Discharge_Estimate>
          <Power_Curve_Coef Status="0">0.166700</Power_Curve_Coef>
          <Cut_Top_Bins Status="0">0</Cut_Top_Bins>
          <Cut_Bins_Above_Sidelobe Status="0">0</Cut_Bins_Above_Sidelobe>
          <River_Left_Edge_Type Status="0">0</River_Left_Edge_Type>
          <Left_Edge_Slope_Coeff Status="0">0.500000</Left_Edge_Slope_Coeff>
          <River_Right_Edge_Type Status="0">0</River_Right_Edge_Type>
          <Right_Edge_Slope_Coeff Status="0">0.500000</Right_Edge_Slope_Coeff>
          <Shore_Pings_Avg Status="0">10</Shore_Pings_Avg>
       </Discharge>
       <Edge_Estimates>
          <Begin_Shore_Distance Status="0">0.000000</Begin_Shore_Distance>
          <Begin_Left_Bank Status="0">YES</Begin_Left_Bank>
          <End_Shore_Distance Status="0">0.000000</End_Shore_Distance>
       </Edge_Estimates>
       <Offsets>
          <ADCP_Transducer_Depth Status="0">0.000000</ADCP_Transducer_Depth>
          <Magnetic_Variation Status="0">0.000000</Magnetic_Variation>
          <Heading_Offset Status="0">0.000000</Heading_Offset>
          <One_Cycle_K Status="0">0.000000</One_Cycle_K>
          <One_Cycle_Offset Status="0">0.000000</One_Cycle_Offset>
          <Two_Cycle_K Status="0">0.000000</Two_Cycle_K>
          <Two_Cycle_Offset Status="0">0.000000</Two_Cycle_Offset>
       </Offsets>
       <Processing>
          <Speed_of_Sound_Correction Status="0">0</Speed_of_Sound_Correction>
          <Salinity Status="0">0.000000</Salinity>
          <Fixed_Speed_Of_Sound Status="0">1500</Fixed_Speed_Of_Sound>
          <Mark_Below_Botom_Bad Status="0">YES</Mark_Below_Botom_Bad>
          <Mark_Below_Sidelobe_Bad Status="0">YES</Mark_Below_Sidelobe_Bad>
          <Screen_Depth Status="0">NO</Screen_Depth>
          <Screen_BT_Depth Status="0">NO</Screen_BT_Depth>
          <Use_Weighted_Mean_Depth Status="0">NO</Use_Weighted_Mean_Depth>
          <Backscatter_Type Status="0">0</Backscatter_Type>
          <Intensity_Scale Status="0">0.430000</Intensity_Scale>
          <Absorption Status="0">0.139000</Absorption>
          <Projection_Angle Status="0">0.000000</Projection_Angle>
          <River_Depth_Source Status="0">4</River_Depth_Source>
          <Cross_Area_Type Status="0">2</Cross_Area_Type>
          <Use_3_Beam_Solution_For_BT Status="0">YES</Use_3_Beam_Solution_For_BT>
          <Use_3_Beam_Solution_For_WT Status="0">YES</Use_3_Beam_Solution_For_WT>
          <BT_Error_Velocity_Threshold Status="0">0.100000</BT_Error_Velocity_Threshold>
          <WT_Error_Velocity_Threshold Status="0">10.000000</WT_Error_Velocity_Threshold>
          <BT_Up_Velocity_Threshold Status="0">10.000000</BT_Up_Velocity_Threshold>
          <WT_Up_Velocity_Threshold Status="0">10.000000</WT_Up_Velocity_Threshold>
          <Fish_Intensity_Threshold Status="0">255</Fish_Intensity_Threshold>
          <Near_Zone_Distance Status="0">2.100000</Near_Zone_Distance>
       </Processing>
       <Recording>
          <Filename_Prefix Status="-1">Imperal Valley</Filename_Prefix>
          <Output_Directory Status="-1">C:\RTI_Capture\imperial\Imperal Valley_20170816_095301</Output_Directory>
          <Root_Directory Status="-1" />
          <MeasurmentNmb />
          <GPS_Recording Status="-1">NO</GPS_Recording>
          <DS_Recording Status="-1">NO</DS_Recording>
          <EH_Recording Status="-1">NO</EH_Recording>
          <ASCII_Output_Recording Status="0">NO</ASCII_Output_Recording>
          <Maximum_File_Size Status="-1">0</Maximum_File_Size>
          <Next_Transect_Number Status="-1">0</Next_Transect_Number>
          <Add_Date_Time Status="-1">0</Add_Date_Time>
          <Use_Delimiter Status="-1">1</Use_Delimiter>
          <Custom_Delimiter Status="-1">_</Custom_Delimiter>
          <Use_Prefix Status="-1">YES</Use_Prefix>
          <Use_MeasurementNmb Status="-1">YES</Use_MeasurementNmb>
          <Use_TransectNmb Status="-1">YES</Use_TransectNmb>
          <Use_SequenceNmb Status="-1">NO</Use_SequenceNmb>
          <Add_Lat_Long Status="-1">NO</Add_Lat_Long>
       </Recording>
       <Wizard_Info>
          <ADCP_Type>1</ADCP_Type>
          <ADCP_FW_Version>0.00</ADCP_FW_Version>
          <Use_Ext_Heading>NO</Use_Ext_Heading>
          <Use_VerticalBeam_Profile>NO</Use_VerticalBeam_Profile>
          <Use_Integrated_Heading>NO</Use_Integrated_Heading>
          <Use_GPS>NO</Use_GPS>
          <Use_GPS_Internal>NO</Use_GPS_Internal>
          <Internal_GPS_Baud_Rate_Index>4</Internal_GPS_Baud_Rate_Index>
          <Use_Depth_Sounder>NO</Use_Depth_Sounder>
          <Max_Water_Depth>5.000000</Max_Water_Depth>
          <Max_Water_Speed>0.500000</Max_Water_Speed>
          <Max_Boat_Speed>0.500000</Max_Boat_Speed>
          <Material>2</Material>
          <Water_Mode>0</Water_Mode>
          <Bottom_Mode>0</Bottom_Mode>
          <Beam_Angle>20</Beam_Angle>
          <Pressure_Sensor>NO</Pressure_Sensor>
          <Water_Mode_13_Avail>0</Water_Mode_13_Avail>
          <Use_StreamPro_Def_Cfg>1</Use_StreamPro_Def_Cfg>
          <StreamPro_Bin_Size>0.000000</StreamPro_Bin_Size>
          <StreamPro_Bin_Num>0</StreamPro_Bin_Num>
       </Wizard_Info>
       <DMFilter>
          <Enable_Error_Velocity_Filter>NO</Enable_Error_Velocity_Filter>
          <Error_Velocity_Multiplier>4.000000</Error_Velocity_Multiplier>
          <Enable_Depth_Filter>NO</Enable_Depth_Filter>
          <Depth_Filter_Width>20</Depth_Filter_Width>
          <Depth_Filter_Half_Width>10</Depth_Filter_Half_Width>
          <Depth_Filter_Multiplier>15.000000</Depth_Filter_Multiplier>
          <Depth_Filter_Cycles>3</Depth_Filter_Cycles>
          <Enable_Boat_Velocity_Filter>NO</Enable_Boat_Velocity_Filter>
          <Boat_Velocity_Filter_Width>10</Boat_Velocity_Filter_Width>
          <Boat_Velocity_Filter_Half_Width>10</Boat_Velocity_Filter_Half_Width>
          <Boat_Velocity_Filter_Multiplier>9.000000</Boat_Velocity_Filter_Multiplier>
          <Boat_Velocity_Filter_Cycles>3</Boat_Velocity_Filter_Cycles>
          <Enable_Filter_Expert_Mode>NO</Enable_Filter_Expert_Mode>
       </DMFilter>
    </Configuration>
    </Transect>

"""