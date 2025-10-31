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

import re
from typing import Dict

# Pre-compile the IPv6 regex once for performance and clarity.
# This is a SIMPLE matcher that covers:
#  - Full form:           xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx:xxxx
#  - Trailing ::         (compressed tail)
#  - Leading ::          (compressed head)
# It does not aim to be a complete RFC-compliant validator.
_IPV6_SIMPLE_RE = re.compile(
    r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|"   # full form
    r"^([0-9a-fA-F]{1,4}:){1,7}:$|"                # compressed tail (ends with ::)
    r"^:([0-9a-fA-F]{1,4}:){1,7}$"                 # compressed head (starts with ::)
)


def is_valid_ipv6(address: str) -> bool:
    """
    Return True if `address` looks like a valid (simplified) IPv6 literal.

    This uses a simplified regex suitable for many SRv6 locator checks,
    not a fully RFC-compliant validator.

    Args:
        address: IPv6 string to validate.

    Returns:
        bool: True if the address matches the simplified patterns; False otherwise.
    """
    return _IPV6_SIMPLE_RE.match(address) is not None


def run_srv6_test(prefix: str) -> str:
    """
    Dummy SRv6 automation entry point that first validates the SRv6 prefix.

    Args:
        prefix: SRv6 locator/prefix (e.g., '2001:db8:1::/48' or '2001:db8::1').

    Returns:
        str: A message indicating validation failure or a placeholder success note.
    """
    if not is_valid_ipv6(prefix):
        return f"Invalid SRv6 prefix: {prefix}"

    # Placeholder: insert your real SRv6 automation here
    return f"Running automation for SRv6 prefix {prefix}"


def parse_srv6_config(config: str) -> Dict:
    """
    Parse a minimal SRv6 CLI-like configuration blob.

    Expected directives (order is flexible):
      - 'source-address <IPv6>'
      - 'locator <NAME>'
      - 'prefix <IPv6>/<mask>'             (applies to the most recent locator)
      - 'micro-segment behavior <value>'   (applies to the most recent locator)

    The parser is whitespace-tolerant and does not require indentation.

    Args:
        config: Multiline string containing SRv6-related lines.

    Returns:
        Dict: Dictionary with keys:
              - "source_address": str | None
              - "locators": { <locator_name>: {"prefix": str, "micro_segment": str, ...}, ... }
    """
    data = {
        "source_address": None,
        "locators": {}
    }

    lines = config.strip().splitlines()
    current_locator = None  # Tracks which locator subsequent properties apply to

    for raw_line in lines:
        line = raw_line.strip()

        # Skip empty/comment lines if present
        if not line or line.startswith("#"):
            continue

        # Example: "source-address 2001:db8::1"
        if line.startswith("source-address"):
            parts = line.split()
            # Defensive: ensure there's a value after the keyword
            if len(parts) >= 2:
                data["source_address"] = parts[1]
            continue

        # Example: "locator LOC1"
        if line.startswith("locator "):
            parts = line.split()
            if len(parts) >= 2:
                current_locator = parts[1]
                # Initialize structure for this locator
                data["locators"].setdefault(current_locator, {})
            else:
                # No locator name provided; reset current locator to avoid mis-assignment
                current_locator = None
            continue

        # Subsequent keys require a current locator context
        if current_locator:
            # Example: "prefix 2001:db8:1::/48"
            if line.startswith("prefix"):
                parts = line.split()
                if len(parts) >= 2:
                    data["locators"][current_locator]["prefix"] = parts[1]
                continue

            # Example: "micro-segment behavior uN"
            if line.startswith("micro-segment behavior"):
                # Keep everything after the keyword to allow multi-token values
                behavior_value = line.replace("micro-segment behavior", "", 1).strip()
                data["locators"][current_locator]["micro_segment"] = behavior_value
                continue

        # Any other lines are ignored by this lightweight parser

    return data
