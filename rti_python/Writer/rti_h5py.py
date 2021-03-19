import h5py


class RtiH5py:

    def __init__(self, file_path):
        self.file = None
        self.conn(file_path)

    def conn(self, file_path):
        """
        Open the connection.
        :param file_path: File path to h5py file.
        """
        self.file = h5py.File(file_path, "a")

    def close(self):
        """
        Close the connection.
        """
        self.file.close()

    def write(self, ens_df):
        """
        Write the given ensemble dataframe to the file.
        :param ens_df: Ensemble dataframe.
        :return:
        """
        if self.file:
            self.file['ens'] = ens_df.to_records(index=False)       # Convert the df to numpy array and write without index


