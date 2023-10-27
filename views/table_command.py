import utils.tools as t
import discord
from classes import Person
import utils.settings as s
import asyncio


async def table_command(interaction: discord.Interaction):
	person = Person(interaction)
	if person.user.id in s.ADMINS:
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM tables")
			raw = cursor.fetchall()
	else:
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM tables WHERE dm_id = ?", (person.user.id,))
			raw = cursor.fetchall()

	tables = []
	for line in raw:
		tables.append(discord.SelectOption(label = line[0]))

	table = TableCommand(interaction)

	table.list_of_items.append(
		SelectTable(
			table,
			placeholder = "Select which table you want to edit.",
			min_values = 1,
			options = tables
		)
	)

	table.list_of_items.append(
		SelectMainCommand(
			table,
			placeholder = "Select what you want to do.",
			min_values = 1,
			options = [
				discord.SelectOption(label = "Edit Permissions"),
				discord.SelectOption(label = "Change Table Settings")
			]
		)
	)

	await interaction.response.send_message("", view = table.create_view(), ephemeral = True)


class TableCommand:
	def __init__(self, interaction: discord.Interaction):
		self.interaction_og = interaction
		self.table_name: str = ""  # name of the chosen table
		self.command: str = ""  # what command is being executed on it
		self.people: list[discord.User] = []  # people to execute the command with (optional)
		self.list_of_items: list[discord.ui.Item] = []

	def create_view(self):
		view = discord.ui.View()

		for item in self.list_of_items:
			view.add_item(item)

		return view

	def create_message(self):
		message = []

		if self.table_name:
			message.append(f"Affecting: {self.table_name}")

		if self.command:
			message.append(f"Chosen command: {self.command}")

		return "\n".join(message)


class Table:
	def __init__(self, table_raw):
		self.name: str = table_raw[0]
		self.dm: discord.Member = t.bot.get_user(table_raw[1])
		self.player_role: discord.Role = t.bot.get_guild(562373378967732226).get_role(table_raw[2])
		self.guest_role: discord.Role = t.bot.get_guild(562373378967732226).get_role(table_raw[3])
		if table_raw[4]:
			self.auto_guest_add: bool = bool(int(table_raw[4]))
		else:
			self.auto_guest_add: bool = False


# - - - - - - - - - - Selects - - - - - - - - - -


class SelectTable(discord.ui.Select):
	def __init__(self, table: TableCommand, options: list[discord.SelectOption], placeholder = None, min_values = None, max_values = None):
		super().__init__(options = options, placeholder = placeholder, min_values = min_values, max_values = max_values)
		self.table = table

	async def callback(self, interaction: discord.Interaction):
		self.table.table_name = self.values[0]

		for item in self.table.list_of_items:
			if type(item) == SelectTable:
				self.table.list_of_items.remove(item)
				break

		await interaction.response.edit_message(content = self.table.create_message(), view = self.table.create_view())


class SelectMainCommand(discord.ui.Select):
	def __init__(self, table: TableCommand, options: list[discord.SelectOption], placeholder = None, min_values = None, max_values = None):
		super().__init__(options = options, placeholder = placeholder, min_values = min_values, max_values = max_values)
		self.table = table

	async def callback(self, interaction: discord.Interaction):
		self.table.command = self.values[0]

		for item in self.table.list_of_items:
			if type(item) == SelectMainCommand:
				self.table.list_of_items.remove(item)
				break

		if self.table.command == "Edit Permissions":
			self.table.list_of_items.append(
				SelectSubCommand(
					self.table,
					placeholder = "Select what you want to do.",
					min_values = 1,
					options = [
						discord.SelectOption(label = "Change to Player"),
						discord.SelectOption(label = "Change to Guest"),
						discord.SelectOption(label = "Remove from Table")
					]
				)
			)

			self.table.list_of_items.append(
				SelectUser(
					self.table,
					placeholder = "Select the target user(s).",
					min_values = 1,
					max_values = 5
				)
			)

			self.table.list_of_items.append(
				ConfirmPermissions(
					self.table
				)
			)
		elif self.table.command == "Change Table Settings":
			self.table.list_of_items.append(
				SelectAutoGuestSetting(
					self.table,
					placeholder = "Auto Manage Guest access to threads",
					options = [
						discord.SelectOption(label = "Auto add/remove guests from Threads"),
						discord.SelectOption(label = "Do not automatically manage Threads")
					]
				)
			)

		await interaction.response.edit_message(content = self.table.create_message(), view = self.table.create_view())


class SelectAutoGuestSetting(discord.ui.Select):
	def __init__(self, table: TableCommand, options: list[discord.SelectOption], placeholder = None, min_values = None, max_values = None):
		super().__init__(options = options, placeholder = placeholder, min_values = min_values, max_values = max_values)
		self.table = table

	async def callback(self, interaction: discord.Interaction):
		selection: bool = self.values[0] == "Auto add/remove guests from Threads"

		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				'UPDATE tables SET auto_guest_add = ? WHERE table_name = ?',
				(selection, self.table.table_name)
			)

		await t.send_message(interaction, text = "Table Updated!", ephemeral = True)

		if selection:
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute(
					"SELECT main_channel_id, guest_id FROM tables WHERE table_name = ?",
					(self.table.table_name, )
				)
				raw = cursor.fetchall()[0]
			main_channel: discord.TextChannel = interaction.guild.get_channel(raw[0])
			threads: list[discord.Thread] = main_channel.threads
			guest_role: discord.Role = interaction.guild.get_role(raw[1])

			count = 0
			for thread in threads:
				await thread.send(f"({guest_role.mention})", silent = True)
				if count < 5:
					count += 1
				else:
					count = 0
					await asyncio.sleep(5)


class SelectSubCommand(discord.ui.Select):
	def __init__(self, table: TableCommand, options: list[discord.SelectOption], placeholder = None, min_values = None, max_values = None):
		super().__init__(options = options, placeholder = placeholder, min_values = min_values, max_values = max_values)
		self.table = table

	async def callback(self, interaction: discord.Interaction):
		self.table.command = self.values[0]
		await interaction.response.defer()


class SelectUser(discord.ui.UserSelect):
	def __init__(self, table: TableCommand, placeholder = None, min_values = None, max_values = None):
		super().__init__(placeholder = placeholder, min_values = min_values, max_values = max_values)
		self.table = table

	async def callback(self, interaction: discord.Interaction):
		self.table.people = self.values
		await interaction.response.defer()


# - - - - - - - - - - Buttons - - - - - - - - - -


class ConfirmPermissions(discord.ui.Button):
	def __init__(self, table: TableCommand, emoji = "✅", style = discord.ButtonStyle.green, label = "submit"):
		super().__init__(emoji = emoji, style = style, label = label)
		self.table = table

	async def callback(self, interaction: discord.Interaction):
		if self.table.command == "" or self.table.table_name == "" or self.table.people == []:
			await t.send_message(interaction, text = "Missing Arguments, please fill out all fields", ephemeral = True)
			return

		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM tables WHERE table_name = ?", (self.table.table_name,))
			table_raw = cursor.fetchall()[0]

		table_full = Table(table_raw)

		if self.table.command == "Change to Player":
			for person in self.table.people:
				person: discord.Member
				for role in person.roles:
					if table_full.guest_role == role:
						await person.remove_roles(table_full.guest_role)
						break

				await person.add_roles(table_full.player_role)
				await t.send_message(person, text = f"Your access to table ``{self.table.table_name}`` has been set to Player by the DM.")
		elif self.table.command == "Change to Guest":
			for person in self.table.people:
				for role in person.roles:
					if table_full.player_role == role:
						await person.remove_roles(table_full.player_role)
						break

				await person.add_roles(table_full.guest_role)
				await t.send_message(person, text = f"Your access to table ``{self.table.table_name}`` has been set to Guest by the DM.")
		else:  # remove
			for person in self.table.people:
				for role in person.roles:
					if table_full.guest_role == role:
						await person.remove_roles(table_full.guest_role)
						await t.send_message(person, text = f"Your access to table ``{self.table.table_name}`` has been removed by the DM.")
						break
					elif table_full.player_role == role:
						await person.remove_roles(table_full.player_role)
						await t.send_message(person, text = f"Your access to table ``{self.table.table_name}`` has been removed by the DM.")
						break

		await interaction.response.edit_message(content = "Role(s) successfully updated!", view = None)


pass
