from typing import List, Set
from peewee import DoesNotExist
from persistence import helper_script_site, helper_url
from persistence.BaseModel import ScriptSiteEntity, ScriptServerEntity, IpAddressEntity, ScriptSiteLandsAssociation, \
    UrlEntity


def insert(ssitee: ScriptSiteEntity, sservere: ScriptServerEntity or None, https: bool) -> ScriptSiteLandsAssociation:
    ssla, created = ScriptSiteLandsAssociation.get_or_create(script_site=ssitee, script_server=sservere, https=https)
    return ssla


def get_all_from_script_site_string(url: str) -> List[ScriptSiteLandsAssociation]:
    try:
        sse = helper_script_site.get(url)
    except DoesNotExist:
        raise
    result = list()
    query = ScriptSiteLandsAssociation.select()\
        .join_from(ScriptSiteLandsAssociation, ScriptSiteEntity)\
        .where(ScriptSiteLandsAssociation.script_site == sse)
    for row in query:
        result.append(row)
    return result


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


def get_all_from_entity_script_site_and_scheme(sse: ScriptSiteEntity, https: bool) -> List[ScriptSiteLandsAssociation]:
    result = list()
    query = ScriptSiteLandsAssociation.select()\
        .where((ScriptSiteLandsAssociation.script_site == sse) &
            (ScriptSiteLandsAssociation.https == https))
    for row in query:
        result.append(row)
    return result


def get_all_from_string_script_site_and_scheme(script_site: str, https: bool) -> List[ScriptSiteLandsAssociation]:
    try:
        sse = helper_script_site.get(script_site)
    except DoesNotExist:
        raise
    return get_all_from_entity_script_site_and_scheme(sse, https)


def update(wsla: ScriptSiteLandsAssociation, new_s_server_e: ScriptServerEntity) -> None:
    query = ScriptSiteLandsAssociation.update(script_server=new_s_server_e) \
        .where((ScriptSiteLandsAssociation.script_site == wsla.script_site) &
               (ScriptSiteLandsAssociation.https == wsla.https))
    query.execute()


def get_https_unresolved() -> Set[ScriptSiteLandsAssociation]:
    query = ScriptSiteLandsAssociation.select()\
        .where((ScriptSiteLandsAssociation.script_server.is_null(True)) & (ScriptSiteLandsAssociation.https == True))
    result = set()
    for row in query:
        result.add(row)
    return result


def get_http_unresolved() -> Set[ScriptSiteLandsAssociation]:
    query = ScriptSiteLandsAssociation.select()\
        .where((ScriptSiteLandsAssociation.script_server.is_null(True)) & (ScriptSiteLandsAssociation.https == False))
    result = set()
    for row in query:
        result.add(row)
    return result
