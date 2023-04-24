import discord
from discord import Permissions
from discord.ext import commands
import json
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

with open("config.json", "r") as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]
TARGET_GUILD_ID = config["DISCORD_GUILD_ID"]
TARGET_CHANNEL_ID = config["DESTINATION_DISCORD_CHANNEL_ID"]
INITIAL_CHANNEL_ID = config["DISCORD_CHANNEL_ID"]
UNIQUE_USERS_THRESHOLD = config["UNIQUE_USERS_THRESHOLD"]
DELAY_TIME = config["DELAY_TIME"]


class HofCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sent_messages = set()
        self.target_channel_permissions = asyncio.run(
            self.get_target_channel_permissions()
        )

    async def get_target_channel_permissions(self):
        guild = self.bot.get_guild(TARGET_GUILD_ID)
        channel = guild.get_channel(TARGET_CHANNEL_ID)
        me = guild.me
        return channel.permissions_for(me)

    def has_required_permissions(self, permissions: Permissions):
        required_permissions = ["send_messages", "embed_links"]
        missing_permissions = [
            perm_name
            for perm_name in required_permissions
            if not getattr(permissions, perm_name)
        ]
        return len(missing_permissions) == 0, missing_permissions

    async def check_unique_reactions(self, payload):
        initial_channel_id = INITIAL_CHANNEL_ID
        if payload.channel_id == initial_channel_id:
            channel = self.bot.get_channel(payload.channel_id)
            message = await channel.fetch_message(payload.message_id)
            await asyncio.sleep(DELAY_TIME)
            message = await channel.fetch_message(payload.message_id)

            if message.id in self.sent_messages:
                return

            unique_users = set()
            for reaction in message.reactions:
                if reaction.emoji not in ["🔍", "✉️"]:
                    async for user in reaction.users():
                        unique_users.add(user.id)

            if len(unique_users) >= UNIQUE_USERS_THRESHOLD:
                self.sent_messages.add(message.id)
                destination_channel_id = TARGET_CHANNEL_ID
                destination_channel = self.bot.get_channel(destination_channel_id)
                logger.info(
                    f"Sending message to {destination_channel.name} in {destination_channel.guild.name}"
                )

                has_perms, missing_perms = self.has_required_permissions(
                    self.target_channel_permissions
                )
                if not has_perms:
                    logger.warning(
                        f"Missing permissions in target channel: {', '.join(missing_perms)}"
                    )
                    return
                else:
                    logger.info("Has permissions")
                    embed = discord.Embed(
                        title=f"Reactions: {len(unique_users)} | {message.channel.name}",
                        description=f"[Original Post](https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id})",
                        timestamp=message.created_at,
                        color=discord.Color.gold(),
                    )
                    embed.set_author(
                        name=f"{message.author}",
                        icon_url=message.author.avatar.url,
                    )
                    if message.attachments and message.attachments[0].url:
                        embed.set_image(url=message.attachments[0].url)

                    await destination_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.check_unique_reactions(payload)


async def setup(bot):
    await bot.add_cog(HofCog(bot))
