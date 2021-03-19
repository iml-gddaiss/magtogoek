import logging


class RtiLogger:
    """
    This is used to initialize the Logging.  This just sets the logging options.
    If you want to also log to a file, then give the file path.
    To Log:

    import logging
    logging.debug("DEBUG MESSAGE")
    """

    # Used to call a global logger
    # logger = logging.getLogger(RtiLogger.LOGGER_NAME)
    # logger.debug("debug message")
    LOGGER_NAME = 'root'

    @staticmethod
    def setup_custom_logger(name='root',
                            log_level=logging.DEBUG,
                            log_format='%(asctime)s - %(levelname)s - %(module)s - (%(threadName)-10s) - %(message)s',
                            file_path=None):

        # If a file path is given, then also log to a file
        if file_path:
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(logging.Formatter(log_format))
            logging.getLogger().addHandler(file_handler)

        formatter = logging.Formatter(fmt=log_format)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.setLevel(log_level)
        logger.addHandler(handler)
        return logger
