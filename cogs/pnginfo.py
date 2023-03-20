from io import BytesIO
import json

import discord
from PIL import Image
from discord.ext import commands

from util.image_metadata import extract_metadata

with open('config.json', 'r') as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]
TARGET_GUILD_ID = config["DISCORD_GUILD_ID"]
TARGET_CHANNEL_ID = config["DISCORD_CHANNEL_ID"]


class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild.id == TARGET_GUILD_ID and message.channel.id == TARGET_CHANNEL_ID:
            print("Inside the target guild and channel")
            if message.attachments:
                attachment = message.attachments[0]
                if attachment.content_type.startswith('image/'):
                    await message.add_reaction('🔍')
                    await message.add_reaction('📥')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.user_id != self.bot.user.id:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            user = await self.bot.fetch_user(payload.user_id)
            attachment = message.attachments[0]

            buffer = BytesIO()
            await attachment.save(buffer)

            if payload.emoji.name == '🔍':
                with Image.open(buffer):
                    buffer.seek(0)
                    metadata = extract_metadata(buffer, filename=attachment.filename)
                    formatted_metadata = "\n".join([f"{key}: {value}" for key, value in metadata.items()])
                    await user.send(f"```{formatted_metadata}```")
                await message.remove_reaction('🔍', user)
            elif payload.emoji.name == '📥':
                buffer.seek(0)
                await user.send(file=discord.File(buffer, filename=attachment.filename))
                await message.remove_reaction('📥', user)


async def setup(bot):
    await bot.add_cog(ImageCog(bot))
