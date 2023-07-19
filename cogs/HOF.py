import discord
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
INITIAL_CHANNEL_IDS = config["DISCORD_CHANNEL_IDS"]
UNIQUE_USERS_THRESHOLD = config["UNIQUE_USERS_THRESHOLD"]
DELAY_TIME = config["DELAY_TIME"]


class HofCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sent_messages = set()
        self.reactions_per_message = {}

    async def check_unique_reactions(self, payload, reaction_added):
        initial_channel_ids = INITIAL_CHANNEL_IDS
        for initial_channel_id in initial_channel_ids:
            if payload.channel_id == initial_channel_id:
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                await asyncio.sleep(DELAY_TIME)
                message = await channel.fetch_message(payload.message_id)

                if message.id in self.sent_messages:
                    return

                message_id = payload.message_id
                if message_id not in self.reactions_per_message:
                    self.reactions_per_message[message_id] = set()

                unique_users = self.reactions_per_message[message_id]

                for reaction in message.reactions:
                    if reaction.emoji not in ["🔍", "✉️"]:
                        async for user in reaction.users():
                            if user.id != message.author.id:
                                unique_users.add(user.id)

                self.reactions_per_message[message_id] = unique_users

                if len(unique_users) >= UNIQUE_USERS_THRESHOLD and reaction_added:
                    self.sent_messages.add(message.id)
                    destination_channel_id = TARGET_CHANNEL_ID
                    destination_channel = self.bot.get_channel(destination_channel_id)
                    logger.info(
                        f"Sending message to {destination_channel.name} in {destination_channel.guild.name} from {message.channel.name}"
                    )

                    content = (
                        f"**Reactions:** {len(unique_users)}\n"
                        f"**Original Post:** https://discord.com/channels/{message.guild.id}/{message.channel.id}/{message.id}\n"
                        f"**Author:** {message.author}\n"
                    )
                    if message.attachments and message.attachments[0].url:
                        content += f"**Attachment:** {message.attachments[0].url}\n"

                    await destination_channel.send(content)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.check_unique_reactions(payload, reaction_added=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.check_unique_reactions(payload, reaction_added=False)


async def setup(bot):
    await bot.add_cog(HofCog(bot))
