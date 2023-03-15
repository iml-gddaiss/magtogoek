import pytest
from click.testing import CliRunner
from magtogoek.app import magtogoek
import os


def call_command(command, args):
    runner = CliRunner()
    return runner.invoke(command, args=args)


def test_mtgk_info():
    result = call_command(magtogoek, args=['--info'])
    assert result.exit_code == 0


def test_config_adcp(filename='test_config.ini'):
    result = call_command(magtogoek, args=['config', 'adcp', filename, '--gen-name'])
    assert result.exit_code == 0
    os.remove(filename)


def test_config_platform(filename='test_plaform.json'):
    result = call_command(magtogoek, args=['config', 'platform', filename])
    assert result.exit_code == 0
    os.remove(filename)



