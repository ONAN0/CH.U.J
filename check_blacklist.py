import os
import json
import logging
from dotenv import load_dotenv
from datetime import datetime , timedelta

# ───────────────────────────────
# Load environment variables
# ───────────────────────────────
load_dotenv()
# folders
logs_folder = os.getenv('LOG_FOLDER')
err_folder = os.getenv('ERRORS_FOLDER')
jsons_folder = os.getenv('JSONS_FOLDER')
# files
blacklist_file: str = os.getenv("BLACKLIST_FILE")
err_file = os.getenv("ERROR_FILE")
# path
blacklist_path: str = f"{jsons_folder}{blacklist_file}"
err_log_path: str = f"{logs_folder}{err_folder}"

unban_period = 30 # days
limit_day = (datetime.today() - timedelta(days=unban_period)).date()

today = datetime.today().strftime("%Y-%m-%d")
os.makedirs(err_log_path, exist_ok=True)

logging.basicConfig(
   filename=f"{logs_folder}{err_folder}{err_file}",
   level=logging.DEBUG,
   format='[ {asctime} ] [ check_blacklist.py ] [{levelname:^9s}] {message}',
   style="{",
   datefmt="%Y-%m-%d | %H:%M:%S"
)

try:
   with open(blacklist_path, "r") as file:
      blacklist: list[dict] = json.load(file)
except FileNotFoundError as e:
   logging.exception(f"File not found: {e}")

blacklist = [item for item in blacklist if datetime.strptime(item["timeOfBan"], "%Y-%m-%d").date() >= limit_day]

try:
   with open(blacklist_path, "w") as file:
      json.dump(blacklist, file)
except Exception as e:
   logging.exception(f"Error writing to blacklist file: {e}")
