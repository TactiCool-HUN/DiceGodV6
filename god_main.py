from discord import app_commands
from discord.app_commands import Choice
from ast import literal_eval
# import sheet_handler as sh
from utils.bot_setup import bot
from data_holder import help_descirption
import commands as com
from utils import settings as s, tools as t
import classes as c
import roller as r
import textwrap
from views.vote_command import vote_command
from views.die_command import die_command
from views.table_command import table_command
from views.deck_command import deck_command
from views.title_handler import title_command
from secondary_functions import chatbot, emoji_role
from secondary_functions.table_maker import table_maker_main
import discord.ext
import asyncio
import random
import ast
import re
from icecream import ic


async def activity_changer():
	timer = 12 * 60 * 60  # 12 hours in seconds
	activity = None
	while True:
		act_type = random.randint(0, 2)
		match act_type:
			case 0:  # playing
				choices = [
					"with people's nerves", 1,
					"with the Deathnote", 1,
					"the innocent", 1,
					"with PCs' lives", 1,
					"DnD 5e", 0.2,
					"Pathfinder 2e", 0.8,
					"Pathfinder 5e", 0.05,
				]
				activity = discord.Game(t.choice(choices))
			case 1:  # listening to
				choices = [
					"cries of agony", 1,
					"the joy of a laughing GM", 1,
					"the joy of slaughter", 1,
					"the growing hum of the cult", 2,
					"the what Mag has to say", 0.1,
				]
				activity = discord.Activity(name = t.choice(choices), type = 2)
			case 2:  # watching
				choices = [
					"PCs die", 1,
					"from above", 1,
					"Fanki rolling nat1s", 0.4,
					"Popa rolling nat20s", 0.4,
					"as people derail the campaign", 1,
				]
				activity = discord.Activity(name = t.choice(choices), type = 3)
				"""case 3:  # competing in
					choices = [
						"for a T-Rex", 1,
						"a TPK competition", 1,
						"with Foundry", 1,
						"for the most bugs", 1,
					]
					activity = discord.Activity(name = t.choice(choices), type = 5)"""

		await bot.change_presence(status = discord.Status.online, activity = activity)
		await asyncio.sleep(timer)


@bot.event
async def on_ready():
	asyncio.create_task(activity_changer())

	print(f"{bot.user.name.upper()} is online!")

	try:
		synced = await bot.tree.sync()
		print(f"Synced {len(synced)} command(s)")
	except Exception as e:
		print(e)


@bot.event
async def on_message(message: discord.Message):
	if message.author != bot.user:
		asyncio.create_task(chatbot.bot_responses(message))
		asyncio.create_task(bot.process_commands(message))


@bot.event
async def on_raw_reaction_add(reaction: discord.RawReactionActionEvent):
	if reaction.member != bot.user:
		txt = await emoji_role.emoji_role_command(reaction)
		if txt == "empty":
			if random.randint(1, 20) == 20:
				channel = bot.get_guild(reaction.guild_id).get_channel(reaction.channel_id)
				message: discord.Message = await channel.fetch_message(reaction.message_id)
				await message.add_reaction(reaction.emoji)


@bot.event
async def on_raw_thread_update(thread_update_event: discord.RawThreadUpdateEvent):
	thread = bot.get_guild(thread_update_event.guild_id).get_thread(thread_update_event.thread_id)
	with t.DatabaseConnection("data.db") as connection:
		cursor = connection.cursor()
		cursor.execute(
			"SELECT main_channel_id, guest_id FROM tables WHERE auto_guest_add = 1"
		)
		raw = cursor.fetchall()

	for table_raw in raw:
		if table_raw[0] == thread.parent.id:
			guest_role: discord.Role = thread.guild.get_role(table_raw[1])
			await thread.send(f"({guest_role.mention})", silent = True)
			break


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
	if before.roles == after.roles:
		return

	guild = before.guild
	member = before

	with t.DatabaseConnection("data.db") as connection:
		cursor = connection.cursor()
		cursor.execute(
			"SELECT * FROM tables WHERE auto_guest_add = 1"
		)
		raw = cursor.fetchall()

	guest_roles = []
	for table in raw:
		guest_roles.append(table[3])

	roles_removed: list[discord.Role] = []
	roles_added: list[discord.Role] = []

	for role in before.roles:
		if role not in after.roles:
			roles_removed.append(role)

	for role in after.roles:
		if role not in before.roles:
			roles_added.append(role)

	if roles_added:
		for role in roles_added:
			if role.id == 1159498034795794603:  # person just joined
				splitter_1 = guild.get_role(1170868005824122921)
				splitter_2 = guild.get_role(1170867216812609606)
				splitter_3 = guild.get_role(1170867216812609606)
				splitter_4 = guild.get_role(1170866746194931742)
				splitter_5 = guild.get_role(1170864676574351380)
				await member.add_roles(splitter_1)
				await member.add_roles(splitter_2)
				await member.add_roles(splitter_3)
				await member.add_roles(splitter_4)
				await member.add_roles(splitter_5)
			elif role.id in guest_roles:  # someone got a guest role
				with t.DatabaseConnection("data.db") as connection:
					cursor = connection.cursor()
					cursor.execute(
						"SELECT * FROM tables WHERE guest_id = ?",
						(role.id, )
					)
					raw = cursor.fetchall()[0]
				main_channel: discord.TextChannel = role.guild.get_channel(raw[5])
				threads: list[discord.Thread] = main_channel.threads

				count = 0
				for thread in threads:
					await thread.send(f"({after.mention})", silent = True)
					if count < 5:
						count += 1
					else:
						count = 0
						await asyncio.sleep(5)

	if roles_removed:
		for role in roles_removed:
			if role.id in guest_roles:  # someone lost a guest role
				with t.DatabaseConnection("data.db") as connection:
					cursor = connection.cursor()
					cursor.execute(
						"SELECT * FROM tables WHERE guest_id = ?",
						(role.id,)
					)
					raw = cursor.fetchall()[0]
				main_channel: discord.TextChannel = role.guild.get_channel(raw[5])
				threads: list[discord.Thread] = main_channel.threads

				count = 0
				for thread in threads:
					await thread.remove_user(after)
					if count < 5:
						count += 1
					else:
						count = 0
						await asyncio.sleep(5)


@bot.event
async def on_thread_create(thread: discord.Thread):
	with t.DatabaseConnection("data.db") as connection:
		cursor = connection.cursor()
		cursor.execute(
			"SELECT main_channel_id FROM tables WHERE auto_guest_add = ?",
			(1, )
		)
		raw = cursor.fetchall()

	temp = []
	for i in raw:
		temp.append(i[0])
	raw = temp

	if thread.parent.id in raw:
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"SELECT guest_id FROM tables WHERE main_channel_id = ?",
				(thread.parent.id,)
			)
			raw = cursor.fetchall()

		guest_role = t.bot.get_guild(562373378967732226).get_role(raw[0][0])

		await thread.send(f"({guest_role.mention})", silent = True)


@bot.command(name = 'thing')
async def _thingy(message: discord.Message):
	c.Person(message)


@bot.tree.command(name = "thing")
async def __thingy(interaction: discord.Interaction):
	c.Person(interaction)


@bot.command(name = "ping")
async def ping_command(ctx: discord.ext.commands.Context):
	response_list = [
		"pong", 48,
		"ping", 1,
		"Yes, yes. I'm here, just let me brew another coffee...", 1
	]
	result = t.choice(response_list)
	if result == "ping":
		await t.send_message(ctx, text = result, reply = True)
		await asyncio.sleep(2)
		await t.send_message(ctx, text = "oh, wait no\npong!", reply = True)
	else:
		await t.send_message(ctx, text = result, reply = True)


@bot.command(name = "pong")
async def pong_command(ctx: discord.ext.commands.Context):
	response_list = [
		"ping", 49,
		"You wrote \"pong\" instead of \"ping\" and now you feel special don't you?", 1
	]
	result = t.choice(response_list)
	await t.send_message(ctx, text = result, reply = True)


@bot.command(name = 'emoji')
async def emoji_command(emoji):
	print(emoji.user_message.content)


@bot.command(name = "kill")
async def kill_command(ctx: discord.ext.commands.Context, *, other = None):
	print(f'{ctx.author} said "{other}", how rude...')
	# noinspection SpellCheckingInspection
	await ctx.message.add_reaction("<:angycat:817122720227524628>")
	if ctx.author.id in s.ADMINS and ctx.message.mentions:
		result = f"-die {ctx.message.mentions[0].mention}"
	else:
		# noinspection SpellCheckingInspection
		response_list = [
			"Don't be so rude...", 1,
			"ruuuuude", 1,
			"You accidentally mispelled the \"-die\" command.", 1,
			f"-die {ctx.author.mention}", 1,
			f"Quit it {ctx.author.mention}!", 1
		]
		result = t.choice(response_list)
	if result[0] == "-":
		sent = await t.send_message(ctx, text = result, reply = True, is_return = True)
		sent = await sent.reply("Contacting Pinkertons, please do not leave your current area. (○)")
		for i in range(20):
			if i % 2 == 0:
				await sent.edit(content = "Contacting Pinkertons, please do not leave your current area. (●)")
			else:
				await sent.edit(content = "Contacting Pinkertons, please do not leave your current area. (○)")
			await asyncio.sleep(1)
		await sent.edit(content = "Pinkertons connection established: Publishing address.")
		await asyncio.sleep(5)
		await sent.edit(content = "Pinkertons connection established: Requesting agent.")
		await asyncio.sleep(6)
		await sent.edit(content = "Pinkertons connection established: Agent granted.\nStandby for annihilation.")
	else:
		await t.send_message(ctx, text = result, reply = True)


@bot.command(name = "roll", aliases = ["r", "e"])
async def _roll_command_(ctx: discord.ext.commands.Context, *, text):
	await com.roll_command(ctx, text)


@bot.command(name = "yeet")
async def _yeet_command_(ctx: discord.ext.commands.Context, *, text):
	if random.randint(1, 50) == 1:
		text = "I saw that it went off the table but I can't find it anywhere, you gotta roll a new one, we'll find it after session."
		await t.send_message(ctx, text = text, reply = True)
	elif random.randint(1, 12) == 1:
		followups = [c.FollowupButton("✅", text, "roll"), c.FollowupButton("❎", None, "disable")]
		# noinspection SpellCheckingInspection
		message = "You yeeted the die of the table, does it still count?"
		await t.send_message(ctx, text = message, reply = True, followups = followups)
	else:
		await com.roll_command(ctx, text)


@bot.command(name = "coinflip", aliases = ["coin"])
async def coin_old(ctx: discord.ext.commands.Context):
	response_list = [
		f"{c.Person(ctx).user.display_name} flipped a coin and it landed on... it's side?", 1,
		f"{c.Person(ctx).user.display_name} flipped a coin and it landed on **heads**!", 49,
		f"{c.Person(ctx).user.display_name} flipped a coin and it landed on **tails**!", 51
	]
	await t.send_message(ctx, text = t.choice(response_list))


@bot.tree.command(name = "coinflip", description = "Flip a coin! (such complexity, but hey if you read it here is a tip: -coin has 1% more tails)")
async def coin_slash(interaction: discord.Interaction):
	response_list = [
		f"{c.Person(interaction).user.display_name} flipped a coin and it landed on... it's side?", 1,
		f"{c.Person(interaction).user.display_name} flipped a coin and it landed on **heads**!", 51,
		f"{c.Person(interaction).user.display_name} flipped a coin and it landed on **tails**!", 49
	]
	await t.send_message(interaction, text = t.choice(response_list))


@bot.command(name = "pc", aliases = ["char", "character"])
async def pc_old(ctx: discord.ext.commands.Context, command, char_name = None, sheet_name = None, person = None, color = None):
	await com.pc_command(ctx, command, char_name, sheet_name, '', person, color)


@bot.tree.command(name = "pc", description = "Connect your Google Sheet(tm) to Dice God. You can also: set, clear, update, or delete characters.")
@app_commands.describe(command="Choose what main functionality you want to use with the command.")
@app_commands.choices(command=[
	app_commands.Choice(name = "create - Create a new character, requires: char_name, sheet_name", value = "create"),
	app_commands.Choice(name = "update - Update a character to a new sheet, requires: char_name, sheet_name", value = "update"),
	app_commands.Choice(name = "set image - Add a !portrait! image to your character. requires: char_name, image_url.", value = "image"),
	app_commands.Choice(name = "set color - Add a custom color to your character, requires: char_name, color", value = "color"),
	app_commands.Choice(name = "access - Grant or revoke access to the character from someone, requires: char_name, person", value = "access"),
	app_commands.Choice(name = "set - Set an existing character as your active, requires: char_name.", value = "set"),
	app_commands.Choice(name = "clear - Clear your active character, requires: [nothing]", value = "clear"),
	app_commands.Choice(name = "delete - Delete a character connection, requires: char_name, balls", value = "delete")])
@discord.app_commands.describe(char_name = "Name the character you want to make or use.")
@discord.app_commands.describe(sheet_name = "Provide the exact name of the Google Sheet you want to interact with.")
@discord.app_commands.describe(image_url = "Provide an openly accessible !portrait! image's url.")
@discord.app_commands.describe(person = "Ping a person. Only needed for the Access command.")
@discord.app_commands.describe(color = "Custom color for this PC")
async def pc_slash(interaction: discord.Interaction, command: Choice[str], char_name: str = None, sheet_name: str = None, image_url: str = None, person: discord.Member = None, color: str = None):
	await com.pc_command(interaction, command.value, char_name, sheet_name, image_url, person, color)


@bot.tree.command(name = "die", description = "Create custom named dice, any complex roll. You can also: update, or delete already existing ones.")
async def die_slash(interaction: discord.Interaction):
	await die_command(interaction)


@bot.tree.command(name = "settings", description = "Change your global settings for DiceGod, like name changing, roll tags, or chat ignore.")
@app_commands.choices(change_name=[
	app_commands.Choice(name = "on", value = 1),
	app_commands.Choice(name = "off", value = 0)])
@app_commands.choices(auto_roll_tagging=[
	app_commands.Choice(name = "on", value = 1),
	app_commands.Choice(name = "off", value = 0)])
@discord.app_commands.describe(markov_chance = "Set the markov response chance percentage for yourself. 0 for none, 100 for always")
@app_commands.choices(chat_ignore=[
	app_commands.Choice(name = "on", value = 1),
	app_commands.Choice(name = "off", value = 0)])
@app_commands.choices(uwuify_messages=[
	app_commands.Choice(name = "on", value = 1),
	app_commands.Choice(name = "off", value = 0)])
@discord.app_commands.describe(color = "Set your color! (use #000000 or 0x000000 hex code)")
@discord.app_commands.describe(tag = 'Set which tag your rolls will be saved! (use "clear" to empty it)')
async def settings(interaction: discord.Interaction, change_name: Choice[int] = None, auto_roll_tagging: Choice[int] = None, markov_chance: str = None, chat_ignore: Choice[int] = None, uwuify_messages: Choice[int] = None, color: str = None, tag: str = None):
	person = c.Person(interaction)
	ephemeral = True
	test_roll = False
	response = "Settings changed!"

	if color is not None:
		if color[0] == "#":
			color = f"0x{color[1:]}"
		person.color = color
		person.update()
		response += "\nColor set, there should be a test roll below.\n If no test roll appears here use ``0`` for the color code in this command and it'll reset your color."
		test_roll = True
		ephemeral = False

	if change_name is not None:
		change_name = change_name.value
		if change_name:
			if person.active:
				try:
					await t.identifier_to_member(interaction).edit(nick = person.set_name())
				except Exception as e:
					print(e)
			person.change_name = True
			response += "\nFrom now on your name will be set by the bot as you change characters."
			ephemeral = True
		else:
			person.change_name = False
			try:
				await t.identifier_to_member(interaction).edit(nick = person.clear_name())
			except Exception as e:
				print(e)
			response += "\nFrom now on your name will not be set by the bot (it is also reset)."
			ephemeral = True
		person.update()

	if auto_roll_tagging is not None:
		auto_roll_tagging = auto_roll_tagging.value
		if auto_roll_tagging:
			person.auto_tag = 1
			if person.active:
				person.tag = person.active
			response += f"\nYour roll tags now automatically follows your active character changes."
		else:
			person.auto_tag = 0
			if person.active:
				person.tag = None
			response += f"\nYour roll tags no longer automatically follows your active character changes. It has also been cleared."
		person.update()

	if markov_chance is not None:
		markov_chance.replace("%", "")
		if markov_chance.isnumeric() and 0 <= int(markov_chance) <= 100:
			person.markov_chance = int(markov_chance)
			person.update()
			response += f"\nMarkov response chance set to {markov_chance}%"
		else:
			response += f"\n__Markov chance needs to be a numeric value between 0 and 100."

	if chat_ignore is not None:
		person.chat_ignore = chat_ignore.value
		person.update()
		if person.chat_ignore:
			response += f"\nDice God will no longer respond to you outside of commands."
		else:
			response += f"\nDice God will once again respond to you outside of commands."

	if uwuify_messages is not None:
		person.uwuify = uwuify_messages.value
		person.update()
		if not person.uwuify:
			response += f"\nDice God will no longer uwuify your messages."
		else:
			response += f"\nDice God will once again uwuify your messages (note: requires chat_ignore to be off)."

	if tag is not None:
		tag = tag.lower()
		if tag == "clear":
			tag = None
		person.tag = tag
		person.update()
		if tag is None:
			response += f'\nYour rolls will not have a tag associated with them.'
		else:
			response += f'\nYour rolls will be saved tag the "{tag}" name.'

	await t.send_message(interaction, text = response, ephemeral = ephemeral)
	if test_roll:
		await com.roll_command(interaction, "1d1")


@bot.tree.command(name = "condition", description = "Set exhaustion or conditions on your active character.")
@app_commands.choices(conditions=[
	app_commands.Choice(name = "blinded", value = "blinded"),
	app_commands.Choice(name = "charmed", value = "charmed"),
	app_commands.Choice(name = "deafened", value = "deafened"),
	app_commands.Choice(name = "stunned", value = "stunned"),
	app_commands.Choice(name = "frightened", value = "frightened"),
	app_commands.Choice(name = "grappled", value = "grappled"),
	app_commands.Choice(name = "incapacitated", value = "incapacitated"),
	app_commands.Choice(name = "paralyzed", value = "paralyzed"),
	app_commands.Choice(name = "petrified", value = "petrified"),
	app_commands.Choice(name = "poisoned", value = "poisoned"),
	app_commands.Choice(name = "prone", value = "prone"),
	app_commands.Choice(name = "restrained", value = "restrained"),
	app_commands.Choice(name = "unconscious", value = "unconscious"),
	app_commands.Choice(name = "invisible", value = "invisible"),
	app_commands.Choice(name = "exhaustion", value = "exhaustion"),
	app_commands.Choice(name = "clear_all", value = "clear"), ])
@app_commands.choices(on_or_off=[
	app_commands.Choice(name = "on", value = "True"),
	app_commands.Choice(name = "off", value = "False"),
	app_commands.Choice(name = "toggle", value = "toggle"), ])
@app_commands.choices(exhaustion_level=[
	app_commands.Choice(name = "0", value = "0"),
	app_commands.Choice(name = "1", value = "1"),
	app_commands.Choice(name = "2", value = "2"),
	app_commands.Choice(name = "3", value = "3"),
	app_commands.Choice(name = "4", value = "4"),
	app_commands.Choice(name = "5", value = "5"),
	app_commands.Choice(name = "6", value = "6"),
	app_commands.Choice(name = "up", value = "up"),
	app_commands.Choice(name = "down", value = "down"), ])
async def condition(interaction: discord.Interaction, conditions: Choice[str], on_or_off: Choice[str] = None, exhaustion_level: Choice[str] = None):
	if conditions:
		conditions = conditions.value
	if on_or_off:
		if on_or_off.value == "toggle":
			on_or_off = None
		elif on_or_off.value == "True":
			on_or_off = True
		elif on_or_off.value == "False":
			on_or_off = False
	if exhaustion_level:
		exhaustion_level = exhaustion_level.value
	await interaction.response.defer()
	await com.condition_command(interaction, conditions, on_or_off, exhaustion_level)


@bot.tree.command(name = "money_tracking", description = "Add income or loss statements to your active character's Money Tracker.")
@app_commands.describe(name = "Name the transaction")
@app_commands.choices(income_loss = [
	app_commands.Choice(name = "income", value = "income"),
	app_commands.Choice(name = "loss", value = "loss")])
@app_commands.describe(platinum = "Amount of platinum pieces")
@app_commands.describe(gold = "Amount of gold pieces")
@app_commands.describe(electrum = "Amount of electrum pieces")
@app_commands.describe(silver = "Amount of silver pieces")
@app_commands.describe(copper = "Amount of copper pieces")
@app_commands.describe(multiplier = "Multiplier, default: 1")
async def money_tracking(interaction: discord.Interaction, name: str, income_loss: Choice[str], platinum: int = 0, gold: int = 0, electrum: int = 0, silver: int = 0, copper: int = 0, multiplier: int = 1):
	person = c.Person(interaction)
	if person.active:
		await interaction.response.defer(ephemeral = True)
		income_loss = income_loss.value

		await asyncio.to_thread(r.sh.money, interaction, name, income_loss, platinum, gold, electrum, silver, copper, multiplier)

		if income_loss == "income":
			txt = f"{person.active} gained under transaction name ``{name}``"
		else:
			txt = f"{person.active} lost under transaction name ``{name}``"
		if platinum:
			txt = f"{txt} {platinum * multiplier} PP"
		if gold:
			txt = f"{txt} {gold * multiplier} GP"
		if electrum:
			txt = f"{txt} {electrum * multiplier} EP"
		if silver:
			txt = f"{txt} {silver * multiplier} SP"
		if copper:
			txt = f"{txt} {copper * multiplier} CP"

		await t.send_message(interaction, text = f"{txt}!", ephemeral = True)
	else:
		await t.send_message(interaction, text = "No active character found.", ephemeral = True)


# noinspection SpellCheckingInspection
@bot.tree.command(name = "spellpoint", description = "Use, recover, or otherwise manipulate your spell points.")
@app_commands.choices(command = [
	app_commands.Choice(name = "use", value = "use"),
	app_commands.Choice(name = "recover", value = "recover"),
	app_commands.Choice(name = "set", value = "set"),
	app_commands.Choice(name = "reset", value = "reset"),
])
@app_commands.describe(amount = "amount of points")
@app_commands.choices(spell_level = [
	app_commands.Choice(name = "1st", value = 1),
	app_commands.Choice(name = "2nd", value = 2),
	app_commands.Choice(name = "3rd", value = 3),
	app_commands.Choice(name = "4th", value = 4),
	app_commands.Choice(name = "5th", value = 5),
	app_commands.Choice(name = "6th", value = 6),
	app_commands.Choice(name = "7th", value = 7),
	app_commands.Choice(name = "8th", value = 8),
	app_commands.Choice(name = "9th", value = 9), ])
async def spell_points(interaction: discord.Interaction, command: Choice[str], amount: int = 0, spell_level: Choice[int] = None):
	await interaction.response.defer(ephemeral = True)
	if spell_level:
		spell_level = int(spell_level.value)
	public, private = r.sh.spell_point(interaction, command.value, amount, spell_level)
	await t.send_message(interaction, text = private, ephemeral = True)
	await t.send_message(interaction, text = public)


# noinspection SpellCheckingInspection
@bot.command(name = "hurt", aliases = ["heal", "healing", "hert"])
async def hp_stuff(ctx: discord.ext.commands.Context, *, amount):
	await com.hp_command(ctx, amount)


# noinspection SpellCheckingInspection
@bot.command(name = "churt", aliases = ["cheal", "chealing"])
async def companion_hp_stuff(ctx: discord.ext.commands.Context, *, amount):
	await com.hp_command(ctx, amount, is_companion = True)


@bot.command(name = "temp", aliases = ["temporary"])
async def temp_command(ctx: discord.ext.commands.Context, *, amount):
	person = c.Person(ctx)
	if person.active is None:
		await t.send_message(ctx, text = "No active character found.", reply = True)
	else:
		sent = await t.load(ctx)
		temp = await asyncio.to_thread(com.sh.set_temp, ctx, amount, False, False)
		txt, followups = await temp
		await sent.delete()
		await t.send_message(ctx, text = txt, reply = True, followups = followups)


# noinspection SpellCheckingInspection
@bot.command(name = "ctemp", aliases = ["ctemporary"])
async def companion_temp_command(ctx: discord.ext.commands.Context, *, amount):
	person = c.Person(ctx)
	if person.active is None:
		await t.send_message(ctx, text = "No active character found.", reply = True)
	else:
		sent = await t.load(ctx)
		txt, followups = await asyncio.to_thread(com.sh.set_temp, ctx, amount, False, True)
		await sent.delete()
		await t.send_message(ctx, text = txt, reply = True, followups = followups)


@bot.command(name = "rest")
async def rest_old(ctx: discord.ext.commands.Context, length = "long", hit_dice = None):
	sent = await t.load(ctx)
	await com.rest_command(ctx, length, hit_dice, sent)


@bot.tree.command(name = "rest", description = "Use long or short rest with your active character.")
@app_commands.choices(length=[
	app_commands.Choice(name = "short", value = "short"),
	app_commands.Choice(name = "long", value = "long"), ])
@app_commands.describe(hit_dice = 'Write in how many and what hit dice you want to use, example: "2d8"')
async def rest_slash(interaction: discord.Interaction, length: Choice[str], hit_dice: str = None):
	await interaction.response.defer()
	await com.rest_command(interaction, length.value, hit_dice)


@bot.tree.command(name='list', description = "List out your characters, inventory, spells, or dice")
@app_commands.choices(what_to_list = [
	app_commands.Choice(name = "characters", value = "characters"),
	app_commands.Choice(name = "inventory", value = "inventory"),
	app_commands.Choice(name = "spells", value = "spells"),
	app_commands.Choice(name = "dice", value = "dice"),
])
@app_commands.describe(based_on = 'In case of listing inventory (type)')
@app_commands.choices(ephemeral = [
	app_commands.Choice(name = "private", value = 1),
	app_commands.Choice(name = "public", value = 0),
])
async def listing(interaction: discord.Interaction, what_to_list: Choice[str], based_on: str = None, ephemeral: Choice[int] = None):
	if ephemeral is None:
		ephemeral = True
	else:
		ephemeral = bool(ephemeral.value)
	person = c.Person(interaction)
	what_to_list = what_to_list.value
	if based_on:
		based_on = based_on.lower()
	display = ""
	await interaction.response.defer(ephemeral = ephemeral)

	match what_to_list:
		case "characters":
			display = f"{person.user.display_name}'s characters:"
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM sheets WHERE owner_id = ?", (person.user.id,))
				raw_pack = cursor.fetchall()
			for raw in raw_pack:
				if raw[2] == person.active:
					display = f"{display}\n**{raw[2]} ({raw[3]})**"
				else:
					display = f"{display}\n{raw[2]} ({raw[3]})"
				if raw[3] != "MainV5":
					version = re.findall("V[0-9].[0-9][0-9].[0-9][0-9]", raw[3])[0]
					version = int(version[1:].replace(".", ""))
					if version < int(s.VERSION_CONTROL):
						display = f"{display} !out of date sheet!"
		case "inventory":
			if person.active:
				sheet = c.Sheet(interaction).sheet
				display = f"{person.active}'s inventory:"
				data = com.sh.get_inventory(sheet, based_on)
				display = f"{display}\n{data}"
			else:
				display = "No active character found."
		case "spells":
			if person.active:
				display = f"{person.active}'s spells:"
				data = com.sh.get_spell_list(interaction)
				display = f"{display}\n{data}"
			else:
				display = "No active character found."
		case "dice":
			display = f"{person.user.display_name}'s dice:"
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM dice WHERE owner_id = ?", (person.user.id,))
				raw_pack = cursor.fetchall()
			if raw_pack:
				for raw in raw_pack:
					display = f"{display}\n{raw[1]} ({raw[3]})"
			else:
				display = f"{person.user.display_name} has no dice."

	await t.send_message(interaction, text = display, ephemeral = ephemeral)


@bot.tree.command(name = "spell", description = "Get the full description and properties of a spell.")
@app_commands.describe(spell_name = "can be partial")
async def spell_slash(interaction: discord.Interaction, spell_name: str):
	await interaction.response.defer()
	await com.spell_command(interaction, spell_name, None)


@bot.command(name = "spell", aliases = ["s"])
async def spell_old(ctx: discord.ext.commands.Context, *, spell_name):
	sent = await t.load(ctx)
	await com.spell_command(ctx, spell_name, sent)


@bot.tree.command(name = "cast", description = "Get the full description of the spell and cast it from your characters slots or points.")
@app_commands.choices(spell_level = [
	app_commands.Choice(name = "1st", value = 1),
	app_commands.Choice(name = "2nd", value = 2),
	app_commands.Choice(name = "3rd", value = 3),
	app_commands.Choice(name = "4th", value = 4),
	app_commands.Choice(name = "5th", value = 5),
	app_commands.Choice(name = "6th", value = 6),
	app_commands.Choice(name = "7th", value = 7),
	app_commands.Choice(name = "8th", value = 8),
	app_commands.Choice(name = "9th", value = 9),
])
async def cast_slash(interaction: discord.Interaction, spell_name: str, spell_level: Choice[int]):
	await interaction.response.defer()
	await com.cast_command(interaction, spell_name, None, spell_level.value)


@bot.command(name = "cast", aliases = ["c"])
async def cast_old(ctx: discord.ext.commands.Context, *, spell_name):
	sent = await t.load(ctx)
	splits = spell_name.split(" ")
	level = splits[-1]
	try:
		level = int(re.findall("[1-9]", level)[0])
		spell_name = "".join(splits[:-1])
		await com.cast_command(ctx, spell_name, sent, level)
	except IndexError:
		await t.send_message(ctx, text = f"Please add spell level separately after the cast command: ``--c {spell_name} lvl1``")


@bot.tree.command(name = "statistics", description = "Display your or others roll statistics.")
@app_commands.describe(person = "@ the person you want to get statistics about.")
@app_commands.describe(tag = "Write in a the tag you want to use as a filter.")
@app_commands.choices(get_all_rolls = [
	app_commands.Choice(name = "yes", value = 1),
	app_commands.Choice(name = "no", value = 0),
])
@app_commands.choices(ephemeral = [
	app_commands.Choice(name = "private", value = 1),
	app_commands.Choice(name = "public", value = 0),
])
async def statistics(interaction: discord.Interaction, person: discord.Member = None, tag: str = None, get_all_rolls: Choice[int] = None, ephemeral: Choice[int] = None):
	if get_all_rolls is None:
		get_all_rolls = False
	else:
		get_all_rolls = int(get_all_rolls.value)
	if ephemeral is None:
		ephemeral = False
	else:
		ephemeral = int(ephemeral.value)
	if person is None:
		person = c.Person(interaction)
	else:
		person = c.Person(discord_id = person.id)

	await interaction.response.defer(ephemeral = ephemeral)

	if get_all_rolls:
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM statistics")
			rolls = cursor.fetchall()
	else:
		rolls = person.get_rolls()

	if tag:
		new_rolls = []
		for roll in rolls:
			if roll[6] == tag:
				new_rolls.append(roll)
		rolls = new_rolls
	else:
		tag = "<all>"

	rolls_used = []
	rolls_dict = {}
	fields = []

	for roll in rolls:
		if int(roll[4]):
			rolls_used.append(roll)
		try:
			rolls_dict[roll[3]].append(roll[2])
		except KeyError:
			rolls_dict[roll[3]] = [roll[2]]

	key_order = [20, 100, 12, 10, 8, 6, 4, 2]
	new_order = {}
	for k in key_order:
		if k in rolls_dict:
			new_order[k] = rolls_dict[k]
	for k in rolls_dict:
		if k not in new_order:
			new_order[k] = rolls_dict[k]
	rolls_dict = new_order

	for key in rolls_dict:
		minimum = 0
		maximum = 0
		frequent_num = 0
		frequent = t.most_frequent(rolls_dict[key])
		for roll in rolls_dict[key]:
			if roll == 1:
				minimum += 1
			elif roll == key:
				maximum += 1
			if roll == frequent:
				frequent_num += 1

		average = round(sum(rolls_dict[key]) / len(rolls_dict[key]), 2)
		txt = f"""Rolled: {len(rolls_dict[key])}
			Average: {average}
			Most frequent roll: {frequent}
			Rolled {frequent_num} times ({round(frequent_num / len(rolls_dict[key]) * 100, 2)}%)
			Minimum rolls: {minimum} ({round(minimum / len(rolls_dict[key]) * 100, 2)}%)
			Maximum rolls: {maximum} ({round(maximum / len(rolls_dict[key]) * 100, 2)}%)"""

		fields.append([f"d{key} stats", txt])

	general = f"Tag: {tag}\nRolled: {len(rolls)}"
	general = general + f"\nFrom which {len(rolls_used)} ({round(len(rolls_used) / len(rolls) * 100, 2)}%) were actually used."

	embed = discord.Embed(
		title = "General Statistics",
		description = general,
		color = ast.literal_eval(person.color))
	members = interaction.guild.members
	for member in members:
		if member.id == person.user.id:
			embed.set_author(name = person.user.display_name, icon_url = member.avatar.url)
			break

	for element in fields:
		embed.add_field(name = element[0], value = element[1])
	embed.add_field(name = "Color", value = person.color, inline = False)
	embed.add_field(name = "Name Change", value = person.change_name, inline = False)
	embed.add_field(name = "Active", value = person.active, inline = False)
	embed.add_field(name = "Auto Tag", value = person.auto_tag, inline = False)
	embed.add_field(name = "Current Tag", value = person.tag, inline = False)

	await t.send_message(interaction, embed = embed)


@bot.tree.command(name = "x_admin_clear", description = "Admin only.")
@app_commands.describe(sheet = "Sheet name.")
@app_commands.describe(player = "@player")
@app_commands.describe(dm = "@dm (optional)")
async def clear_command(interaction: discord.Interaction, sheet: str, player: discord.Member, dm: discord.Member = None):
	await interaction.response.defer(ephemeral = True)
	admin = c.Person(interaction)
	if admin.user.id not in s.ADMINS:
		await t.send_message(interaction, text = "Unauthorised use.\nContacting Pinkertons please wait.")
		return
	await com.sh.clear_sheet(interaction, sheet, player, dm)


@bot.tree.command(name = "transfer", description = "Transfers parts of your sheet to a new version so you don't have to copy pasta manually.")
@app_commands.choices(what_to_transfer = [
	app_commands.Choice(name = "inventory", value = "inventory"),
	app_commands.Choice(name = "money tracker", value = "money_tracker"),
])
@app_commands.describe(old_sheet = "Old sheet name")
@app_commands.describe(new_sheet = "New sheet name")
async def transfer_slash(interaction: discord.Interaction, what_to_transfer: Choice[str], old_sheet: str, new_sheet: str):
	await interaction.response.defer(ephemeral = True)

	if not com.sh.ping_sheet(old_sheet):
		await t.send_message(interaction, text = "``{old_sheet}`` was not found.")
		return
	if not com.sh.ping_sheet(new_sheet):
		await t.send_message(interaction, text = f"``{new_sheet}`` was not found.")
		return

	what_to_transfer = what_to_transfer.value

	match what_to_transfer:
		case "inventory":
			com.sh.transfer_inventory(old_sheet, new_sheet)
			await t.send_message(interaction, text = f"Inventory successfully transferred!\n``{old_sheet}`` -> ``{new_sheet}``")
		case "money_tracker":
			com.sh.transfer_money(old_sheet, new_sheet)
			await t.send_message(interaction, text = f"Money Tracker successfully transferred!\n``{old_sheet}`` -> ``{new_sheet}``")


@bot.tree.command(name = "sort_inventory", description = "Sorts the active character's Inventory.")
@app_commands.choices(based_on = [
	app_commands.Choice(name = "name", value = "name"),
	app_commands.Choice(name = "type", value = "type"),
	app_commands.Choice(name = "info", value = "info"),
	app_commands.Choice(name = "count", value = "count"),
	app_commands.Choice(name = "amount", value = "amount"),
	app_commands.Choice(name = "weight", value = "weight"),
	app_commands.Choice(name = "sum_weight", value = "sum_weight"),
	app_commands.Choice(name = "auto_fill", value = "auto_fill")
])
@app_commands.choices(leave_spaces_between_types = [
	app_commands.Choice(name = "Yes", value = 1),
	app_commands.Choice(name = "No", value = 0)
])
@app_commands.choices(reverse_order = [
	app_commands.Choice(name = "Yes", value = 1),
	app_commands.Choice(name = "No", value = 0)
])
async def sort_inventory_slash(interaction: discord.Interaction, based_on: Choice[str], leave_spaces_between_types: Choice[int] = None, reverse_order: Choice[int] = None):
	await interaction.response.defer(ephemeral = True)
	person = c.Person(interaction)
	if not person.active:
		await t.send_message(interaction, text = f"You do not have an active character")
		return

	if leave_spaces_between_types is None:
		spaces = False
	else:
		spaces = int(leave_spaces_between_types.value)
	if reverse_order is None:
		reverse = False
	else:
		reverse = int(reverse_order.value)
	based_on = based_on.value
	sheet = c.Sheet(interaction)

	reply = com.sh.sort_inventory(sheet, based_on, spaces, reverse)
	if reply is None:
		await t.send_message(interaction, text = f"{sheet.character}'s inventory successfully sorted!")
	else:
		await t.send_message(interaction, text = reply)


help_list = help_descirption.help_list
help_type_fix = [
	app_commands.Choice(name = "Command List", value = "command_list"),
	app_commands.Choice(name = "Emoji Lookup", value = "emoji_lookup"),
]
for help_dict in help_list:
	help_type_fix.append(app_commands.Choice(name = help_dict["name"], value = help_dict["name"]))


@bot.tree.command(name = "help", description = "Display the command list or the documentation of each command.")
@app_commands.choices(help_type = help_type_fix)
@app_commands.choices(ephemeral = [
	app_commands.Choice(name = "private", value = 1),
	app_commands.Choice(name = "public", value = 0),
])
async def help_slash(interaction: discord.Interaction, help_type: Choice[str], ephemeral: Choice[int] = None):
	person = c.Person(interaction)
	help_type = help_type.value
	if not ephemeral:
		ephemeral = True
	else:
		ephemeral = bool(ephemeral.value)
	await interaction.response.defer(ephemeral = ephemeral)

	if help_type == "command_list":
		embed = discord.Embed(
			title = "Emoji Lookup Table",
			description = "",
			color = literal_eval(person.color)
		)
		embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)

		for inner_dict in help_list:
			embed.add_field(name = inner_dict["name"], value = inner_dict["short_description"], inline = False)
	elif help_type == "emoji_lookup":
		embed = discord.Embed(
			title = "Emoji Lookup Table",
			description = """
				:arrows_counterclockwise:  - reroll the same roll
				:boom: - crit
				:regional_indicator_q: - queue rolls
				:wave: - one handed damage
				:open_hands: - two handed damage
				:muscle: - flexible damage 
				:rosette: - zealot barb extra damage
				:fireworks: - paladin 2d8 smite damage
				:sparkler: - paladin 1d8 smite damage
				:stars: - paladin improved divine smite
				:dart: - runner precision smite
				:eye: - runner's hunter ambush strike
				:brain: - psychic blades
				:drop_of_blood: - blood hunter crimson rite damage
				[no icon yet] - charger feat (not implemented yet)
				:four_leaf_clover: - inspiration point give
				<:EldritchSmite:1071167194165170207> - eldritch smite
				:magic_wand: - polearm master
			""",
			color = literal_eval(person.color)
		)
		embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)
	else:
		inner_dict = None
		for inner_dict in help_list:
			if inner_dict["name"] == help_type:
				break
		embed = discord.Embed(
			title = inner_dict["name"].capitalize(),
			color = literal_eval(person.color)
		)
		embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)

		temp = "``, ``".join(inner_dict["calls"])
		embed.add_field(name = "Call", value = f"Call Type: {inner_dict['call_type']}\nCalls: ``{temp}``", inline = False)
		if len(inner_dict["long_description"]) > 1024:
			chunks = textwrap.wrap(inner_dict["long_description"], 1024, break_long_words = False, replace_whitespace = False)
			for part in chunks:
				embed.add_field(name = "", value = part, inline = False)
		else:
			embed.add_field(name = "Description", value = inner_dict["long_description"], inline = False)
		if inner_dict["example_uses"]:
			temp = "``, ``".join(inner_dict["example_uses"])
			embed.add_field(name = "Example(s):", value = f"``{temp}``", inline = False)

	await t.send_message(interaction, embed = embed)


@bot.tree.command(name = "x_admin_table", description = "Admin command used to create or destroy tables.")
@app_commands.choices(command = [
	app_commands.Choice(name = "create table", value = "create"),
	app_commands.Choice(name = "delete table", value = "delete"),
])
@app_commands.describe(table_name = "name of the table")
@app_commands.describe(gm = "@ the GM")
@app_commands.describe(player_role = "player role")
@app_commands.describe(guest_role = "guest role")
@app_commands.describe(main_channel = "channel")
async def table_admin(interaction: discord.Interaction, command: Choice[str], table_name: str, gm: discord.Member = None, player_role: discord.Role = None, guest_role: discord.Role = None, main_channel: discord.TextChannel = None):
	person = c.Person(interaction)
	if person.user.id not in s.ADMINS:
		await t.send_message(interaction, text = "This command is made for admins only. Please use /table to manage your tables.", ephemeral = True)
	else:
		interaction.response.defer()
		command = command.value
		table_name = table_name.capitalize()

		if command == "create":
			if not gm or not player_role or not guest_role:
				await t.send_message(interaction, text = "Missing Argument", ephemeral = True)
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute(
					f"INSERT INTO tables(table_name, dm_id, role_id, guest_id, auto_guest_add, main_channel_id) VALUES (?, ?, ?, ?, 0, ?)",
					(table_name, gm.id, player_role.id, guest_role.id, main_channel.id)
				)
			await t.send_message(interaction, f"Table with name ``{table_name}`` created.", ephemeral = True)
			await t.send_message(gm, f"You are the DM of the following table: ``{table_name}``.\nYou can add a player with the /table command.\nAll changes will notify the person in question!")
		else:
			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute(f"SELECT * FROM tables WHERE table_name = ?", (table_name,))
				raw = cursor.fetchall()

			if raw is not []:
				with t.DatabaseConnection("data.db") as connection:
					cursor = connection.cursor()
					cursor.execute(f"DELETE FROM tables WHERE table_name = ?", (table_name,))

				await t.send_message(interaction, text = f"Table ``{table_name}`` has been deleted.", ephemeral = True)
				await t.send_message(c.Person(discord_id = raw[0][1]), text = f"You are no longer the DM of the following table: ``{table_name}``.\nReason: table no longer exists.")
			else:
				await t.send_message(interaction, text = f"Table ``{table_name}`` not found.", ephemeral = True)


@bot.tree.command(name = "x_admin_emoji_role", description = "Admin command to set up emoji roles")
@app_commands.describe(channel_id = "id of channel")
@app_commands.describe(message_id = "id of message")
@app_commands.describe(emoji = "emoji")
@app_commands.describe(role = "role")
async def emoji_role_setup(interaction: discord.Interaction, channel_id: str, message_id: str, emoji: str, role: discord.Role):
	person = c.Person(interaction)
	if person.user.id in s.ADMINS:
		with t.DatabaseConnection("emoji_role.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"INSERT INTO emoji_role(guild_id, channel_id, message_id, emoji, role_id) VALUES (?, ?, ?, ?, ?)",
				(interaction.guild_id, channel_id, message_id, emoji, role.id)
			)

		channel = interaction.guild.get_channel(int(channel_id))
		message: discord.Message = await channel.fetch_message(int(message_id))
		await message.add_reaction(emoji)
		await t.send_message(interaction, text = f"Emoji_role successfully set up", ephemeral = True)
	else:
		await t.send_message(interaction, text = f"You are not an admin.", ephemeral = True)


@bot.tree.command(name = "table", description = "Manage your own tables! (send it in empty)")
async def table_slash(interaction: discord.Interaction):
	await table_command(interaction)


@bot.tree.command(name = "create_table", description = "Create your own table! (send it in empty)")
async def create_table(interaction: discord.Interaction):
	await table_maker_main(interaction)


@bot.command(name = "vote", aliases = ["v"])
async def vote_slash(ctx, *, text_dump_):
	await vote_command(ctx, text_dump_)


@bot.tree.command(name = "x_admin_title", description = "Admin command to manage titles")
async def title_admin(interaction: discord.Interaction):
	person = c.Person(interaction)
	if person.user.id in s.ADMINS:
		await title_command(interaction)


@bot.tree.command(name = "titles", description = "Request someone's titles.")
@app_commands.describe(person = "@ the person")
async def title_request(interaction: discord.Interaction, person: discord.User = None):
	if not person:
		person = interaction.user
		outside_call = False
	else:
		outside_call = True

	titles = t.get_titles(person)

	person = c.Person(discord_id = person.id)

	major = []
	minor = []
	for title in titles:
		if title.rank == "Major":
			major.append(title.name)
		else:
			minor.append(title.name)
	major = "\n- ".join(major)
	minor = "\n- ".join(minor)

	if major:
		major = f"- {major}"
	if minor:
		minor = f"- {minor}"

	embed = discord.Embed(
		title = f"Major Titles",
		description = major,
		color = literal_eval(person.color)
	)
	embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)
	embed.add_field(name = "Minor Titles", value = minor, inline = False)
	if outside_call:
		embed.set_footer(text = f"Requested by {interaction.user.display_name}")

	await t.send_message(interaction, embed = embed)


@bot.command(name = "draw", aliases = ["d"])
async def draw(ctx: discord.ext.commands.Context, deck: str):
	await com.draw_card(ctx, deck)


@bot.command(name = "shuffle", aliases = ["reshuffle"])
async def shuffle(ctx: discord.ext.commands.Context, deck: str):
	if random.randint(1, 20) == 20:
		loader = await t.load(ctx, "Everyday I'm shufflin'")
	else:
		loader = await t.load(ctx, "Shuffling in progress.")
	await com.shuffle_deck(ctx, deck)
	await loader.delete()


@bot.tree.command(name = "deck", description = "Create, edit, or remove your decks.")
async def deck_slash(interaction: discord.Interaction):
	await deck_command(interaction)


@bot.tree.command(name = "veterancy", description = "Get the veterancy rank of a person.")
@app_commands.describe(person = "@ the person")
async def veterancy(interaction: discord.Interaction, person: discord.User = None):
	await com.veterancy_command(interaction, person)


@bot.tree.command(name = "x_admin_veterancy_recalc", description = "Recalculates the veterancy of a person.")
async def recalc_veterancy(interaction: discord.Interaction, person: discord.User = None):
	await com.veterancy_command(interaction, person, True)


with open("data_holder/token.txt", "r") as f:
	_lines_ = f.readlines()

TOKEN = _lines_[0].strip()

bot.run(TOKEN)
