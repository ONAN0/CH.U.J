import os
import json
from datetime import datetime
from dotenv import load_dotenv
from chujlib import setup_logging
import requests

load_dotenv()
songs_url = os.getenv("SONGS_URL")
log_conf_file: str = os.getenv("LOG_CONF_FILE")

# folders
logs_folder = os.getenv("LOG_FOLDER")
err_folder = os.getenv("ERRORS_FOLDER")
songs_folder = os.getenv("SONGS_FOLDER")
jsons_folder = os.getenv("JSONS_FOLDER")

#files
err_file = os.getenv("ERROR_FILE")
last_song_file = os.getenv("LAST_SONG_FILE")

#paths
err_path: str = f"{logs_folder}{err_folder}{err_file}"
songs_logs_path: str = f"{logs_folder}{songs_folder}"
last_song_path: str = f"{jsons_folder}{last_song_file}"

os.makedirs(songs_logs_path, exist_ok=True)

logger = setup_logging("get_songs_logger",log_conf_file, err_path, False)

def del_duplicates(new_songs: list[dict], all_songs: list[dict] | None = None) -> list[dict]:
   all_songs = all_songs or []
   selected_songs: list[dict] = []
   all_songs_set: set[str] = {f"{song['artist']} - {song['title']}" for song in all_songs}

   for song in new_songs:
      if f"{song['artist']} - {song['title']}" in all_songs_set:
         continue

      selected_songs.append(song)

   all_songs.extend(selected_songs)

   return all_songs 

def fetch_song(song_url: str) -> dict:
   while True:
      try:
         response = requests.get(song_url, timeout=10)

         if response.status_code == 200:
            break

         logger.error(f"Failed request, status code: {response.status_code}")

      except requests.RequestException as exception:
         logger.exception(f"Request failed: {exception}")
   
   return response.json()

def imp_json(filepath:str) -> dict | list[dict] | None:
   try:
      with open(filepath, "r") as file:
         return json.load(file)
   except FileNotFoundError as exception:
      logger.exception(f"File not found: {exception}")
      return None

def exp_json(filepath:str, data: dict | list[dict]) -> None:
   try:
      with open(filepath, "w") as file:
         json.dump(data, file)
   except FileNotFoundError as exception:
      logger.exception(f"File not found: {exception}")

def main():
   song: dict = fetch_song(songs_url)

   today = datetime.now()
   songs_file: str = f"{songs_logs_path}{today.strftime('%Y-%m-%d')}.json"

   if "artist" not in song or "songTitle" not in song:
      return 0

   if os.path.exists(last_song_path):
      last_song: dict = imp_json(last_song_path)

      if song["artist"] == last_song["artist"] and song["songTitle"] == last_song["songTitle"]:
         return 0

   items: list[dict] = [{"time":today.strftime("%H:%M"), "artist":song["artist"], "title":song["songTitle"]}]

   if os.path.exists(songs_file):
      existing_songs: list[dict] = imp_json(songs_file)
      items: list[dict] = del_duplicates(items, existing_songs)
   
   exp_json(songs_file, items)
   exp_json(last_song_path, song)

   return 0

if __name__ == "__main__":
   main()
