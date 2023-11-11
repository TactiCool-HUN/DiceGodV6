import utils.tools as t
import discord


class TitleClass:
	def __init__(self, interaction):
		self.og_interact: discord.Interaction = interaction
		self.command: str = ""
		self.title_name: str = ""
		self.people: list[discord.User] = []
		self.list_of_items: list[discord.ui.Item] = []

	def create_message(self):
		if self.people:
			txt = f"Affected People/Person:"
			first = True
			for person in self.people:
				if first:
					txt = f"{txt} {person.display_name}"
					first = False
				else:
					txt = f"{txt}, {person.display_name}"

			return txt
		else:
			return ""

	def create_view(self):
		view = discord.ui.View()

		for item in self.list_of_items:
			view.add_item(item)

		return view


async def title_command(interaction: discord.Interaction):
	my_title = TitleClass(interaction)

	my_title.list_of_items.append(
		SelectUser(
			my_title,
			placeholder = "Select the target user(s).",
			min_values = 1,
			max_values = 5
		)
	)

	# noinspection PyUnresolvedReferences
	await interaction.response.send_message(content = my_title.create_message(), view = my_title.create_view(), ephemeral = True)


# - - - - - - - - - - Selects - - - - - - - - - -


class SelectUser(discord.ui.UserSelect):
	def __init__(self, my_title: TitleClass, placeholder = None, min_values = None, max_values = None):
		super().__init__(placeholder = placeholder, min_values = min_values, max_values = max_values)
		self.my_title = my_title

	async def callback(self, interaction: discord.Interaction):
		self.my_title.people = self.values

		for item in self.my_title.list_of_items:
			if isinstance(item, SelectUser):
				self.my_title.list_of_items.remove(item)
				break

		self.my_title.list_of_items.append(
			SelectMainCommand(
				self.my_title,
				placeholder = "Select what you want to do.",
				min_values = 1,
				options = [
					discord.SelectOption(label = "Add Title"),
					discord.SelectOption(label = "Remove Title")
				]
			)
		)

		# noinspection PyUnresolvedReferences
		await interaction.response.edit_message(content = self.my_title.create_message(), view = self.my_title.create_view())


class SelectMainCommand(discord.ui.Select):
	def __init__(self, my_title: TitleClass, options: list[discord.SelectOption], placeholder = None, min_values = None, max_values = None):
		super().__init__(options = options, placeholder = placeholder, min_values = min_values, max_values = max_values)
		self.my_title = my_title

	async def callback(self, interaction: discord.Interaction):
		self.my_title.command = self.values[0]

		for item in self.my_title.list_of_items:
			if isinstance(item, SelectMainCommand):
				self.my_title.list_of_items.remove(item)
				break

		if self.my_title.command == "Add Title":
			# noinspection PyUnresolvedReferences
			await interaction.response.send_modal(AddTitleModal(self.my_title))
		elif self.my_title.command == "Remove Title":
			titles = t.get_titles(self.my_title.people)
			common_titles: list[discord.SelectOption] = []
			for title in titles:
				common_titles.append(discord.SelectOption(label = title.name))

			self.my_title.list_of_items.append(
				SelectTitleRemove(
					self.my_title,
					placeholder = "Select which title(s) to remove.",
					min_values = 1,
					options = common_titles
				)
			)

			# noinspection PyUnresolvedReferences
			await interaction.response.edit_message(content = self.my_title.create_message(), view = self.my_title.create_view())


class SelectTitleRemove(discord.ui.Select):
	def __init__(self, my_title: TitleClass, options: list[discord.SelectOption], placeholder = None, min_values = None, max_values = None):
		super().__init__(options = options, placeholder = placeholder, min_values = min_values, max_values = max_values)
		self.my_title = my_title

	async def callback(self, interaction: discord.Interaction):
		for title in self.values:
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM titles WHERE title = ?", (title,))
				raw = cursor.fetchall()

			if len(raw) != 1:
				raise ValueError

			raw = raw[0]

			for person in self.my_title.people:
				with t.DatabaseConnection("data.db") as connection:
					cursor = connection.cursor()
					cursor.execute("DELETE FROM title_people WHERE title_id = ? AND discord_id = ?", (raw[0], person.id))

			# noinspection PyUnresolvedReferences
			await interaction.response.edit_message(content = "Title successfully removed.", view = None)


class AddTitleModal(discord.ui.Modal):
	def __init__(self, my_title):
		super().__init__(title = "Add Title")
		self.my_title = my_title

	title_name = discord.ui.TextInput(
		label = "Title Name",
		style = discord.TextStyle.short,
		placeholder = "title's name",
		required = True,
		min_length = 3
	)
	title_rank = discord.ui.TextInput(
		label = "Title Rank",
		style = discord.TextStyle.short,
		placeholder = "Major / Minor",
		required = True,
		min_length = 5,
		max_length = 5
	)

	async def on_submit(self, interaction: discord.Interaction) -> None:
		self.title_name = self.title_name.value
		self.title_rank = self.title_rank.value

		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM titles WHERE title = ?", (self.title_name,))
			raw = cursor.fetchall()

		if not raw:
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("INSERT INTO titles(title, rank) VALUES (?, ?)", (self.title_name, self.title_rank))
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM titles WHERE title = ?", (self.title_name,))
				raw = cursor.fetchall()
		elif raw[0][2] != self.title_rank:
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("UPDATE titles SET rank = ? WHERE id = ?", (self.title_rank, raw[0][0]))

		title_id = raw[0][0]

		for person in self.my_title.people:
			title_exists = False
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM title_people WHERE discord_id = ?", (person.id,))
				raw = cursor.fetchall()
			for title_person in raw:
				if title_id == title_person[2]:
					title_exists = True
			if not title_exists:
				with t.DatabaseConnection("data.db") as connection:
					cursor = connection.cursor()
					cursor.execute("INSERT INTO title_people(discord_id, title_id) VALUES (?, ?)", (person.id, title_id))

		await t.send_message(interaction, text = "Title(s) successfully added.", ephemeral = True)


pass
