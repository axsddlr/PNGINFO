import asyncio
import json
import os

from discord.ext import commands

from util.image_metadata import extract_metadata

# Opening the config.json file and loading it into the config variable.
with open('config.json', 'r') as f:
    config = json.load(f)

TOKEN = config["DISCORD_TOKEN"]


class PNGINFO(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def get_metadata(self, ctx, message_id: int):
        """
        Extracts metadata from the image attachment in the message with the specified ID.
        """
        # Get the message with the specified ID
        message = await ctx.fetch_message(message_id)

        # Check if the message contains an image attachment
        if len(message.attachments) == 0:
            await ctx.send("No image found in message.")
            return

        # Create a directory to store the image files (if it doesn't exist)
        directory = "images"
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Save the image file to the images directory with the original filename
        filename = message.attachments[0].filename
        image_path = os.path.join(directory, filename)
        await message.attachments[0].save(image_path)

        # Extract metadata from the saved image file
        metadata_dict = extract_metadata(image_path)

        # Send the metadata as a JSON object in a Discord message
        metadata_json = json.dumps(metadata_dict, indent=4)
        await ctx.send(f"```{metadata_json}```")

        # Delete the image file after 10 seconds
        await asyncio.sleep(10)
        os.remove(image_path)


async def setup(bot):  # set async function
    await bot.add_cog(PNGINFO(bot))
