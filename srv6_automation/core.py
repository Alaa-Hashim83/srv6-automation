import re
from typing import Dict

def is_valid_ipv6(address: str) -> bool:
    pattern = (
        r"^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$|"
        r"^([0-9a-fA-F]{1,4}:){1,7}:$|"
        r"^:([0-9a-fA-F]{1,4}:){1,7}$"
    )
    return re.match(pattern, address) is not None

def run_srv6_test(prefix: str) -> str:
    if not is_valid_ipv6(prefix):
        return f"Invalid SRv6 prefix: {prefix}"
    # Placeholder for automation logic
    return f"Running automation for SRv6 prefix {prefix}"
    
def parse_srv6_config(config: str) -> Dict:
    data = {
        "source_address": None,
        "locators": {}
    }

    lines = config.strip().splitlines()
    current_locator = None

    for line in lines:
        line = line.strip()

        if line.startswith("source-address"):
            data["source_address"] = line.split()[1]

        elif line.startswith("locator "):
            parts = line.split()
            if len(parts) >= 2:
                current_locator = parts[1]
                data["locators"][current_locator] = {}

        elif line.startswith("prefix") and current_locator:
            prefix = line.split()[1]
            data["locators"][current_locator]["prefix"] = prefix

        elif line.startswith("micro-segment behavior") and current_locator:
            behavior = line.replace("micro-segment behavior", "").strip()
            data["locators"][current_locator]["micro_segment"] = behavior

    return data


