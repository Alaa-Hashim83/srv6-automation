# SRv6 Automation with Python

This project automates Segment Routing over IPv6 (SRv6) configuration and validation on Cisco IOS-XR devices using Python libraries like Netmiko and NAPALM.

## Objectives
- Automate the creation of SRv6 tunnels and locator configuration.
- Validate configuration using CLI command outputs.
- Simplify and speed up testing cycles for new IOS-XR builds.

## Tools & Technologies
- Python 3
- Netmiko
- NAPALM
- Cisco IOS-XR
- GitHub Actions (planned for CI testing)

## Features
- Auto-generates SRv6 configurations
- Connects to routers via SSH
- Validates forwarding plane status
- Outputs logs and verification results

## Example
```bash
python3 automate_srv6.py --device router1.yaml --config srv6_config.yaml
