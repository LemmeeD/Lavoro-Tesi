import ipaddress
from typing import Set
from peewee import DoesNotExist
from persistence import helper_domain_name, helper_name_server
from persistence.BaseModel import IpAddressEntity, DomainNameEntity, AccessAssociation


def insert(address_param: str or ipaddress.IPv4Address) -> IpAddressEntity:
    address = None
    if isinstance(address_param, ipaddress.IPv4Address):
        address = address_param
    else:
        try:
            address = ipaddress.IPv4Address(address_param)
        except ValueError:
            raise
    iae, created = IpAddressEntity.get_or_create(exploded_notation=address.exploded)
    return iae


def get(ip_address: str) -> IpAddressEntity:
    try:
        ip = ipaddress.IPv4Address(ip_address)
    except ValueError:
        raise
    try:
        iae = IpAddressEntity.get_by_id(ip.exploded)
    except DoesNotExist:
        raise
    return iae


def get_first_of(domain_name_parameter: DomainNameEntity or str) -> IpAddressEntity:
    dne = None
    if isinstance(domain_name_parameter, DomainNameEntity):
        dne = domain_name_parameter
    else:
        try:
            dne = helper_domain_name.get(domain_name_parameter)
        except DoesNotExist:
            raise
    query = AccessAssociation.select()\
        .where(AccessAssociation.domain_name == dne)\
        .limit(1)
    for row in query:
        return row.ip_address
    raise DoesNotExist


def get_all_of(dne: DomainNameEntity) -> Set[IpAddressEntity]:
    result = set()
    query = AccessAssociation.select()\
        .where(AccessAssociation.domain_name == dne)
    for row in query:
        result.add(row.ip_address)
    return result
