import urllib.error

import pytest

from freight import FreightClient, NoRouteError, QuoteError

BODY = (
    b'{"carrier": "Harborline", "price": {"amount": "137.50", "currency": "EUR"}, '
    b'"transit_days": 2, "fuel_surcharge_pct": "6.5"}'
)


def fake_transport(request, timeout):
    return BODY


def failing(error):
    def transport(request, timeout):
        raise error

    return transport


def test_quote_requests_the_expected_url():
    seen = []

    def transport(request, timeout):
        seen.append((request.full_url, timeout))
        return BODY

    client = FreightClient(base_url="https://rates.test.internal/v3/", transport=transport)
    quote = client.quote("NLRTM", "DEHAM", weight_kg=420, timeout=3.0)
    assert seen == [("https://rates.test.internal/v3/quote?from=NLRTM&to=DEHAM&kg=420", 3.0)]
    assert quote.carrier == "Harborline"


def test_unserved_route_is_a_no_route_error():
    error = urllib.error.HTTPError("u", 404, "Not Found", None, None)
    with pytest.raises(NoRouteError):
        FreightClient(transport=failing(error)).quote("NLRTM", "USNYC", 100)


@pytest.mark.parametrize(
    "error",
    [urllib.error.HTTPError("u", 503, "Unavailable", None, None), urllib.error.URLError("down"), TimeoutError("slow")],
)
def test_other_failures_are_quote_errors(error):
    with pytest.raises(QuoteError, match="rate service unavailable") as info:
        FreightClient(transport=failing(error)).quote("NLRTM", "DEHAM", 100)
    assert not isinstance(info.value, NoRouteError)


@pytest.mark.parametrize(
    ("origin", "destination", "weight"),
    [("nlrtm", "DEHAM", 10), ("NLRTM", "DEH", 10), ("N1RTM", "DEHAM", 10), ("NLRTM", "DEHAM", 0),
     ("NLRTM", "DEHAM", 20001), ("NLRTM", "DEHAM", 10.5), ("NLRTM", "DEHAM", True)],
)
def test_arguments_are_checked_before_requesting(origin, destination, weight):
    with pytest.raises(ValueError):
        FreightClient(transport=failing(AssertionError("no request expected"))).quote(origin, destination, weight)


def test_live_quote_for_standard_pallet():
    client = FreightClient()
    quote = client.quote("NLRTM", "DEHAM", weight_kg=420)  # real rate service
    assert quote.currency == "EUR"
    assert quote.total > 0
