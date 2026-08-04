import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

from chujlib import *

episodes_url = os.getenv("EPISODES_URL")
log_conf_file: str = os.getenv("LOG_CONF_FILE")

#folders
logs_folder = os.getenv("LOG_FOLDER")
err_folder = os.getenv("ERRORS_FOLDER")
episodes_folder = os.getenv("EPISODES_FOLDER")

#files
err_file = os.getenv("ERROR_FILE")

#paths
err_path: str = f"{logs_folder}{err_folder}{err_file}"
episodes_logs_path = f"{logs_folder}{episodes_folder}"

os.makedirs(episodes_logs_path, exist_ok=True)

logger = setup_logging("get_episodes_logger",log_conf_file, err_path, 1)

def get_episodes_for_offset(today, year_offset: int = 0, month_offset: int = 0) -> list:
   
   target_date = today - relativedelta(years=year_offset, months=month_offset)

   start = target_date.replace(hour=0, minute=1, second=0, microsecond=0)
   end = target_date.replace(hour=23, minute=59, second=0, microsecond=0)

   params = {
      "filter[Date][_between]": f"{start.isoformat()},{end.isoformat()}",
      "sort": "Date",
   }

   response = requests.get(episodes_url, params=params, timeout=10)
   response.raise_for_status()

   return response.json().get("data", [])

def main():
   start_year: int = 2017
   today = datetime.now()
   #today = datetime(2026,1,31)
   year_difference: int = today.year - start_year
   month_difference: int = 3

   episodes_path: str = f"{episodes_logs_path}{today.strftime('%Y-%m-%d')}.json"

   offsets = {
      "year_offset": year_difference,
      "month_offset": month_difference
   }

   episodes_list = []

   for offset_type in offsets:
      for offset_value in range(1, offsets[offset_type] + 1):
         if offset_value > 0:
            try:
               episodes = get_episodes_for_offset(today=today, **{offset_type: offset_value})
               episodes_list.extend(episodes)
               if episodes:
                  logger.info(f"{episodes[0]["Title"]}")

            except requests.RequestException as exception:
               logger.exception(f"Failed for {offset_type} {offset_value}: {exception}")

   try:
      exp_json(episodes_path, episodes_list)
   except Exception as exception:
      logger.exception(exception)

   return 0

if __name__ == "__main__":
   main()