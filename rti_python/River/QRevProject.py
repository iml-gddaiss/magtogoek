import datetime
import os
import json
import logging
from rti_python.River.QRevTransect import RTTtransect


class RTTrowe(object):
    """
    Project file to hold all the configurations, settings and transect information
    for a River project.  The file is in JSON format.  The file extension is RTT
    (Rowe Technologies Transects).

    All the transect files will be stored in the same folder as the project
    file.
    """

    VERSION = 1.0
    FILE_EXTENSION = ".rtt"                         # Rowe Technologies Transects

    def __init__(self, project_name: str):
        # QRev Variables
        self.project = {
            'Name': project_name,
            'Version': RTTrowe.VERSION,
            'Locked': None,
        }

        # Site Information
        self.site_info = {
            'Agency': '',
            'Country': '',
            'State': '',
            'County': '',
            'District': '',
            'HydrologicUnit': '',
            'Party': '',
            'BoatMotorUsed': '',
            'ProcessedBy': '',
            'ADCPSerialNmb': '',
            'Description': '',
            'Grid_Reference': '',
            'Number': '',
            'Name': '',
            'River_Name': '',
            'Measurement_Date': datetime.datetime.now().strftime('%m/%d/%y'),
            'Rating_Number': 1,
            'Wind_Speed': '',
            'Wind_Direction': '',
            'Edge_Measurement_Method': '',
            'Magnetic_Var_Method': '',
            'Measurement_Rating': '',
            'ControlCode1': '',
            'ControlCode2': '',
            'ControlCode3': '',
            'MeasurementNmb': '',
            'Remarks': '',
            'TimeZone': '',
            'DeploymentType': 0,
            'Use_Inside_Gage_Height': 1,
            'Magnetic_Var_Method_Index': 0,
            'Measurement_Rating_Index': 0,
            'ControlCode1_Index': 0,
            'ControlCode2_Index': 0,
            'ControlCode3_Index': 0,
            'Inside_Gage_Height': 0.000000,
            'Outside_Gage_Height': 0.000000,
            'Gage_Height_Change': 0.000000,
            'Rating_Discharge': 0.000000,
            'Index_Velocity': 0.000000,
            'Rated_Area': 0.000000,
            'Water_Temperature': 0.0,
            'Tail_Water_Level': 0.000000,
            'Reference': 'BT',
            'Use_Old_Sidelobe_Method': 0,
        }

        # Transects
        self.transects = []

        # Moving Bed Transect Tests
        self.mbt_transects = []

        # Discharge Summary
        self.summary = {
            'NONE': {
                'Use': [],
                'Begin_Left': [],
                'FileName': [],
                'LeftEdgeSlopeCoeff': [],
                'RightEdgeSlopeCoeff': [],
                'IsSubSectioned': [],
                'TransectNmb': [],
                'TotalNmbEnsembles': [],
                'TotalBadEnsembles': [],
                'TotalLostEnsembles': [],
                'LargestGapInSecondsLostOrBad': [],
                'StartEnsemble': [],
                'EndEnsemble': [],
                'StartTime': [],
                'EndTime': [],
                'TotalQ': [],
                'TopQ': [],
                'MeasuredQ': [],
                'BottomQ': [],
                'LeftQ': [],
                'RightQ': [],
                'LeftDistance': [],
                'RightDistance': [],
                'Width': [],
                'TotalArea': [],
                'QperArea': [],
                'FlowDirection': [],
                'MaxWaterDepth': [],
                'MeanWaterDepth': [],
                'MaxWaterSpeed': [],
                'MeanRiverVel': [],
                'MeanBoatSpeed': [],
                'MeanBoatCourse': [],
                'PercentGoodBins': [],
                'STDPitch': [],
                'STDRoll': [],
                'MeanAbsPitch': [],
                'MeanAbsRoll': [],
                'MeanGoodLeftEdgeBins': [],
                'MeanGoodRightEdgeBins': [],
                'PowerCurveCoeff': [],
                'DepthRef': [],
                'ADCPTemperature': [],
                'BlankingDistance': [],
                'BinSize': [],
                'BTMode': [],
                'WTMode': [],
                'BTPings': [],
                'WTPings': [],
                'MinNmbSats': [],
                'MaxNmbSats': [],
                'MinHDOP': [],
                'MaxHDOP': [],
            },
            'BT': {
                'Use': [],
                'Begin_Left': [],
                'FileName': [],
                'LeftEdgeSlopeCoeff': [],
                'RightEdgeSlopeCoeff': [],
                'IsSubSectioned': [],
                'TransectNmb': [],
                'TotalNmbEnsembles': [],
                'TotalBadEnsembles': [],
                'TotalLostEnsembles': [],
                'LargestGapInSecondsLostOrBad': [],
                'StartEnsemble': [],
                'EndEnsemble': [],
                'StartTime': [],
                'EndTime': [],
                'TotalQ': [],
                'TopQ': [],
                'MeasuredQ': [],
                'BottomQ': [],
                'LeftQ': [],
                'RightQ': [],
                'LeftDistance': [],
                'RightDistance': [],
                'Width': [],
                'TotalArea': [],
                'QperArea': [],
                'FlowDirection': [],
                'MaxWaterDepth': [],
                'MeanWaterDepth': [],
                'MaxWaterSpeed': [],
                'MeanRiverVel': [],
                'MeanBoatSpeed': [],
                'MeanBoatCourse': [],
                'PercentGoodBins': [],
                'STDPitch': [],
                'STDRoll': [],
                'MeanAbsPitch': [],
                'MeanAbsRoll': [],
                'MeanGoodLeftEdgeBins': [],
                'MeanGoodRightEdgeBins': [],
                'PowerCurveCoeff': [],
                'DepthRef': [],
                'ADCPTemperature': [],
                'BlankingDistance': [],
                'BinSize': [],
                'BTMode': [],
                'WTMode': [],
                'BTPings': [],
                'WTPings': [],
                'MinNmbSats': [],
                'MaxNmbSats': [],
                'MinHDOP': [],
                'MaxHDOP': [],
            },
            'GGA': {
                'Use': [],
                'Begin_Left': [],
                'FileName': [],
                'LeftEdgeSlopeCoeff': [],
                'RightEdgeSlopeCoeff': [],
                'IsSubSectioned': [],
                'TransectNmb': [],
                'TotalNmbEnsembles': [],
                'TotalBadEnsembles': [],
                'TotalLostEnsembles': [],
                'LargestGapInSecondsLostOrBad': [],
                'StartEnsemble': [],
                'EndEnsemble': [],
                'StartTime': [],
                'EndTime': [],
                'TotalQ': [],
                'TopQ': [],
                'MeasuredQ': [],
                'BottomQ': [],
                'LeftQ': [],
                'RightQ': [],
                'LeftDistance': [],
                'RightDistance': [],
                'Width': [],
                'TotalArea': [],
                'QperArea': [],
                'FlowDirection': [],
                'MaxWaterDepth': [],
                'MeanWaterDepth': [],
                'MaxWaterSpeed': [],
                'MeanRiverVel': [],
                'MeanBoatSpeed': [],
                'MeanBoatCourse': [],
                'PercentGoodBins': [],
                'STDPitch': [],
                'STDRoll': [],
                'MeanAbsPitch': [],
                'MeanAbsRoll': [],
                'MeanGoodLeftEdgeBins': [],
                'MeanGoodRightEdgeBins': [],
                'PowerCurveCoeff': [],
                'DepthRef': [],
                'ADCPTemperature': [],
                'BlankingDistance': [],
                'BinSize': [],
                'BTMode': [],
                'WTMode': [],
                'BTPings': [],
                'WTPings': [],
                'MinNmbSats': [],
                'MaxNmbSats': [],
                'MinHDOP': [],
                'MaxHDOP': [],
            },
            'VTG': {
                'Use': [],
                'Begin_Left': [],
                'FileName': [],
                'LeftEdgeSlopeCoeff': [],
                'RightEdgeSlopeCoeff': [],
                'IsSubSectioned': [],
                'TransectNmb': [],
                'TotalNmbEnsembles': [],
                'TotalBadEnsembles': [],
                'TotalLostEnsembles': [],
                'LargestGapInSecondsLostOrBad': [],
                'StartEnsemble': [],
                'EndEnsemble': [],
                'StartTime': [],
                'EndTime': [],
                'TotalQ': [],
                'TopQ': [],
                'MeasuredQ': [],
                'BottomQ': [],
                'LeftQ': [],
                'RightQ': [],
                'LeftDistance': [],
                'RightDistance': [],
                'Width': [],
                'TotalArea': [],
                'QperArea': [],
                'FlowDirection': [],
                'MaxWaterDepth': [],
                'MeanWaterDepth': [],
                'MaxWaterSpeed': [],
                'MeanRiverVel': [],
                'MeanBoatSpeed': [],
                'MeanBoatCourse': [],
                'PercentGoodBins': [],
                'STDPitch': [],
                'STDRoll': [],
                'MeanAbsPitch': [],
                'MeanAbsRoll': [],
                'MeanGoodLeftEdgeBins': [],
                'MeanGoodRightEdgeBins': [],
                'PowerCurveCoeff': [],
                'DepthRef': [],
                'ADCPTemperature': [],
                'BlankingDistance': [],
                'BinSize': [],
                'BTMode': [],
                'WTMode': [],
                'BTPings': [],
                'WTPings': [],
                'MinNmbSats': [],
                'MaxNmbSats': [],
                'MinHDOP': [],
                'MaxHDOP': [],
            }
        }

        # QA_QC
        self.qaqc = {}

        # Folder Path for the project and all the transect files
        self.path = None

    def add_transect(self, transect: RTTtransect):
        """
        Add a transect to the project.
        :param transect Transect object.
        """
        self.transects.append(transect)

    def transect_to_json(self):
        """
        Convert the list of transects to a dictionary
        so the data can be stored in the JSON file.
        """
        transect_json_list = []
        for transect in self.transects:
            transect_json_list.append(transect.to_dict())

        return transect_json_list

    def write_json_file(self):
        """
        Export the data to a JSON file.
        This will create a top level RTI, then put all the
        dictionaries in to the top level.

        :return The file path to file created.
        """
        file_path = os.path.join(self.path, self.project["Name"] + RTTrowe.FILE_EXTENSION)
        project_dict = {
            'RTI': {
                'project': self.project,
                'site_info': self.site_info,
                'transects': self.transect_to_json(),
                'summary': self.summary,
                'qaqc': self.qaqc,
            }
        }

        # Create the project path
        if not os.path.exists(self.path):
            os.mkdir(self.path)

        # Create a project file
        with open(file_path, 'w') as outfile:
            json_object = json.dumps(project_dict, indent=4)
            outfile.write(json_object)
            logging.info(json_object)

        return file_path

    def parse_project(self, file_path: str):
        """
        Read in the project file.  The project is a JSON file.
        Read and populate all the dictionaries with the values.
        :param file_path File path to the project file.
        """

        if os.path.exists(file_path):

            # Set just the folder path for the project
            self.path = os.path.dirname(file_path)

            with open(file_path) as infile:
                # Read in the JSON data
                project_json = json.load(infile)

                # Store the JSON data
                self.project = project_json['RTI']['project']
                self.site_info = project_json['RTI']['site_info']
                self.summary = project_json['RTI']['summary']
                self.qaqc = project_json['RTI']['qaqc']

                # Add all the transects
                for json_transect in project_json['RTI']['transects']:
                    transect = RTTtransect()
                    transect.parse_config(json_transect)
                    self.transects.append(transect)


"""
TRDI MMT File Format


<?xml version="1.0" encoding="UTF-8"?>
<WinRiver>
   <Project Name="imperal valley_20170816_095301_0_1.2 mhz 4 beam 20 degree piston_pd0.mmt" Version="2.20.0000.0000" Flags="0">
      <Locked>False</Locked>
      <Site_Information Type="1" Checked="1" Status="0" Error="0">
         <Agency />
         <Country />
         <State />
         <County />
         <District />
         <HydrologicUnit />
         <Party />
         <BoatMotorUsed />
         <ProcessedBy />
         <ADCPSerialNmb />
         <Description />
         <Grid_Reference />
         <Number />
         <Name />
         <River_Name />
         <Measurement_Date>08/16/2017</Measurement_Date>
         <Rating_Number>1</Rating_Number>
         <Wind_Speed />
         <Wind_Direction />
         <Edge_Measurement_Method />
         <Magnetic_Var_Method />
         <Measurement_Rating />
         <ControlCode1 />
         <ControlCode2 />
         <ControlCode3 />
         <MeasurementNmb />
         <Remarks />
         <TimeZone />
         <DeploymentType>0</DeploymentType>
         <Use_Inside_Gage_Height>1</Use_Inside_Gage_Height>
         <Magnetic_Var_Method_Index>0</Magnetic_Var_Method_Index>
         <Measurement_Rating_Index>0</Measurement_Rating_Index>
         <ControlCode1_Index>0</ControlCode1_Index>
         <ControlCode2_Index>0</ControlCode2_Index>
         <ControlCode3_Index>0</ControlCode3_Index>
         <Inside_Gage_Height>0.000000</Inside_Gage_Height>
         <Outside_Gage_Height>0.000000</Outside_Gage_Height>
         <Gage_Height_Change>0.000000</Gage_Height_Change>
         <Rating_Discharge>0.000000</Rating_Discharge>
         <Index_Velocity>0.000000</Index_Velocity>
         <Rated_Area>0.000000</Rated_Area>
         <Water_Temperature>-32768.000000</Water_Temperature>
         <Tail_Water_Level>0.000000</Tail_Water_Level>
         <Reference>BT</Reference>
         <Use_Old_Sidelobe_Method>0</Use_Old_Sidelobe_Method>
      </Site_Information>
      <Site_Discharge Type="2" Checked="1" Status="0" Error="0">
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
         <Discharge_Summary>
            <None>
               <Index_0>
                  <UseInSummary>1</UseInSummary>
                  <BeginLeft>1</BeginLeft>
                  <IsSubSectioned>0</IsSubSectioned>
                  <FileName>Imperal Valley000</FileName>
                  <TransectNmb>000</TransectNmb>
                  <TotalNmbEnsembles>1766</TotalNmbEnsembles>
                  <TotalBadEnsembles>127</TotalBadEnsembles>
                  <TotalLostEnsembles>5</TotalLostEnsembles>
                  <LargestGapInSecondsLostOrBad>15.000000</LargestGapInSecondsLostOrBad>
                  <StartEnsemble>738</StartEnsemble>
                  <EndEnsemble>2508</EndEnsemble>
                  <StartTime>1502877188.000000</StartTime>
                  <EndTime>1502878958.000000</EndTime>
                  <TotalQ>25.652</TotalQ>
                  <TopQ>7.020</TopQ>
                  <MeasuredQ>14.232</MeasuredQ>
                  <BottomQ>4.400</BottomQ>
                  <LeftQ>0.000</LeftQ>
                  <RightQ>0.000</RightQ>
                  <LeftDistance>0.000</LeftDistance>
                  <RightDistance>0.000</RightDistance>
                  <Width>18.903</Width>
                  <TotalArea>39.871</TotalArea>
                  <QperArea>0.643</QperArea>
                  <FlowDirection>263.562</FlowDirection>
                  <MaxWaterDepth>2.310</MaxWaterDepth>
                  <MeanWaterDepth>2.059</MeanWaterDepth>
                  <MaxWaterSpeed>2.467</MaxWaterSpeed>
                  <MeanRiverVel>0.683</MeanRiverVel>
                  <MeanBoatSpeed>0.055</MeanBoatSpeed>
                  <MeanBoatCourse>14.641</MeanBoatCourse>
                  <PercentGoodBins>82.740</PercentGoodBins>
                  <STDPitch>0.225</STDPitch>
                  <STDRoll>0.186</STDRoll>
                  <MeanAbsPitch>0.188</MeanAbsPitch>
                  <MeanAbsRoll>0.159</MeanAbsRoll>
                  <MeanGoodLeftEdgeBins>1.000</MeanGoodLeftEdgeBins>
                  <MeanGoodRightEdgeBins>1.800</MeanGoodRightEdgeBins>
                  <PowerCurveCoeff>0.167</PowerCurveCoeff>
                  <LeftEdgeSlopeCoeff>0.353</LeftEdgeSlopeCoeff>
                  <RightEdgeSlopeCoeff>0.353</RightEdgeSlopeCoeff>
                  <DepthRef>4</DepthRef>
                  <ADCPTemperature>28.62</ADCPTemperature>
                  <BlankingDistance>0.00</BlankingDistance>
                  <BinSize>0.20</BinSize>
                  <BTMode>0</BTMode>
                  <WTMode>0</WTMode>
                  <BTPings>1</BTPings>
                  <WTPings>2</WTPings>
                  <MinNmbSats>0</MinNmbSats>
                  <MaxNmbSats>0</MaxNmbSats>
                  <MinHDOP>0.000000</MinHDOP>
                  <MaxHDOP>0.000000</MaxHDOP>
               </Index_0>
            </None>
            <BottomTrack>
               <Index_0>
                  <UseInSummary>1</UseInSummary>
                  <BeginLeft>1</BeginLeft>
                  <IsSubSectioned>0</IsSubSectioned>
                  <FileName>Imperal Valley000</FileName>
                  <TransectNmb>000</TransectNmb>
                  <TotalNmbEnsembles>1766</TotalNmbEnsembles>
                  <TotalBadEnsembles>127</TotalBadEnsembles>
                  <TotalLostEnsembles>5</TotalLostEnsembles>
                  <LargestGapInSecondsLostOrBad>15.000000</LargestGapInSecondsLostOrBad>
                  <StartEnsemble>738</StartEnsemble>
                  <EndEnsemble>2508</EndEnsemble>
                  <StartTime>1502877188.000000</StartTime>
                  <EndTime>1502878958.000000</EndTime>
                  <TotalQ>25.652</TotalQ>
                  <TopQ>7.020</TopQ>
                  <MeasuredQ>14.232</MeasuredQ>
                  <BottomQ>4.400</BottomQ>
                  <LeftQ>0.000</LeftQ>
                  <RightQ>0.000</RightQ>
                  <LeftDistance>0.000</LeftDistance>
                  <RightDistance>0.000</RightDistance>
                  <Width>18.903</Width>
                  <TotalArea>39.871</TotalArea>
                  <QperArea>0.643</QperArea>
                  <FlowDirection>263.562</FlowDirection>
                  <MaxWaterDepth>2.310</MaxWaterDepth>
                  <MeanWaterDepth>2.059</MeanWaterDepth>
                  <MaxWaterSpeed>2.467</MaxWaterSpeed>
                  <MeanRiverVel>0.683</MeanRiverVel>
                  <MeanBoatSpeed>0.055</MeanBoatSpeed>
                  <MeanBoatCourse>14.641</MeanBoatCourse>
                  <PercentGoodBins>82.740</PercentGoodBins>
                  <STDPitch>0.225</STDPitch>
                  <STDRoll>0.186</STDRoll>
                  <MeanAbsPitch>0.188</MeanAbsPitch>
                  <MeanAbsRoll>0.159</MeanAbsRoll>
                  <MeanGoodLeftEdgeBins>1.000</MeanGoodLeftEdgeBins>
                  <MeanGoodRightEdgeBins>1.800</MeanGoodRightEdgeBins>
                  <PowerCurveCoeff>0.167</PowerCurveCoeff>
                  <LeftEdgeSlopeCoeff>0.353</LeftEdgeSlopeCoeff>
                  <RightEdgeSlopeCoeff>0.353</RightEdgeSlopeCoeff>
                  <DepthRef>4</DepthRef>
                  <ADCPTemperature>28.62</ADCPTemperature>
                  <BlankingDistance>0.00</BlankingDistance>
                  <BinSize>0.20</BinSize>
                  <BTMode>0</BTMode>
                  <WTMode>0</WTMode>
                  <BTPings>1</BTPings>
                  <WTPings>2</WTPings>
                  <MinNmbSats>0</MinNmbSats>
                  <MaxNmbSats>0</MaxNmbSats>
                  <MinHDOP>0.000000</MinHDOP>
                  <MaxHDOP>0.000000</MaxHDOP>
               </Index_0>
            </BottomTrack>
            <GGA>
               <Index_0>
                  <UseInSummary>1</UseInSummary>
                  <BeginLeft>1</BeginLeft>
                  <IsSubSectioned>0</IsSubSectioned>
                  <FileName>Imperal Valley000</FileName>
                  <TransectNmb>000</TransectNmb>
                  <TotalNmbEnsembles>1766</TotalNmbEnsembles>
                  <TotalBadEnsembles>1766</TotalBadEnsembles>
                  <TotalLostEnsembles>5</TotalLostEnsembles>
                  <LargestGapInSecondsLostOrBad>0.000000</LargestGapInSecondsLostOrBad>
                  <StartEnsemble>738</StartEnsemble>
                  <EndEnsemble>2508</EndEnsemble>
                  <StartTime>1502877188.000000</StartTime>
                  <EndTime>1502878958.000000</EndTime>
                  <TotalQ>0.000</TotalQ>
                  <TopQ>0.000</TopQ>
                  <MeasuredQ>0.000</MeasuredQ>
                  <BottomQ>0.000</BottomQ>
                  <LeftQ>0.000</LeftQ>
                  <RightQ>0.000</RightQ>
                  <LeftDistance>0.000</LeftDistance>
                  <RightDistance>0.000</RightDistance>
                  <Width>0.000</Width>
                  <TotalArea>0.000</TotalArea>
                  <QperArea>0.000</QperArea>
                  <FlowDirection>0.000</FlowDirection>
                  <MaxWaterDepth>2.310</MaxWaterDepth>
                  <MeanWaterDepth>2.059</MeanWaterDepth>
                  <MaxWaterSpeed>0.000</MaxWaterSpeed>
                  <MeanRiverVel>0.000</MeanRiverVel>
                  <MeanBoatSpeed>0.000</MeanBoatSpeed>
                  <MeanBoatCourse>0.000</MeanBoatCourse>
                  <PercentGoodBins>0.000</PercentGoodBins>
                  <STDPitch>0.225</STDPitch>
                  <STDRoll>0.186</STDRoll>
                  <MeanAbsPitch>0.188</MeanAbsPitch>
                  <MeanAbsRoll>0.159</MeanAbsRoll>
                  <MeanGoodLeftEdgeBins>0.000</MeanGoodLeftEdgeBins>
                  <MeanGoodRightEdgeBins>0.000</MeanGoodRightEdgeBins>
                  <PowerCurveCoeff>0.167</PowerCurveCoeff>
                  <LeftEdgeSlopeCoeff>0.353</LeftEdgeSlopeCoeff>
                  <RightEdgeSlopeCoeff>0.353</RightEdgeSlopeCoeff>
                  <DepthRef>4</DepthRef>
                  <ADCPTemperature>28.62</ADCPTemperature>
                  <BlankingDistance>0.00</BlankingDistance>
                  <BinSize>0.20</BinSize>
                  <BTMode>0</BTMode>
                  <WTMode>0</WTMode>
                  <BTPings>1</BTPings>
                  <WTPings>2</WTPings>
                  <MinNmbSats>0</MinNmbSats>
                  <MaxNmbSats>0</MaxNmbSats>
                  <MinHDOP>0.000000</MinHDOP>
                  <MaxHDOP>0.000000</MaxHDOP>
               </Index_0>
            </GGA>
            <VTG>
               <Index_0>
                  <UseInSummary>1</UseInSummary>
                  <BeginLeft>1</BeginLeft>
                  <IsSubSectioned>0</IsSubSectioned>
                  <FileName>Imperal Valley000</FileName>
                  <TransectNmb>000</TransectNmb>
                  <TotalNmbEnsembles>1766</TotalNmbEnsembles>
                  <TotalBadEnsembles>1766</TotalBadEnsembles>
                  <TotalLostEnsembles>5</TotalLostEnsembles>
                  <LargestGapInSecondsLostOrBad>0.000000</LargestGapInSecondsLostOrBad>
                  <StartEnsemble>738</StartEnsemble>
                  <EndEnsemble>2508</EndEnsemble>
                  <StartTime>1502877188.000000</StartTime>
                  <EndTime>1502878958.000000</EndTime>
                  <TotalQ>0.000</TotalQ>
                  <TopQ>0.000</TopQ>
                  <MeasuredQ>0.000</MeasuredQ>
                  <BottomQ>0.000</BottomQ>
                  <LeftQ>0.000</LeftQ>
                  <RightQ>0.000</RightQ>
                  <LeftDistance>0.000</LeftDistance>
                  <RightDistance>0.000</RightDistance>
                  <Width>0.000</Width>
                  <TotalArea>0.000</TotalArea>
                  <QperArea>0.000</QperArea>
                  <FlowDirection>0.000</FlowDirection>
                  <MaxWaterDepth>2.310</MaxWaterDepth>
                  <MeanWaterDepth>2.059</MeanWaterDepth>
                  <MaxWaterSpeed>0.000</MaxWaterSpeed>
                  <MeanRiverVel>0.000</MeanRiverVel>
                  <MeanBoatSpeed>0.000</MeanBoatSpeed>
                  <MeanBoatCourse>0.000</MeanBoatCourse>
                  <PercentGoodBins>0.000</PercentGoodBins>
                  <STDPitch>0.225</STDPitch>
                  <STDRoll>0.186</STDRoll>
                  <MeanAbsPitch>0.188</MeanAbsPitch>
                  <MeanAbsRoll>0.159</MeanAbsRoll>
                  <MeanGoodLeftEdgeBins>0.000</MeanGoodLeftEdgeBins>
                  <MeanGoodRightEdgeBins>0.000</MeanGoodRightEdgeBins>
                  <PowerCurveCoeff>0.167</PowerCurveCoeff>
                  <LeftEdgeSlopeCoeff>0.353</LeftEdgeSlopeCoeff>
                  <RightEdgeSlopeCoeff>0.353</RightEdgeSlopeCoeff>
                  <DepthRef>4</DepthRef>
                  <ADCPTemperature>28.62</ADCPTemperature>
                  <BlankingDistance>0.00</BlankingDistance>
                  <BinSize>0.20</BinSize>
                  <BTMode>0</BTMode>
                  <WTMode>0</WTMode>
                  <BTPings>1</BTPings>
                  <WTPings>2</WTPings>
                  <MinNmbSats>0</MinNmbSats>
                  <MaxNmbSats>0</MaxNmbSats>
                  <MinHDOP>0.000000</MinHDOP>
                  <MaxHDOP>0.000000</MaxHDOP>
               </Index_0>
            </VTG>
            <GGA2>
               <Index_0>
                  <UseInSummary>1</UseInSummary>
                  <BeginLeft>1</BeginLeft>
                  <IsSubSectioned>0</IsSubSectioned>
                  <FileName>Imperal Valley000</FileName>
                  <TransectNmb>000</TransectNmb>
                  <TotalNmbEnsembles>1766</TotalNmbEnsembles>
                  <TotalBadEnsembles>1766</TotalBadEnsembles>
                  <TotalLostEnsembles>5</TotalLostEnsembles>
                  <LargestGapInSecondsLostOrBad>0.000000</LargestGapInSecondsLostOrBad>
                  <StartEnsemble>738</StartEnsemble>
                  <EndEnsemble>2508</EndEnsemble>
                  <StartTime>1502877188.000000</StartTime>
                  <EndTime>1502878958.000000</EndTime>
                  <TotalQ>0.000</TotalQ>
                  <TopQ>0.000</TopQ>
                  <MeasuredQ>0.000</MeasuredQ>
                  <BottomQ>0.000</BottomQ>
                  <LeftQ>0.000</LeftQ>
                  <RightQ>0.000</RightQ>
                  <LeftDistance>0.000</LeftDistance>
                  <RightDistance>0.000</RightDistance>
                  <Width>0.000</Width>
                  <TotalArea>0.000</TotalArea>
                  <QperArea>0.000</QperArea>
                  <FlowDirection>0.000</FlowDirection>
                  <MaxWaterDepth>2.310</MaxWaterDepth>
                  <MeanWaterDepth>2.059</MeanWaterDepth>
                  <MaxWaterSpeed>0.000</MaxWaterSpeed>
                  <MeanRiverVel>0.000</MeanRiverVel>
                  <MeanBoatSpeed>0.000</MeanBoatSpeed>
                  <MeanBoatCourse>0.000</MeanBoatCourse>
                  <PercentGoodBins>0.000</PercentGoodBins>
                  <STDPitch>0.225</STDPitch>
                  <STDRoll>0.186</STDRoll>
                  <MeanAbsPitch>0.188</MeanAbsPitch>
                  <MeanAbsRoll>0.159</MeanAbsRoll>
                  <MeanGoodLeftEdgeBins>0.000</MeanGoodLeftEdgeBins>
                  <MeanGoodRightEdgeBins>0.000</MeanGoodRightEdgeBins>
                  <PowerCurveCoeff>0.167</PowerCurveCoeff>
                  <LeftEdgeSlopeCoeff>0.353</LeftEdgeSlopeCoeff>
                  <RightEdgeSlopeCoeff>0.353</RightEdgeSlopeCoeff>
                  <DepthRef>4</DepthRef>
                  <ADCPTemperature>28.62</ADCPTemperature>
                  <BlankingDistance>0.00</BlankingDistance>
                  <BinSize>0.20</BinSize>
                  <BTMode>0</BTMode>
                  <WTMode>0</WTMode>
                  <BTPings>1</BTPings>
                  <WTPings>2</WTPings>
                  <MinNmbSats>0</MinNmbSats>
                  <MaxNmbSats>0</MaxNmbSats>
                  <MinHDOP>0.000000</MinHDOP>
                  <MaxHDOP>0.000000</MaxHDOP>
               </Index_0>
            </GGA2>
            <VTG2>
               <Index_0>
                  <UseInSummary>1</UseInSummary>
                  <BeginLeft>1</BeginLeft>
                  <IsSubSectioned>0</IsSubSectioned>
                  <FileName>Imperal Valley000</FileName>
                  <TransectNmb>000</TransectNmb>
                  <TotalNmbEnsembles>1766</TotalNmbEnsembles>
                  <TotalBadEnsembles>1766</TotalBadEnsembles>
                  <TotalLostEnsembles>5</TotalLostEnsembles>
                  <LargestGapInSecondsLostOrBad>0.000000</LargestGapInSecondsLostOrBad>
                  <StartEnsemble>738</StartEnsemble>
                  <EndEnsemble>2508</EndEnsemble>
                  <StartTime>1502877188.000000</StartTime>
                  <EndTime>1502878958.000000</EndTime>
                  <TotalQ>0.000</TotalQ>
                  <TopQ>0.000</TopQ>
                  <MeasuredQ>0.000</MeasuredQ>
                  <BottomQ>0.000</BottomQ>
                  <LeftQ>0.000</LeftQ>
                  <RightQ>0.000</RightQ>
                  <LeftDistance>0.000</LeftDistance>
                  <RightDistance>0.000</RightDistance>
                  <Width>0.000</Width>
                  <TotalArea>0.000</TotalArea>
                  <QperArea>0.000</QperArea>
                  <FlowDirection>0.000</FlowDirection>
                  <MaxWaterDepth>2.310</MaxWaterDepth>
                  <MeanWaterDepth>2.059</MeanWaterDepth>
                  <MaxWaterSpeed>0.000</MaxWaterSpeed>
                  <MeanRiverVel>0.000</MeanRiverVel>
                  <MeanBoatSpeed>0.000</MeanBoatSpeed>
                  <MeanBoatCourse>0.000</MeanBoatCourse>
                  <PercentGoodBins>0.000</PercentGoodBins>
                  <STDPitch>0.225</STDPitch>
                  <STDRoll>0.186</STDRoll>
                  <MeanAbsPitch>0.188</MeanAbsPitch>
                  <MeanAbsRoll>0.159</MeanAbsRoll>
                  <MeanGoodLeftEdgeBins>0.000</MeanGoodLeftEdgeBins>
                  <MeanGoodRightEdgeBins>0.000</MeanGoodRightEdgeBins>
                  <PowerCurveCoeff>0.167</PowerCurveCoeff>
                  <LeftEdgeSlopeCoeff>0.353</LeftEdgeSlopeCoeff>
                  <RightEdgeSlopeCoeff>0.353</RightEdgeSlopeCoeff>
                  <DepthRef>4</DepthRef>
                  <ADCPTemperature>28.62</ADCPTemperature>
                  <BlankingDistance>0.00</BlankingDistance>
                  <BinSize>0.20</BinSize>
                  <BTMode>0</BTMode>
                  <WTMode>0</WTMode>
                  <BTPings>1</BTPings>
                  <WTPings>2</WTPings>
                  <MinNmbSats>0</MinNmbSats>
                  <MaxNmbSats>0</MaxNmbSats>
                  <MinHDOP>0.000000</MinHDOP>
                  <MaxHDOP>0.000000</MaxHDOP>
               </Index_0>
            </VTG2>
         </Discharge_Summary>
      </Site_Discharge>
      <QA_QC Type="3" Checked="1" Status="0" Error="0">
         <Moving_Bed_Test Type="22" Checked="1" Status="0" Error="0">
            <Moving_Bed_Test_Summary>
               <MB_Tests />
               <MB_Corrections>
                  <Index_0>
                     <UseInSummary>1</UseInSummary>
                     <TransectNumber>0</TransectNumber>
                     <BottomTrackDischarge>25.651654</BottomTrackDischarge>
                     <CorrectedDischarge>25.651654</CorrectedDischarge>
                     <PercentDifference>0.000000</PercentDifference>
                     <MeanNearBedVelocity>0.000000</MeanNearBedVelocity>
                     <AccumulatedNormalizedDischargeRatio>-0.509049</AccumulatedNormalizedDischargeRatio>
                     <TotalTopQRefBT>7.019841</TotalTopQRefBT>
                     <TotalMidQRefBT>14.232113</TotalMidQRefBT>
                     <TotalBotQRefBT>4.399700</TotalBotQRefBT>
                     <LeftQRefBT>0.000000</LeftQRefBT>
                     <RightQRefBT>0.000000</RightQRefBT>
                     <AccumulatedDischarge>-12.346452</AccumulatedDischarge>
                     <MovingBottomGoodEnsCount>1638</MovingBottomGoodEnsCount>
                     <AccumulatedNorthNearBedVel>-99.311227</AccumulatedNorthNearBedVel>
                     <AccumulatedEastNearBedVel>-827.547901</AccumulatedEastNearBedVel>
                     <CorrectionFactor>0.000000</CorrectionFactor>
                  </Index_0>
               </MB_Corrections>
            </Moving_Bed_Test_Summary>
         </Moving_Bed_Test>
      </QA_QC>
      <Collect_Data Type="4" Checked="1" Status="0" Error="0" />
      <DisplaySettings>
         <Globals>
            <Depth_Max>5.000000</Depth_Max>
         </Globals>
      </DisplaySettings>
   </Project>
</WinRiver>

"""


