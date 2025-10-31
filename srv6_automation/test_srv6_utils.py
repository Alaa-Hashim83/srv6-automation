import pytest
from srv6_utils import (
    is_valid_ipv6,
    is_valid_ipv6_prefix,
    run_srv6_test,
    parse_srv6_config,
)

# -------- IPv6 validation --------

@pytest.mark.parametrize("addr", [
    "2001:db8::1",
    "::1",
    "fe80::",
    "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
    "2001:db8:0:1::",
])
def test_is_valid_ipv6_true(addr):
    assert is_valid_ipv6(addr) is True

@pytest.mark.parametrize("addr", [
    "2001:db8::/48",     # network, not an address
    "2001:db8:::1",      # too many colons
    "gggg::1",           # invalid hex
    "",                  # empty
    "192.168.1.1",       # IPv4
])
def test_is_valid_ipv6_false(addr):
    assert is_valid_ipv6(addr) is False


# -------- IPv6 prefix validation --------

@pytest.mark.parametrize("cidr", [
    "2001:db8::/32",
    "2001:db8:1::/48",
    "2001:db8:abcd:1234::/64",
    "::/0",
    "fe80::/10",
])
def test_is_valid_ipv6_prefix_true(cidr):
    assert is_valid_ipv6_prefix(cidr) is True

@pytest.mark.parametrize("cidr", [
    "2001:db8::1",     # address, not network (we still accept strict=False, but without /len it's invalid)
    "2001:db8::/129",  # invalid mask
    "2001:db8::/abc",  # invalid mask
    "bad::/64",        # invalid hex
    "192.168.1.0/24",  # IPv4 network
])
def test_is_valid_ipv6_prefix_false(cidr):
    assert is_valid_ipv6_prefix(cidr) is False


# -------- run_srv6_test --------

def test_run_srv6_test_valid():
    assert "Running automation" in run_srv6_test("2001:db8::/32")

def test_run_srv6_test_invalid():
    msg = run_srv6_test("bad::/999")
    assert msg.startswith("Invalid SRv6 prefix")


# -------- parse_srv6_config --------

def test_parse_basic_config():
    text = """
    # sample
    source-address 2001:db8::1
    locator LOC1
      prefix 2001:db8:1::/48
      micro-segment behavior uN
    locator LOC2
      prefix 2001:db8:2::/48
    """
    data = parse_srv6_config(text)
    assert data["source_address"] == "2001:db8::1"
    assert "LOC1" in data["locators"]
    assert data["locators"]["LOC1"]["prefix"] == "2001:db8:1::/48"
    assert data["locators"]["LOC1"]["micro_segment"] == "uN"
    assert data["locators"]["LOC2"]["prefix"] == "2001:db8:2::/48"

def test_parse_is_tolerant_of_variants():
    text = """
    SOURCE-ADDRESS 2001:db8::123
    locator A
      PREFIX 2001:db8:aaaa::/48
      MICRO_segment-behavior uA
    """
    data = parse_srv6_config(text)
    assert data["source_address"] == "2001:db8::123"
    assert data["locators"]["A"]["prefix"] == "2001:db8:aaaa::/48"
    assert data["locators"]["A"]["micro_segment"] == "uA"

def test_parse_ignores_unknown_lines_and_comments():
    text = """
    # comment
    locator X
      something-unknown here
      prefix 2001:db8:1::/48  # trailing comment allowed
    """
    data = parse_srv6_config(text)
    assert data["locators"]["X"]["prefix"].startswith("2001:db8:1::/48")
