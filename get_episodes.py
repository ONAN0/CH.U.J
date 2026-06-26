import os
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
import requests
import logging

load_dotenv()
episodes_url = os.getenv("EPISODES_URL")
#folders
logs_folder = os.getenv("LOG_FOLDER")
err_folder = os.getenv("ERRORS_FOLDER")
episodes_folder = os.getenv("EPISODES_FOLDER")
#files
err_file = os.getenv("ERROR_FILE")
#paths
err_logs_path = f"{logs_folder}{err_folder}"
episodes_logs_path = f"{logs_folder}{episodes_folder}"

os.makedirs(err_logs_path, exist_ok=True)
os.makedirs(episodes_logs_path, exist_ok=True)

logging.basicConfig(
   filename=f"{err_logs_path}{err_file}",
   level=logging.ERROR,
   format='[ {asctime} ] [ get_episodes.py ] [{levelname:^9s}] {message}',
   style="{",
   datefmt="%Y-%m-%d | %H:%M:%S"
)

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

def exp_json(filepath:str, data: dict | list[dict]) -> None:
   try:
      with open(filepath, "w") as file:
         json.dump(data, file)
   except FileNotFoundError as exception:
      logging.exception(f"File not found: {exception}")

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

            except requests.RequestException as exception:
               logging.exception(f"Failed for {offset_type} {offset_value}: {exception}")

   exp_json(episodes_path, episodes_list)

   return 0

if __name__ == "__main__":
   main()