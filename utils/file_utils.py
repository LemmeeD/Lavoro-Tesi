import os
from datetime import datetime
from pathlib import Path
from typing import List
from exceptions.FileWithExtensionNotFoundError import FileWithExtensionNotFoundError
from exceptions.FilenameNotFoundError import FilenameNotFoundError
from static_variables import INPUT_FOLDER_NAME


def get_project_root_directory() -> Path:
    """
    This method returns the Path object of the project root directory (PRD) regardless of which script is executed
    (example: main.py file is executed or some test belonging to the /testing package).
    The hypothesis of the correct
    behaviour is that this method belongs to a file put in a sub-folder of the PRD.

    :return: The project root directory Path object.
    :rtype: Path
    """
    return Path(__file__).parent.parent


def search_for_file_type_in_subdirectory(subdirectory_name: str, extension: str, project_root_directory=Path.cwd()) -> List[Path]:   # extension with point
    """
    Given (the correct) path of the project root directory (PRD), this method searches for files of a certain extension
    in a certain subdirectory of the PRD.
    Path.cwd() returns the current working directory which depends upon the entry point of the application; in
    particular, if we start the application from the main.py file in the PRD, every time Path.cwd() is encountered
    (even in methods belonging to files that are in sub-folders with respect to PRD) then the actual PRD is returned.
    If the application is started from a file that belongs to the entities package, then Path.cwd() will return the
    entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD parameter is set to default as
    if the entry point is main.py file (which is the only entry point considered).

    :param subdirectory_name: The subdirectory name to find.
    :type subdirectory_name: str
    :param extension: The extension of the files interested.
    :type extension: str
    :param project_root_directory: The Path object pointing at the project root directory.
    :type project_root_directory: Path
    :raise FileWithExtensionNotFoundError: If such files are absent.
    :return: List of all matched files as Path objects. Impossible to be empty, otherwise the exception is raised.
    :rtype: List[Path]
    """
    result = sorted(project_root_directory.glob(f'{subdirectory_name}/*{extension}'))
    if len(result) == 0:
        raise FileWithExtensionNotFoundError(extension, subdirectory_name)
    else:
        return result       # MEMO: use str(result[index]) to get absolute path of file


def search_for_filename_in_subdirectory(subdirectory_name: str, filename: str, project_root_directory=Path.cwd()) -> List[Path]:   # filename with extension
    """
    Given (the correct) path of the project root directory (PRD), this method searches for files with a certain filename
    in a certain subdirectory of the PRD.
    Path.cwd() returns the current working directory which depends upon the entry
    point of the application; in particular, if we start the application from the main.py file in the PRD, every time
    Path.cwd() is encountered (even in methods belonging to files that are in sub-folders with respect to PRD) then the
    actual PRD is returned. If the application is started from a file that belongs to the entities package, then
    Path.cwd() will return the entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD
    parameter is set to default as if the entry point is main.py file (which is the only entry point considered).

    :param subdirectory_name: The subdirectory name to find.
    :type subdirectory_name: str
    :param filename: The filename of the files interested.
    :type filename: str
    :param project_root_directory: The Path object pointing at the project root directory.
    :type project_root_directory: Path
    :raise FilenameNotFoundError: If such files are absent.
    :return: List of all matched files as Path objects. Impossible to be empty, otherwise the exception is raised.
    :rtype: List[Path]
    """
    result = sorted(project_root_directory.glob(f'{subdirectory_name}/{filename}'))
    if len(result) == 0:
        raise FilenameNotFoundError(filename, subdirectory_name)
    else:
        return result


def set_file_in_folder(subdirectory_name: str, filename: str, project_root_directory=Path.cwd()) -> Path:
    """
    Given (the correct) path of the project root directory (PRD), this method searches for a file with a certain
    filename in a certain subdirectory of the PRD that can be non-existent. The matter is to return the Path object,
    the effective use of this object (read if exists, write the file represented by this path, ...) is up to others.
    If the subdirectory doesn't exists, it will be created automatically.
    Path.cwd() returns the current working directory which depends upon the entry point of the application; in
    particular, if we start the application from the main.py file in the PRD, every time Path.cwd() is encountered
    (even in methods belonging to files that are in sub-folders with respect to PRD) then the actual PRD is returned.
    If the application is started from a file that belongs to the entities package, then Path.cwd() will return the
    entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD parameter is set to default as
    if the entry point is main.py file (which is the only entry point considered).

    :param subdirectory_name: The subdirectory name to find.
    :type subdirectory_name: str
    :param filename: The filename of the file interested with the extension.
    :type filename: str
    :param project_root_directory: The Path object pointing at the project root directory.
    :type project_root_directory: Path
    :return: The Path object associated with the parameters.
    :rtype: Path
    """
    for directory in project_root_directory.iterdir():
        if directory.is_dir() and directory.name == subdirectory_name:
            file = Path(f"{str(directory)}{os.sep}{filename}")
            return file
        else:
            pass
    folder = Path(f"{str(Path.cwd())}{os.sep}{subdirectory_name}")
    folder.mkdir(parents=True, exist_ok=True)
    file = Path(f"{str(folder)}{os.sep}{filename}")
    return file


def last_modified(path_to_file: str) -> float:
    """
    Get the date that a file was last modified in seconds (since epoch).

    :raise OSError: If something happened.
    :returns: The date expressed as seconds since epoch.
    :rtype: float
    """
    try:
        stat = os.stat(path_to_file)
    except OSError:
        raise
    return stat.st_mtime


def is_tsv_database_updated(project_root_directory=Path.cwd()) -> bool:
    """
    This method checks if the .tsv database downloaded in the input folder is updated: we consider the database
    'updated' if it was downloaded at most one hour ago; this because in https://iptoasn.com/ it is said that the
    database is updated hourly. It returns False even in the case that the file is absent.

    :return: A boolean saying if it is updated or not (or there is no file).
    :rtype: bool
    """
    try:
        paths = search_for_file_type_in_subdirectory(INPUT_FOLDER_NAME, '.tsv', project_root_directory)
    except FileWithExtensionNotFoundError:
        return False
    file = paths[0]
    try:
        ct = last_modified(str(file))
    except OSError:
        return False
    dt = datetime.fromtimestamp(ct)
    now = datetime.now()
    diff_sec = (now - dt).seconds
    if diff_sec / (60*24) >= 1:  # more than 1 hour is passed
        return False
    else:
        return True
