import csv
from pathlib import Path
from typing import List
from exceptions.FilenameNotFoundError import FilenameNotFoundError
from exceptions.NotResourceRecordTypeError import NotResourceRecordTypeError
from utils import file_utils, csv_utils
from entities.RRecord import RRecord
from entities.TypesRR import TypesRR
from exceptions.NoRecordInCacheError import NoRecordInCacheError


class LocalDnsResolverCache:
    """
    This class represent a simple sort of personalized Cache that keep tracks of all resource records in a list.

    ...

    Instance Attributes
    -------------------
    cache : `list[RRecord]`
        The list of resource records.
    separator : `str`
        The character separator between all the attributes of a Resource Record object, used when logs is exported to
        file.
    """
    cache: List[RRecord]
    separator: str

    def __init__(self, separator=";"):
        """
        Instantiate a LocalResolverCache initializing all the attributes defined above. You can set a personalized
        separator.

        :param separator: The character separator used when exporting the file. Default is TAB (\t).
        :type separator: str
        """
        self.cache = list()
        self.separator = separator

    def add_entry(self, entry: RRecord) -> None:
        """
        Adds a resource record.

        :param entry: The resource record.
        :type entry: RRecord
        """
        self.cache.append(entry)

    def set_separator(self, separator: str):
        """
        Set the separator.

        :param separator: The character separator.
        :type separator: str
        """
        self.separator = separator

    def look_up_first(self, domain_name: str, type_rr: TypesRR) -> RRecord:
        """
        Search for the first occurrence of a resource record of name and type as parameters told.

        :param domain_name: The domain name.
        :type domain_name: str
        :param type_rr: The resource record type.
        :type type_rr: TypesRR
        :raises NoRecordInCacheError: If there is no resource record satisfying the parameters in cache list.
        :returns: The first occurrence of name and resource record type as parameters told.
        :rtype: RRecord
        """
        for rr in self.cache:
            if rr.name == domain_name and rr.type.to_string() == type_rr.to_string():
                return rr
        raise NoRecordInCacheError(domain_name, type_rr)

    def look_up(self, domain_name: str, type_rr: TypesRR) -> List[RRecord]:
        """
        Search for all occurrences of resource records of name and type as parameters told.

        :param domain_name: The domain name.
        :type domain_name: str
        :param type_rr: The resource record type.
        :type type_rr: TypesRR
        :raises NoRecordInCacheError: If there is no resource record satisfying the parameters in cache list.
        :returns: A list containing all occurrences of name and resource record type as parameters told.
        :rtype: List[RRecord]
        """
        result = []
        for rr in self.cache:
            if rr.name == domain_name and rr.type.to_string() == type_rr.to_string():
                result.append(rr)
        if len(result) == 0:
            raise NoRecordInCacheError(domain_name, type_rr)
        else:
            return result

    def load_csv(self, path: str, take_snapshot=True) -> None:
        """
        Method that load from a .csv all the entries in this object cache list. More specifically, this method load the
        .csv file from a filepath (absolute or relative). It provides an optional flag to copy the state of cache in a
        file for later consumption.

        :param path: Path of file to load, as absolute or relative path.
        :type path: str
        :param take_snapshot: Flag for keeping track of cache when errors occur.
        :type take_snapshot: bool
        :raise ValueError: If it is impossible to parse a resource record from a line in the .csv file.
        :raise PermissionError: If filepath points to a directory.
        :raise FileNotFoundError: If it is impossible to open the file.
        :raise OSError: If a general I/O error occurs.
        """
        try:
            f = open(path, "r")
            for line in f:
                try:
                    rr = RRecord.parse_from_csv_entry_as_str(line)
                    self.cache.append(rr)
                except ValueError:
                    pass
                except NotResourceRecordTypeError:
                    pass
            f.close()
            if take_snapshot:
                self.take_snapshot()
        except ValueError:
            raise
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise

    def load_csv_from_output_folder(self, project_root_directory=Path.cwd()) -> None:
        """
        Method that load from a .csv all the entries in this object cache list. More specifically, this method load the
        .csv file from the output folder of the project root directory (if set correctly). So just invoking this
        method will load the cache (if) exported from the previous execution.
        Path.cwd() returns the current working directory which depends upon the entry point of the application; in
        particular, if we starts the application from the main.py file in the PRD, every time Path.cwd() is encountered
        (even in methods belonging to files that are in sub-folders with respect to PRD) then the actual PRD is
        returned. If the application is started from a file that belongs to the entities package, then Path.cwd() will
        return the entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD parameter is set
        to default as if the entry point is main.py file (which is the only entry point considered).

        :param project_root_directory: Path of the project root.
        :type project_root_directory: Path
        :raise FilenameNotFoundError: If file with such filename doesn't exist.
        :raises ValueError: If it is impossible to parse a resource record from a line in the .csv file.
        :raise PermissionError: If filepath points to a directory.
        :raises FileNotFoundError: If it is impossible to open the file.
        :raises OSError: If a general I/O error occurs.
        """
        file = None
        try:
            result = file_utils.search_for_filename_in_subdirectory("output", "cache.csv", project_root_directory)
            file = result[0]
        except FilenameNotFoundError:
            raise
        try:
            self.load_csv(str(file))
        except ValueError:
            raise
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise

    def write_to_csv(self, filepath: str) -> None:
        """
        Export the cache in the list to a .csv file described by a filepath.

        :param filepath: Path of file to write, as absolute or relative path.
        :type filepath: str
        :raise PermissionError: If filepath points to a directory.
        :raises FileNotFoundError: If it is impossible to open the file.
        :raises OSError: If a general I/O error occurs.
        """
        file = Path(filepath)
        try:
            with file.open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, dialect=f'{csv_utils.return_personalized_dialect_name(self.separator)}')
                for rr in self.cache:
                    temp_list = list()
                    temp_list.append(rr.name)
                    temp_list.append(rr.type.to_string())
                    tmp = "["
                    for index, val in enumerate(rr.values):
                        tmp += val
                        if not index == len(rr.values) - 1:
                            tmp += ","
                    tmp += "]"
                    temp_list.append(tmp)
                    writer.writerow(temp_list)
                f.close()
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise

    def write_to_txt(self, filepath: str) -> None:
        """
        Export the cache in the list to a .txt file described by a filepath.

        :param filepath: Path of file to write, as absolute or relative path.
        :type filepath: str
        :raise PermissionError: If filepath points to a directory.
        :raises FileNotFoundError: If it is impossible to open the file.
        :raises OSError: If a general I/O error occurs.
        """
        file = Path(filepath)
        file_abs_path = str(file)
        try:
            with open(file_abs_path, 'w') as f:  # 'w' or 'x'
                for rr in self.cache:
                    temp = f"{rr.name}{self.separator}{rr.type.to_string()}{self.separator}["
                    for index, val in enumerate(rr.values):
                        temp += val
                        if not index == len(rr.values) - 1:
                            temp += " "
                    temp += "]\n"
                    f.write(temp)
                f.close()
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise

    def write_to_csv_in_output_folder(self, filename="cache", project_root_directory=Path.cwd()) -> None:
        """
        Export the cache in the list to a .csv file in the output folder of the project directory (if set correctly).
        It uses the separator set to separate every attribute of the resource record.
        Path.cwd() returns the current working directory which depends upon the entry point of the application; in
        particular, if we starts the application from the main.py file in the PRD, every time Path.cwd() is encountered
        (even in methods belonging to files that are in sub-folders with respect to PRD) then the actual PRD is
        returned. If the application is started from a file that belongs to the entities package, then Path.cwd() will
        return the entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD parameter is set
        to default as if the entry point is main.py file (which is the only entry point considered).

        :param filename: The personalized filename without extension, default is cache.
        :type filename: str
        :param project_root_directory: The Path object pointing at the project root directory.
        :type project_root_directory: Path
        :raises PermissionError: If filepath points to a directory.
        :raises FileNotFoundError: If it is impossible to open the file.
        :raises OSError: If a general I/O error occurs.
        """
        file = file_utils.set_file_in_folder("output", filename+".csv", project_root_directory)
        file_abs_path = str(file)
        try:
            self.write_to_csv(file_abs_path)
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise

    def write_to_txt_in_output_folder(self, filename="cache", project_root_directory=Path.cwd()) -> None:
        """
        Export the cache in the list to a .txt file in the output folder of the project directory. It uses the separator
        set to separate every attribute of the resource record.
        Path.cwd() returns the current working directory which depends upon the entry point of the application; in
        particular, if we starts the application from the main.py file in the PRD, every time Path.cwd() is encountered
        (even in methods belonging to files that are in sub-folders with respect to PRD) then the actual PRD is
        returned. If the application is started from a file that belongs to the entities package, then Path.cwd() will
        return the entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD parameter is set
        to default as if the entry point is main.py file (which is the only entry point considered).

        :param filename: The personalized filename without extension, default is cache.
        :type filename: str
        :param project_root_directory: The Path object pointing at the project root directory.
        :type project_root_directory: Path
        :raises PermissionError: If filepath points to a directory.
        :raises FileNotFoundError: If it is impossible to open the file.
        :raises OSError: If a general I/O error occurs.
        """
        file = file_utils.set_file_in_folder("output", filename+".txt", project_root_directory)
        file_abs_path = str(file)
        try:
            self.write_to_txt(file_abs_path)
        except PermissionError:
            raise
        except FileNotFoundError:
            raise
        except OSError:
            raise

    def merge_from(self, other: 'LocalDnsResolverCache') -> None:       # FORWARD DECLARATIONS (REFERENCES)
        """
        Method that takes another LocalResolverCache object and adds (without duplicates) all the resource records from
        the other object cache to this (self object).

        :param other: Another LocalResolverCache object.
        :type other: LocalDnsResolverCache
        """
        for record in other.cache:
            if record not in self.cache:
                self.cache.append(record)

    def take_snapshot(self) -> None:
        """
        Method that copies the current state of the cache list in the input folder.

        """
        file = file_utils.set_file_in_folder("SNAPSHOTS", "temp_cache.csv")
        if not file.exists():
            pass
        with file.open('w', encoding='utf-8', newline='') as f:
            write = csv.writer(f, dialect=csv_utils.return_personalized_dialect_name(f"{self.separator}"))
            for rr in self.cache:
                temp_list = list()
                temp_list.append(rr.name)
                temp_list.append(rr.type.to_string())
                tmp = "["
                for index, val in enumerate(rr.values):
                    tmp += val
                    if not index == len(rr.values) - 1:
                        tmp += ","
                tmp += "]"
                temp_list.append(tmp)
                write.writerow(temp_list)
            f.close()