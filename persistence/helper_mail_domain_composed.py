from typing import Set, List, Union, Dict
from peewee import chunked
from persistence.BaseModel import MailDomainEntity, MailDomainComposedAssociation, MailServerEntity, BATCH_SIZE_MAX, \
    NORMALIZATION_CONSTANT


def insert(mde: MailDomainEntity, mse: MailServerEntity or None) -> MailDomainComposedAssociation:
    mdca, created = MailDomainComposedAssociation.get_or_create(mail_domain=mde, mail_server=mse)
    return mdca


# insert + update = upsert
def bulk_upserts(data_source: List[Dict[str, Union[MailDomainEntity, MailServerEntity, None]]]) -> None:
    """
    Must be invoked inside a peewee transaction. Transaction needs the database object (db).
    Example:
        with db.atomic() as transaction:
            bulk_upserts(...)

    :param data_source: Fields name and values of multiple MailDomainComposedAssociation objects in the form of a
    dictionary.
    :type data_source: List[Dict[str, Union[MailDomainEntity, MailServerEntity, None]]]
    """
    num_of_fields = 2
    batch_size = int(BATCH_SIZE_MAX / (num_of_fields + NORMALIZATION_CONSTANT))
    for batch in chunked(data_source, batch_size):
        MailDomainComposedAssociation.insert_many(batch).on_conflict_replace().execute()


def get_of_entity_mail_domain(mde: MailDomainEntity) -> Set[MailDomainComposedAssociation]:
    query = MailDomainComposedAssociation.select()\
        .where(MailDomainComposedAssociation.mail_domain == mde)
    result = set()
    for row in query:
        result.add(row)
    return result


def get_unresolved() -> Set[MailDomainComposedAssociation]:
    query = MailDomainComposedAssociation.select()\
        .where(MailDomainComposedAssociation.mail_server.is_null(True))
    result = set()
    for row in query:
        result.add(row)
    return result
