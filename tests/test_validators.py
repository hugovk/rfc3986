# -*- coding: utf-8 -*-
"""Tests for the validators module."""
import rfc3986
from rfc3986 import exceptions
from rfc3986 import validators

import pytest


def test_defaults():
    """Verify the default Validator settings."""
    validator = validators.Validator()

    assert validator.require_presence_of == {
        c: False for c in validator.COMPONENT_NAMES
    }
    assert validator.allow_password is True
    assert validator.allowed_schemes == set()
    assert validator.allowed_hosts == set()
    assert validator.allowed_ports == set()


def test_allowing_schemes():
    """Verify the ability to select schemes to be allowed."""
    validator = validators.Validator().allow_schemes('http', 'https')

    assert 'http' in validator.allowed_schemes
    assert 'https' in validator.allowed_schemes


def test_allowing_hosts():
    """Verify the ability to select hosts to be allowed."""
    validator = validators.Validator().allow_hosts(
        'pypi.python.org', 'pypi.org',
    )

    assert 'pypi.python.org' in validator.allowed_hosts
    assert 'pypi.org' in validator.allowed_hosts


def test_allowing_ports():
    """Verify the ability select ports to be allowed."""
    validator = validators.Validator().allow_ports('80', '100')

    assert 80 in validator.allowed_ports
    assert 100 in validator.allowed_ports


def test_requiring_invalid_component():
    """Verify that we validate required component names."""
    with pytest.raises(ValueError):
        validators.Validator().require_components('frob')


def test_use_of_password():
    """Verify the behaviour of {forbid,allow}_use_of_password."""
    validator = validators.Validator()
    assert validator.allow_password is True

    validator.forbid_use_of_password()
    assert validator.allow_password is False

    validator.allow_use_of_password()
    assert validator.allow_password is True


@pytest.mark.parametrize('uri', [
    rfc3986.uri_reference('https://user:password@github.com'),
    rfc3986.uri_reference('https://user:password@github.com/path'),
    rfc3986.uri_reference('https://user:password@github.com/path?query'),
    rfc3986.uri_reference('https://user:password@github.com/path?query#frag'),
    rfc3986.uri_reference('//user:password@github.com'),
])
def test_forbidden_passwords(uri):
    """Verify that passwords are disallowed."""
    validator = validators.Validator().forbid_use_of_password()
    with pytest.raises(exceptions.PasswordForbidden):
        validator.validate(uri)


@pytest.mark.parametrize('uri', [
    rfc3986.uri_reference('https://user@github.com'),
    rfc3986.uri_reference('https://user@github.com/path'),
    rfc3986.uri_reference('https://user@github.com/path?query'),
    rfc3986.uri_reference('https://user@github.com/path?query#frag'),
    rfc3986.uri_reference('//user@github.com'),
    rfc3986.uri_reference('//github.com'),
    rfc3986.uri_reference('https://github.com'),
])
def test_passwordless_uris_pass_validation(uri):
    """Verify password-less URLs validate properly."""
    validator = validators.Validator().forbid_use_of_password()
    validator.validate(uri)


@pytest.mark.parametrize('uri', [
    rfc3986.uri_reference('https://'),
    rfc3986.uri_reference('/path/to/resource'),
])
def test_missing_host_component(uri):
    """Verify that missing host components cause errors."""
    validator = validators.Validator().require_components('host')
    with pytest.raises(exceptions.MissingComponentError):
        validator.validate(uri)


@pytest.mark.parametrize('uri', [
    rfc3986.uri_reference('https://'),
    rfc3986.uri_reference('//google.com'),
    rfc3986.uri_reference('//google.com?query=value'),
    rfc3986.uri_reference('//google.com#fragment'),
    rfc3986.uri_reference('https://google.com'),
    rfc3986.uri_reference('https://google.com#fragment'),
    rfc3986.uri_reference('https://google.com?query=value'),
])
def test_missing_path_component(uri):
    """Verify that missing path components cause errors."""
    validator = validators.Validator().require_components('path')
    with pytest.raises(exceptions.MissingComponentError):
        validator.validate(uri)


@pytest.mark.parametrize('uri', [
    rfc3986.uri_reference('//google.com'),
    rfc3986.uri_reference('//google.com?query=value'),
    rfc3986.uri_reference('//google.com#fragment'),
])
def test_multiple_missing_components(uri):
    """Verify that multiple missing components are caught."""
    validator = validators.Validator().require_components('scheme', 'path')
    with pytest.raises(exceptions.MissingComponentError) as captured_exc:
        validator.validate(uri)
    exception = captured_exc.value
    assert 2 == len(exception.args[-1])
