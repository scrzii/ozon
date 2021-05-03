import pickle
import os

from .extensions import smet


class Serializer:
    """
    Class for serializing all object or simple field of object
    """

    def __init__(self):  # Override me
        pass

    def export_to(self, field: str, value: object):  # Override me
        pass

    def import_from(self, field: str) -> object:  # Override me
        pass

    def field_exists(self, fields: str) -> bool:  # Override me
        pass


class FileSerializer(Serializer):
    """
    This class realizes file serializing with Pickle
    Each object is stored in simple .pickle-file
    """
    def __init__(self, file_path: str):
        """
        All files must be in one directory (file_path)
        :param file_path:
        """
        super().__init__()
        self.file_path = smet(file_path)

    def export_to(self, field: str, data: object):
        pickle.dump(data, open(self.file_path + smet(field, ".pickle"), "wb"))

    def import_from(self, field: str):
        return pickle.load(open(self.file_path + smet(field, ".pickle"), "rb"))

    def field_exists(self, field: str) -> bool:
        return os.path.exists(self.file_path + smet(field, ".pickle"))
