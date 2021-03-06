import unittest
from persistence import helper_application_results
from utils import file_utils


class DumpUnresolvedEntitiesIntegrityCase(unittest.TestCase):
    """
    DEFINITIVE TEST

    """
    @classmethod
    def setUpClass(cls) -> None:
        cls.PRD = file_utils.get_project_root_directory()

    def test_1_dump_unresolved_entities(self):
        print(f"\n------- START TEST 1 -------")
        unresolved_entities = helper_application_results.get_unresolved_entities()
        helper_application_results.dump_all_unresolved_entities(self.PRD, unresolved_entities, ';')
        print(f"------- END TEST 1 -------")


if __name__ == '__main__':
    unittest.main()
