# srv6_automation/cli.py

import click
from srv6_automation.core import run_srv6_test

@click.command()
@click.argument('prefix')
def main(prefix):
    """Run SRv6 automation on a given IPv6 prefix"""
    result = run_srv6_test(prefix)
    click.echo(result)

if __name__ == '__main__':
    main()
