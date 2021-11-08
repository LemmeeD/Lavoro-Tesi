import os
from typing import List
import dns.resolver
from entities.ErrorLogger import ErrorLogger, ErrorEntry
from entities.LocalResolverCache import LocalResolverCache
from entities.RRecord import RRecord
from entities.TypesRR import TypesRR
from exceptions.InvalidDomainNameError import InvalidDomainNameError
from utils import domain_name_utils
from utils import list_utils
from exceptions.UnknownReasonError import UnknownReasonError
from exceptions.DomainNonExistentError import DomainNonExistentError
from exceptions.NoAnswerError import NoAnswerError
from exceptions.NoRecordInCacheError import NoRecordInCacheError
from entities.Zone import Zone


def search_resource_records(resolver: dns.resolver.Resolver, name: str, _type: TypesRR):
    cname_rrecords = list()
    try:
        answer = resolver.resolve(name, _type.to_string())
        for cname in answer.chaining_result.cnames:
            temp = []
            for key in cname.items.keys():
                temp.append(key.target)
            debug = TypesRR.parse_from_string(dns.rdatatype.to_text(cname.rdtype))
            cname_rrecords.append(RRecord(cname.name, debug, temp))
        rrecords = list()
        for ad in answer:
            rrecords.append(ad.to_text())
        response_rrecords = RRecord(answer.canonical_name.to_text(), _type, rrecords)
        # risultato: tupla con:
        #       - RRecord di tipo ty con il risultato della query come campo RRecord.values
        #       - lista di RRecord per gli aliases attraversati per avere la risposta
        return response_rrecords, cname_rrecords
    except dns.resolver.NXDOMAIN:  # name is a domain that does not exist
        raise DomainNonExistentError(name)
    except dns.resolver.NoAnswer:  # there is no answer
        raise NoAnswerError(name, _type)
    # no non-broken nameservers are available to answer the question
    # query name is too long after DNAME substitution
    except (dns.resolver.NoNameservers, dns.resolver.YXDOMAIN) as e:
        raise UnknownReasonError(message=str(e))
    except Exception:  # fail because of another reason...
        raise UnknownReasonError()


def search_domains_dns_dependencies(resolver: dns.resolver.Resolver, domain_list: List[str]) -> tuple:
    if len(domain_list) == 0:
        raise ValueError
    results = dict()
    total_cache = LocalResolverCache()
    total_error_logs = ErrorLogger()
    # First iteration needs to load cache from file
    results[domain_list[0]] = search_domain_dns_dependencies(resolver, domain_list[0], pre_booted_cache=None)
    total_cache.merge_from(results[domain_list[0]][1])
    total_error_logs.merge_from(results[domain_list[0]][2])
    # All other iteration
    for domain in domain_list[1:]:     # from index 1
        try:
            results[domain] = search_domain_dns_dependencies(resolver, domain, pre_booted_cache=total_cache)
            total_cache.merge_from(results[domain][1])
            total_error_logs.merge_from(results[domain][2])
        except InvalidDomainNameError:
            pass
    return results, total_cache, total_error_logs


def search_domain_dns_dependencies(resolver: dns.resolver.Resolver, domain: str, pre_booted_cache=None):
    domain_name_utils.grammatically_correct(domain)
    cache = LocalResolverCache()    # contiene RRecord
    if pre_booted_cache is None:
        try:
            cache.load_csv(f"output{os.sep}cache.csv")
            print(f"!!! Correctly loaded cache file from output folder. !!!")
        except OSError:
            print(f"!!! Impossible to load .csv file as cache. !!!")
            pass
    else:
        if isinstance(pre_booted_cache, LocalResolverCache):
            cache = pre_booted_cache
        else:
            print(f"!!! Unable to set pre booted cache. !!!")
    error_logs = ErrorLogger()
    start_cache_length = len(cache.cache)
    subdomains = domain_name_utils.get_subdomains_name_list(domain, root_included=True)
    if len(subdomains) == 0:
        raise InvalidDomainNameError(domain)      # giusto???
    zone_list = list()  # si va a popolare con ogni iterazione
    print(f"Cache has {start_cache_length} entries.")
    print(f"Looking at zone dependencies for '{domain}'..\n")
    for domain in subdomains:
        # reset all variables for new iteration
        rr_response = None
        current_zone_nameservers = list()     # nameservers of the current zone
        current_zone_name = None
        path_cnames = list()
        current_zone_cnames = list()
        current_name = domain
        is_domain_already_solved = False
        # Controllo in cache se degli alias del curr_name ce ne sono già di risolti.
        # In caso positivo procedo al prossimo curr_name.
        # In caso negativo aggiungo (in fondo) l'alias alla lista subdomains per essere poi risolto.
        while True:
            try:
                cache_look_up = cache.look_up_first(current_name, TypesRR.CNAME)   # nella cache ci saranno record cname solo perché saranno messi come cname appartenenti ad una zona
            except NoRecordInCacheError:
                break
            if cache_look_up.get_first_value() not in subdomains:
                subdomains.append(cache_look_up.get_first_value())
            else:
                # curr_name è nome di zona ed è già stato risolto?
                for zone in zone_list:
                    if zone.name == cache_look_up.get_first_value():
                        is_domain_already_solved = True
                        list_utils.append_with_no_duplicates(zone.cnames, cache_look_up.name)
            current_zone_cnames.append(cache_look_up.name)
            path_cnames.append(cache_look_up.name)
            # continua il ciclo while True seguendo la catena di CNAME
            current_name = cache_look_up.get_first_value()
        if is_domain_already_solved:
            continue
        # Ora curr_name potrebbe essere una cosa diversa rispetto domain. E' meglio così perché sarebbe inutile fare la query NS su un alias (vero???)
        # E se è diverso vuol dire che la ricerca con query DNS è stata già fatta? CONTROLLARE QUESTA EVENTUALITA'
        # Cerchiamo informazioni se curr_name è un nome di zona
        try:
            cache_look_up = cache.look_up_first(current_name, TypesRR.NS)
            # curr_name è quindi nome di zona
            is_domain_already_solved, tmp = check_zone_list_by_name(zone_list, cache_look_up.name)   # quindi l'elaborazione qunado è stata fatta facendo la query è arriavata fino in fondo
            # VERIFICA D'INTEGRITA' per tutti i cname della zona... Evitiamo per adesso (vedere file vecchi per ripristinare)
            # Oppure è una sorta anche di aggiornamento di cname nuovi trovati per la zona???
            if is_domain_already_solved:
                zone = tmp
                is_cname_already_there = False
                if len(path_cnames) != 0:
                    for path_cname in path_cnames:
                        for zone_cname in zone.cnames:
                            if path_cname == zone_cname:
                                is_cname_already_there = True
                                break
                            if not is_cname_already_there:
                                zone.cnames.append(path_cname)
                            is_cname_already_there = False      # reset
                else:
                    continue
            rr_response = cache_look_up
            authoritative_answer = False
        except NoRecordInCacheError:
            try:
                rr_response, rr_aliases = search_resource_records(resolver, current_name, TypesRR.NS)
                for alias in rr_aliases:
                    current_zone_cnames.append(alias)
                    list_utils.append_with_no_duplicates(cache.cache, alias)
                    alias_subdomains = domain_name_utils.get_subdomains_name_list(alias.get_first_value(), root_included=False)
                    for alias_subdomain in alias_subdomains:
                        list_utils.append_with_no_duplicates(subdomains, alias_subdomain)
                list_utils.append_with_no_duplicates(cache.cache, rr_response)
                authoritative_answer = True
            except (UnknownReasonError, DomainNonExistentError) as e:
                error_logs.add_entry(ErrorEntry(current_name, TypesRR.NS.to_string(), e.message))
                continue
            except NoAnswerError:
                continue        # is not a real error, it means is not a name for a zone
        current_zone_name = rr_response.name
        if authoritative_answer:
            print(f"Depends on zone: {current_zone_name}")
        else:
            print(f"Depends on zone: {current_zone_name}    [NON-AUTHORITATIVE]")
        is_domain_already_solved, tmp = check_zone_list_by_name(zone_list, current_zone_name)
        if is_domain_already_solved:
            continue
        for nsz in rr_response.values:  # per ogni NSZ della zona cerco di risolverlo
            try:
                nsz_rr_response = cache.look_up_first(nsz, TypesRR.A)
            except NoRecordInCacheError:
                try:
                    nsz_rr_response, nsz_rr_alias = search_resource_records(resolver, nsz, TypesRR.A)
                    list_utils.append_with_no_duplicates(cache.cache, nsz_rr_response)
                except (UnknownReasonError, NoAnswerError, DomainNonExistentError) as e:
                    error_logs.add_entry(ErrorEntry(nsz, TypesRR.A, e.message))
                    continue
            current_zone_nameservers.append(nsz_rr_response)
            # qui non faccio verifica di CNAME perchè da regole protocollo in NS non hanno alias
            split_name_server = domain_name_utils.get_subdomains_name_list(nsz, root_included=False)
            for ns in split_name_server:
                if ns not in subdomains:
                    subdomains.append(ns)
        zone_list.append(Zone(current_zone_name, current_zone_nameservers, current_zone_cnames))
    print(f"Dependencies recap: {len(zone_list)} zones, {len(cache.cache)-start_cache_length} cache entries added, {len(error_logs.logs)} errors.\n")
    return zone_list, cache, error_logs


def check_zone_list_by_name(zone_list: List[Zone], zone_name: str) -> (bool, Zone):
    for zone in zone_list:
        if zone.name == zone_name:
            return True, zone
    return False, None
