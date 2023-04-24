import json
import os

import discord
from discord.ext import commands
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
)


with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def startup(self):
        await bot.wait_until_ready()
        await bot.tree.sync()
        print("Sucessfully synced applications commands")
        print(f"Connected as {bot.user}")

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                    print("{0} is online".format(filename[:-3]))
                except Exception as e:
                    print("{0} was not loaded".format(filename))
                    print(f"[ERROR] {e}")

        self.loop.create_task(self.startup())


bot = Bot()
# get string from config file
bot.run(TOKEN)
