from typing import List
from entities.enums.TypesRR import TypesRR
from exceptions.NotResourceRecordTypeError import NotResourceRecordTypeError
from utils import domain_name_utils


class RRecord:
    """
    This class represent a simple resource record. Semantically it represents only the data structures, not the fact
    that is a real existent resource record.

    ...

    Attributes
    ----------
    name : `str`
        The name field of the resource record.
    type : `TypesRR`
        The type field of the resource record.
    values : `List[str]`
        The values field of the resource record.
    """

    def __init__(self, name: str, type_rr: TypesRR, values: str or List[str]):
        """
        Instantiate a RRecord object initializing all the attributes defined above.

        :param name: The name.
        :type name: str
        :param type_rr: The type.
        :type type_rr: TypesRR
        :param values: The values.
        :type values: str or List[str]
        """
        self.name = name
        self.type = type_rr
        if isinstance(values, str):
            temp = list()
            temp.append(values)
            self.values = temp
        else:
            self.values = values

    def __eq__(self, other: any) -> bool:
        """
        This method returns True only if self and other are semantically equal.
        This equality depends upon the developer.

        :param other: Another RRecord object.
        :type other: RRecord
        :return: True or False if the 2 objects are equal.
        :rtype: bool
        """
        if isinstance(other, RRecord):
            if domain_name_utils.equals(self.name, other.name) and self.type == other.type:
                return True
            else:
                return False
        else:
            return False

    def get_first_value(self) -> str:
        """
        Gets the first value in the values field.

        :return: The first value.
        :rtype: str
        """
        return self.values[0]

    @staticmethod
    def parse_from_csv_entry_as_str(entry: str, separator=';') -> 'RRecord':     # FORWARD DECLARATIONS (REFERENCES)
        """
        A static method that takes a string which represents a resource record as described in this
        class.

        :param entry: The string.
        :type entry: str
        :param separator: The string character that separates columns (of an entry) in the string.
        :type separator: str
        :raise ValueError: If the string separated from the comma are least than 3.
        :raise NotResourceRecordTypeError: If the type associated with the type is not matchable with any type as
        described in class/enum TypesRR.
        :returns: The parsed RRecord object.
        :rtype: RRecord
        """
        temp = entry.replace("[", "")
        temp = temp.replace("]", "")
        temp = temp.replace("\n", "")
        split_entry = temp.split(separator)
        if len(split_entry) != 3:
            raise ValueError()
        try:
            type_rr = TypesRR.parse_from_string(split_entry[1])
        except NotResourceRecordTypeError:
            raise
        # parsing values
        split_values = split_entry[2].split(',')
        values = []
        for val in split_values:
            values.append(val)
        return RRecord(split_entry[0], type_rr, values)

    @staticmethod
    def parse_mail_server_from_value(value: str) -> str:
        split_value = value.split(' ')
        return split_value[1]       # TODO: se è un IP? Da gestire

    def __str__(self):
        """
        This method returns a string representation of this object.

        :return: A string representation of this object.
        :rtype: str
        """
        return f"{self.name}\t{self.type.to_string()}\t{str(self.values)}"
