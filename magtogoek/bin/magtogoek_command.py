"""
Test for dev click
"""
import click
from pathlib import Path

from magtogoek.metadata.toolbox import json2dict

logos = json2dict(Path(__file__).parents[0] / Path("logo.json"))

magtogoek_version = "0.0.1"  # FIXME


def logo(process=None):
    click.echo("=" * 80)
    click.echo(click.style(logos["magtogoek"], fg="blue"))
    if process == "adcp":
        click.echo(click.style(logos["adcp"], fg="red"))
    click.echo(
        click.style(
            f"version: {magtogoek_version}".ljust(72, " ") + " config ", fg="green"
        )
    )
    click.echo("=" * 80)


@click.group(invoke_without_command=True)
def description():
    click.echo("DESCRIPTION")


class GlobalHelp(click.Command):
    def format_help(self, ctx, formatter):
        print(ctx.__dict__)
        click.echo("My custom help message")


@click.command(cls=GlobalHelp)
@click.argument("process", required=False, default=None, type=str)
@click.argument("config_name", nargs=-1, type=str)
def test(process, config_name):

    if config_name:
        click.echo("Takes optional makes file and exit")
        exit()

    if process:
        logo(process)
        config_name = click.prompt("Provide a file name for the config `ini` file. ")
        click.echo("takes optional arguments and exit")
        exit()

    logo()
    process = click.prompt("What type of data do you want to process: [adcp] ")
    click.clear()
    logo(process)
    config_name = click.prompt("Provide a file name for the config `ini` file. ")
    click.echo("takes optional arguments and exit")
    exit()


# click.clear()


def main():
    test()
