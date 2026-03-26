"""Unit tests for LDAP client helpers - no LDAP server needed."""
import pytest
from ldap.client import (
    sanitize_query,
    user_search_filter,
    group_search_filter,
    parse_github_username,
    extract_cn_from_dn,
    _entry_to_user,
    MIN_QUERY_LENGTH,
    LDAPClient,
    LDAPUser,
    LDAPGroup,
)


class TestSanitizeQuery:
    def test_normal_query(self):
        assert sanitize_query("jdoe") == "jdoe"

    def test_strips_whitespace(self):
        assert sanitize_query("  jdoe  ") == "jdoe"

    def test_strips_newlines(self):
        assert sanitize_query("foo\nbar") == "foobar"

    def test_strips_carriage_return(self):
        assert sanitize_query("foo\rbar") == "foobar"

    def test_strips_crlf(self):
        assert sanitize_query("foo\r\nbar") == "foobar"

    def test_truncates_long_query(self):
        long = "a" * 60
        assert len(sanitize_query(long)) == 50

    def test_empty_string(self):
        assert sanitize_query("") == ""


class TestUserSearchFilter:
    def test_single_word(self):
        result = user_search_filter("jdoe")
        assert result == "(|(uid=*jdoe*)(givenName=*jdoe*)(sn=*jdoe*))"

    def test_multi_word(self):
        result = user_search_filter("Jane Do")
        assert result == "(&(|(uid=*Jane*)(givenName=*Jane*)(sn=*Jane*))(|(uid=*Do*)(givenName=*Do*)(sn=*Do*)))"

    def test_special_chars_escaped(self):
        result = user_search_filter("user(test)")
        assert "\\28" in result
        assert "\\29" in result

    def test_asterisk_escaped(self):
        result = user_search_filter("user*")
        assert "\\2a" in result

    def test_empty_returns_wildcard(self):
        assert user_search_filter("") == "(uid=*)"


class TestGroupSearchFilter:
    def test_simple_query(self):
        assert group_search_filter("aipcc") == "(cn=aipcc*)"

    def test_special_chars_escaped(self):
        result = group_search_filter("group(test)")
        assert "\\28" in result


class TestParseGithubUsername:
    def test_valid_url(self):
        assert parse_github_username("Github->https://github.com/jdoe") == "jdoe"

    def test_trailing_slash(self):
        assert parse_github_username("Github->https://github.com/jdoe/") == "jdoe"

    def test_extra_path(self):
        assert parse_github_username("Github->https://github.com/jdoe/repos") == "jdoe"

    def test_non_github(self):
        assert parse_github_username("Twitter->https://twitter.com/jdoe") == ""

    def test_empty(self):
        assert parse_github_username("") == ""

    def test_partial_prefix(self):
        assert parse_github_username("Github->https://github.com/") == ""

    def test_wrong_case(self):
        assert parse_github_username("github->https://github.com/jdoe") == ""


class TestExtractCnFromDn:
    def test_standard_dn(self):
        assert extract_cn_from_dn("cn=aipcc-eng-all,ou=managedGroups,dc=redhat,dc=com") == "aipcc-eng-all"

    def test_spaces(self):
        assert extract_cn_from_dn("cn=My Group, ou=groups, dc=example, dc=com") == "My Group"

    def test_no_cn(self):
        assert extract_cn_from_dn("ou=managedGroups,dc=redhat,dc=com") == ""

    def test_empty(self):
        assert extract_cn_from_dn("") == ""

    def test_uppercase_cn(self):
        assert extract_cn_from_dn("CN=TestGroup,ou=groups,dc=example,dc=com") == "TestGroup"


class TestLDAPClientInit:
    def test_default_group_base_dn_derived(self):
        client = LDAPClient("ldaps://ldap.example.com", "ou=users,dc=redhat,dc=com")
        assert client.group_base_dn == "ou=managedGroups,dc=redhat,dc=com"

    def test_explicit_group_base_dn(self):
        client = LDAPClient("ldaps://ldap.example.com", "ou=users,dc=example,dc=com", "ou=groups,dc=example,dc=com")
        assert client.group_base_dn == "ou=groups,dc=example,dc=com"

    def test_cache_set_and_get(self):
        client = LDAPClient("ldaps://ldap.example.com", "ou=users,dc=redhat,dc=com")
        client._cache_set("test-key", "test-value")
        assert client._cache_get("test-key") == "test-value"

    def test_cache_miss(self):
        client = LDAPClient("ldaps://ldap.example.com", "ou=users,dc=redhat,dc=com")
        assert client._cache_get("nonexistent") is None

    def test_search_users_short_query_returns_empty(self):
        client = LDAPClient("ldaps://ldap.example.com", "ou=users,dc=redhat,dc=com")
        assert client.search_users("m") == []

    def test_search_groups_short_query_returns_empty(self):
        client = LDAPClient("ldaps://ldap.example.com", "ou=users,dc=redhat,dc=com")
        assert client.search_groups("a") == []

    def test_get_user_empty_uid_returns_none(self):
        client = LDAPClient("ldaps://ldap.example.com", "ou=users,dc=redhat,dc=com")
        assert client.get_user("") is None


class TestLDAPUserToDict:
    def test_to_dict_camel_case_keys(self):
        user = LDAPUser(uid="iezra", full_name="Itzik Ezra", email="iezra@redhat.com",
                        title="QE Engineer", github_username="ItzikEzra-rh", groups=["hw-accel-qe"])
        d = user.to_dict()
        assert d == {
            "uid": "iezra",
            "fullName": "Itzik Ezra",
            "email": "iezra@redhat.com",
            "title": "QE Engineer",
            "githubUsername": "ItzikEzra-rh",
            "groups": ["hw-accel-qe"],
        }

    def test_to_dict_defaults(self):
        user = LDAPUser()
        d = user.to_dict()
        assert d["uid"] == ""
        assert d["groups"] == []


class TestLDAPGroupToDict:
    def test_to_dict(self):
        group = LDAPGroup(name="aipcc-eng-all", description="All AIPCC engineers")
        assert group.to_dict() == {"name": "aipcc-eng-all", "description": "All AIPCC engineers"}


class TestEntryToUser:
    """Test _entry_to_user with mock ldap3-like entry objects."""

    def _make_entry(self, attrs):
        """Create a mock entry with attribute-like access."""
        class AttrVal:
            def __init__(self, val):
                self.value = val
                self.values = val if isinstance(val, list) else [val]
        class Entry:
            pass
        entry = Entry()
        for k, v in attrs.items():
            setattr(entry, k, AttrVal(v))
        return entry

    def test_full_entry(self):
        entry = self._make_entry({
            "uid": "jdoe",
            "cn": "Jane Doe",
            "mail": "jdoe@redhat.com",
            "title": "Engineer",
            "rhatSocialURL": ["Github->https://github.com/janedoe"],
            "memberOf": ["cn=team-a,ou=managedGroups,dc=redhat,dc=com"],
        })
        user = _entry_to_user(entry)
        assert user.uid == "jdoe"
        assert user.full_name == "Jane Doe"
        assert user.email == "jdoe@redhat.com"
        assert user.github_username == "janedoe"
        assert user.groups == ["team-a"]

    def test_missing_optional_attrs(self):
        entry = self._make_entry({"uid": "jdoe", "cn": "Jane Doe"})
        user = _entry_to_user(entry)
        assert user.uid == "jdoe"
        assert user.email == ""
        assert user.github_username == ""
        assert user.groups == []

    def test_completely_empty_entry(self):
        entry = self._make_entry({})
        user = _entry_to_user(entry)
        assert user.uid == ""
        assert user.full_name == ""
