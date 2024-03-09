import contextlib

import discord
from discord import app_commands

# NOTE: Bot must have privileged intents enabled to use the members intent.

# Replace with your bot token and guild ID.
BOT_TOKEN = "YOUR_BOT_TOKEN"

# Replace with your guild ID you want to use the slash commands in.
MY_GUILD = discord.Object(id=1215090504581255249)

# Replace with your message ID and role IDs for the emoji reactions.
EMOJI_ROLE_MESSAGE_ID = 1216061282822914189
ROLE_ID_1 = 1215102405222469663
ROLE_ID_2 = 1215102500332503082
ROLE_ID_3 = 1215102675809468436
UNICODE_EMOJI_1 = "🔴"
UNICODE_EMOJI_2 = "🟡"
CUSTOM_EMOJI_ID_1 = 1215109562005327964

# Replace with your mod log channel ID for the report command.
MOD_LOG_CHANNEL_ID = 1216065031121408000


EMOJI_TO_ROLE = {
    discord.PartialEmoji(name=UNICODE_EMOJI_1): ROLE_ID_1,
    discord.PartialEmoji(name=UNICODE_EMOJI_2): ROLE_ID_2,
    discord.PartialEmoji(name="custom_emoji", id=CUSTOM_EMOJI_ID_1): ROLE_ID_3,
}


class MyClient(discord.Client):
    """A subclass of `discord.Client` that demonstrates the use of slash commands, context menus, and role reactions."""

    def __init__(self: discord.Client, *args, **kwargs) -> None:
        """Initialize the bot."""
        super().__init__(*args, **kwargs)
        self.tree = app_commands.CommandTree(self)
        self.role_message_id = EMOJI_ROLE_MESSAGE_ID
        self.emoji_to_role = EMOJI_TO_ROLE

    async def setup_hook(self: discord.Client) -> None:
        """Sync the global commands and guild commands on startup."""
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    async def on_ready(self: discord.Client) -> None:
        """Print a message when the bot is ready."""
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

        await self.setup_hook()


    async def on_raw_reaction_add(self: discord.Client, payload: discord.RawReactionActionEvent) -> None:
        """Give a role based on a reaction emoji."""
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            return

        try:
            role_id = self.emoji_to_role[payload.emoji]
        except KeyError:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        with contextlib.suppress(discord.HTTPException):
            await payload.member.add_roles(role)

    async def on_raw_reaction_remove(self: discord.Client, payload: discord.RawReactionActionEvent) -> None:
        """Remove a role based on a reaction emoji."""
        if payload.message_id != self.role_message_id:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            return

        try:
            role_id = self.emoji_to_role[payload.emoji]
        except KeyError:
            return

        role = guild.get_role(role_id)
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        with contextlib.suppress(discord.HTTPException):
            await member.remove_roles(role)


intents = discord.Intents.default()
intents.members = True
client = MyClient(intents=intents)


@client.tree.command()
async def hello(interaction: discord.Interaction) -> None:
    """Say hello!."""
    await interaction.response.send_message(f"Hi, {interaction.user.mention}")


@client.tree.context_menu(name="Show Join Date")
async def show_join_date(interaction: discord.Interaction, member: discord.Member) -> None:
    """Show the join date of a member."""
    await interaction.response.send_message(f"{member} joined at {discord.utils.format_dt(member.joined_at)}")


@client.tree.context_menu(name="Report to Moderators")
async def report_message(interaction: discord.Interaction, message: discord.Message) -> None:
    """Report a message to the moderators."""
    await interaction.response.send_message(
        f"Thanks for reporting this message by {message.author.mention} to our moderators.", ephemeral=True,
    )

    log_channel = interaction.guild.get_channel(MOD_LOG_CHANNEL_ID)

    embed = discord.Embed(title="Reported Message")
    if message.content:
        embed.description = message.content

    embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
    embed.timestamp = message.created_at

    url_view = discord.ui.View()
    url_view.add_item(discord.ui.Button(label="Go to Message", style=discord.ButtonStyle.url, url=message.jump_url))

    await log_channel.send(embed=embed, view=url_view)

client.run(BOT_TOKEN)
