from io import BytesIO
import json

import discord
from PIL import Image
from discord.ext import commands
from discord import RawReactionActionEvent

from util.image_metadata import (
    extract_metadata,
    get_embed,
    read_info_from_image_stealth,
)

with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]
TARGET_GUILD_ID = config["DISCORD_GUILD_ID"]
TARGET_CHANNEL_ID = config["DISCORD_CHANNEL_ID"]


class ImageCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.attachments:
            return

        if not message.attachments:  # Check if the message has attachments
            return

        attachment = message.attachments[0]
        if (
            not attachment.content_type.startswith("image/")
            or attachment.content_type == "image/gif"
        ):
            return

        if (
            message.guild.id == TARGET_GUILD_ID
            and message.channel.id == TARGET_CHANNEL_ID
        ):
            buffer = BytesIO()
            await attachment.save(buffer)

            with Image.open(buffer) as image:
                buffer.seek(0)
                metadata_text = read_info_from_image_stealth(image)

            if metadata_text:
                await message.add_reaction("🔍")
            else:
                await message.add_reaction("ℹ️")

            await message.add_reaction("✉️")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        if payload.user_id != self.bot.user.id:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            user = await self.bot.fetch_user(payload.user_id)
            attachment = message.attachments[0]

            buffer = BytesIO()
            await attachment.save(buffer)

            # Check the bot's permissions in the channel
            # bot_member = channel.guild.get_member(self.bot.user.id)
            # bot_permissions = channel.permissions_for(bot_member)

            # Print the bot's permissions
            # print(f"Bot permissions in channel {channel.name}: {bot_permissions}")

            if payload.emoji.name == "🔍":
                with Image.open(buffer) as image:
                    buffer.seek(0)
                    metadata = extract_metadata(
                        buffer, image, filename=attachment.filename
                    )
                    embed_dict = {key: str(value) for key, value in metadata.items()}
                    embed = get_embed(embed_dict, message)
                    if user:  # Check if user is not None
                        await user.send(embed=embed)
                # await message.remove_reaction("🔍", user)
            elif payload.emoji.name == "✉️":
                buffer.seek(0)
                if user:  # Check if user is not None
                    await user.send(
                        file=discord.File(buffer, filename=attachment.filename)
                    )
                # await message.remove_reaction("✉️", user)
            elif payload.emoji.name == "ℹ️" and not payload.member.bot:
                if user:  # Check if user is not None
                    await user.send(
                        f"{user.mention}, This extension is for bypassing Discord exif data stripping Only works for png image. Here's the link to the GitHub repository for more information:\nhttps://github.com/ashen-sensored/sd_webui_stealth_pnginfo"
                    )


async def setup(bot):
    await bot.add_cog(ImageCog(bot))
