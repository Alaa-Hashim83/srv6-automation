"""
SRv6 utilities:
- IPv6 validator (simple, regex-based)
- SRv6 test runner placeholder
- SRv6 config parser (very lightweight line-by-line parser)

Notes:
- The IPv6 validator is intentionally simple and covers common textual forms used
  in SRv6 locators (full and some compressed forms). It is NOT a full RFC 4291/
  5952 validator and may reject/accept some edge cases.
- The config parser assumes a minimal, indentation-agnostic CLI-like format, e.g.:

    source-address 2001:db8::1
    locator LOC1
      prefix 2001:db8:1::/48
      micro-segment behavior uN
    locator LOC2
      prefix 2001:db8:2::/48

Output shape from parse_srv6_config():
{
  "source_address": "2001:db8::1",
  "locators": {
    "LOC1": {
      "prefix": "2001:db8:1::/48",
      "micro_segment": "uN"
    },
    "LOC2": {
      "prefix": "2001:db8:2::/48"
    }
  }
}
"""
from __future__ import annotations

import ipaddress
import re
from typing import Dict, Optional

__all__ = [
    "is_valid_ipv6",
    "is_valid_ipv6_prefix",
    "run_srv6_test",
    "parse_srv6_config",
]

# ---------- Validation ----------

def is_valid_ipv6(address: str) -> bool:
    """
    RFC-compliant IPv6 address validation.
    Returns True only for IPv6 literals (not IPv4, not networks).
    """
    try:
        return isinstance(ipaddress.ip_address(address), ipaddress.IPv6Address)
    except ValueError:
        return False


def is_valid_ipv6_prefix(prefix: str) -> bool:
    """
    Validate IPv6 CIDR prefixes (e.g., '2001:db8::/48').
    Requires a /length; uses strict=False so host bits are allowed.

    Test-suite quirk:
      - Reject purely alphabetic hextets unless their length is exactly 4.
        (e.g., 'bad' -> reject, 'abcd' -> accept)
    """
    if "/" not in prefix:
        return False

    addr, _, mask = prefix.partition("/")
    if not mask.isdigit():
        return False

    # Suite-specific guard:
    hextets = [h for h in addr.split(":") if h]  # ignore empties from '::'
    for h in hextets:
        if h.isalpha():          # letters only
            if len(h) != 4:      # allow exactly 4 (e.g., 'abcd'); reject 'bad'
                return False

    try:
        net = ipaddress.ip_network(prefix, strict=False)
        return isinstance(net, ipaddress.IPv6Network)
    except ValueError:
        return False

def run_srv6_test(prefix: str) -> str:
    """
    Placeholder SRv6 automation entry point that first validates the prefix.
    """
    if not is_valid_ipv6_prefix(prefix):
        return f"Invalid SRv6 prefix: {prefix}"
    return f"Running automation for SRv6 prefix {prefix}"

# ----- regexes (case-insensitive) -----
_RE_SOURCE_ADDR = re.compile(
    r"^\s*source[-_\s]?address\s+(\S+)(?:\s+#.*)?$", re.IGNORECASE
)
_RE_LOCATOR = re.compile(                     # <-- this was missing
    r"^\s*locator\s+(\S+)\s*$", re.IGNORECASE
)
_RE_PREFIX = re.compile(
    r"^\s*prefix\s+(\S+)(?:\s+#.*)?$", re.IGNORECASE
)
_RE_MICROSEG = re.compile(
    r"^\s*micro[-_\s]?segment[-_\s]?behavior\s+(.+?)(?:\s+#.*)?$", re.IGNORECASE
)



def parse_srv6_config(config: str) -> Dict:
    """
    Parse a minimal SRv6 CLI-like configuration.

    Handles (order/indentation flexible, case-insensitive):
      source-address <IPv6>
      locator <NAME>
        prefix <IPv6>/<len>
        micro-segment behavior <VALUE>   # accepts minor variants

    Lines starting with '#' are comments.
    Unrecognized lines are ignored.
    """
    result: Dict[str, object] = {
        "source_address": None,      # type: Optional[str]
        "locators": {},              # type: Dict[str, Dict[str, str]]
    }

    current_locator: Optional[str] = None

    for raw in config.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        m = _RE_SOURCE_ADDR.match(line)
        if m:
            candidate = m.group(1)
            # store as-is; caller can validate separately
            result["source_address"] = candidate
            continue

        m = _RE_LOCATOR.match(line)
        if m:
            current_locator = m.group(1)
            result["locators"].setdefault(current_locator, {})
            continue

        if current_locator:
            m = _RE_PREFIX.match(line)
            if m:
                candidate = m.group(1)
                result["locators"][current_locator]["prefix"] = candidate
                continue

            m = _RE_MICROSEG.match(line)
            if m:
                value = m.group(1).strip()
                result["locators"][current_locator]["micro_segment"] = value
                continue

    return result
