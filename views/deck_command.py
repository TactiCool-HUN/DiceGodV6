import discord
import utils.tools as t
from classes import Person, Deck, Card


async def deck_command(interaction: discord.Interaction):
	person = Person(interaction)

	with t.DatabaseConnection("card_base.db") as connection:
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM decks WHERE owner_id = ?", (person.user.id,))
		raw = cursor.fetchall()

	if len(raw) > 0:
		select_options = DeckCommandSelect(
			person,
			placeholder = "Select what you want to do.",
			options = [
				discord.SelectOption(label = "Create New Deck"),
				discord.SelectOption(label = "Edit Existing Deck"),
				discord.SelectOption(label = "Add Art to Deck"),
				discord.SelectOption(label = "Delete Deck")
			]
		)
		view = discord.ui.View()
		view.add_item(select_options)
		await interaction.response.send_message("", view = view, ephemeral = True)
	else:
		await interaction.response.send_modal(DeckCreateModal())


class DeckCreateModal(discord.ui.Modal, title = "Create Deck"):
	deck_name = discord.ui.TextInput(
		label = "Deck Name",
		style = discord.TextStyle.short,
		placeholder = "name your deck",
		required = True,
		min_length = 3
	)
	deck_cards = discord.ui.TextInput(
		label = "Deck Cards",
		style = discord.TextStyle.long,
		placeholder = "write in cards like this: Big Money, Joker, Blue Eyed White Dragon, card1",
		required = True
	)

	async def on_submit(self, interaction: discord.Interaction) -> None:
		person = Person(discord_id = interaction.user.id)
		self.deck_name = self.deck_name.value
		self.deck_cards = self.deck_cards.value
		if t.exists(self.deck_name, "deck"):
			await t.send_message(interaction, text = f"The name ``{self.deck_name}`` is already used by another deck.", ephemeral = True)
		else:
			raw_cards = self.deck_cards.split(", ")
			cards = []
			for card in raw_cards:
				cards.append(Card(None, card, 1))
			Deck(self.deck_name, person.user.id, cards, True)
			if t.exists(self.deck_name, "deck"):
				await t.send_message(interaction, text = f"Deck name ``{self.deck_name}`` successfully created!", ephemeral = True)
			else:
				await t.send_message(interaction, text = "There was an error in the deck creation process, I recommend notifying Tacti about this error, if you can try to remember your exact inputs.", ephemeral = True)


class DeckEditModal(discord.ui.Modal, title = "Edit Deck"):
	def __init__(self, deck_selected):
		super().__init__()
		self.deck_selected = deck_selected
		deck = Deck(deck_selected)
		txt = []
		for card in deck.cards:
			txt.append(card.name)
		self.og_cards = ", ".join(txt)
		self.deck_cards.default = self.og_cards
		self.deck_name.default = deck_selected

	deck_name = discord.ui.TextInput(
		label = "Deck Name",
		style = discord.TextStyle.short,
		placeholder = "what the new deck name should be",
		required = False,
		min_length = 3
	)
	deck_cards = discord.ui.TextInput(
		label = "Deck Cards",
		style = discord.TextStyle.long,
		required = False
	)

	async def on_submit(self, interaction: discord.Interaction) -> None:
		self.deck_name = self.deck_name.value
		self.deck_cards = self.deck_cards.value

		deck = Deck(self.deck_selected)
		message = []
		if self.deck_name != deck.name:
			if t.exists(self.deck_name, "deck"):
				await t.send_message(interaction, text = f"The name ``{self.deck_name}`` is already used by another deck.", ephemeral = True)
				return
			message.append(f"Deck Name change from ``{deck.name}`` to ``{self.deck_name}``.")
			deck.name = self.deck_name
		if self.deck_cards != self.og_cards:
			message.append(f"Deck Cards changed.")
			cards = []
			for card in self.deck_cards.split(", "):
				cards.append(Card(None, card, 1))
			deck.cards = cards

		deck.update()

		await t.send_message(interaction, text = "\n".join(message), ephemeral = True)


class DeckCommandSelect(discord.ui.Select):
	def __init__(self, person, options: list[discord.SelectOption], placeholder = None):
		super().__init__(options = options, placeholder = placeholder)
		self.person = person

	async def callback(self, interaction: discord.Interaction):
		match self.values[0]:
			case "Create New Deck":
				await interaction.response.send_modal(DeckCreateModal())
			case "Edit Existing Deck":
				with t.DatabaseConnection("card_base.db") as connection:
					cursor = connection.cursor()
					cursor.execute("SELECT * FROM decks WHERE owner_id = ?", (self.person.user.id,))
					raw = cursor.fetchall()

				decks = []
				for deck in raw:
					decks.append(discord.SelectOption(label = deck[2]))

				decks = DeckEditSelect(
					decks,
					placeholder = "Select which deck to edit."
				)
				view = discord.ui.View()
				view.add_item(decks)
				await interaction.response.edit_message(content = "", view = view)
			case "Add Art to Deck":
				with t.DatabaseConnection("card_base.db") as connection:
					cursor = connection.cursor()
					cursor.execute("SELECT * FROM decks WHERE owner_id = ?", (self.person.user.id,))
					raw = cursor.fetchall()

				decks = []
				for deck in raw:
					decks.append(discord.SelectOption(label = deck[2]))

				decks = DeckArtSelect(
					decks,
					placeholder = "Select which deck to assign art to."
				)

				view = discord.ui.View()
				view.add_item(decks)
				await interaction.response.edit_message(content = "# Please have all the art links available outside of Discord when you start!", view = view)
			case "Delete Deck":
				with t.DatabaseConnection("card_base.db") as connection:
					cursor = connection.cursor()
					cursor.execute("SELECT * FROM decks WHERE owner_id = ?", (self.person.user.id,))
					raw = cursor.fetchall()

				decks = []
				for deck in raw:
					decks.append(discord.SelectOption(label = deck[2]))

				decks = DeckDeleteSelect(
					decks,
					placeholder = "Select which deck to delete."
				)
				view = discord.ui.View()
				view.add_item(decks)
				await interaction.response.edit_message(content = "", view = view)


class DeckEditSelect(discord.ui.Select):
	def __init__(self, options: list[discord.SelectOption], placeholder = None):
		super().__init__(options = options, placeholder = placeholder)

	async def callback(self, interaction: discord.Interaction):
		await interaction.response.send_modal(DeckEditModal(self.values[0]))


class DeckDeleteSelect(discord.ui.Select):
	def __init__(self, options: list[discord.SelectOption], placeholder = None):
		super().__init__(options = options, placeholder = placeholder)

	async def callback(self, interaction: discord.Interaction):
		button = DeckDeleteButton(self.values[0])

		view = discord.ui.View()
		view.add_item(button)

		await interaction.response.edit_message(content = f"Delete {self.values[0]}?", view = view)


class DeckDeleteButton(discord.ui.Button):
	def __init__(self, deck_to_delete, emoji = None, style = discord.ButtonStyle.red, label = "Confirm Delete"):
		super().__init__(emoji = emoji, style = style, label = label)
		self.deck_to_delete = deck_to_delete

	async def callback(self, interaction: discord.Interaction):
		deck = Deck(self.deck_to_delete)
		deck.delete()
		self.disabled = True
		message = t.random.choice([
			f"``{self.deck_to_delete}`` won't bother us anymore.",
			f"``{self.deck_to_delete}`` has been eliminated.",
			f"``{self.deck_to_delete}`` met it's doom.",
			f"``{self.deck_to_delete}`` has been torn to a thousand pieces and fed to abyssal chickens.",
			f"The deck decked. ||{self.deck_to_delete}||",
			f"``{interaction.user.display_name}`` has murdered ``{self.deck_to_delete}`` in cold blood! This cannot go unanswered, may the Dice God bring you bad luck when you most need it!|| ...oh, that's me.||"
		])
		await interaction.response.edit_message(content = message)


class DeckArtSelect(discord.ui.Select):
	def __init__(self, options: list[discord.SelectOption], placeholder = None):
		super().__init__(options = options, placeholder = placeholder)

	async def callback(self, interaction: discord.Interaction):

		button = DeckArtButton(Deck(self.values[0]))

		view = discord.ui.View()
		view.add_item(button)

		await interaction.response.edit_message(content = "# Please have all the art links available outside of Discord when you start!", view = view)


class DeckArtButton(discord.ui.Button):
	def __init__(self, deck_to_art: Deck, emoji = None, style = discord.ButtonStyle.red, label = "Start Assigning Art"):
		super().__init__(emoji = emoji, style = style, label = label)
		self.deck_to_art = deck_to_art

	async def callback(self, interaction: discord.Interaction):
		await interaction.response.send_modal(DeckArtModal(self.deck_to_art, None))


class DeckArtModal(discord.ui.Modal, title = "Edit Deck"):
	def __init__(self, deck: Deck, card_inc: int | None):
		super().__init__()
		self.deck = deck
		if card_inc:
			for card in deck.cards:
				if card.card_id == card_inc:
					self.card = card
					self.card_art.label = card.name
					break
		else:
			self.card = deck.cards[0]

		if self.card.card_url:
			self.card_art.default = self.card.card_url

	card_art = discord.ui.TextInput(
		label = "Adjust Card Art",
		style = discord.TextStyle.short,
		placeholder = "Art URL",
		required = False,
		min_length = 3
	)

	async def on_submit(self, interaction: discord.Interaction) -> None:
		self.card.card_url = self.card_art.value[0]

		for i, card in enumerate(self.deck.cards):
			if card.card_id == self.card.card_id:
				self.deck.cards[i] = self.card
				break

		pick = False
		for card in self.deck.cards:
			if pick:
				await interaction.response.send_modal(DeckArtModal(self.deck, card.card_id))
				return
			if card.card_id == self.card.card_id:
				pick = True
		else:
			return


pass
