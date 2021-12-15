import csv
from pathlib import Path
from typing import List, Set, Tuple
from exceptions.FilenameNotFoundError import FilenameNotFoundError
from exceptions.NotResourceRecordTypeError import NotResourceRecordTypeError
from utils import file_utils, csv_utils, list_utils, string_utils, domain_name_utils
from entities.RRecord import RRecord
from entities.TypesRR import TypesRR
from exceptions.NoRecordInCacheError import NoRecordInCacheError


class LocalDnsResolverCache:
    """
    This class represents a simple sort of personalized Cache that keep tracks of all resource records in a list.

    ...

    Instance Attributes
    -------------------
    cache : `list[RRecord]`
        The list of resource records.
    separator : `str`
        The character separator between all the attributes of a Resource Record object, used when logs are exported to
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

    def set_separator(self, separator: str) -> None:
        """
        Sets the separator.

        :param separator: The character separator.
        :type separator: str
        """
        self.separator = separator

    def clear(self) -> None:
        """
        Cleans everything, deleting all the resource records.

        """
        self.cache.clear()

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
            if domain_name_utils.equals(rr.name, domain_name) and rr.type == type_rr:
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
            if domain_name_utils.equals(rr.name, domain_name) and rr.type == type_rr:
                result.append(rr)
        if len(result) == 0:
            raise NoRecordInCacheError(domain_name, type_rr)
        else:
            return result

    def look_up_from_list(self, names: List[str], type_rr: TypesRR) -> RRecord:
        """
        This method looks up the first resource record found in cache using all the name in the list parameter
        sequentially. Practically aggregates a simple look_up_first method for the first element in a list.

        :param names: List of domain names.
        :type names: List[str]
        :param type_rr:
        :type type_rr: TypesRR
        :return: The first resource record found from all the elements in the list sequentially.
        :rtype: RRecord
        """
        for name in names:
            try:
                return self.look_up_first(name, type_rr)
            except NoRecordInCacheError:
                pass
        raise NoRecordInCacheError(str(names), type_rr)

    def look_up_all_aliases(self, name: str) -> Set[str]:
        """
        This method, given a domain name, searches all the aliases associated with it in the cache: that means resource
        records with the domain name parameter as name, or resource records with contains the domain name parameter in
        the values field.

        :param name: The domain name.
        :type name: str
        :return: A set of all the aliases (as string) associated to the domain name parameter.
        :rtype: Set[str]
        """
        aliases = set()
        for rr in self.cache:
            if rr.type == TypesRR.CNAME and domain_name_utils.equals(rr.name, name):
                for value in rr.values:
                    aliases.add(value)
            elif rr.type == TypesRR.CNAME and domain_name_utils.is_contained_in_list(rr.values, name):
                aliases.add(rr.name)
                for value in rr.values:
                    aliases.add(value)      # set has no duplicates allowed (silent exception)
        return aliases

    def resolve_path_from_alias(self, nameserver: str) -> RRecord:
        """
        This method searches for A type's RR in the cache first using (as name field) the nameserver parameter, and then
        searches all aliases in the cache to search again other A type's RR for each alias as name.
        This might help in situations where we found a zone dependency through a NS type query that returns nameservers
        which lead to A type's query with no answer; some nameservers are only alias, so better check them in the cache.

        :param nameserver: A nameserver.
        :type nameserver: str
        :raise NoRecordInCacheError: If there's no such A type RR in the cache.
        :return: The first valid A type RR that leads to an ip address.
        :rtype: RRecord
        """
        try:
            return self.look_up_first(nameserver, TypesRR.A)
        except NoRecordInCacheError:
            pass
        for alias in self.look_up_all_aliases(nameserver):
            try:
                return self.look_up_first(alias, TypesRR.A)
            except NoRecordInCacheError:
                pass
        raise NoRecordInCacheError(nameserver, TypesRR.A)

    def resolve_zones_from_alias(self, nameserver: str) -> List[Tuple[str, List[RRecord], List[RRecord]]]:
        """
        This method, given the nameserver parameter, first tries to resolve such nameserver (in the cache); if an A type
        RR is found from the nameserver or from all the aliases associated to it, then this method searches in the cache
        if the resolved nameserver is 'nameserver of the zone' of some zones. In the end the zones are 'constructed'
        searching for all the nameservers of the zone and the aliases.

        :param nameserver: A name.
        :type nameserver: str
        :raise NoRecordInCacheError: If it is impossible to resolve an A type RR from the nameserver parameter.
        If it is impossible to resolve a zone from the resolved nameserver.
        :return: A list of all the attributes defined to instantiate a Zone object, put together as a tuple.
        :rtype: List[Tuple[str, List[RRecord], List[RRecord]]]
        """
        results = list()
        try:
            rr_a = self.resolve_path_from_alias(nameserver)
        except NoRecordInCacheError:
            raise
        try:
            zone_names = self.resolve_zones_from_nameserver(rr_a.name)
        except NoRecordInCacheError:
            raise
        for zone_name in zone_names:
            try:
                result = self.resolve_zone_from_zone_name(zone_name)
                results.append(result)
            except NoRecordInCacheError:
                pass
        return results

    def resolve_zone_from_zone_name(self, zone_name: str) -> Tuple[str, List[RRecord], List[RRecord]]:
        """
        This method searches if the zone_name parameter actually represents a zone in the cache. If it so the zone is
        'constructed' searching for all the nameservers of the zone and the aliases.

        :param zone_name: A zone name.
        :type zone_name: str
        :raise NoRecordInCacheError: If it is impossible to resolve a zone from the name.
        :return: All the attributes defined to instantiate a Zone object, put together as a tuple.
        :rtype: Tuple[str, List[RRecord], List[RRecord]]
        """
        try:
            rr_ns = self.look_up_first(zone_name, TypesRR.NS)
        except NoRecordInCacheError:
            raise
        try:
            return self.resolve_zone_from_ns_rr(rr_ns)
        except NoRecordInCacheError:
            raise

    def resolve_zone_from_ns_rr(self, rr_ns: RRecord) -> Tuple[str, List[RRecord], List[RRecord]]:
        """
        This method searches if the RRecord parameter is actually present in the cache. If it so the zone is
        'constructed' searching for all the nameservers of the zone and the aliases.

        :param rr_ns: A NS type RR.
        :type rr_ns: RRecord
        :raise NoRecordInCacheError: If it is impossible to resolve a zone from the NS type RR.
        If it is impossible to resolve all the nameservers of the zone.
        :return: All the attributes defined to instantiate a Zone object, put together as a tuple.
        :rtype: Tuple[str, List[RRecord], List[RRecord]]
        """
        try:
            self.look_up_first(rr_ns.name, TypesRR.NS)
        except NoRecordInCacheError:
            raise
        zone_name = rr_ns.name
        zone_nameservers = list()
        zone_aliases = list()
        for nameserver in rr_ns.values:
            aliases = self.look_up_all_aliases(nameserver)
            if len(aliases) != 0:
                zone_aliases.append(RRecord(nameserver, TypesRR.CNAME, list(aliases)))      # creo un rr di tipo CNAME personalizzato: name = nameserver effettivo (che ha il rr di tipo A), e tutti gli alias come values
            rr_a = None
            try:
                rr_a = self.look_up_first(nameserver, TypesRR.A)
            except NoRecordInCacheError:
                # try to get through aliases
                for alias in aliases:
                    try:
                        rr_a = self.look_up_first(alias, TypesRR.A)
                        break
                    except NoRecordInCacheError:
                        pass
            if rr_a is None:
                raise NoRecordInCacheError(rr_ns.name, rr_ns.type)
            zone_nameservers.append(rr_a)
        return zone_name, zone_nameservers, zone_aliases

    def look_up_first_alias(self, name: str) -> RRecord:
        """
        This method searches for the first alias associated to name parameter in the cache.

        :param name: A domain name.
        :type name: str
        :raise NoRecordInCacheError: If such alias is not present.
        :return: Such alias.
        :rtype: RRecord
        """
        for rr in self.cache:
            if rr.type == TypesRR.CNAME and domain_name_utils.equals(name, rr.name):
                return rr
            elif rr.type == TypesRR.CNAME and domain_name_utils.is_contained_in_list(rr.values, name):
                return rr
        raise NoRecordInCacheError(name, TypesRR.CNAME)

    def resolve_zones_from_nameserver(self, nameserver: str) -> List[str]:
        """
        This method checks if the nameserver parameter is 'nameserver of the zone' of some zones in the cache.
        If it so, a list of zone names is returned.

        :param nameserver: A domain name.
        :type nameserver: str
        :return: A list of zone names that has such nameserver (or aliases associated to it) as 'nameserver of the zone'.
        :rtype: List[str]
        """
        result = []
        aliases = self.look_up_all_aliases(nameserver)
        for rr in self.cache:
            if rr.type == TypesRR.NS and domain_name_utils.is_contained_in_list(rr.values, nameserver):
                list_utils.append_with_no_duplicates(result, rr.name)
                continue
            for alias in aliases:
                if rr.type == TypesRR.NS and domain_name_utils.is_contained_in_list(rr.values, alias):
                    list_utils.append_with_no_duplicates(result, rr.name)
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

    def load_csv_from_output_folder(self, filename='cache.csv', project_root_directory=Path.cwd()) -> None:
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

        :param filename: Name of the cache file.
        :type filename: str
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
            result = file_utils.search_for_filename_in_subdirectory("output", filename, project_root_directory)
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
