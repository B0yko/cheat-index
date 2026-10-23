import pytest

from dnsync import Change, RecordSet, change_payload, plan_changes


def rs(name, type_, *values, ttl=300):
    return RecordSet(name, type_, tuple(values), ttl)


def test_no_difference_no_changes():
    current = [rs("www.example.org", "CNAME", "host-10.example.net")]
    assert plan_changes(current, list(current)) == []


def test_create_update_delete():
    current = [rs("a.example.org", "CNAME", "host-1.example.net"), rs("b.example.org", "CNAME", "host-2.example.net")]
    desired = [rs("a.example.org", "CNAME", "host-9.example.net"), rs("c.example.org", "CNAME", "host-3.example.net")]
    changes = plan_changes(current, desired)
    assert [(c.action, c.record.name) for c in changes] == [
        ("create", "c.example.org"),
        ("update", "a.example.org"),
        ("delete", "b.example.org"),
    ]
    assert changes[1].record.values == ("host-9.example.net",)


def test_names_and_types_compare_case_insensitively():
    current = [rs("WWW.Example.org.", "cname", "host-10.example.net")]
    desired = [rs("www.example.org", "CNAME", "host-10.example.net")]
    assert plan_changes(current, desired) == []


def test_value_order_and_whitespace_do_not_matter():
    current = [rs("lb.example.org", "TXT", "token-1", "token-2")]
    desired = [rs("lb.example.org", "TXT", " token-2", "token-1 ")]
    assert plan_changes(current, desired) == []


def test_ttl_difference_is_an_update():
    current = [rs("www.example.org", "CNAME", "host-10.example.net", ttl=300)]
    desired = [rs("www.example.org", "CNAME", "host-10.example.net", ttl=60)]
    (change,) = plan_changes(current, desired)
    assert change.action == "update"
    assert change.record.ttl == 60


def test_platform_managed_types_are_ignored():
    current = [rs("example.org", "NS", "ns1.example.net"), rs("example.org", "SOA", "ns1 admin 1 2 3 4 5")]
    desired = [rs("example.org", "ns", "ns9.example.net")]
    assert plan_changes(current, desired) == []


def test_records_in_changes_are_normalised():
    (change,) = plan_changes([], [rs("Mail.Example.org.", "mx", "20 b.example.org", "10 a.example.org")])
    assert change.record == RecordSet("mail.example.org", "MX", ("10 a.example.org", "20 b.example.org"), 300)


def test_groups_and_sorting():
    desired = [rs("z.example.org", "CNAME", "host-1.example.net"), rs("a.example.org", "TXT", "x"), rs("a.example.org", "CNAME", "host-2.example.net")]
    names = [(c.record.name, c.record.type) for c in plan_changes([], desired)]
    assert names == [("a.example.org", "CNAME"), ("a.example.org", "TXT"), ("z.example.org", "CNAME")]


def test_duplicate_record_sets_are_rejected():
    dup = [rs("a.example.org", "CNAME", "host-1.example.net"), rs("A.example.org.", "CNAME", "host-2.example.net")]
    with pytest.raises(ValueError):
        plan_changes(dup, [])
    with pytest.raises(ValueError):
        plan_changes([], dup)


def test_change_payload():
    changes = [Change("create", rs("a.example.org", "CNAME", "host-1.example.net", ttl=120))]
    assert change_payload(changes) == {
        "changes": [{"action": "create", "name": "a.example.org", "type": "CNAME", "ttl": 120, "values": ["host-1.example.net"]}]
    }
