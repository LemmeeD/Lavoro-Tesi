from typing import List
from entities.DomainName import DomainName
from entities.paths.Path import Path
from entities.RRecord import RRecord
from entities.enums.TypesRR import TypesRR
from exceptions.DomainNameNotInPathError import DomainNameNotInPathError
from exceptions.PathIntegrityError import PathIntegrityError
from exceptions.UselessMethodInvocationError import UselessMethodInvocationError


class CNAMEPath(Path):
    def __init__(self, rr_list: List[RRecord]):
        if not Path.check_path_integrity(rr_list):
            raise PathIntegrityError
        for rr in rr_list:
            if rr.type != TypesRR.CNAME:
                raise ValueError
        self.path = rr_list

    def get_resolution(self) -> RRecord:
        return self.path[-1]

    def get_aliases_chain(self) -> List[RRecord]:
        return self.path[0:-1]

    def get_canonical_name(self) -> DomainName:
        return self.get_resolution().name

    def get_qname(self) -> DomainName:
        return self.path[0].name

    def get_list(self) -> List[RRecord]:
        return self.path

    def resolve(self, domain_name: DomainName) -> RRecord:
        for rr in self.path:
            if rr.name == domain_name:
                return self.get_resolution()
        if self.get_resolution().name == domain_name:
            return self.get_resolution()
        raise DomainNameNotInPathError(domain_name)

    def get_path_from(self, domain_name: DomainName) -> 'CNAMEPath':        # FORWARD DECLARATIONS (REFERENCES)
        for i, rr in enumerate(self.path):
            if rr.name == domain_name:
                return CNAMEPath(self.path[i:])
        raise DomainNameNotInPathError(domain_name)

    def __iter__(self):
        return self.path.__iter__()

    def __next__(self):
        return self.path.__iter__().__next__()
