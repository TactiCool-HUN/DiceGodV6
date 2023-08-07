from utils.database_handler import DatabaseConnection
from datetime import datetime
from ast import literal_eval
from utils.bot_setup import bot
import commands as com
from utils import settings as s
import classes as c
import discord.ext
import asyncio
import random
import math
from views.followup_view import FollowupView, FollowupButton


def identifier_to_member(identifier: discord.Interaction | discord.ext.commands.Context) -> discord.Member:
	if isinstance(identifier, discord.Interaction):
		identifier: discord.Interaction
		return identifier.user
	else:
		identifier: discord.ext.commands.Context
		return identifier.author


def exists(identifier, data_type):
	match data_type:
		case "person":
			with DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM people WHERE discord_id = ?", (identifier,))
				person = cursor.fetchall()
			if person:
				return True
		case "char":
			with DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM sheets WHERE character = ?", (identifier,))
				char = cursor.fetchall()
			if char:
				return True
		case "sheet_name":
			with DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM sheets WHERE sheet = ?", (identifier,))
				sheet = cursor.fetchall()
			if sheet:
				return True
		case "die":
			with DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM dice WHERE name = ?", (identifier,))
				die = cursor.fetchall()
			if die:
				return True

	return False


def is_rented(sheet, user):
	with DatabaseConnection("data.db") as connection:
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM sheet_rents WHERE user_id = ?", (user.id,))
		raw = cursor.fetchall()
	for rent in raw:
		if rent[3] == sheet.character:
			return True
	return False


def choice(incoming):  # weighted list or dict
	choice_list = []
	weight_list = []

	if type(incoming) == list:
		for i, item in enumerate(incoming):
			if i % 2 == 1:
				weight_list.append(item)
			else:
				choice_list.append(item)
	else:
		for item in incoming:
			choice_list.append(item)
			weight_list.append(incoming[item])

	result = random.choices(choice_list, weights = weight_list)[0]
	return result


def num2word(num):
	if num < 0:
		negative = True
		num = -1 * num
	elif num == 0:
		return ":zero:"
	else:
		negative = False
	numbers = [":zero:", ":one:", ":two:", ":three:", ":four:", ":five:", ":six:", ":seven:", ":eight:", ":nine:", ":ten:"]
	one = num % 10  # singles digit
	two = int(((num % 100) - one) / 10)  # tens digit
	three = int(((num % 1000) - (two * 10) - one) / 100)  # hundreds digit
	four = int(((num % 10000) - (three * 100) - (two * 10) - one) / 1000)  # thousands digit
	five = int(((num % 100000) - (four * 1000) - (three * 100) - (two * 10) - one) / 10000)  # ten thousand digit
	six = int(((num % 1000000) - (five * 10000) - (four * 1000) - (three * 100) - (two * 10) - one) / 100000)  # a hundred thousand digit
	values = [six, five, four, three, two, one]
	#  values = [1, 2, 0, 4]
	while True:
		if values[0] == 0:
			values.remove(values[0])
		else:
			break
	if negative:
		word = ":no_entry:"
	else:
		word = ""
	for word_raw in values:
		word += numbers[word_raw]
	return word


def sign_merger(sign_list):
	num = 0
	for sign in sign_list:
		if sign == "-":
			num += 1
	if num % 2 == 0:
		return "+"
	else:
		return "-"


def get_followup_view(followups: list[FollowupButton], identifier: discord.Message | discord.Interaction | discord.ext.commands.Context) -> FollowupView:
	is_crit = False
	is_reroll = False
	ordered = False
	for button in followups:
		button: FollowupButton
		if button.emoji.name == "\U0001F504":
			is_reroll = True
		elif button.emoji.name == "💥":
			is_crit = True
		if is_reroll and is_crit:
			ordered = True
			break

	negatives = []
	if ordered and len(followups) < 13:
		row_1 = 0
		for button in followups:
			button: FollowupButton
			if button.emoji.name == "\U0001F504":
				button.row = 0
			elif button.emoji.name == "💥":
				button.row = 0
			elif button.emoji.name == "🇶":
				button.row = 0
			elif row_1 < 5:
				button.row = 1
				"""temp = FollowupButton(button.emoji, button.data, f"roll_negative")
				temp.row = 2
				temp.disabled = True
				temp.style = discord.ButtonStyle.grey
				temp.label = f"-{button.label}"
				negatives.append(temp)"""
				row_1 += 1
			else:
				button.row = 3
				"""temp = FollowupButton(button.emoji, button.data, f"roll_negative")
				temp.row = 4
				temp.disabled = True
				temp.style = discord.ButtonStyle.grey
				temp.label = f"-{button.label}"
				negatives.append(temp)"""

	view = FollowupView(identifier)
	for i in followups:
		view.add_item(i)
	for i in negatives:
		view.add_item(i)

	return view


async def send_message(identifier: discord.Message | discord.Interaction | discord.ext.commands.Context | discord.Member | c.Person, text: str = None, embed: discord.Embed = None, followups: list[FollowupButton] = None, **kwargs: bool):
	ephemeral = kwargs.get("ephemeral", False)
	reply = kwargs.get("reply", False)
	silent = kwargs.get("silent", True)
	tts = kwargs.get("tts", False)

	match type(identifier):
		case discord.Message | discord.Interaction | discord.ext.commands.Context:  # send message
			if isinstance(identifier, discord.Interaction):
				identifier: discord.Interaction = identifier

				if followups:
					view = get_followup_view(followups, identifier)
				else:
					view = discord.ui.View()

				try:
					sent = await identifier.response.send_message(content = text, embed = embed, view = view, silent = silent, tts = tts, ephemeral = ephemeral)
				except discord.InteractionResponded:
					sent = await identifier.followup.send(content = text, embed = embed, view = view, silent = silent, tts = tts, ephemeral = ephemeral)
			elif isinstance(identifier, discord.Message) or isinstance(identifier, discord.ext.commands.Context):
				if isinstance(identifier, discord.ext.commands.Context):
					message: discord.Message = identifier.message
				else:
					message: discord.Message = identifier

				if followups:
					view = get_followup_view(followups, identifier)
				else:
					view = None

				if reply:
					sent = await message.reply(content = text, embed = embed, view = view, silent = silent, tts = tts)
				else:
					sent = await message.channel.send(content = text, embed = embed, view = view, silent = silent, tts = tts)
			else:
				raise TypeError
		case c.Person | discord.Member:  # send DM
			if isinstance(identifier, c.Person):
				member = identifier.user
			else:
				member = identifier

			channel: discord.DMChannel = await member.create_dm()
			sent = await channel.send(content = text, embed = embed, silent = silent, tts = tts)
		case _:
			raise AttributeError

	return sent


"""async def send_message_old(ctx, message, reply: bool = False, embed: bool = False, followups: list[FollowupButton] = None, is_return: bool = False, ephemeral: bool = False, silent: bool = True, tts: bool = False):
	if followups:
		view = FollowupView(ctx)
		for i in followups:
			view.add_item(i)
	else:
		view = None
	if reply:
		if embed:
			sent = await ctx.reply(embed = message, ephemeral = ephemeral, silent = silent, view = view)
		else:
			sent = await ctx.reply(message, ephemeral = ephemeral, silent = silent, tts = tts, view = view)
	else:
		if embed:
			sent = await ctx.send(embed = message, ephemeral = ephemeral, silent = silent, view = view)
		else:
			sent = await ctx.send(message, ephemeral = ephemeral, silent = silent, tts = tts, view = view)
	if is_return:
		return sent
	return


async def send_dm(ctx, message, embed = False, discord_id = None, silent = False):
	if discord_id:
		user = c.Person(discord_id = discord_id).user
	else:
		user = ctx.author
	channel = await user.create_dm()
	if embed:
		await channel.send(embed = message, silent = silent)
	else:
		await channel.send(message, silent = silent)"""


def is_sheet_based(split):
	for i in s.SKILLS:
		if i == split[:len(i)]:
			return "SKILLS", split[:len(i)], split[len(i):]
	for i in s.PROF:
		if i == split[:len(i)]:
			return "PROF", split[:len(i)], split[len(i):]
	for i in s.SAVES:
		if i == split[:len(i)]:
			return "SAVES", split[:len(i)], split[len(i):]
	for i in s.C_SKILLS:
		if i == split[:len(i)]:
			return "C_SKILLS", split[:len(i)], split[len(i):]
	for i in s.C_SAVES:
		if i == split[:len(i)]:
			return "C_SAVES", split[:len(i)], split[len(i):]
	for i in s.ATTACKS:
		if i == split[:len(i)]:
			return "ATTACKS", split[:len(i)], split[len(i):]
	for i in s.C_ATTACKS:
		if i == split[:len(i)]:
			return "C_ATTACKS", split[:len(i)], split[len(i):]
	for i in s.DAMAGE:
		if i == split[:len(i)]:
			return "DAMAGE", split[:len(i)], split[len(i):]
	for i in s.C_DAMAGE:
		if i == split[:len(i)]:
			return "C_DAMAGE", split[:len(i)], split[len(i):]
	for i in s.SPELL_MOD:
		if i == split[:len(i)]:
			return "SPELL_MOD", split[:len(i)], split[len(i):]
	for i in s.SPELL_ATTACK:
		if i == split[:len(i)]:
			return "SPELL_ATTACK", split[:len(i)], split[len(i):]
	for i in s.ABILITIES:
		if i == split[:len(i)]:
			return "ABILITIES", split[:len(i)], split[len(i):]
	return False


def is_die(split):
	with DatabaseConnection("data.db") as connection:
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM dice")
		raw = cursor.fetchall()
	for i in raw:
		if i[1] == split[:len(i[1])]:
			return split[:len(i[1])], split[len(i[1]):]
	return False


def get_inventory_spaces(version):
	version = int(version)
	data = {}
	if version >= 50000:
		data["name"] = 0
		data["type"] = 5
		data["description1"] = 10
		data["description2"] = 20
		data["info"] = 30
		data["amount"] = 34
		data["count"] = 37
		data["weight"] = 39
		data["auto_fill"] = 45
		area = "B12:AV312"
		empties = [41, 43]
	elif version >= 40000:
		data["name"] = 0
		data["type"] = 5
		data["description1"] = 10
		data["description2"] = 21
		data["info"] = 32
		data["amount"] = 36
		data["count"] = 39
		data["weight"] = 41
		area = "B12:AV312"
		empties = []
	else:
		data["name"] = 0
		data["type"] = 6
		data["description1"] = 10
		data["description2"] = 22
		data["info"] = 34
		data["amount"] = 37
		data["count"] = 39
		data["weight"] = 41
		area = "B12:AR312"
		empties = []

	default = {
		"name": "",
		"type": "",
		"description1": "",
		"description2": "",
		"info": "",
		"amount": 0,
		"count": True,
		"weight": 0,
		"auto_fill": False
	}

	empty_line = []
	for i in range(data[list(data)[-1]] + 1):
		if i in empties:
			empty_line.append(None)
		else:
			empty_line.append("")
	for k in data:
		empty_line[data[k]] = default[k]

	return data, area, empty_line


async def load(ctx: discord.ext.commands.Context, load_message = None) -> discord.Message:
	if load_message is None:
		load_message = f'Command: "{ctx.message.clean_content.replace(bot.command_prefix, "")}"'
	loader = choice(s.LOADERS)
	load_txt = f"``{load_message}``\n{loader}"
	sent = await send_message(ctx, text = load_txt, silent = True)
	# asyncio.create_task(await asyncio.to_thread(loading_loop, sent, load_message, loader))
	return sent


"""async def loading_loop(sent, message, loader):
	x = 0
	run = True
	while run:
		for i in loader:
			x = x + 1
			if message:
				temp = f"``{message}``\n{i}"
			else:
				temp = i
			await asyncio.sleep(1)
			try:
				await sent.edit(content = temp)
			except discord.errors.NotFound:
				run = False
				break

		if x > 100:
			await sent.edit(content = "Load expired. We'll get 'em next time.")"""


def seconds_to_clock(seconds):
	seconds = math.ceil(seconds)
	minutes = math.floor(seconds / 60)
	seconds = seconds % 60
	if seconds < 10:
		seconds = f"0{seconds}"
	clock = f"{minutes}:{seconds}"
	return clock


async def clear_progress(player, sheet, progress, start_time, current_inc = None, add_inc = None, sent_inc = None):
	player = c.Person(discord_id = player.id)

	temp = 0
	for item in progress:
		if item == "Overall":
			continue
		temp = temp + progress[item][1]
	progress["Overall"][1] = temp

	if current_inc and add_inc:
		progress[current_inc][0] = min(progress[current_inc][0] + add_inc, progress[current_inc][1])
		progress["Overall"][0] = min(progress["Overall"][0] + add_inc, progress["Overall"][1])

	embed = discord.Embed(
		title = f"Preparations of {sheet}",
		description = f"The sheet ``{sheet}`` is being prepared for you. You can see the progress below. When it's ready You'll be sent an access link!",
		color = literal_eval(player.color)
	)
	for element in progress:
		current = progress[element][0]  # 100
		maximum = progress[element][1]
		percentage = current / maximum
		full = math.ceil(20 * percentage)
		bar = ""
		for i in range(20):
			if i < full:
				bar = f"{bar}█"
			else:
				bar = f"{bar}░"

		percentage = math.ceil(percentage * 100)
		if element == "Overall":
			if current < 5:
				time_left = "[calculating]"
			else:
				remaining = maximum - current  # 200
				seconds_spent = (datetime.now() - start_time).seconds  # 200
				time_left = seconds_spent / current * remaining
				time_left = seconds_to_clock(time_left)
			add = f"\nEstimated time remaining: {time_left}\n(at this point random numbers might be more accurate xD)"
		elif element == "Notes":
			add = '\n(probably scamming you)'
		else:
			add = ""
		embed.add_field(name = element.title(), value = f"{percentage}% | {bar} | {current}/{maximum}{add}", inline = False)

	if sent_inc is None:
		return await send_message(player, embed = embed)
	else:
		await sent_inc.edit(embed = embed)


def limited_calc_splitter(area, split_num: int, place: str, output: str) -> str:  # area = A1:AW53
	for i, line in enumerate(area):
		while len(line) < 46:
			line.append("")
		area[i] = line
	row = split_num // 2  # 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
	column = split_num % 2  # 0, 1

	if row < 3:
		if place == "name":
			row = 1 + row * 5
			column = 5 + column * 24
		elif place == "source":
			row = 2 + row * 5
			column = 9 + column * 24
		elif place == "description":
			row = 3 + row * 5
			column = 1 + column * 24
		elif place == "current":
			row = 4 + row * 5
			column = 5 + column * 24
		elif place == "maximum":
			row = 4 + row * 5
			column = 12 + column * 24
		elif place == "recharge":
			row = 4 + row * 5
			column = 19 + column * 24
		elif place == "note":
			row = None
			column = None
		else:
			raise ValueError("limited calc splitter got unexpected input")
	else:
		if place == "name":
			row = -12 + row * 7
			column = 5 + column * 24
		elif place == "source":
			row = -11 + row * 7
			column = 9 + column * 24
		elif place == "description":
			row = -10 + row * 7
			column = 1 + column * 24
		elif place == "current":
			row = -9 + row * 7
			column = 5 + column * 24
		elif place == "maximum":
			row = -9 + row * 7
			column = 12 + column * 24
		elif place == "recharge":
			row = -9 + row * 7
			column = 19 + column * 24
		elif place == "note":
			row = -7 + row * 7
			column = 1 + column * 24
		else:
			raise ValueError("limited calc splitter got unexpected input")
	if output == "value":
		output = area[row][column].lower().replace(" ", "")
	elif output == "place":
		output = f"{s.LETTERS[column]}{row + 1}"
	else:
		raise ValueError("limited calc splitter got unexpected input")
	return output


def most_frequent(list_inc):
	counter = 0
	num = list_inc[0]

	for i in list_inc:
		curr_frequency = list_inc.count(i)
		if curr_frequency > counter:
			counter = curr_frequency
			num = i

	return num


def mention_texts(id_list: list[int]) -> str:
	new_list = []
	for my_id in id_list:
		new_list.append(f"<@{my_id}>")

	return ", ".join(new_list)


"""async def place_emojis(sent, emojis):
	for emoji in emojis:
		await sent.add_reaction(emoji)


async def followup_instance(ctx, sent_inc, followups):
	queue = False
	queued_text = ""
	crit = False
	crit_sent = None

	emoticons = []
	for followup in followups:
		emoticons.append(followup.emoji)
	asyncio.create_task(place_emojis(sent_inc, emoticons))

	def check(reaction_, user_):
		return (user_ == ctx.author) and (str(reaction_.emoji) in emoticons or reaction_.emoji in emoticons) and (reaction_.user_message.id == sent_inc.id)

	active = True
	while active:
		try:
			reaction, user = await bot.wait_for("reaction_add", timeout = 180, check = check)
			for followup in followups:
				if str(reaction.emoji) != followup.emoji and reaction.emoji != followup.emoji:
					continue

				match followup.type:
					case "roll":
						if queue:
							queued_text += f"+{followup.data}"
						else:
							asyncio.create_task(com.roll_command(ctx, followup.data, crit = crit))
							queued_text = ""
							await sent_inc.remove_reaction(followup.emoji, user)
					case "queue":
						if queue:
							asyncio.create_task(com.roll_command(ctx, queued_text, crit = crit))
							queued_text = ""
							queue = False
							for emoji in emoticons:
								await sent_inc.remove_reaction(emoji, user)
						else:
							queue = True
							await sent_inc.remove_reaction(followup.emoji, user)
					case "crit":
						crit = not crit
						if crit_sent:
							await crit_sent.delete()
						if crit:
							crit_sent = await sent_inc.reply(f"Emoji rolls are now critical for this roll!")
						else:
							crit_sent = await sent_inc.reply(f"Emoji rolls are now __not__ critical for this roll!")
						await sent_inc.remove_reaction(followup.emoji, user)
					case "heal_hurt":
						asyncio.create_task(com.hp_command(ctx, followup.data[0], followup.data[1]))
						await sent_inc.delete()
						active = False
					case "rest":
						sent = await load(ctx)
						asyncio.create_task(com.rest_command(ctx, length = "long", sent = sent))
						await sent_inc.delete()
						active = False
					case "spell":
						asyncio.create_task(send_message(ctx, followup.data.create_embed(), embed = True, reply = True, followups = followup.data.followups))
						await sent_inc.delete()
						active = False
					case "cast":
						sent = await load(ctx)
						await sent_inc.delete()
						asyncio.create_task(com.cast_command(ctx, followup.data[0], sent, None, followup.data[1], True))
						active = False
					case "return_true":
						await sent_inc.remove_reaction(followup.emoji, user)
						return True
					case "return_false":
						await sent_inc.remove_reaction(followup.emoji, user)
						return False
					case "disable":
						if followup.data:
							await send_message(ctx, followup.data)
						active = False
					case "delete_message":
						if followup.data:
							try:
								await followup.data.delete()
							except discord.errors.NotFound:
								pass
						await sent_inc.delete()
						active = False
					case "add_inspiration":
						text = com.sh.change_inspiration(ctx, "add", 1)
						await send_message(ctx, text)
						await sent_inc.clear_reaction(followup.emoji)
					case "condition":
						for emoji in emoticons:
							await sent_inc.clear_reaction(emoji)
						active = False
						for condition in followup.data:
							reply = await com.sh.set_condition(ctx, condition[0], condition[1], None)
							if reply:
								await send_message(ctx, reply, reply = True)
					case "coin":
						response_list = [
							f"{c.Person(ctx).user.display_name} flipped a coin and it landed on... it's side?", 1,
							f"{c.Person(ctx).user.display_name} flipped a coin and it landed on **heads**!", 49,
							f"{c.Person(ctx).user.display_name} flipped a coin and it landed on **tails**!", 51
						]
						await send_message(ctx, choice(response_list))
						if followup.data:
							await send_message(ctx, followup.data)
						active = False
					case "confirm_temphp":
						txt, _ = await com.sh.set_temp(ctx, followup.data[0], True, followup.data[1])
						await send_message(ctx, txt, reply = True)
						for emoji in emoticons:
							await sent_inc.clear_reaction(emoji)
		except asyncio.TimeoutError:
			for emoji in emoticons:
				await sent_inc.clear_reaction(emoji)
			active = False"""


async def send_pack(pack: c.Pack, is_reply: bool = True, ephemeral: bool = False):
	person = c.Person(pack.identifier)
	result = 0
	complex_roll = ""
	has_dynamic = False
	has_death = False
	all_damage_types = []
	roll_display_pack = []
	all_roll_notes = []

	for roll in pack.single_rolls:
		if roll.pre_send:
			for text in roll.pre_send:
				if "lol" in roll.pre_send and person.user.id == 875753704685436938:
					tts = True
					reply = False
				else:
					tts = False
					reply = True
				asyncio.create_task(send_message(pack.identifier, text = text, reply = reply, silent = False, tts = tts))

		all_roll_notes += roll.roll_note

		for damage in roll.damage_type:
			temp = s.DAMAGE_TYPES.get(damage)
			if temp not in all_damage_types:
				all_damage_types.append(temp)

		match roll.speciality:
			case "init":
				asyncio.create_task(com.sh.init_resources(pack.identifier))
			case "deathsave":
				has_death = roll.die_result

		if roll.dynamic:
			has_dynamic = True
		if roll.sign == "-":
			result += -int(roll.full_result)
		else:
			result += int(roll.full_result)

		if roll.dice_number:
			if complex_roll == "":
				complex_roll = f"{roll.full_result} [{roll.create_name()}]"
				if roll.sign == "-":
					complex_roll = f"- {complex_roll}"
			else:
				complex_roll = f"{complex_roll} {roll.sign} {roll.full_result} [{roll.create_name()}]"

			value_disp = ""
			count = 1
			for roll_no, local_result in enumerate(roll.results):
				person.add_roll(local_result[0], roll.die_size, local_result[1], roll.raw_text)
				if len(value_disp) > 900:
					roll_display_pack.append([f"**Rolls [{roll.create_name(short = True)}]**", value_disp])
					value_disp = ""
					count = 1
				if local_result[1]:
					if count == 1:
						value_disp = f"{value_disp}Roll #{roll_no + 1}: **{local_result[0]}**"
						count = 2
					else:
						value_disp = f"{value_disp} | Roll #{roll_no + 1}: **{local_result[0]}**\n"
						count = 1
				else:
					if count == 1:
						value_disp = f"{value_disp}~~Roll #{roll_no + 1}: **{local_result[0]}**~~"
						count = 2
					else:
						value_disp = f"{value_disp} | ~~Roll #{roll_no + 1}: **{local_result[0]}**~~\n"
						count = 1
			roll_display_pack.append([f"**Rolls [{roll.create_name(short = True)}]**", value_disp])
		else:
			if complex_roll == "":
				if roll.sign == "+":
					complex_roll = f"{roll.full_result}"
				else:
					complex_roll = f"{roll.sign} {roll.full_result}"
			else:
				complex_roll = f"{complex_roll} {roll.sign} {roll.full_result}"

	embed = discord.Embed(
		title = f"**Roll Result:** {num2word(result)} {''.join(all_damage_types)}",
		description = complex_roll,
		color = literal_eval(person.color)
	)

	if has_dynamic:
		sheet = c.Sheet(pack.identifier)
		if sheet.char_image:
			url = sheet.char_image
		else:
			url = person.user.avatar.url
		embed.set_author(name = person.active, icon_url = url)
	else:
		embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)

	for element in roll_display_pack:
		embed.add_field(name = element[0], value = element[1])

	if all_roll_notes:
		footer = "".join(all_roll_notes)

		embed.set_footer(text = footer)

	if has_death:
		await com.sh.set_deathsave(pack.identifier, has_death, result)
	await send_message(pack.identifier, embed = embed, reply = is_reply, followups = pack.followups, ephemeral = ephemeral)


async def send_multipack(packs: list[c.Pack], roll_text: str, is_reply: bool = True, ephemeral: bool = False) -> None:
	person = c.Person(packs[0].identifier)
	all_roll_notes = []
	all_damage_types = []

	if len(packs) > 4:
		inline = True
	else:
		inline = False

	result = 0
	has_dynamic = False

	embed = discord.Embed(
		title = f"Multi-Roll",
		color = literal_eval(person.color)
	)

	for i, pack in enumerate(packs):
		has_death = False
		pack_result = 0
		pack_descriptions = []

		for roll in pack.single_rolls:
			roll_descriptions = []

			if roll.pre_send:
				for text in roll.pre_send:
					if "lol" in roll.pre_send and person.user.id == 875753704685436938:
						tts = True
						reply = False
					else:
						tts = False
						reply = True
					asyncio.create_task(send_message(pack.identifier, text = text, reply = reply, silent = False, tts = tts))

			all_roll_notes += roll.roll_note

			for damage in roll.damage_type:
				temp = s.DAMAGE_TYPES.get(damage)
				if temp not in all_damage_types:
					all_damage_types.append(temp)

			match roll.speciality:
				case "init":
					asyncio.create_task(com.sh.init_resources(pack.identifier))
				case "deathsave":
					has_death = roll.die_result

			if roll.dynamic:
				has_dynamic = True
			if roll.sign == "-":
				result += -int(roll.full_result)
				pack_result += -int(roll.full_result)
			else:
				result += int(roll.full_result)
				pack_result += int(roll.full_result)

			value_disp = ""
			count = 1
			for roll_no, local_result in enumerate(roll.results):
				person.add_roll(local_result[0], roll.die_size, local_result[1], roll.raw_text)
				if len(value_disp) > 900:
					roll_descriptions.append(f"__Rolls [{roll.create_name(short = True)}]__\n{value_disp}")
					value_disp = ""
					count = 1
				if local_result[1]:
					if count == 1:
						value_disp = f"{value_disp}Roll #{roll_no + 1}: **{local_result[0]}**"
						count = 2
					else:
						value_disp = f"{value_disp} | Roll #{roll_no + 1}: **{local_result[0]}**\n"
						count = 1
				else:
					if count == 1:
						value_disp = f"{value_disp}~~Roll #{roll_no + 1}: **{local_result[0]}**~~"
						count = 2
					else:
						value_disp = f"{value_disp} | ~~Roll #{roll_no + 1}: **{local_result[0]}**~~\n"
						count = 1

			roll_descriptions.append(f"__Rolls [{roll.create_name(short = True)}]__\n{value_disp}")
			pack_descriptions.append("\n".join(roll_descriptions))

		if has_death:
			await com.sh.set_deathsave(pack.identifier, has_death, pack_result)
		embed.add_field(name = f"Sum #{i + 1} - {num2word(pack_result)}", value = "\n".join(pack_descriptions), inline = inline)

	embed.description = f"Combined Sum: {result}\nRoll Text: {roll_text}\nTimes: {len(packs)}"

	if all_roll_notes:
		footer = "".join(all_roll_notes)

		embed.set_footer(text = footer)

	if has_dynamic:
		sheet = c.Sheet(packs[0].identifier)
		if sheet.char_image:
			url = sheet.char_image
		else:
			url = person.user.avatar.url
		embed.set_author(name = person.active, icon_url = url)
	else:
		embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)

	asyncio.create_task(send_message(packs[0].identifier, embed = embed, reply = is_reply, followups = packs[0].followups, ephemeral = ephemeral))


pass
