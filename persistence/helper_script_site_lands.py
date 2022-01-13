from typing import List
from peewee import DoesNotExist
from persistence.BaseModel import ScriptSiteEntity, ScriptServerEntity, IpAddressEntity, ScriptSiteLandsAssociation


def insert(ssitee: ScriptSiteEntity, sservere: ScriptServerEntity or None, https: bool, iae: IpAddressEntity or None) -> ScriptSiteLandsAssociation:
    ssla, created = ScriptSiteLandsAssociation.get_or_create(script_site=ssitee, script_server=sservere, https=https, ip_address=iae)
    return ssla


def get_all_from_script_site_entity(sse: ScriptSiteEntity) -> List[ScriptSiteLandsAssociation]:
    result = list()
    query = ScriptSiteLandsAssociation.select()\
        .join_from(ScriptSiteLandsAssociation, ScriptSiteEntity)\
        .where(ScriptSiteLandsAssociation.script_site == sse)
    for row in query:
        result.append(row)
    return result


def delete_all_from_script_site_entity(sse: ScriptSiteEntity):
    try:
        tmp = get_all_from_script_site_entity(sse)
        for relation in tmp:
            relation.delete_instance()
    except DoesNotExist:
        pass