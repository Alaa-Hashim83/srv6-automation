SRv6 Automation & Validation Framework (Python)

This project provides a modular and test-driven framework to automate, validate, and parse Segment Routing over IPv6 (SRv6) configurations—primarily for Cisco IOS-XR platforms, with support for other vendors planned.

It includes:
- SRv6 prefix validation & parsing
- Config parsing (locator / prefixes / END / PSP / USP)
- Automation hooks (via Netmiko / NAPALM)
- Fully tested with pytest (25 tests passed)
- Ready for CI/CD via GitHub Actions

Objectives:
- Automate SRv6 configuration & locator deployment
- Parse and validate SRv6 configurations programmatically
- Validate configuration from device CLI outputs
- Speed up test cycles for IOS-XR software builds
- Maintain testable, clean, modular Python code

Tools & Technologies:
- Python 3
- Netmiko
- NAPALM
- Cisco IOS-XR
- Pytest
- GitHub Actions (planned for CI)

Current Features:
- IPv6 & SRv6 prefix validation using ipaddress
- Enhanced SRv6 config parser:
  * Supports source-address, multiple locators, multiple prefixes
  * Supports micro-segment/END behaviors (uN, End.DX6, etc.)
  * Parses PSP / USP flags: psp, no psp, usp enable, etc.
  * Case-insensitive + trailing # comment support
- Backward-compatible output structure
- Fully tested with pytest

Repository Structure:
srv6-automation/
├── srv6_automation/
│   ├── srv6_utils.py
│   ├── cli.py
│   └── __init__.py
├── test/
│   └── test_srv6_utils.py
├── pyproject.toml
├── setup.py
├── requirements.txt
└── README.txt

Testing:
python -m pytest -q

Example – Validate SRv6 Prefix:
from srv6_automation.srv6_utils import is_valid_ipv6_prefix
print(is_valid_ipv6_prefix("2001:db8::/48"))  # True
print(is_valid_ipv6_prefix("bad::/64"))       # False

Example – Parse SRv6 Configuration:
from srv6_automation.srv6_utils import parse_srv6_config

config = '''
source-address 2001:db8::1
locator LOC1
  prefix 2001:db8:1::/48 behavior End.DX6 psp
  prefix 2001:db8:2::/48
'''

data = parse_srv6_config(config)
print(data["locators"]["LOC1"]["prefixes"])

Future Enhancements:
- GitHub Actions CI pipeline
- SRv6 CLI generator
- Netmiko/NAPALM config push
- NETCONF/YANG support
- RESTCONF & gNMI integration
- JSON/YAML export

CLI Example (work in progress):
python3 -m srv6_automation.cli --device router1.yaml --config srv6_config.yaml

Contributing:
Fork, contribute, or open an issue. All contributions are welcome.

Support:
Star ⭐ the repo if helpful and share with other network engineers.
