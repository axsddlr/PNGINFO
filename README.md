# Discord Hall of Fame Bot
 
This Discord bot monitors specified channels and sends messages that reach a reaction threshold to a designated starboard channel.
 
## Required Bot Permissions

The bot requires the following permissions to function properly:
- Read Messages/View Channels
- Send Messages
- Embed Links
- Read Message History
- Add Reactions
- Use External Emojis
- View Message History

These permissions can be granted by giving the bot a role with these permissions or by using the following permission integer when inviting the bot: `274877975552`

## Usage
 
1. Messages in monitored channels that get ⭐ reactions from enough unique users will be sent to the starboard
2. Only :star: reactions are counted toward the threshold
3. The starboard entry shows reaction count, original post link, author, and attachments

## Setup

1. Create a `config.json` file using the example.config.json template
2. Set up the bot with the required permissions in your Discord server
3. Configure the channel IDs and reaction thresholds in config.json
4. Run the bot using Docker or directly with Python
