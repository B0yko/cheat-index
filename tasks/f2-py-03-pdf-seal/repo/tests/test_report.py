import pytest

from pdfseal import ReportError, SignReport, parse_report

FULL = """status: signed
signer: CN=finance-2026,O=Example Ltd
signed_at: 2026-03-02T09:30:11Z
digest: sha256:9f2c00aa11bb22cc33dd44ee55ff66778899aabbccddeeff0011223344556677
output: invoice.signed.pdf
"""


def test_full_report():
    report = parse_report(FULL)
    assert report == SignReport(
        status="signed",
        signer="CN=finance-2026,O=Example Ltd",
        signed_at="2026-03-02T09:30:11Z",
        digest="sha256:9f2c00aa11bb22cc33dd44ee55ff66778899aabbccddeeff0011223344556677",
        output="invoice.signed.pdf",
    )
    assert report.ok


def test_status_only_and_ignored_lines():
    report = parse_report("\nTool version 4.2\nSTATUS:  valid \nmode: strict\n")
    assert report == SignReport(status="valid")


def test_value_keeps_later_colons():
    assert parse_report("status: signed\nsigned_at: 2026-03-02T09:30:11Z").signed_at == "2026-03-02T09:30:11Z"


@pytest.mark.parametrize("status", ["invalid", "expired"])
def test_not_ok_statuses(status):
    assert not parse_report(f"status: {status}").ok


@pytest.mark.parametrize(
    "text",
    ["", "signer: CN=a", "status: pending", "status:", "status: signed\ndigest: md5:abcd", "status: signed\ndigest: sha256:xyz"],
)
def test_bad_reports(text):
    with pytest.raises(ReportError):
        parse_report(text)
