import discord
from discord.ext import commands
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s:%(levelname)s:%(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class HofCog(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.sent_messages = set()
        self.reactions_per_message = {}
        
        # Convert config values to proper types
        self.initial_channel_ids = set(
            map(int, config["DISCORD_CHANNEL_ID"])
            if isinstance(config["DISCORD_CHANNEL_ID"], list)
            else {int(config["DISCORD_CHANNEL_ID"])}
        )
        self.destination_channel_id = int(config["DESTINATION_DISCORD_CHANNEL_ID"])
        self.unique_users_threshold = int(config["UNIQUE_USERS_THRESHOLD"])
        self.delay_time = int(config["DELAY_TIME"])

    async def check_unique_reactions(self, payload, reaction_added):
        # Faster set membership check
        if payload.channel_id not in self.initial_channel_ids:
            return

        try:
            channel = self.bot.get_channel(payload.channel_id)
            if not channel:
                logger.error(f"Channel {payload.channel_id} not found")
                return

            await asyncio.sleep(self.delay_time)
            
            message = await channel.fetch_message(payload.message_id)
            if message.id in self.sent_messages:
                return

            # Initialize message tracking
            message_id = message.id
            if message_id not in self.reactions_per_message:
                self.reactions_per_message[message_id] = set()

            unique_users = self.reactions_per_message[message_id]
            
            # Only count star reactions
            for reaction in message.reactions:
                if str(reaction.emoji) != "⭐":  # Star emoji filter
                    continue
                async for user in reaction.users():
                    if user.id != message.author.id:
                        unique_users.add(user.id)

            # Update tracking before threshold check
            self.reactions_per_message[message_id] = unique_users
            reaction_count = len(unique_users)

            if reaction_count >= self.unique_users_threshold and reaction_added:
                self.sent_messages.add(message.id)
                destination_channel = self.bot.get_channel(self.destination_channel_id)
                if not destination_channel:
                    logger.error(f"Destination channel {self.destination_channel_id} not found")
                    return

                logger.info(
                    f"Sending message {message.id} to {destination_channel.name} "
                    f"in {destination_channel.guild.name}"
                )

                # Build embed
                embed = discord.Embed(
                    description=message.content,
                    timestamp=message.created_at,
                    color=0xFFD700  # Gold color for star theme
                )
                
                # Set author with their name and avatar
                embed.set_author(
                    name=message.author.display_name,
                    icon_url=message.author.display_avatar.url
                )
                
                # Add channel reference and reaction count
                embed.set_footer(text=f"#{message.channel.name}")
                embed.title = f"⭐ {reaction_count}"
                
                # Add original message link
                embed.add_field(name="Original", value=f"[Jump to message]({message.jump_url})", inline=False)
                
                # Handle attachments
                if message.attachments:
                    embed.set_image(url=message.attachments[0].url)
                    # If there are additional attachments, add them as fields
                    if len(message.attachments) > 1:
                        attachment_links = [f"[Attachment {i+1}]({att.url})" for i, att in enumerate(message.attachments[1:])]
                        embed.add_field(name="Additional Attachments", value="\n".join(attachment_links), inline=False)

                await destination_channel.send(embed=embed)

        except discord.NotFound:
            logger.warning(f"Message {payload.message_id} was deleted before processing")
        except discord.Forbidden:
            logger.error(f"Missing permissions in channel {payload.channel_id}")
        except Exception as e:
            logger.error(f"Error processing message {payload.message_id}: {str(e)}")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.check_unique_reactions(payload, reaction_added=True)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.check_unique_reactions(payload, reaction_added=False)


async def setup(bot, **kwargs):
    await bot.add_cog(HofCog(bot, kwargs["config"]))
