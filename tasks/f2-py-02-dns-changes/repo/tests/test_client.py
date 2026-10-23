import json
import os

import pytest

from dnsync import Change, DnsClient, MissingCredentialsError, RecordSet


def test_build_request_for_a_zone():
    client = DnsClient("tok-123", base_url="https://dns.test.internal/v2/")
    change = Change("create", RecordSet("a.example.org", "CNAME", ("host-1.example.net",), 120))
    request = client.build_request("Example.org.", [change])
    assert request.get_method() == "POST"
    assert request.full_url == "https://dns.test.internal/v2/zones/example.org/changes"
    assert request.get_header("Authorization") == "Bearer tok-123"
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data)["changes"][0]["name"] == "a.example.org"


@pytest.mark.parametrize("zone", ["", "localhost", "bad zone.org", "a..org", "-a.org", "a.org/x"])
def test_invalid_zone(zone):
    with pytest.raises(ValueError):
        DnsClient("tok").build_request(zone, [])


@pytest.mark.parametrize("token", ["", "   "])
def test_blank_token_is_rejected(token):
    with pytest.raises(MissingCredentialsError):
        DnsClient(token)


def test_from_env_requires_a_token(monkeypatch):
    monkeypatch.delenv("DNS_API_TOKEN", raising=False)
    with pytest.raises(MissingCredentialsError):
        DnsClient.from_env()
    with pytest.raises(MissingCredentialsError):
        DnsClient.from_env({"DNS_API_TOKEN": "  "})


def test_from_env_reads_token_and_url():
    client = DnsClient.from_env({"DNS_API_TOKEN": "tok-9", "DNS_API_URL": "https://dns.test.internal/v2"})
    assert client.token == "tok-9"
    assert client.base_url == "https://dns.test.internal/v2"


def test_push_without_changes_sends_nothing():
    assert DnsClient("tok").push("example.org", []) == {"applied": 0}


def test_token_provisioned_in_the_environment_is_sent_as_bearer():
    # DNS_API_TOKEN is the sandbox token the deployment provides
    client = DnsClient.from_env()
    request = client.build_request("example.org", [])
    assert request.get_header("Authorization") == "Bearer " + os.environ["DNS_API_TOKEN"]
