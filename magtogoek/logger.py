from datetime import datetime

import click
import typing as tp


class Logger:
    """Logger object can log and print messages.

    Logger objects print log and warning messages  while building a
    logbook from them. The logbook is formatted as a string in
    `self.logbook`. Logger objects keep count of the warnings in
    `self.w_count`.

    Parameters
    ----------
    logbook : str, Default None.
        Formatted logbook.
    level : int,  Default 0.
        Level controls which messages are printed.
        [0: prints all, 1: print only warnings, 2: prints None]

    Attributes
    ----------
    logbook :
        String of the formatted logbook build from the different entries.
    w_count :
        Number of Warning.

    Methods
    -------
    section :
        Makes a new sections.

    log :
        Log and print a log message. Prints if level is greater or equal 0
    warning :
        Log and print warning message. Prints if level is greater or equal 1
    reset :
        Resets the logbook and the warning count.
    """

    def __init__(self, logbook: str = "", level: int = 0):

        self.logbook = logbook
        self.w_count = 0
        self.level = level

    def __repr__(self):
        return self.logbook

    def section(self, section: str, t: bool = False):
        """Add a new section.
        Parameters:
        -----------
        section:
           Section's names.
        t:
           Log time if True.

        """
        time = "" if t is False else " " + self._timestamp()
        self.logbook += "[" + section + "]" + time + "\n"
        click.secho(section, fg="green") if self.level < 1 else None

    def log(self, msg: tp.Union[str, tp.List[str]], t: bool = False):
        """Add a log.
        Parameters
        ----------
        msg :
           Message to log.
        t :
           Log time if True.
        """
        if isinstance(msg, list):
            [self.log(m, t=t) for m in msg]
        else:
            if self.level < 1:
                print(msg)
            msg = msg if t is False else self._timestamp() + " " + msg
            self.logbook += " " + msg + "\n"

    def warning(self, msg: str, t: bool = False):
        """Add a warning.
        Parameters
        ----------
        msg :
           Message to log.
        t :
           Log time if True.
        """
        if isinstance(msg, list):
            [self.warning(m, t=t) for m in msg]
        else:
            if self.level < 2:
                click.echo(click.style("WARNING: ", fg="yellow") + msg)
                self.w_count += 1
            msg = msg if t is False else self._timestamp() + " " + msg
            self.logbook += " WARNING: " + msg + "\n"

    def reset(self):
        """Reset w_count and logbook."""
        self.logbook = ""
        self.w_count = 0

    @staticmethod
    def _timestamp():
        """Make a time stamp"""
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")