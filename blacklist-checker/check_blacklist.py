import os
from datetime import datetime , timedelta

from chujlib import *

log_conf_file: str = os.getenv("LOG_CONF_FILE")

err_file = os.getenv("ERR_FILE")
blacklist_file: str = os.getenv("BLACKLIST_FILE")

UNBAN_PERIOD = 30 # days
limit_day = (datetime.today() - timedelta(days=UNBAN_PERIOD)).date()

logger = setup_logging("check_blacklist_logger", log_conf_file, err_file, 2)

try:
   blacklist: list[dict] = imp_json(blacklist_file)
except Exception as exception:
   logger.exception(exception)

blacklist = [item for item in blacklist if datetime.strptime(item["timeOfBan"], "%Y-%m-%d").date() >= limit_day]

try:
   exp_json(blacklist_file, blacklist)
except Exception as exception:
   logger.exception(exception)
