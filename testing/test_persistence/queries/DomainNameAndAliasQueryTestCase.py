import unittest
from peewee import DoesNotExist
from exceptions.NoAliasFoundError import NoAliasFoundError
from exceptions.NoAvailablePathError import NoAvailablePathError
from persistence import helper_zone, helper_domain_name, helper_alias, helper_ip_network, helper_rov


class DomainNameAndAliasQueryTestCase(unittest.TestCase):
    def test_01_query_zone_dependencies_from_domain_name(self):
        print(f"\n------- [1] QUERY ZONE DEPENDENCIES FROM DOMAIN NAME -------")
        # PARAMETER
        domain_name = 'www.youtube.com.'
        # QUERY
        print(f"Parameter: {domain_name}")
        try:
            zes = helper_zone.get_zone_dependencies_of_domain_name(domain_name)
            print(f"Zone dependencies of domain name: {domain_name}")
            for i, ze in enumerate(zes):
                print(f"zone[{i + 1}/{len(zes)}]: {ze.name}")
        except DoesNotExist as e:
            print(f"!!! {str(e)} !!!")
        print(f"------- [1] END QUERY ZONE DEPENDENCIES FROM DOMAIN NAME -------")

    def test_02_query_aliases_from_domain_name(self):
        print(f"\n------- [2] QUERY ALIAS AND ACCESS PATH FROM DOMAIN NAME -------")
        # PARAMETER
        domain_name = 'ipdunivx.unipd.it.'
        # QUERY
        print(f"Parameter: {domain_name}")
        try:
            dnes = helper_alias.get_all_aliases_from_name(domain_name)
            for i, dne in enumerate(dnes):
                print(f"alias[{i + 1}/{len(dnes)}]: {dne.name}")
        except (DoesNotExist, NoAliasFoundError) as e:
            print(f"!!! {str(e)} !!!")
        print(f"------- [2] END QUERY ALIAS AND ACCESS PATH FROM DOMAIN NAME -------")

    def test_03_query_access_path_from_domain_name(self):
        print(f"\n------- [3] QUERY ACCESS PATH FROM DOMAIN NAME -------")
        # PARAMETER
        domain_name = 'dns.unipd.it.'
        # QUERY
        print(f"Parameter: {domain_name}")
        try:
            domain_name_entity = helper_domain_name.get(domain_name)
            try:
                iae, dnes = helper_domain_name.resolve_access_path(domain_name_entity, get_only_first_address=True)
                print(f"Access path of domain name: {domain_name}")
                for i, dne in enumerate(dnes):
                    print(f"path[{i + 1}/{len(dnes)}]: {dne.name}")
                print(f"(first) IP resolved: {iae.exploded_notation}")
                try:
                    ine = helper_ip_network.get_of(iae)
                    print(f"Belonging IP network of such IP address: {ine.compressed_notation}")
                except DoesNotExist as exc:
                    print(f"!!! {str(exc)} !!!")
            except NoAvailablePathError as e:
                print(f"!!! {str(e)} !!!")
        except DoesNotExist as exc:
            print(f"!!! {str(exc)} !!!")
        print(f"------- [3] END QUERY ACCESS PATH FROM DOMAIN NAME -------")


if __name__ == '__main__':
    unittest.main()