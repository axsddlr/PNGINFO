from io import BytesIO
import json

import discord
from PIL import Image
from discord.ext import commands
from discord import RawReactionActionEvent
from pathlib import Path
import yaml

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

        for attachment in message.attachments:
            if (
                not attachment.content_type.startswith("image/")
                or attachment.content_type == "image/gif"
            ):
                continue

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

            if payload.emoji.name == "🔍":
                if len(message.attachments) == 1:
                    attachment = message.attachments[0]
                    buffer = BytesIO()
                    await attachment.save(buffer)
                    with Image.open(buffer) as image:
                        buffer.seek(0)
                        metadata = extract_metadata(
                            buffer, image, filename=attachment.filename
                        )
                        embed_dict = {
                            key: str(value) for key, value in metadata.items()
                        }
                        embed = get_embed(embed_dict, message)
                        if user:
                            await user.send(embed=embed)
                else:
                    parameters_yaml_data = []
                    for attachment in message.attachments:
                        buffer = BytesIO()
                        await attachment.save(buffer)
                        with Image.open(buffer) as image:
                            buffer.seek(0)
                            metadata = extract_metadata(
                                buffer, image, filename=attachment.filename
                            )
                            negative_prompt = (
                                metadata.get("Negative Prompt", "")
                                .replace("\\", "")
                                .replace("\n", " ")
                            )
                            prompt = metadata.get("Prompt", "").replace("\n", " ")

                            # Reorder metadata to place "Prompt" above "Negative Prompt"
                            reordered_metadata = {
                                "Prompt": prompt,
                                "Negative Prompt": negative_prompt,
                                **{
                                    k: v
                                    for k, v in metadata.items()
                                    if k not in ["Prompt", "Negative Prompt"]
                                },
                            }

                            parameters_yaml_data.append(
                                f"\n{attachment.filename}:\n{yaml.dump(reordered_metadata, default_flow_style=False, allow_unicode=True)}\n---\n"
                            )

                    yaml_data = "".join(parameters_yaml_data)
                    parameters_file = discord.File(
                        BytesIO(yaml_data.encode("utf-8")), filename="parameters.yml"
                    )
                    if user:
                        original_post_link = f"https://discordapp.com/channels/{message.guild.id}/{message.channel.id}/{message.id}"
                        await user.send(
                            content=f"Original post: {original_post_link}",
                            file=parameters_file,
                        )
            elif payload.emoji.name == "✉️":
                if user:
                    files = []
                    for attachment in message.attachments:
                        buffer = BytesIO()
                        await attachment.save(buffer)
                        buffer.seek(0)
                        files.append(discord.File(buffer, filename=attachment.filename))

                    await user.send(files=files)


async def setup(bot):
    await bot.add_cog(ImageCog(bot))
