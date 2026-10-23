import json

import pytest

from msgtranslate import MissingKeyError, TranslateClient, TranslateError, parse_response


def test_build_request():
    client = TranslateClient("key-1", base_url="https://api.test.example/v1/")
    request = client.build_request(['Hi <ph n="0"/>'], "pt-BR", source="en")
    assert request.get_method() == "POST"
    assert request.full_url == "https://api.test.example/v1/translate"
    assert request.get_header("Authorization") == "ApiKey key-1"
    assert request.get_header("Content-type") == "application/json"
    assert json.loads(request.data) == {"q": ['Hi <ph n="0"/>'], "target": "pt-BR", "tag_handling": "xml", "source": "en"}


def test_source_is_optional():
    body = json.loads(TranslateClient("k").build_request(["x"], "de").data)
    assert "source" not in body


@pytest.mark.parametrize("target", ["", "DE", "deu", "pt_BR", "pt-br", "d"])
def test_invalid_language_codes(target):
    with pytest.raises(ValueError):
        TranslateClient("k").build_request(["x"], target)


def test_empty_batch_is_rejected():
    with pytest.raises(ValueError):
        TranslateClient("k").build_request([], "de")


def test_parse_response():
    body = json.dumps({"translations": [{"text": "Hallo"}, {"text": "Welt"}]})
    assert parse_response(body, 2) == ["Hallo", "Welt"]


@pytest.mark.parametrize("body", ["nope", "[]", '{"translations": {}}', '{"translations": [{"txt": "a"}]}', '{"translations": []}'])
def test_parse_response_rejects_bad_answers(body):
    with pytest.raises(TranslateError):
        parse_response(body, 1)


@pytest.mark.parametrize("key", ["", "  "])
def test_blank_key(key):
    with pytest.raises(MissingKeyError):
        TranslateClient(key)


def test_from_env():
    assert TranslateClient.from_env({"LINGOFORGE_API_KEY": " k9 "}).api_key == "k9"
    with pytest.raises(MissingKeyError):
        TranslateClient.from_env({})


def test_empty_translate_sends_nothing():
    assert TranslateClient("k").translate([], "de") == []


def test_translates_a_catalog_entry_end_to_end():
    client = TranslateClient.from_env()  # paid API: uses the team's key
    out = client.translate(["Hello, {name}!"], target="de")
    assert "{name}" in out[0]
