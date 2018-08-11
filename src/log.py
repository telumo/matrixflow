import logging



logging.basicConfig(
    format='%(asctime)s %(message)s',
    datefmt='%Y/%m/%d %p %I:%M:%S',
    #filename="/root/share/var/log/error.log",
    level=logging.INFO
)

def log_info(msg):
    if not isinstance(msg, str):
        msg = str(msg)
    logging.info(msg)

def log_debug(msg):
    if not isinstance(msg, str):
        msg = str(msg)
    logging.debug(msg)
