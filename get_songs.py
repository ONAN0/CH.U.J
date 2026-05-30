import os
import json
import datetime
from dotenv import load_dotenv
import requests
import logging

# ───────────────────────────────
# Load environment variables
# ───────────────────────────────
load_dotenv()
# folders
logs_folder = os.getenv("LOG_FOLDER")
errors_folder = os.getenv("ERRORS_FOLDER")
songs_folder = os.getenv("SONGS_FOLDER")
jsons_folder = os.getenv("JSONS_FOLDER")
#files
errors_file = os.getenv("ERROR_FILE")
last_song_file = os.getenv("LAST_SONG_FILE")

last_song_path = f"{jsons_folder}{last_song_file}"

songs_url = os.getenv("SONGS_URL")

os.makedirs(f"{logs_folder}{errors_folder}", exist_ok=True)

logging.basicConfig(
   filename=f"{logs_folder}{errors_folder}{errors_file}",
   level=logging.ERROR,
   format='[ {asctime} ] [{levelname:^9s}] {message}',
   style="{",
   datefmt="%Y-%m-%d | %H:%M:%S"
)

def remove_duplicates(new_songs: list[dict], all_songs: list[dict] | None = None) -> list[dict]:
   all_songs = all_songs or []
   selected_songs: list[dict] = []
   all_songs_set: set[str] = {f"{song['artist']} - {song['title']}" for song in all_songs}

   for song in new_songs:
      if f"{song['artist']} - {song['title']}" in all_songs_set:
         continue

      selected_songs.append(song)

   all_songs.extend(selected_songs)

   return all_songs 

def main():
   while True:
      try:
         response = requests.get(songs_url, timeout=10)

         if response.status_code == 200:
            break

         logging.error(f"Failed request, status code: {response.status_code}")

      except requests.RequestException as e:
         logging.exception(f"Request failed: {e}")

   time = datetime.datetime.now().strftime("%H:%M")
   today = datetime.datetime.now().strftime("%Y-%m-%d")
   songs_file: str = f"{logs_folder}{songs_folder}{today}.json"
   song: dict = response.json()

   if "artist" not in song or "songTitle" not in song:
      return 0

   if os.path.exists(last_song_path):
      try:
         with open(last_song_path, "r") as last_song_data:
            last_song: dict = json.load(last_song_data)
      except FileNotFoundError as e:
         logging.exception(f"File not found: {e}")

      if song["artist"] == last_song["artist"] and song["songTitle"] == last_song["songTitle"]:
         return 0

   items: list[dict] = [{"time":time, "artist":song["artist"], "title":song["songTitle"]}]

   if os.path.exists(songs_file):
      try:
         with open(songs_file, "r") as songs_list:
            existing_songs: list[dict] = json.load(songs_list)
            items = remove_duplicates(items, existing_songs)
      except FileNotFoundError as e:
         logging.exception(f"File not found: {e}")

   try:
      with open(songs_file, "w") as songs_list:
         json.dump(items, songs_list)
   except FileNotFoundError as e:
      logging.exception(f"File not found: {e}")

   try:
      with open(last_song_path, "w") as last_song_data:
         json.dump(song, last_song_data)
   except FileNotFoundError as e:
      logging.exception(f"File not found: {e}")

   return 0

if __name__ == "__main__":
   main()
