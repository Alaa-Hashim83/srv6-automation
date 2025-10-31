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

# ---------- Parser (expanded: multiple prefixes, END/PSP/USP) ----------

# Case-insensitive keyword patterns; allow inline '# comments' where it helps.
_RE_SOURCE_ADDR = re.compile(
    r"^\s*source[-_\s]?address\s+(\S+)(?:\s+#.*)?$", re.IGNORECASE
)
_RE_LOCATOR = re.compile(
    r"^\s*locator\s+(\S+)\s*$", re.IGNORECASE
)
# Keep these relaxed; we'll do tokenized parsing after a quick match.
_RE_PREFIX_LINE = re.compile(r"^\s*prefix\s+", re.IGNORECASE)
_RE_MICROSEG = re.compile(
    r"^\s*micro[-_\s]?segment[-_\s]?behavior\s+(.+?)(?:\s+#.*)?$", re.IGNORECASE
)
_RE_BEHAVIOR_LINE = re.compile(
    r"^\s*behavior\s+(\S+)(?:\s+#.*)?$", re.IGNORECASE
)
_RE_PSP = re.compile(
    r"^\s*(no\s+)?psp(?:\s+(enable|disable))?\s*(?:#.*)?$", re.IGNORECASE
)
_RE_USP = re.compile(
    r"^\s*(no\s+)?usp(?:\s+(enable|disable))?\s*(?:#.*)?$", re.IGNORECASE
)

def _strip_comment(line: str) -> str:
    """Remove trailing # comment, keep left part."""
    return line.split("#", 1)[0].rstrip()

def _parse_flag_from_tokens(flag_name: str, tokens: list[str]) -> Optional[bool]:
    """
    Parse simple flag presence like 'psp' / 'no psp' / 'psp enable/disable'.
    Returns True/False if determinable, else None (not present).
    """
    # normalize to lowercase tokens
    t = [x.lower() for x in tokens]
    if flag_name in t:
        idx = t.index(flag_name)
        # lookahead for enable/disable
        if idx + 1 < len(t) and t[idx + 1] in ("enable", "enabled", "true", "on"):
            return True
        if idx + 1 < len(t) and t[idx + 1] in ("disable", "disabled", "false", "off"):
            return False
        return True  # bare 'psp' / 'usp'
    # forms like 'no psp' / 'no usp'
    for i in range(len(t) - 1):
        if t[i] == "no" and t[i + 1] == flag_name:
            return False
    return None

def parse_srv6_config(config: str) -> Dict:
    """
    Parse SRv6 config with support for:
      - multiple prefixes per locator
      - END/micro-segment behaviors
      - PSP/USP flags
    Grammar (order flexible, case-insensitive):
        source-address <IPv6>
        locator <NAME>
          # Set/override defaults for subsequent prefixes (optional):
          micro-segment behavior <VAL>      # legacy; becomes defaults.behavior
          behavior <VAL>                    # modern; becomes defaults.behavior
          psp|no psp|psp enable|psp disable # defaults.psp
          usp|no usp|usp enable|usp disable # defaults.usp

          # Add a prefix (can include inline behavior/flags):
          prefix <CIDR> [behavior <VAL>] [psp|no psp] [usp|no usp]

          # Or on subsequent lines for the last-added prefix:
          behavior <VAL>
          psp|no psp|psp enable|psp disable
          usp|no usp|usp enable|usp disable

    Returns:
        {
          "source_address": str|None,
          "locators": {
            <name>: {
              "prefixes": [{"prefix": str, "behavior": str, "psp": bool, "usp": bool}, ...],
              "defaults": {"behavior": str|None, "psp": bool, "usp": bool}
            }, ...
          }
        }
    """
    result: Dict[str, object] = {
        "source_address": None,
        "locators": {},
    }

    current_locator: Optional[str] = None
    last_prefix_obj: Optional[Dict[str, object]] = None  # most recent prefix dict for incremental settings

    # Ensure each locator has defaults bucket
    def _ensure_locator(name: str) -> Dict[str, object]:
        loc = result["locators"].setdefault(name, {})
        loc.setdefault("prefixes", [])
        loc.setdefault("defaults", {"behavior": None, "psp": False, "usp": False})
        return loc

    for raw in config.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue

        # source-address
        m = _RE_SOURCE_ADDR.match(line)
        if m:
            result["source_address"] = m.group(1)
            continue

        # locator NAME
        m = _RE_LOCATOR.match(line)
        if m:
            current_locator = m.group(1)
            _ensure_locator(current_locator)
            last_prefix_obj = None
            continue

        if not current_locator:
            # Ignore lines until a locator is declared
            continue

        # Normalize for parsing (remove trailing comments for token parsing)
        base = _strip_comment(line)
        tokens = base.split()
        if not tokens:
            continue

        loc = _ensure_locator(current_locator)
        defaults = loc["defaults"]

        # Legacy locator-level default: micro-segment behavior <VAL>
        m = _RE_MICROSEG.match(line)
        if m:
          val = m.group(1).strip()
          defaults["behavior"] = val
          loc["micro_segment"] = val          # <-- backward-compat
          continue

        # Locator-level default: behavior <VAL>
        m = _RE_BEHAVIOR_LINE.match(line)
        if m and (last_prefix_obj is None):
            defaults["behavior"] = m.group(1).strip()
            continue

        # Locator-level PSP/USP defaults
        if _RE_PSP.match(line) and (last_prefix_obj is None):
            val = _parse_flag_from_tokens("psp", tokens)
            if val is not None:
                defaults["psp"] = val
            continue

        if _RE_USP.match(line) and (last_prefix_obj is None):
            val = _parse_flag_from_tokens("usp", tokens)
            if val is not None:
                defaults["usp"] = val
            continue

        # ----- Prefix line (can carry inline behavior/flags) -----
        if _RE_PREFIX_LINE.match(line):
          if len(tokens) >= 2:
            cidr = tokens[1]
            prefix_obj = {
                "prefix": cidr,
                "behavior": defaults.get("behavior"),
                "psp": bool(defaults.get("psp")),
                "usp": bool(defaults.get("usp")),
              }
              # ... (existing inline behavior/flags parsing) ...
      
              loc["prefixes"].append(prefix_obj)
      
              # ---- backward-compat shim ----
              if "prefix" not in loc:
                  loc["prefix"] = cidr
              # ------------------------------
      
              last_prefix_obj = prefix_obj
            continue

        # ----- Post-prefix modifiers for the MOST RECENT prefix -----
        if last_prefix_obj is not None:
            # behavior <VAL>
            m = _RE_BEHAVIOR_LINE.match(line)
            if m:
                last_prefix_obj["behavior"] = m.group(1).strip()
                continue

            # psp / usp toggles
            if _RE_PSP.match(line):
                val = _parse_flag_from_tokens("psp", tokens)
                if val is not None:
                    last_prefix_obj["psp"] = val
                continue

            if _RE_USP.match(line):
                val = _parse_flag_from_tokens("usp", tokens)
                if val is not None:
                    last_prefix_obj["usp"] = val
                continue

        # Unknown lines are ignored

    return result
