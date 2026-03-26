"""
LDAP client for user and group lookups against Red Hat LDAP.
Ported from ambient-code/platform (Go) to Python.
"""
import threading
from dataclasses import dataclass, field

from cachetools import TTLCache
from ldap3 import Server, Connection, Tls, SUBTREE
from ldap3.utils.conv import escape_filter_chars
import ssl

# Constants
DEFAULT_CONN_TIMEOUT = 5
DEFAULT_QUERY_TIMEOUT = 3
DEFAULT_MAX_RESULTS = 10
DEFAULT_CACHE_TTL = 300  # 5 minutes
MIN_QUERY_LENGTH = 2
MAX_QUERY_LENGTH = 50

USER_ATTRIBUTES = ["uid", "cn", "mail", "title", "rhatSocialURL", "memberOf"]


@dataclass
class LDAPUser:
    uid: str = ""
    full_name: str = ""
    email: str = ""
    title: str = ""
    github_username: str = ""
    groups: list = field(default_factory=list)

    def to_dict(self):
        return {
            "uid": self.uid,
            "fullName": self.full_name,
            "email": self.email,
            "title": self.title,
            "githubUsername": self.github_username,
            "groups": self.groups,
        }


@dataclass
class LDAPGroup:
    name: str = ""
    description: str = ""

    def to_dict(self):
        return {"name": self.name, "description": self.description}


def sanitize_query(q: str) -> str:
    q = q.strip()
    q = q.replace("\n", "").replace("\r", "")
    if len(q) > MAX_QUERY_LENGTH:
        q = q[:MAX_QUERY_LENGTH]
    return q


def user_search_filter(query: str) -> str:
    words = query.split()
    if not words:
        return "(uid=*)"
    if len(words) == 1:
        escaped = escape_filter_chars(words[0])
        return f"(|(uid=*{escaped}*)(givenName=*{escaped}*)(sn=*{escaped}*))"
    parts = []
    for w in words:
        escaped = escape_filter_chars(w)
        parts.append(f"(|(uid=*{escaped}*)(givenName=*{escaped}*)(sn=*{escaped}*))")
    return "(&" + "".join(parts) + ")"


def group_search_filter(query: str) -> str:
    escaped = escape_filter_chars(query)
    return f"(cn={escaped}*)"


def parse_github_username(social_url: str) -> str:
    prefix = "Github->https://github.com/"
    if not social_url.startswith(prefix):
        return ""
    username = social_url[len(prefix):]
    username = username.rstrip("/")
    if "/" in username:
        username = username[: username.index("/")]
    return username


def extract_cn_from_dn(dn: str) -> str:
    if not dn:
        return ""
    for part in dn.split(","):
        part = part.strip()
        if part.lower().startswith("cn="):
            return part[3:]
    return ""


def _entry_to_user(entry) -> LDAPUser:
    user = LDAPUser(
        uid=(entry.uid.value or "") if hasattr(entry, "uid") else "",
        full_name=(entry.cn.value or "") if hasattr(entry, "cn") else "",
        email=(entry.mail.value or "") if hasattr(entry, "mail") else "",
        title=(entry.title.value or "") if hasattr(entry, "title") else "",
    )
    if hasattr(entry, "rhatSocialURL"):
        urls = entry.rhatSocialURL.values if hasattr(entry.rhatSocialURL, "values") else []
        for url in urls:
            gh = parse_github_username(str(url))
            if gh:
                user.github_username = gh
                break
    if hasattr(entry, "memberOf"):
        members = entry.memberOf.values if hasattr(entry.memberOf, "values") else []
        for dn_val in members:
            cn = extract_cn_from_dn(str(dn_val))
            if cn:
                user.groups.append(cn)
    return user


class LDAPClient:
    def __init__(self, url: str, base_dn: str, group_base_dn: str = "", skip_tls_verify: bool = False):
        self.url = url
        self.base_dn = base_dn
        self.skip_tls_verify = skip_tls_verify
        if group_base_dn:
            self.group_base_dn = group_base_dn
        else:
            parts = base_dn.split(",", 1)
            if len(parts) == 2:
                self.group_base_dn = f"ou=managedGroups,{parts[1]}"
            else:
                self.group_base_dn = "ou=managedGroups,dc=redhat,dc=com"
        self._cache = TTLCache(maxsize=100, ttl=DEFAULT_CACHE_TTL)
        self._cache_lock = threading.Lock()

    def _connect(self) -> Connection:
        tls_config = None
        if self.url.startswith("ldaps://"):
            tls_config = Tls(validate=ssl.CERT_NONE if self.skip_tls_verify else ssl.CERT_REQUIRED)
        server = Server(self.url, use_ssl=self.url.startswith("ldaps://"), tls=tls_config, connect_timeout=DEFAULT_CONN_TIMEOUT)
        conn = Connection(server, auto_bind=True, read_only=True)
        return conn

    def _cache_get(self, key: str):
        with self._cache_lock:
            return self._cache.get(key)

    def _cache_set(self, key: str, value):
        with self._cache_lock:
            self._cache[key] = value

    def search_users(self, query: str) -> list[LDAPUser]:
        query = sanitize_query(query)
        if len(query) < MIN_QUERY_LENGTH:
            return []
        cache_key = f"users:{query}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        conn = self._connect()
        try:
            conn.search(search_base=self.base_dn, search_filter=user_search_filter(query), search_scope=SUBTREE, attributes=USER_ATTRIBUTES, size_limit=DEFAULT_MAX_RESULTS, time_limit=DEFAULT_QUERY_TIMEOUT)
            users = [_entry_to_user(entry) for entry in conn.entries]
            self._cache_set(cache_key, users)
            return users
        finally:
            conn.unbind()

    def search_groups(self, query: str) -> list[LDAPGroup]:
        query = sanitize_query(query)
        if len(query) < MIN_QUERY_LENGTH:
            return []
        cache_key = f"groups:{query}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        conn = self._connect()
        try:
            conn.search(search_base=self.group_base_dn, search_filter=group_search_filter(query), search_scope=SUBTREE, attributes=["cn", "description"], size_limit=DEFAULT_MAX_RESULTS, time_limit=DEFAULT_QUERY_TIMEOUT)
            groups = [
                LDAPGroup(
                    name=(entry.cn.value or "") if hasattr(entry, "cn") else "",
                    description=(entry.description.value or "") if hasattr(entry, "description") else "",
                )
                for entry in conn.entries
            ]
            self._cache_set(cache_key, groups)
            return groups
        finally:
            conn.unbind()

    def get_user(self, uid: str) -> LDAPUser | None:
        uid = sanitize_query(uid)
        if not uid:
            return None
        cache_key = f"user:{uid}"
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached
        conn = self._connect()
        try:
            escaped = escape_filter_chars(uid)
            conn.search(search_base=self.base_dn, search_filter=f"(uid={escaped})", search_scope=SUBTREE, attributes=USER_ATTRIBUTES, size_limit=1, time_limit=DEFAULT_QUERY_TIMEOUT)
            if not conn.entries:
                return None
            user = _entry_to_user(conn.entries[0])
            self._cache_set(cache_key, user)
            return user
        finally:
            conn.unbind()
