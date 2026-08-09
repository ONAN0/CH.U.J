import os
import json
import random
import datetime
from datetime import datetime, time
import discord
from discord import app_commands
from discord.ext import tasks
from functools import wraps   
from zoneinfo import ZoneInfo
from pathlib import Path

from chujlib import *

update_name: str = os.getenv("UPDATE_NAME")
log_conf_file: str = os.getenv("LOG_CONF_FILE")

songs_dir = os.getenv("SONGS_DIR")
episodes_dir = os.getenv("EPISODES_DIR")
authors_dir = os.getenv("AUTHORS_DIR")
days_dir = os.getenv("DAYS_DIR")

# discord
token: str = os.getenv("DISCORD_TOKEN")
guild = discord.Object(id=int(os.getenv("SERVER_ID")))
song_channel_id: int = int(os.getenv("SONG_CHANNEL_ID"))

# files
logo = Path(os.getenv("LOGO"))
glitch_img = Path(os.getenv("GLITCH_IMG"))
chuj_img = Path(os.getenv("CHUJ_IMG"))
fireworks = Path(os.getenv("FIREWORKS"))

# json
last_msg_file = os.getenv("LAST_MSG_FILE")
day_template_file = os.getenv("DAY_TEMPLATES_FILE")
quotes_file = os.getenv("QUOTES_FILE")
blacklist_file = os.getenv("BLACKLIST_FILE")

err_file = os.getenv("ERR_FILE")
logger = setup_logging("CHUJ_logger",log_conf_file, err_file, 1)

# ───────────────────────────────
# Discord client setup
# ───────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# ────────────────────────────────────────────────
# Decorator: restrict commands to specific channel
# ────────────────────────────────────────────────
def channel_only(channel_id: int):
   def decorator(func):
      @wraps(func)
      async def wrapper(interaction: discord.Interaction, *args, **kwargs):
         if interaction.channel.id != channel_id:
            await interaction.response.send_message(
               "Tu nemôžem",
               ephemeral=True
            )
            return
         return await func(interaction, *args, **kwargs)
      return wrapper
   return decorator

# ───────────────────────────────
# Additional functions
# ───────────────────────────────
def error_handler(name: str, value: str) -> tuple[discord.File, discord.Embed]:
   file = discord.File(glitch_img, filename=glitch_img.name)
   embed = discord.Embed(
      title="",
      description="# :warning: Chyba",
      color=0xFF0000,
   )
   embed.set_thumbnail(url=f"attachment://{glitch_img.name}")
   embed.add_field(name=name, value=value, inline=False)

   logger.error(f"{name}: {value}")
   return file, embed

def get_todays_template() -> dict | tuple[discord.File, discord.Embed]:
   try:
      with open(day_template_file) as day_template_list:
         todays_index: int = datetime.now().weekday()
         week: list[dict] = json.load(day_template_list)
         week[todays_index]['color'] = int(week[todays_index]['color'], 16)
      return week[todays_index]

   except FileNotFoundError:
      return error_handler("Súbor sa nenašiel",f"Skontroluj **{day_template_file}**") 

def get_songs(all_songs: list[dict], exclude: list[dict] | None = None) -> list[dict]:
   exclude = exclude or []
   selected_songs: list[dict] = []
   five_songs: list[dict] = []
   exclude_set: set[str] = {f"{song['artist']} - {song['title']}" for song in exclude}

   for song in all_songs:
      if song["artist"] == f"Unknown Artist":
         continue
      
      if f"{song['artist']} - {song['title']}" in exclude_set:
         continue
      
      selected_songs.append(song)

   if len(selected_songs) > 5:
      five_songs = random.sample(selected_songs, 5)
   else:
      five_songs = selected_songs

   return five_songs

def get_availabe_quotes(all_full_quotes:list[dict]) -> list[dict]:
   quotes: list[dict] = []

   for person in all_full_quotes:
      if person['isEmpty']:
         continue
      
      for quote in person['quotes']:
         if quote['wasUsed']:
            continue
      
         quotes.append({
               "image": person['image'],
               "author": person['author'],
               "quote": quote['quote'],
               "year": quote['year']
            })

   if not quotes:
      for person in all_full_quotes:
         for quote in person['quotes']:
            quote['wasUsed'] = False

            quotes.append({
               "image": person['image'],
               "author": person['author'],
               "quote": quote['quote'],
               "year": quote['year']
            })

         person['isEmpty'] = False

   return quotes

def select_quote() -> dict | tuple[discord.File, discord.Embed]:   
   try:
      with open(quotes_file, 'r') as quotes_list:
         quotes: list[dict] = json.load(quotes_list)
   except FileNotFoundError:
      return error_handler("Súbor sa nenašiel",f"Skontroluj **{quotes_file}**")

   available_quotes: list[dict] = get_availabe_quotes(quotes)

   chosen_quote: dict = random.choice(available_quotes)

   for person in quotes:
      if person['author'] != chosen_quote['author']:
         continue

      for quote in person['quotes']:
         if quote['quote'] == chosen_quote['quote']:
            quote['wasUsed'] = True
            
      if all(quote['wasUsed'] for quote in person['quotes']):
         person['isEmpty'] = True
   
   try:
      with open(quotes_file, 'w') as quotes_list:
         json.dump(quotes, quotes_list)
   except FileNotFoundError:
      return error_handler("Súbor sa nenašiel",f"Skontroluj **{quotes_file}**")

   return chosen_quote

def create_song_list(songs_file: str) -> tuple[discord.File, discord.Embed]:
   # Generates an embed with 5 random songs from today's song_file.
   blacklist: list[dict] = []
   todays_template: dict | tuple[discord.File, discord.Embed] = get_todays_template()

   # if the template returned is a dict, it was successful, create the (file, embed) message
   # else if it returns an error (tuple[file, embed]), just pass it through
   if isinstance(todays_template, dict):
      try:
         with open(blacklist_file, "r") as ban_file:
            blacklist = json.load(ban_file)
      except FileNotFoundError:
         return error_handler("Súbor sa nenašiel",f"Skontroluj **{blacklist_file}** v priečinku s pesničkami")

      try:
         with open(songs_file, "r") as song_file:
            songs_list: list[dict] = json.load(song_file)
      except FileNotFoundError:
         return error_handler("Súbor sa nenašiel",f"Skontroluj **{songs_file}** v priečinku s pesničkami")

      if 'songs_list' in locals():
         if not songs_list:
            return error_handler("Žiadne pesničky",f"Skontroluj **{songs_file}**") 
         else:      
            list_of_songs = get_songs(songs_list, blacklist)

            if not list_of_songs:
               file = discord.File(fireworks, filename=fireworks.name)
               description: str = "Gratulujem :partying_face:"
               logger.critical(f"Spustil sa ohňostroj.")
            else:
               file = discord.File(f"{days_dir}{todays_template['gif']}", filename=todays_template['gif'])
               description: str = "Dnešné pesničky:"

            embed = discord.Embed(
               title=f"{todays_template['emoji']} *{todays_template['color_name']}*",
               description=f"# {description}",
               color=todays_template['color'],
            )

            if not list_of_songs:
               embed.set_thumbnail(url=f"attachment://{fireworks}")
               embed.add_field(name="Neviem ako sa ti to podarilo, ale všetky dnešné pesničky sú na blackliste.", value="", inline=False)
            else:
               embed.set_thumbnail(url=f"attachment://{todays_template['gif']}")
               for song in list_of_songs:
                  try:
                     embed.add_field(name=f"{song['time']} {song['title']}", value=song['artist'], inline=False)
                  except ValueError:
                     embed.add_field(name=song, value="(neznámy formát)", inline=False)

               embed.add_field(name="\u200b", value="Nový deň, nové songy, a snaď aj nová storka. :smile:", inline=False)

            return file, embed

   elif isinstance(todays_template, tuple):
      return todays_template
   
   else:
      return error_handler("Neznáma chyba","Čo sa kurva deje?")

def create_episode_list(episodes_file: str) -> tuple[discord.File, discord.Embed]:
   try:
      with open(episodes_file, "r") as episode_file:
         episodes_list: list[dict] = json.load(episode_file)
   except FileNotFoundError:
      return error_handler("Súbor sa nenašiel",f"Skontroluj **{episodes_file}** v priečinku s pesničkami")

   if 'episodes_list' in locals():
      if not episodes_list:
         file = discord.File(logo, filename=logo.name)
         embed = discord.Embed(description=f"# Neni čo", color=0x96120F)
         embed.set_thumbnail(url=f"attachment://{logo.name}")
         embed.add_field(name="Dnes sa nám nenašla žiadna epizóda vysielaná v tento deň v minulosti.", value="", inline=False)
         return file, embed

      else:
         file = discord.File(logo, filename=logo.name)
         embed = discord.Embed(description=f"# Vysielali sme", color=0x96120F)
         embed.set_thumbnail(url=f"attachment://{logo.name}")

         for episode in episodes_list:
            dt = datetime.fromisoformat(episode['Date'])
            formatted = dt.strftime("%d.%m.%Y o %H:%M")
            try:
               embed.add_field(name=f"{episode['Title']}", value=formatted , inline=False)
            except ValueError:
               embed.add_field(name=episode, value="(neznámy formát)", inline=False)

         return file, embed

async def delete_message(ctx, msg_id: str):
   try:
      channel = getattr(ctx, "channel", None) or ctx
      msg_to_delete = await channel.fetch_message(int(msg_id))
      await msg_to_delete.delete()

      if isinstance(ctx, discord.Interaction):
         if not ctx.response.is_done():
            await ctx.response.send_message("Správa bola zmazaná. :wastebasket:", ephemeral=True)
      else:
         await channel.send("Čau", delete_after=0.2)

   except ValueError:
      msg = "Zlé ID správy, bráško."
   except discord.NotFound:
      msg = "Správu som nenašiel."
   except discord.Forbidden:
      msg = "Nemám povolenie túto správu zmazať."
   except discord.HTTPException:
      msg = "Discord sa sekol, skús znova."
   else:
      return

   if isinstance(ctx, discord.Interaction):
      if not ctx.response.is_done():
         await ctx.response.send_message(msg, ephemeral=True)
      else:
            await ctx.followup.send(msg, ephemeral=True)
   else:
      await channel.send(msg, delete_after=3)

# ─────────────────────────────────────────────────────────────
# DISCORD commands
# ─────────────────────────────────────────────────────────────

@tree.command(name="help", 
   description="vypíše ti manuál s možnými príkazmi",
   guild=guild,
)
@channel_only(song_channel_id)
async def help_command(interaction: discord.Interaction):
   file = discord.File(chuj_img, filename=chuj_img.name)
   embed = discord.Embed(title="", description="# CH.U.J v2.3.0", color=0x96120F)
   embed.add_field(
      name="",
      value=f"the **{update_name}** update",
      inline=False,
   )
   embed.set_thumbnail(url=f"attachment://{chuj_img.name}")

   embed.add_field(name="/help", value="vypíše ti tento manuál", inline=False)
   embed.add_field(name="/rerun", value="pošle nových 5 pesničiek", inline=False)
   embed.add_field(name="/delete <id_spravy>", value="zmaže moju správu", inline=False)
   embed.add_field(name="/blacklist <interpret> <meno_piesne>", value="pridá pieseň na blacklist na 30 dní", inline=False)
   embed.add_field(name="/episodes", value="pošle zoznam epizód vysielaných v rovnaký dátum predošlé roky", inline=False)

   await interaction.response.send_message(file=file, embed=embed)

@tree.command(name="rerun", 
   description="pošle nových 5 pesničiek", 
   guild=guild,
)
@channel_only(song_channel_id)
async def rerun(interaction: discord.Interaction):
   await interaction.response.defer(thinking=True)

   try:
      with open(last_msg_file, "r") as ids_file:
         ids: dict = json.load(ids_file)
         last_songs_id: int = ids['songs']
   except FileNotFoundError:
      file, embed = error_handler("Súbor sa nenašiel",f"Skontroluj **{last_msg_file}**")

   if 'last_songs_id' in locals():
      if not last_songs_id:
         file, embed = error_handler("Žiadne ID správy",f"V súbore **{last_msg_file}** sa nenachádza žiadne ID správy")
      elif last_songs_id > 0:
         await delete_message(interaction, last_songs_id)

         songs_date = datetime.now().strftime("%Y-%m-%d")
         songs_file = f"{songs_dir}{songs_date}.json"
         file, embed = create_song_list(songs_file)
   
   rerun_msg = await interaction.followup.send(file=file,embed=embed)
   ids['songs'] = rerun_msg.id

   with open(last_msg_file, "w") as ids_file:
      json.dump(ids, ids_file)

@tree.command(name="episodes",
   description="pošle zoznam epizód vysielaných v rovnaký dátum minule roky",
   guild=guild,
)
@channel_only(song_channel_id)
async def episodes(interaction: discord.Interaction):
   await interaction.response.defer(thinking=True)
   
   try:
      with open(last_msg_file, "r") as ids_file:
         ids: dict = json.load(ids_file)
         last_episodes_id: int = ids['episodes']
   except FileNotFoundError:
      file, embed = error_handler("Súbor sa nenašiel",f"Skontroluj **{last_msg_file}**")

   if 'last_episodes_id' in locals():
      if not last_episodes_id:
         file, embed = error_handler("Žiadne ID správy",f"V súbore **{last_msg_file}** sa nenachádza žiadne ID správy")
      elif last_episodes_id > 0:
         await delete_message(interaction, last_episodes_id)

         episodes_date = datetime.now().strftime("%Y-%m-%d")
         episodes_file = f"{episodes_dir}{episodes_date}.json"
         file, embed = create_episode_list(episodes_file)

   episodes_msg = await interaction.followup.send(file=file,embed=embed)
   ids['episodes'] = episodes_msg.id

   with open(last_msg_file, "w") as ids_file:
      json.dump(ids, ids_file)

@tree.command(name="delete",
   description="umožňuje ti mazať moje správy, ak sú zbytočne navyše",
   guild=guild,
)
@channel_only(song_channel_id)
async def delete_command(interaction: discord.Interaction, id_spravy: str):
   await delete_message(interaction, id_spravy)

@tree.command(name="blacklist",
   description="pridá pieseň na blacklist na 30 dní",
   guild=guild,
)
@channel_only(song_channel_id)
async def blacklist(interaction: discord.Interaction, interpret: str, meno_piesne: str):
   today = datetime.now().strftime("%Y-%m-%d")
   blacklist_path: str = blacklist_file

   try:
      with open(blacklist_path, "r") as file:
         blacklist: list[dict] = json.load(file)
   except FileNotFoundError as e:
      msg = f"Error reading from blacklist file: {e}"
      logger.error(msg)

   blacklist.append({"artist":interpret, "title":meno_piesne, "timeOfBan":today})

   try:
      with open(blacklist_path, "w") as file:
         json.dump(blacklist, file)
      msg = f"Pieseň **{meno_piesne}** od **{interpret}** bola pridaná na blacklist"
   except Exception as e:
      msg = f"Error writing to blacklist file: {e}"
      logger.error(msg)

   await interaction.response.send_message(msg, ephemeral=True)

# ─────────────────────────────────────────────────────────────
# Periodic tasks
# ─────────────────────────────────────────────────────────────

@tasks.loop(time=time(hour=12, minute=5, tzinfo=ZoneInfo("Europe/Bratislava")))
async def Periodic_rerun():
   channel = client.get_channel(song_channel_id)
   if not channel:
      print("⚠️ Channel not found.")
      return

   try:
      with open(last_msg_file, "r") as ids_file:
         ids: dict = json.load(ids_file)
         last_songs_id: int = ids['songs']
   except FileNotFoundError:
      file, embed = error_handler("Súbor sa nenašiel",f"Skontroluj **{last_msg_file}**")

   if last_songs_id:
      await delete_message(channel, last_songs_id)

   songs_date = datetime.now().strftime("%Y-%m-%d")
   songs_file = f"{songs_dir}{songs_date}.json"
   file, embed = create_song_list(songs_file)
   song_msg = await channel.send(file=file, embed=embed)

   try:
      ids['songs'] = song_msg.id
      with open(last_msg_file, "w") as ids_file:
         json.dump(ids, ids_file)
   except FileNotFoundError:
      error_handler("Súbor sa nenašiel",f"Skontroluj **{last_msg_file}**")

@tasks.loop(time=time(hour=12, minute=6, tzinfo=ZoneInfo("Europe/Bratislava")))
async def Periodic_episodes():
   channel = client.get_channel(song_channel_id)
   if not channel:
      print("⚠️ Channel not found.")
      return

   try:
      with open(last_msg_file, "r") as ids_file:
         ids: dict = json.load(ids_file)
         last_episodes_id: int = ids['episodes']
   except FileNotFoundError:
      file, embed = error_handler("Súbor sa nenašiel",f"Skontroluj **{last_msg_file}**")

   if last_episodes_id:
      await delete_message(channel, last_episodes_id)

   episodes_date = datetime.now().strftime("%Y-%m-%d")
   episodes_file = f"{episodes_dir}{episodes_date}.json"
   file, embed = create_episode_list(episodes_file)
   episode_msg = await channel.send(file=file, embed=embed)

   try:
      ids['episodes'] = episode_msg.id
      with open(last_msg_file, "w") as ids_file:
         json.dump(ids, ids_file)
   except FileNotFoundError:
      error_handler("Súbor sa nenašiel",f"Skontroluj **{last_msg_file}**")

# ─────────────────────────────────────────────────────────────
# Events
# ─────────────────────────────────────────────────────────────

@client.event
async def on_message(message: discord.Message):
   if message.author.bot:
      return

   if message.content.startswith("!TLIS"):
      await message.delete()
      
      quote: dict | tuple[discord.File, discord.Embed] = select_quote()

      if isinstance(quote, dict):
         file = discord.File(f"{authors_dir}{quote['image']}", filename=quote['image'])
         embed = discord.Embed(
            title=quote['quote'],
            description=f"{quote['author']} {quote['year']}",
            color=random.choice([0x96120F, 0x000000, 0xE6E7EB]),
         )
         embed.set_thumbnail(url=f"attachment://{quote['image']}")
      elif isinstance(quote, tuple):
         file, embed = quote
      else:
         file, embed = error_handler("Neznáma chyba","Čo sa kurva deje?")
   
      await message.channel.send(file=file, embed=embed)

@client.event
async def on_ready():
   await tree.sync(guild=guild)
   print("✅ Bot is up and ready!")
   Periodic_rerun.start()
   Periodic_episodes.start()

client.run(token)