from database_handler import DatabaseConnection
from bot_setup import bot
import commands as com
import settings as s
import discord
import asyncio
import random


def exists(identifier, data_type, ctx = None):
	if data_type == "person":
		with DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(f"SELECT * FROM people WHERE discord_id = ?", (identifier,))
			person = cursor.fetchall()
		if person:
			return True
	else:
		raise NotImplemented

	return False


def choice(incoming):  # list or dict
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


async def send_message(ctx, message, reply = False, embed = False, followups = None, is_return = False, ephemeral = False, silent = False, tts = False):
	if reply:
		if embed:
			sent = await ctx.reply(embed = message, ephemeral = ephemeral, silent = silent)
		else:
			sent = await ctx.reply(message, ephemeral = ephemeral, silent = silent, tts = tts)
	else:
		if embed:
			sent = await ctx.send(embed = message, ephemeral = ephemeral, silent = silent)
		else:
			sent = await ctx.send(message, ephemeral = ephemeral, silent = silent, tts = tts)
	if followups:
		asyncio.create_task(followup_instance(ctx, sent, followups))
	if is_return:
		return sent
	return


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
	for i in s.SPELL:
		if i == split[:len(i)]:
			return "SPELL_ATTACK", split[:len(i)], split[len(i):]
	for i in s.SPELL_MOD:
		if i == split[:len(i)]:
			return "SPELL_MOD", split[:len(i)], split[len(i):]
	return False


async def load(ctx, load_message = None):
	if load_message is None:
		load_message = f'Command: "{ctx.message.clean_content.replace(bot.command_prefix, "")}"'
	loader = choice(s.LOADERS)
	load_txt = f"``{load_message}``\n{loader[-1]}"
	sent = await ctx.send(load_txt, silent = True)
	asyncio.create_task(await asyncio.to_thread(loading_loop, sent, load_message, loader))
	return sent


async def loading_loop(sent, message, loader):
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
			await sent.edit(content = "Load expired. We'll get 'em next time.")


async def place_emojis(sent, emojis):
	for emoji in emojis:
		await sent.add_reaction(emoji)


async def followup_instance(ctx, sent_inc, followups):
	emoticons = []
	for followup in followups:
		emoticons.append(followup.emoji)
	asyncio.create_task(place_emojis(sent_inc, emoticons))

	def check(reaction_, user_):
		return (user_ == ctx.author) and (str(reaction_.emoji) in emoticons or reaction_.emoji in emoticons) and (reaction_.message.id == sent_inc.id)

	active = True
	while active:
		try:
			reaction, user = await bot.wait_for("reaction_add", timeout = 180, check = check)
			for followup in followups:
				if str(reaction.emoji) != followup.emoji and reaction.emoji != followup.emoji:
					continue

				if followup.type == "roll":
					asyncio.create_task(com.roll_command(ctx, followup.data))
					await sent_inc.remove_reaction(followup.emoji, user)
				elif followup.type == "disable":
					active = False
		except asyncio.TimeoutError:
			for emoji in emoticons:
				await sent_inc.clear_reaction(emoji)
			active = False


pass
