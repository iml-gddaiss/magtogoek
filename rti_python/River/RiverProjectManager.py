import h5py
import os
from rti_python.Utilities.config import RtiConfig
from rti_python.River.RiverProject import RiverProject
from rti_python.River.Transect import Transect
from rti_python.River.RiverProjectMeta import RiverProjectMeta


class RiverProjectManager:

    VERSION = 1.0

    def __init__(self, rti_config: RtiConfig):
        """
        Initialize the list of projects.
        It will look in the directory listed in the config.ini file.
        :param rti_config: RTI Config config.ini file.
        """
        # Set Config file
        self.config = rti_config
        rti_config.init_river_project_config()

        # List of all the projects available
        self.projects = {}

        # Search for all available projects
        self.search_for_projects()

    def search_for_projects(self):
        """
        Search for any projects already created.
        This will look in the directory set in the config.ini
        file for any HDF5 files already created.  If the file
        already exist in the directory, then the project is added
        to the list.
        :return:
        """
        try:
            # Create the folder path if it does not exist
            if not os.path.exists(self.config.config['RIVER']['output_dir']):
                os.mkdir(self.config.config['RIVER']['output_dir'], 0o666)
                os.chmod(self.config.config['RIVER']['output_dir'], 0o666)
        except OSError as error:
            print("Error Creating output directory.", error)

        # Look inside the folder for any hdf5 files
        for file in os.listdir(self.config.config['RIVER']['output_dir']):
            if file.endswith(".hdf5"):
                # The project name is the file name without the extension
                prj_name = os.path.splitext(file)

                # Use the first part of prj_name which the file name
                # The second value is the file extension
                project_name_without_ext = prj_name[0]

                # Create a project and add it ot the list
                project = RiverProject(self.config, project_name_without_ext, os.path.join(self.config.config['RIVER']['output_dir'], file))
                self.projects[project_name_without_ext] = project

    def get_project_list(self):
        """
        Get the list of available projects.
        :return: List of available projects.
        """
        return self.projects.keys()

    def get_project(self, project_name: str) -> RiverProject:
        """
        Get the file path to the project from the list of HDF5 projects.
        If the project does not exist, return None.
        :param project_name: Project name used in the dictionary.
        :return: File Path to HDF5 Project or None

        """
        #for name in self.projects.keys():
        #    print(name)
        #    print(self.projects[name])
        # Verify project exist
        if project_name in self.projects:
            return self.projects[project_name]

        return None

    def add_project(self, name: str, project_file_path: str) -> RiverProject:
        """
        Add a project to the list of projects.  If the no HDF5 project file can
        be found, return none.
        :param name: Name of the project.
        :param project_file_path: Project File path
        :return: Project file path if it exist or None if no HDF5 file exist.
        """
        if os.path.exists(project_file_path):
            # Check if the project already exist
            # If it does, create a new project name with an index
            project_already_exist_index = 0

            # Create files paths until a unique file name is found
            while name in self.projects.keys():
                # Create a new name with an index
                name = name + "_" + str(project_already_exist_index)

                project_already_exist_index += 1

            # Add project to the list
            self.projects[name] = RiverProject(self.config, name, project_file_path)

            # Create the H5DF file object to verify subgroups exist
            with h5py.File(project_file_path, "a") as prj_file:

                # Check if Transect Subgroup is in the project file
                if RiverProjectMeta.SUBGROUP_TRANSECT not in prj_file:
                    # Create a folder for transects to be stored
                    prj_file.create_group(RiverProjectMeta.SUBGROUP_TRANSECT)

                # Check if the Moving Bed Test Subgroup is in the project file
                if RiverProjectMeta.SUBGROUP_MBT not in prj_file:
                    # Create a folder for moving bed tests
                    prj_file.create_group(RiverProjectMeta.SUBGROUP_MBT)

            # Return the project file
            return self.projects[name]

        # Return None if the project HDF5 does not exist
        return None

    def create_project(self, name: str):
        """
        Create a project and add it to the list of projects.
        This will use the name given to create a new project file.
        The file is a HDF5 file.  The project file will contain all
        the settings and transects and discharge calculation results.

        The HDF5 file is created in the directory set in the config.ini
        file.

        If the project already exist, it will create the project with an
        index number at the end of project name.
        :param name: Name of the project.
        :return: Return the HDF5 project file.
        """
        # Create a file name and path
        file_path = os.path.join(self.config.config['RIVER']['output_dir'], name + ".hdf5")

        # Check if the project already exist
        # If it does, create a new project name with an index
        file_already_exist_index = 0

        # Create a new name with an index
        new_name = name + "_" + str(file_already_exist_index)

        if os.path.exists(file_path):
            # Create a new file with index
            file_path = os.path.join(self.config.config['RIVER']['output_dir'], new_name + ".hdf5")

            # Create files paths until a unique file name is found
            while os.path.exists(file_path):
                file_already_exist_index += 1
                new_name = name + "_" + str(file_already_exist_index)
                file_path = os.path.join(self.config.config['RIVER']['output_dir'], new_name + ".hdf5")

            # Create a project
            prj_file_path = os.path.join(self.config.config['RIVER']['output_dir'], new_name + ".hdf5")
            project = RiverProject(self.config, new_name, prj_file_path)

            # Add project to the list
            self.projects[new_name] = project

            # Set the name variable to new_name now
            # This is set to the name can be set in the attr for the project
            name = new_name
        else:
            # Create a project
            prj_file_path = os.path.join(self.config.config['RIVER']['output_dir'], name + ".hdf5")
            project = RiverProject(self.config, name, prj_file_path)

            # Add project to the list using original project name
            self.projects[name] = project

        # Create the H5DF file
        with h5py.File(file_path, "a") as prj_file:
            # Create a folder for transects to be stored
            prj_file.create_group(RiverProjectMeta.SUBGROUP_TRANSECT)

            # Create a folder for moving bed tests
            prj_file.create_group(RiverProjectMeta.SUBGROUP_MBT)

            # Set meta data for the project file
            prj_file.attrs[RiverProjectMeta.PROJECT_NAME] = name
            prj_file.attrs[RiverProjectMeta.PROJECT_FILE_PATH] = os.path.join(self.config.config['RIVER']['output_dir'], name + ".hdf5")

        # Return the path to the HDF5 project file created
        return self.projects[name]

    def create_transect(self, project_name: str, transect: Transect):

        # Verify project is created.
        if project_name not in self.projects:
            self.create_project(project_name)

        # Open the project file
        # Create the H5DF file
        prj_file = h5py.File(self.projects[project_name].file_path, "a")

        # Create a transect within the transect folder
        transect_grp = prj_file.create_group(RiverProjectMeta.SUBGROUP_TRANSECT + "/" + transect.get_name())

        # Set the meta data for the transect
        self.set_transect_meta(transect_grp, transect)

    def set_transect_meta(self, transect_grp: h5py.Group, transect: Transect):
        transect_grp.attrs[RiverProjectMeta.TRANSECT_STATION_NAME] = transect.station_name
        transect_grp.attrs[RiverProjectMeta.TRANSECT_STATION_INFO] = transect.station_info
        transect_grp.attrs[RiverProjectMeta.TRANSECT_STATION_COMMENTS] = transect.comments



