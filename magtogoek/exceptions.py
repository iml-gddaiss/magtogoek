import sys
import click

class MagtogoekException(Exception):
    pass

class MagtogoekExit(MagtogoekException):
    """Exception raised when the program exits."""
    def __init__(self, message: str=None):
        click.secho(f'{message}',  err=True, fg='red')
        sys.exit()


