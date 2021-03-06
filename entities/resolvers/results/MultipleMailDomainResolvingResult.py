from typing import Optional
from entities.DomainName import DomainName
from entities.error_log.ErrorLog import ErrorLog
from entities.resolvers.results.MailDomainResolvingResult import MailDomainResolvingResult


class MultipleMailDomainResolvingResult:
    """
    This class represents the result of multiple mail servers dependencies resolving.
    It consists in a dictionary that associates each mail domain to a DnsMailServersDependenciesResult object (which
    consists in a list of mail servers).

    ...

    Attributes
    ----------
    dependencies : Dict[DomainName, Optional[DnsMailServersDependenciesResult]]
        Such dictionary.
    error_logs : List[ErrorLog]
        A list of error logs occurred during resolving.
    """
    def __init__(self):
        """
        Initialize object.

        """
        self.dependencies = dict()
        self.error_logs = list()

    def add_dependency(self, mail_domain: DomainName, mail_servers_dependency: Optional[MailDomainResolvingResult]):
        """
        This method adds a new mail domain resolution. None value is used to indicate that the resolving went wrong.

        :param mail_domain: A mail domain.
        :type mail_domain: DomainName
        :param mail_servers_dependency: A DnsMailServersDependenciesResult object.
        :type mail_servers_dependency: MailDomainResolvingResult or None
        """
        if mail_servers_dependency is None:
            self.dependencies[mail_domain] = mail_servers_dependency
        else:
            if mail_domain != mail_servers_dependency.mail_domain_path.get_qname():
                raise ValueError
            else:
                self.dependencies[mail_domain] = mail_servers_dependency

    def append_error_log(self, log: ErrorLog):
        """
        This method appends a new error log.

        :param log: An error log.
        :type log: ErrorLog
        """
        self.error_logs.append(log)
