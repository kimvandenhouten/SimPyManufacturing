import logging.config
import sys

from general.config import Config


def get_logger(name):
    if not getattr(get_logger, 'configured', False):
        config = Config.get("tool", "logging")
        if not config:
            raise KeyError("No logging configuration found")

        # NOTE: due to a bug in the logging library (?), handlers and formatters can't reliably be set through
        # dictConfig(). We set them manually now.

        console_handler = logging.StreamHandler(sys.stdout)
        format_dict = config.pop('formatters', {}).get('formatter', {})
        if format_dict:
            formatter = logging.Formatter(format_dict.get('format'))
            if 'default_time_format' in format_dict:
                formatter.default_time_format = format_dict['default_time_format']
            console_handler.setFormatter(formatter)
        logging.getLogger().addHandler(console_handler)

        logging.config.dictConfig(config)
        setattr(get_logger, 'configured', True)

    return logging.getLogger(name)
