import sys

import pytest

from pdfseal import (
    NotAPdfError,
    SignError,
    ToolNotFoundError,
    UnknownKeyError,
    build_sign_command,
    run_tool,
    sign_pdf,
)

MINIMAL_PDF = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


def test_sign_command_with_all_options():
    assert build_sign_command("out/invoice.pdf", "finance-2026", reason="approved", stamp=True) == [
        "pdfsignctl", "sign", "--key", "finance-2026", "--in", "out/invoice.pdf",
        "--reason", "approved", "--stamp",
    ]  # fmt: skip


def test_sign_command_minimal(tmp_path):
    assert build_sign_command(tmp_path / "A.PDF", "k42") == [
        "pdfsignctl", "sign", "--key", "k42", "--in", str(tmp_path / "A.PDF"),
    ]  # fmt: skip


@pytest.mark.parametrize("key_id", ["", "ab", "Finance", "-fin", "has space", "x" * 41])
def test_bad_key_ids(key_id):
    with pytest.raises(ValueError):
        build_sign_command("a.pdf", key_id)


@pytest.mark.parametrize("path", ["a.txt", "a.pdf.bak", "pdf"])
def test_path_must_be_a_pdf(path):
    with pytest.raises(ValueError):
        build_sign_command(path, "finance-2026")


@pytest.mark.parametrize("reason", ["", "  ", "one\ntwo"])
def test_bad_reasons(reason):
    with pytest.raises(ValueError):
        build_sign_command("a.pdf", "finance-2026", reason=reason)


def test_run_tool_returns_stdout():
    assert run_tool([sys.executable, "-c", "print('status: signed')"]) == "status: signed\n"


def test_exit_codes_map_to_errors():
    with pytest.raises(UnknownKeyError):
        run_tool([sys.executable, "-c", "import sys; sys.exit(3)"])
    with pytest.raises(NotAPdfError):
        run_tool([sys.executable, "-c", "import sys; sys.exit(4)"])
    with pytest.raises(SignError, match="9") as info:
        run_tool([sys.executable, "-c", "import sys; sys.stderr.write('boom'); sys.exit(9)"])
    assert "boom" in str(info.value)


def test_missing_command_and_timeout():
    with pytest.raises(ToolNotFoundError):
        run_tool(["pdfseal-no-such-command"])
    with pytest.raises(SignError, match="timed out"):
        run_tool([sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)


def test_signs_invoice_with_finance_key(tmp_path):
    pdf = tmp_path / "invoice.pdf"
    pdf.write_bytes(MINIMAL_PDF)
    report = sign_pdf(pdf, "finance-2026", reason="approved")  # runs the real pdfsignctl
    assert report.status == "signed"
    assert report.signer.startswith("CN=finance-2026")
    assert report.digest.startswith("sha256:")
