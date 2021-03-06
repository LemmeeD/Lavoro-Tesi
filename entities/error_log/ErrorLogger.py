import csv
from pathlib import Path
from typing import List, Iterable
from entities.error_log.ErrorLog import ErrorLog
from static_variables import OUTPUT_FOLDER_NAME, OUTPUT_ERROR_LOGS_FILE_NAME
from utils import csv_utils, file_utils


class ErrorLogger:
    """
    This class represents a very simple logger for the usage needed in this application.

    ...

    Attributes
    ----------
    _logs : List[ErrorLog]
        List of error logs.
    _separator : str
        A string separator to use when exporting to .csv file.
    """
    def __init__(self, separator='\t'):     # \t = TAB
        """
        Initialize object.

        :param separator: The separator for the csv file format. Default is TAB.
        :type separator: str
        """
        self._logs = list()
        self._separator = separator

    @property
    def logs(self) -> List[ErrorLog]:
        return self._logs

    @property
    def separator(self) -> str:
        return self._separator

    @separator.setter
    def separator(self, new_val) -> None:
        self._separator = new_val

    def add_entry(self, entry: ErrorLog) -> None:
        """
        This method adds a new log.

        :param entry: The new entry.
        :type entry: ErrorLog
        """
        self._logs.append(entry)

    def add_entries(self, entries: Iterable[ErrorLog]) -> None:
        """
        This method adds multiple logs.

        :param entries: The new entries.
        :type entries: List[ErrorLog]
        """
        for log in entries:
            self._logs.append(log)

    def write_to_csv(self, filepath: str) -> None:
        """
        This method export all the error logs to a .csv file using the separator set in the object.

        :param filepath: The filepath of the file to write.
        :type filepath: str
        :raise PermissionError: If there's no permission to execute operation on the file.
        :raise FileNotFoundError: If file is not found.
        :raise OSError: If another OS-related problem occurred.
        """
        file = Path(filepath)
        try:
            with file.open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f, dialect=f'{csv_utils.return_personalized_dialect_name(self.separator)}')
                writer.writerow(['exception', 'entity', 'reason_phrase'])       # .csv headers
                for log in self.logs:
                    temp_list = list()
                    temp_list.append(log.error_type)
                    temp_list.append(log.entity_cause)
                    temp_list.append(log.reason_phrase)
                    writer.writerow(temp_list)
                f.close()
        except (PermissionError, FileNotFoundError, OSError):
            raise

    def write_to_csv_in_output_folder(self, filename=OUTPUT_ERROR_LOGS_FILE_NAME, project_root_directory=Path.cwd()) -> None:
        """
        This method export all the error logs to a .csv file using the separator of the self object in the output folder
        of the project. It needs the Path object of the project root directory (PRD).
        Path.cwd() returns the current working directory which depends upon the entry point of the application; in
        particular, if we start the application from the main.py file in the PRD, every time Path.cwd() is encountered
        (even in methods belonging to files that are in sub-folders with respect to PRD) then the actual PRD is
        returned. If the application is started from a file that belongs to the entities package, then Path.cwd() will
        return the entities sub-folder with respect to the PRD. So to give a bit of modularity, the PRD parameter is set
        to default as if the entry point is main.py file (which is the only entry point considered).

        :param filename: The filename to use (with extension).
        :type filename: str
        :param project_root_directory: The Path object pointing at the project root directory.
        :type project_root_directory: Path
        :raise PermissionError: If there's no permission to execute operation on the file.
        :raise FileNotFoundError: If file is not found.
        :raise OSError: If another OS-related problem occurred.
        """
        file = file_utils.set_file_in_folder(OUTPUT_FOLDER_NAME, filename, project_root_directory)
        file_abs_path = str(file)
        try:
            self.write_to_csv(file_abs_path)
        except (PermissionError, FileNotFoundError, OSError):
            raise
