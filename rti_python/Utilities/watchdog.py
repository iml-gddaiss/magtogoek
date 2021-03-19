from threading import Timer

class Watchdog:
    """
    Monitor a process to make sure it is still running.  If
    the process stops running, this will not be reset.  Then
    you can handle the situation.

    Usage if you want to make sure function finishes in less than x seconds:

    watchdog = Watchdog(x)
    try:
      # do something that might take too long
    except Watchdog:
      # handle watchdog error
    watchdog.stop()
    Usage if you regularly execute something and want to make sure it is executed at least every y seconds:

    import sys

    def myHandler():
      print "Whoa! Watchdog expired. Holy heavens!"
      sys.exit()

    watchdog = Watchdog(y, myHandler)

    def doSomethingRegularly():
      # make sure you do not return in here or call watchdog.reset() before returning
      watchdog.reset()

    """
    def __init__(self, timeout: int, userHandler=None):  # timeout in seconds
        """
        Initialize the watchdog.  Call the handler if the watchdog expires.
        :param timeout: Timeout to wait before checking.
        :param userHandler: Function to call if watchdog not pet.
        """
        self.timeout = timeout
        self.handler = userHandler if userHandler is not None else self.defaultHandler
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def pet(self):
        """
        Pet the watchdog.  If the function is working properly, this function will be called
        and the timer will be reset.
        :return:
        """
        self.timer.cancel()
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def stop(self):
        """
        Stop the watchdog.
        :return:
        """
        self.timer.cancel()

    def defaultHandler(self):
        """
        Default handler if nothing is given.
        :return:
        """
        raise self