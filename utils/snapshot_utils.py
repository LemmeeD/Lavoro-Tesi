from pathlib import Path
from typing import List
from entities.DomainName import DomainName
from entities.Url import Url
from static_variables import SNAPSHOTS_FOLDER_NAME
from utils import file_utils


def take_temporary_snapshot(web_sites: List[Url], mail_domains: List[DomainName], complete_unresolved_database: bool, consider_tld: bool, execute_script_resolving: bool, execute_rov_scraping: bool) -> None:
    """
    Method that executes taking snapshots of the application.

    :param web_sites: List of web sites.
    :type web_sites: List[Url]
    :param mail_domains: List of mail domains.
    :type mail_domains: List[DomainName]
    :param complete_unresolved_database: The complete_unresolved_databaseflag.
    :type complete_unresolved_database: bool
    :param consider_tld: the consider_tld flag.
    :type consider_tld: bool
    :param execute_script_resolving: The execute_script_resolving flag.
    :type execute_script_resolving: bool
    :param execute_rov_scraping: The execute_rov_scraping flag.
    :type execute_rov_scraping: bool
    """
    def auxiliary(url: Url):
        try:
            return url.original()
        except ValueError:
            return url.second_component()
    take_temp_snapshot_of_string_list(list(map(lambda u: auxiliary(u), web_sites)), 'temp_web_sites')
    take_temp_snapshot_of_string_list(list(map(lambda dn: dn.string, mail_domains)), 'temp_mail_domains')
    take_temp_snapshot_of_flags(complete_unresolved_database, consider_tld, execute_script_resolving, execute_rov_scraping, 'temp_flags')


def take_temp_snapshot_of_string_list(string_list: List[str], filename: str, project_root_directory=Path.cwd()) -> None:
    """
    Export a string list as a .txt file in the SNAPSHOTS folder of the project root folder (PRD) with a predefined
    filename.
    Path.cwd() returns the current working directory which depends upon the entry point of the application; in
    particular, if we start the application from the main.py file in the PRD, every time Path.cwd() is encountered
    (even in methods belonging to files that are in sub-folders with respect to PRD) then the actual PRD is returned.
    If the application is started from a file that belongs to the entities package, then Path.cwd() will return the
    entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD parameter is set to default as
    if the entry point is main.py file (which is the only entry point considered).
    :param string_list: A list of string.
    :type string_list: List[str]
    :param filename: Name of file without extension.
    :type filename: str
    :param project_root_directory: The Path object pointing at the project root directory.
    :type project_root_directory: Path
    """
    file = file_utils.set_file_in_folder(SNAPSHOTS_FOLDER_NAME, filename + ".txt",
                                         project_root_directory=project_root_directory)
    with file.open('w', encoding='utf-8') as f:  # 'w' or 'x'
        for string in string_list:
            f.write(string+'\n')
        f.close()


def take_temp_snapshot_of_flags(complete_unresolved_database: bool, consider_tld: bool, execute_script_resolving: bool, execute_rov_scraping: bool, filename: str, project_root_directory=Path.cwd()) -> None:
    """
    Export 2 booleans as a .txt file in the SNAPSHOTS folder of the project root folder (PRD) with a predefined
    filename.
    Path.cwd() returns the current working directory which depends upon the entry point of the application; in
    particular, if we start the application from the main.py file in the PRD, every time Path.cwd() is encountered
    (even in methods belonging to files that are in sub-folders with respect to PRD) then the actual PRD is returned.
    If the application is started from a file that belongs to the entities package, then Path.cwd() will return the
    entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD parameter is set to default as
    if the entry point is main.py file (which is the only entry point considered).
    :param complete_unresolved_database: The complete_unresolved_database flag.
    :type complete_unresolved_database: bool
    :param consider_tld: The consider_tld flag.
    :type consider_tld: bool
    :param execute_script_resolving: The execute_script_resolving flag.
    :type execute_script_resolving: bool
    :param execute_rov_scraping: The execute_rov_scraping flag.
    :type execute_rov_scraping: bool
    :param filename: Name of file without extension.
    :type filename: str
    :param project_root_directory: The Path object pointing at the project root directory.
    :type project_root_directory: Path
    """
    file = file_utils.set_file_in_folder(SNAPSHOTS_FOLDER_NAME, filename + ".txt",
                                         project_root_directory=project_root_directory)
    with file.open('w', encoding='utf-8') as f:  # 'w' or 'x'
        f.write('complete_unresolved_database:'+str(complete_unresolved_database)+'\n')
        f.write('consider_tld:'+str(consider_tld)+'\n')
        f.write('execute_script_resolving:'+str(execute_script_resolving)+'\n')
        f.write('execute_rov_scraping:'+str(execute_rov_scraping))
        f.close()
