import asyncio
from ast import literal_eval
import utils.tools as t
import discord
from classes import Person
from icecream import ic
from utils.bot_setup import bot


async def table_maker_main(interaction: discord.Interaction):
    person = Person(interaction)
    person.user: discord.Member

    for role in person.user.roles:  # check for permission
        if role.id in [956272291111649340, 562618626797076480, 562622258472943646]:  # moderator
            break
    else:
        await t.send_message(interaction, "You are not high enough rank.\nThis command requires a Dungeon Master, Game Master or House Master", ephemeral = True)
        return

    await interaction.response.send_modal(TableMakerModalOne())


class TableMakerModalOne(discord.ui.Modal, title = "Create Table"):
    category_name = discord.ui.TextInput(
        label = "Category Name",
        style = discord.TextStyle.short,
        placeholder = "Name of the category (will be full uppercase)",
        required = True,
        min_length = 3
    )
    main_channel_name = discord.ui.TextInput(
        label = "Main Channel Name",
        style = discord.TextStyle.short,
        placeholder = "Name of the main channel (will be all lowercase)",
        required = True,
        min_length = 3
    )
    bs_channel_name = discord.ui.TextInput(
        label = "Bullshitery Channel Name",
        style = discord.TextStyle.short,
        placeholder = "Name of the bullshitery channel (will be all lowercase)",
        required = True,
        min_length = 3
    )
    lore_channel_name = discord.ui.TextInput(
        label = "Lore Channel Name",
        style = discord.TextStyle.short,
        placeholder = "Name of the lore channel (will be all lowercase)",
        required = True,
        min_length = 3
    )
    voice_channel_name = discord.ui.TextInput(
        label = "Voice Channel Name",
        style = discord.TextStyle.short,
        placeholder = "Name of the main channel (will keep your capitalisation)",
        required = True,
        min_length = 3
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        category_name = self.category_name.value
        main_channel_name = self.main_channel_name.value
        bs_channel_name = self.bs_channel_name.value
        lore_channel_name = self.lore_channel_name.value
        voice_channel_name = self.voice_channel_name.value

        button = TableMakerButton(category_name, main_channel_name, bs_channel_name, lore_channel_name, voice_channel_name)

        view = discord.ui.View()
        view.add_item(button)

        await interaction.response.send_message(
            content = "Because Discord is not smart you need to press a button for the remaining 4 questions...",
            view = view,
            ephemeral = True
        )


class TableMakerButton(discord.ui.Button):
    def __init__(self, category_name, main_channel_name, bs_channel_name, lore_channel_name, voice_channel_name, style = discord.ButtonStyle.green, label = "Shiny Button"):
        super().__init__(style = style, label = label)
        self.category_name = category_name
        self.main_channel_name = main_channel_name
        self.bs_channel_name = bs_channel_name
        self.lore_channel_name = lore_channel_name
        self.voice_channel_name = voice_channel_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TableMakerModalTwo(self.category_name, self.main_channel_name, self.bs_channel_name, self.lore_channel_name, self.voice_channel_name))


class TableMakerModalTwo(discord.ui.Modal, title = "Create Table"):
    def __init__(self, category_name, main_channel_name, bs_channel_name, lore_channel_name, voice_channel_name):
        super().__init__()
        self.category_name = category_name
        self.main_channel_name = main_channel_name
        self.bs_channel_name = bs_channel_name
        self.lore_channel_name = lore_channel_name
        self.voice_channel_name = voice_channel_name

    main_role_name = discord.ui.TextInput(
        label = "Main Role Name",
        style = discord.TextStyle.short,
        placeholder = "Name of the main role (will keep your capitalisation)",
        required = True,
        min_length = 3
    )
    guest_role_name = discord.ui.TextInput(
        label = "Guest Role Name",
        style = discord.TextStyle.short,
        placeholder = "Name of the guest role (will keep your capitalisation)",
        required = True,
        min_length = 3
    )
    main_role_color = discord.ui.TextInput(
        label = "Main Role Hex Colorcode",
        style = discord.TextStyle.short,
        placeholder = "#000000",
        required = True,
        min_length = 7,
        max_length = 7
    )
    guest_role_color = discord.ui.TextInput(
        label = "Guest Role Hex Colorcode",
        style = discord.TextStyle.short,
        placeholder = "#000000",
        required = True,
        min_length = 7,
        max_length = 7
    )
    table_name = discord.ui.TextInput(
        label = 'Name for the "Table" command',
        style = discord.TextStyle.short,
        placeholder = "Table name",
        required = True,
        min_length = 3
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer()

        self.main_role_name = self.main_role_name.value
        self.guest_role_name = self.guest_role_name.value
        self.main_role_color = self.main_role_color.value
        self.guest_role_color = self.guest_role_color.value
        self.table_name = self.table_name.value

        guild = interaction.guild
        main_role = await guild.create_role(
            name = self.main_role_name,
            colour = literal_eval(f"0x{self.main_role_color[1:]}"),
            mentionable = True,
            reason = f"Requested by {interaction.user.name}."
        )
        guest_role = await guild.create_role(
            name = self.guest_role_name,
            colour = literal_eval(f"0x{self.guest_role_color[1:]}"),
            mentionable = True,
            reason = f"Requested by {interaction.user.name}."
        )

        for i, role in enumerate(guild.roles):
            if role.id == 1009089291110072361:
                await main_role.edit(position = (i + 1))
                await guest_role.edit(position = (i + 1))
                break

        await interaction.user.add_roles(main_role)

        await asyncio.sleep(5)

        perm_overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages = False),
            main_role: discord.PermissionOverwrite(read_messages = True),
            guest_role: discord.PermissionOverwrite(read_messages = True),
            interaction.user: discord.PermissionOverwrite(
                read_messages = True,
                send_messages = True,
                manage_channels = True,
                manage_threads = True,
                manage_messages = True,
                manage_permissions = True,
                mute_members = True,
                deafen_members = True
            )
        }

        archive_position = -1
        for channel in guild.channels:
            if channel.id == 874736280783704145:
                archive_position = channel.position
                break

        category_channel = await guild.create_category(
            name = self.category_name,
            overwrites = perm_overwrites,
            reason = f"Requested by {interaction.user.name}.",
            position = (archive_position - 1)
        )

        main_channel = await guild.create_text_channel(
            name = self.main_channel_name,
            overwrites = perm_overwrites,
            reason = f"Requested by {interaction.user.name}.",
            position = (archive_position - 1),
            category = category_channel
        )
        await main_channel.edit(sync_permissions = True)

        bs_channel = await guild.create_text_channel(
            name = self.bs_channel_name,
            overwrites = perm_overwrites,
            reason = f"Requested by {interaction.user.name}.",
            position = (archive_position - 1),
            category = category_channel
        )
        await bs_channel.edit(sync_permissions = True)
        await asyncio.sleep(5)

        perm_overwrites[main_role] = discord.PermissionOverwrite(send_messages = False)
        perm_overwrites[guest_role] = discord.PermissionOverwrite(send_messages = False)
        await guild.create_text_channel(
            name = self.lore_channel_name,
            overwrites = perm_overwrites,
            reason = f"Requested by {interaction.user.name}.",
            position = (archive_position - 1),
            category = category_channel
        )

        voice_channel = await guild.create_voice_channel(
            name = self.voice_channel_name,
            overwrites = perm_overwrites,
            reason = f"Requested by {interaction.user.name}.",
            position = (archive_position - 1),
            category = category_channel
        )
        await voice_channel.edit(sync_permissions = True)
        await asyncio.sleep(5)

        with t.DatabaseConnection("data.db") as connection:
            cursor = connection.cursor()
            cursor.execute(
                f"INSERT INTO tables(table_name, dm_id, role_id, guest_id, auto_guest_add, main_channel_id) VALUES (?, ?, ?, ?, 0, ?)",
                (self.table_name, interaction.user.id, main_role.id, guest_role.id, main_channel.id)
            )
        await t.send_message(interaction, f"Table with name ``{self.table_name}`` created.", ephemeral = True)
        await t.send_message(interaction.user, f"You are now the GM of the following table: ``{self.table_name}``.\nYou can add a player with the /table command.\nAll changes will notify the person in question!")
        await t.send_message(guild.get_member(282869456664002581), f"A table has been created by {interaction.user.name}.")


pass
