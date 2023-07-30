import discord
import utils.settings as s
import utils.tools as t
from classes import Person, Die
from utils.bot_setup import bot


async def die_command(interaction: discord.Interaction):
	ctx = await bot.get_context(interaction)
	person = Person(ctx)

	with t.DatabaseConnection("data.db") as connection:
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM dice WHERE owner_id = ?", (person.user.id,))
		raw = cursor.fetchall()

	if len(raw) > 0:
		select_options = DieCommandSelect(
			person,
			placeholder = "Select what you want to do.",
			options = [
				discord.SelectOption(label = "Create New Die"),
				discord.SelectOption(label = "Edit Existing Die"),
				discord.SelectOption(label = "Delete Die")
			]
		)
		view = discord.ui.View()
		view.add_item(select_options)
		await interaction.response.send_message("", view = view, ephemeral = True)
	else:
		await interaction.response.send_modal(DieCreateModal())


class DieCreateModal(discord.ui.Modal, title = "Create Die"):
	die_name = discord.ui.TextInput(
		label = "Die Name",
		style = discord.TextStyle.short,
		placeholder = "name your die",
		required = True,
		min_length = 3
	)
	die_roll = discord.ui.TextInput(
		label = "Die Roll",
		style = discord.TextStyle.short,
		placeholder = "write in what the die should roll",
		required = True
	)

	async def on_submit(self, interaction: discord.Interaction) -> None:
		person = Person(discord_id = interaction.user.id)
		self.die_name = self.die_name.value
		self.die_roll = self.die_roll.value
		if self.die_name in s.SHEET_ROLLS:
			await interaction.response.send_message(f"The name ``{self.die_name}`` is already used by a built in function.", ephemeral = True)
		elif self.die_name.isnumeric():
			await interaction.response.send_message("The die name cannot start with a number.", ephemeral = True)
		elif t.exists(self.die_name, "die"):
			await interaction.response.send_message(f"The name ``{self.die_name}`` is already used by another die.", ephemeral = True)
		else:
			Die(self.die_name, person.user.id, self.die_roll, True)
			if t.exists(self.die_name, "die"):
				await interaction.response.send_message(f"Die name ``{self.die_name}`` with the roll of ``{self.die_roll}`` successfully created!", ephemeral = True)
			else:
				await interaction.response.send_message("There was an error in the die creation process, I recommend notifying Tacti about this error", ephemeral = True)


class DieEditModal(discord.ui.Modal, title = "Edit Die"):
	def __init__(self, die_selected):
		super().__init__()
		self.die_selected = die_selected

	die_name = discord.ui.TextInput(
		label = "Die Name",
		style = discord.TextStyle.short,
		placeholder = "what the new die name should be (optional)",
		required = False,
		min_length = 3
	)
	die_roll = discord.ui.TextInput(
		label = "New Die Roll",
		style = discord.TextStyle.short,
		placeholder = "what the new die roll should be (optional)",
		required = False
	)

	async def on_submit(self, interaction: discord.Interaction) -> None:
		self.die_name = self.die_name.value
		self.die_roll = self.die_roll.value
		if self.die_name in s.SHEET_ROLLS:
			await interaction.response.send_message(f"The name ``{self.die_name}`` is already used by a built in function.", ephemeral = True)
		elif self.die_name[0].isnumeric():
			await interaction.response.send_message("The die name cannot start with a number.", ephemeral = True)
		elif t.exists(self.die_name, "die"):
			await interaction.response.send_message(f"The name ``{self.die_name}`` is already used by another die.", ephemeral = True)
		else:
			die = Die(self.die_selected)
			message = []
			if self.die_name:
				message.append(f"Die Name change from ``{die.name}`` to ``{self.die_name}``.")
				die.name = self.die_name
			if self.die_roll:
				message.append(f"Die Name change from ``{die.roll}`` to ``{self.die_roll}``.")
				die.roll = self.die_roll

			die.update()

			await interaction.response.send_message("\n".join(message), ephemeral = True)


class DieCommandSelect(discord.ui.Select):
	def __init__(self, person, options: list[discord.SelectOption], placeholder = None):
		super().__init__(options = options, placeholder = placeholder)
		self.person = person

	async def callback(self, interaction: discord.Interaction):
		if self.values[0] == "Create New Die":
			await interaction.response.send_modal(DieCreateModal())
		elif self.values[0] == "Edit Existing Die":
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM dice WHERE owner_id = ?", (self.person.user.id,))
				raw = cursor.fetchall()

			dice = []
			for die in raw:
				dice.append(discord.SelectOption(label = die[1]))

			dice = DieEditSelect(
				dice,
				placeholder = "Select which die to edit."
			)
			view = discord.ui.View()
			view.add_item(dice)
			await interaction.response.edit_message(content = "", view = view)
		elif self.values[0] == "Delete Die":
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM dice WHERE owner_id = ?", (self.person.user.id,))
				raw = cursor.fetchall()

			dice = []
			for die in raw:
				dice.append(discord.SelectOption(label = die[1]))

			dice = DieDeleteSelect(
				dice,
				placeholder = "Select which die to delete."
			)
			view = discord.ui.View()
			view.add_item(dice)
			await interaction.response.edit_message(content = "", view = view)


class DieEditSelect(discord.ui.Select):
	def __init__(self, options: list[discord.SelectOption], placeholder = None):
		super().__init__(options = options, placeholder = placeholder)

	async def callback(self, interaction: discord.Interaction):
		await interaction.response.send_modal(DieEditModal(self.values[0]))


class DieDeleteSelect(discord.ui.Select):
	def __init__(self, options: list[discord.SelectOption], placeholder = None):
		super().__init__(options = options, placeholder = placeholder)

	async def callback(self, interaction: discord.Interaction):
		button = DieDeleteButton(self.values[0])

		view = discord.ui.View()
		view.add_item(button)

		await interaction.response.edit_message(content = f"Delete {self.values[0]}?", view = view)


class DieDeleteButton(discord.ui.Button):
	def __init__(self, die_to_delete, emoji = None, style = discord.ButtonStyle.red, label = "Confirm Delete"):
		super().__init__(emoji = emoji, style = style, label = label)
		self.die_to_delete = die_to_delete

	async def callback(self, interaction: discord.Interaction):
		die = Die(self.die_to_delete)
		die.delete()
		message = t.random.choice([
			f"``{self.die_to_delete}`` won't bother us anymore.",
			f"``{self.die_to_delete}`` has been eliminated.",
			f"``{self.die_to_delete}`` met it's doom.",
			f"``{self.die_to_delete}`` has been torn to a thousand pieces and fed to abyssal chickens.",
			f"The die died. ||{self.die_to_delete}||",
			f"``{interaction.user.display_name}`` has murdered ``{self.die_to_delete}`` in cold blood! This cannot go unanswered, may the Dice God bring you bad luck when you most need it!|| ...oh, that's me.||"
		])
		await interaction.response.edit_message(content = message)


pass
