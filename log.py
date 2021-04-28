import logging, coloredlogs

logging.basicConfig(
    filename="debug.log",
    filemode="w",
    level=logging.INFO,
    format="%(asctime)s.%(msecs)d %(levelname)s %(module)s/%(funcName)s at %(lineno)d: %(message)s",
    datefmt="%H:%M:%S",
)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

fieldstyle = {'asctime': {'color': 'green'},
              'levelname': {'bold': True, 'color': 'white'},
              'filename': {'color': 'cyan'},
              'funcName': {'color': 'blue'}}

levelstyles = {'critical': {'bold': True, 'color': 'red'},
               'debug': {'color': 'magenta'},
               'error': {'color': 'red'},
               'info': {'color': 'white'},
               'warning': {'color': 'yellow'}}

coloredlogs.install(level=logging.INFO, logger=log, fmt='%(filename)s:%(lineno)s %(levelname)s %(message)s', field_styles=fieldstyle, level_styles=levelstyles)