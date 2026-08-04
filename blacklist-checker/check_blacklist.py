import os
from datetime import datetime , timedelta

from chujlib import *

log_conf_file: str = os.getenv("LOG_CONF_FILE")

# folders
logs_folder = os.getenv('LOG_FOLDER')
err_folder = os.getenv('ERRORS_FOLDER')
jsons_folder = os.getenv('JSONS_FOLDER')

# files
err_file = os.getenv("ERROR_FILE")
blacklist_file: str = os.getenv("BLACKLIST_FILE")

# paths
err_path: str = f"{logs_folder}{err_folder}{err_file}"
blacklist_path: str = f"{jsons_folder}{blacklist_file}"

unban_period = 30 # days
limit_day = (datetime.today() - timedelta(days=unban_period)).date()

today = datetime.today().strftime("%Y-%m-%d")

logger = setup_logging("check_blacklist_logger", log_conf_file, err_path, 2)

try:
   blacklist: list[dict] = imp_json(blacklist_path)
except Exception as exception:
   logger.exception(exception)

blacklist = [item for item in blacklist if datetime.strptime(item["timeOfBan"], "%Y-%m-%d").date() >= limit_day]

try:
   exp_json(blacklist_path, blacklist)
except Exception as exception:
   logger.exception(exception)
