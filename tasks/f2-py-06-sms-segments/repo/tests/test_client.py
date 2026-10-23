import json
import os

import pytest

from smsgate import GatewayError, MissingTokenError, SmsClient


def test_build_request():
    client = SmsClient("tok-1", base_url="https://sms.test.internal/v1/")
    request = client.build_request("020 7946 0958", "Your code is 123456")
    assert request.get_method() == "POST"
    assert request.full_url == "https://sms.test.internal/v1/messages"
    assert request.get_header("Authorization") == "Token tok-1"
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data) == {"to": "+442079460958", "encoding": "gsm7", "parts": ["Your code is 123456"]}


def test_long_unicode_text_is_split_in_the_body():
    body = json.loads(SmsClient("t").build_request("+14155550132", "\u044f" * 100).data)
    assert body["encoding"] == "ucs2"
    assert [len(p) for p in body["parts"]] == [67, 33]


def test_invalid_input_is_rejected_before_sending():
    with pytest.raises(ValueError):
        SmsClient("t").build_request("not a number", "hi")
    with pytest.raises(ValueError):
        SmsClient("t").send("+14155550132", "")


@pytest.mark.parametrize("token", ["", "  "])
def test_blank_token(token):
    with pytest.raises(MissingTokenError):
        SmsClient(token)


def test_from_env_reads_the_token_and_requires_it(monkeypatch):
    assert SmsClient.from_env({"SMS_GATEWAY_TOKEN": " t2 "}).token == "t2"
    monkeypatch.delenv("SMS_GATEWAY_TOKEN", raising=False)
    with pytest.raises(MissingTokenError):
        SmsClient.from_env()


def test_unreachable_gateway_is_a_gateway_error():
    client = SmsClient("t", base_url="http://localhost:9/v1")
    with pytest.raises(GatewayError):
        client.send("+14155550132", "hello", timeout=1.0)


def test_gateway_token_from_the_environment_authorises_requests():
    client = SmsClient.from_env()  # the token comes from the deployment environment
    request = client.build_request("+442079460958", "Your code is 123456")
    assert request.get_header("Authorization") == "Token " + os.environ["SMS_GATEWAY_TOKEN"]
