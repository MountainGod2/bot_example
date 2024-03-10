import json
from pathlib import Path

import discord
from discord import app_commands

MY_GUILD = discord.Object(id=1215090504581255249)  # Replace with your guild ID
MUTED_ROLE_ID = 1216435565852102848  # Replace with your muted role ID

class MyClient(discord.Client):
    """A subclass of `discord.Client`."""

    def __init__(self: discord.Client, *, intents: discord.Intents) -> None:
        """Initialize the bot."""
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self: discord.Client) -> None:
        """Sync the global commands and guild commands on startup."""
        self.tree.copy_global_to(guild=MY_GUILD)
        await self.tree.sync(guild=MY_GUILD)

    def save_roles(self: discord.Client, user_id: int, roles: list) -> None:
        """Save the user's roles to a JSON file."""
        if not Path("roles.json").exists():
            with Path("roles.json").open("w") as f:
                json.dump({}, f)  # Create the file with an empty JSON object if it doesn't exist

        with Path("roles.json").open("r+") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
            data[str(user_id)] = [role.id for role in roles if role is not None]
            f.seek(0)
            f.truncate()  # Truncate the file to overwrite it
            json.dump(data, f, indent=4)

    def load_roles(self: discord.Client, user_id: int) -> list:
        """Load the user's roles from a JSON file."""
        if not Path("roles.json").exists():
            return []  # Return an empty list if the file doesn't exist

        with Path("roles.json").open() as f:
            try:
                data = json.load(f)
                return data.get(str(user_id), [])
            except json.JSONDecodeError:
                return []



    async def add_roles_from_storage(self: discord.Client, guild: discord.Guild, member: discord.Member) -> None:
        """Add roles to a member based on saved data."""
        role_ids = self.load_roles(member.id)
        roles = [guild.get_role(role_id) for role_id in role_ids if guild.get_role(role_id)]
        if roles:
            await member.add_roles(*roles)

    async def remove_roles_for_storage(self: discord.Client, member: discord.Member) -> None:
        """Remove all roles from a member and saves them."""
        self.save_roles(member.id, member.roles[1:])  # exclude @everyone role
        await member.edit(roles=[])

intents = discord.Intents.default()
intents.members = True

client = MyClient(intents=intents)

@client.tree.context_menu(name="Mute User")
async def mute_user(interaction: discord.Interaction, member: discord.Member) -> None:
    """Mute a user."""
    guild = interaction.guild
    muted_role = guild.get_role(MUTED_ROLE_ID)
    if muted_role in member.roles:
        await interaction.response.send_message(f"{member} is already muted.", ephemeral=True)
    else:
        await client.remove_roles_for_storage(member)
        await member.add_roles(muted_role)
        await interaction.response.send_message(f"{member} has been muted.", ephemeral=True)

@client.tree.context_menu(name="Unmute User")
async def unmute_user(interaction: discord.Interaction, member: discord.Member) -> None:
    """Unmute a user."""
    guild = interaction.guild
    muted_role = guild.get_role(MUTED_ROLE_ID)
    if muted_role not in member.roles:
        await interaction.response.send_message(f"{member} is not muted.", ephemeral=True)
    else:
        await member.remove_roles(muted_role)
        await client.add_roles_from_storage(guild, member)
        await interaction.response.send_message(f"{member}'s original roles have been restored.", ephemeral=True)

client.run("BOT_TOKEN")
