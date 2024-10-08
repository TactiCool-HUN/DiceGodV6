import discord.channel
from utils.tools import choice, send_message
import classes as c
from utils import settings, bot_setup
import random
import re
from secondary_functions.uwuifier import uwu
from ast import literal_eval
import utils.settings as s
import utils.tools as t
import secondary_functions.markovifier as markov
from secondary_functions.azure_tts import azure_tts
import asyncio


async def bot_responses(message: discord.Message):
	if bot_setup.prefix == "--":
		return
	if isinstance(message.channel, discord.channel.DMChannel):
		return
	if message.channel.category_id == 996065301055688794:  # no talking in dicegod sanctuary
		return
	if message.channel.id == 1032650247622639686:
		return

	person = c.Person(message.author)
	if person.chat_ignore:
		return

	markov.markov_learner(message.content, message.guild.id)

	voice_client = discord.utils.get(t.bot.voice_clients, guild = message.guild)
	try:
		if voice_client.channel.id == message.channel.id and person.tts_perms:
			asyncio.create_task(azure_tts(message, voice_client, person))
	except AttributeError:
		pass

	content = message.clean_content.lower()
	content_splits = re.split(" ", content)
	is_admin = person.user.id in settings.ADMINS
	author = message.author
	responses = []

	for split in content_splits:  # - - - - - funny number - - - - -
		if "69" in split and split[0] != "<" and split[-1] != ">":
			response_list = [
				"Nice!", 1,
				"nice", 1,
				"Nice", 1,
			]
			responses.append(choice(response_list))

	if bot_setup.bot.user.mentioned_in(message) or "dice god" in content or "dicegod" in content:
		# noinspection SpellCheckingInspection
		admin_base = [
			"Yes", 2,
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			markov.markovifier(message.guild.id), 0.3
		]
		# noinspection SpellCheckingInspection
		cultist_base = [
			"Yes", 1,
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"Be careful when you speak my name, mortal.", 0.5,
			"Kinky :3", 0.8,
			markov.markovifier(message.guild.id), 0.3,
			None, 1,
		]
		# noinspection SpellCheckingInspection
		comonner_base = [
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"Be careful when you speak my name, mortal.", 0.5,
			markov.markovifier(message.guild.id), 0.2,
			None, 1,
		]
		# noinspection SpellCheckingInspection
		mag = [
			"Yes", 1,
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"Be careful when you speak my name, mortal.", 1,
			"A Sister of Silence? Hmm, I feel like we might have a lot in common...", 1,
			None, 1,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		eszter = [
			"Yes", 2,
			"No.", 3,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"Be careful when you speak my name, mortal.", 1,
			"Imagine using an emoji as a profile pic...", 0.8,
			"At least I was never confused with a trashcan.", 1,
			'Imagine having the nickname "Spiky", lol', 0.5,
			'Calling me a "False God" when you are a false DM is just ironic...', 1.3,
			"Who hurt you?", 1,
			"The one who wages a war with Lady Luck herself. Your efforts are cute, but futile.", 1,
			'Wtf is "crosswalk talk", like c\'mon', 1,
			None, 1,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		anna = [
			"Yes", 1,
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"<:AnnaSticker:960105630188863498>", 0.5,
			"Be careful when you speak my name, mortal.", 1,
			"X gon' give it to you", 1,
			"Stop arguing, you know I'm right.", 1,
			'"Ethyrin"? What kind of name is that?', 1,
			"Who hurt you?", 1,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		agi = [
			"Yes", 1,
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"<:AgiSticker:960105630465675294>", 0.5,
			"Be careful when you speak my name, mortal.", 1,
			"Who hurt you?", 0.5,
			"Kinky :3", 0.6,
			"🧂", 0.75,
			"I remember the times when you were dead set on never praying to me. I'm glad you changed your mind", 0.25,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		nika = [
			"Yes", 0.3,
			"No.", 2,
			"Maybe?", 2,
			"<:Kyrihihihi:1058348961523576872>", 2,
			"<:NikaSticker:960105630989955173>", 1,
			"Be careful when you speak my name, mortal.", 1.5,
			"Who hurt you?", 0.5,
			"Kinky :3", 1,
			"The one who wages a war with Lady Luck herself. Your efforts are cute, but futile.", 0.3,
			"I can feel you are slowly giving in. You see? Peace is an option.\n**Now kneel before me!**", 0.2,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		mark = [
			"yea, sure", 1,
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"Be careful when you speak my name, mortal.", 1,
			"shut", 1,
			"You are always looking for animals to copy. Not accepting that you are useless either way.", 0.2,
			"🐸", 1,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		rego = [
			"Yes", 1,
			"No.", 1,
			"Maybe?", 1,
			"Kinky :3", 0.4,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"<:RegoSticker:960106779998580757>", 0.6,
			"Be careful when you speak my name, mortal.", 0.5,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		natus = [
			"Yes", 1,
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"Be careful when you speak my name, mortal.", 0.3,
			"You know you could've made more responses for me but naaaah, pfff", 0.5,
			"Kinky :3", 0.8,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		vodka = [
			"Yes", 1,
			"No.", 2,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"Be careful when you speak my name, mortal.", 0.3,
			"Ewww, a black ***cat***... even I might start to drink if I see you around again.", 0.2,
			"Kinky :3", 0.8,
			markov.markovifier(message.guild.id), 0.5,
		]
		# noinspection SpellCheckingInspection
		casual = [
			"Yes", 1,
			"No.", 1,
			"Maybe?", 1,
			"<:Kyrihihihi:1058348961523576872>", 1,
			"Be careful when you speak my name, mortal.", 0.3,
			"Casual? At least not that generic, I'll allow you to worship me.", 0.2,
			"Kinky :3", 0.8,
			markov.markovifier(message.guild.id), 0.5,
		]
		match author.id:
			case 509390185226829827:
				pack = casual
			case 302793255911948289:
				pack = natus
			case 550917109496938496:
				pack = vodka
			case 334249775652274177:
				pack = mag
			case 332925665424834560:
				pack = eszter
			case 520697326679883808:
				pack = anna
			case 463641084971712514:
				pack = agi
			case 875753704685436938:
				pack = nika
			case 377469395007438849:
				pack = mark
			case 618475228695232532:
				pack = rego
			case _:
				if is_admin:
					pack = admin_base
				else:
					for role in author.roles:
						if role.id == 992398146942550116:
							pack = cultist_base
							break
					else:
						pack = comonner_base
		responses.append(choice(pack))

	if "say what?" in content:
		responses.append("what?")

	if "no u" in content or "no you" in content and random.randint(1, 5) == 1:
		responses.append("no u")

	if ("god" in content_splits or "goddess" in content_splits) and author.id in [875753704685436938, 332925665424834560]:  # - - - - - Nika or Eszter- - - - -
		response_list = [
			"You mention gods, yet you refuse to worship Lady Luck herself.\nHow insulting...", 1,
			"Gods mentioned by... You of all people?", 2,
			None, 6
		]
		responses.append(choice(response_list))

	if "meme" in content and random.randint(1, 5) == 1 and not is_admin:
		responses.append("The DNA of the soul.")

	# message stealth
	for response in responses:
		if response is not None:
			if content[0] == "(" and content[-1] == ")" and response[0] != ">":
				await send_message(message, text = f"({response})")
			else:
				await send_message(message, text = response)

	# UwUification
	if person.uwuify:
		embed = discord.Embed(
			description = uwu(message.clean_content),
			color = literal_eval(person.color)
		)
		embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)
		await send_message(message, embed = embed, silent = True)
		await message.delete()
		return

	# random emoji spam
	if random.randint(1, 250) == 169:
		emoji = random.choice(s.EMOJIS)
		await message.add_reaction(emoji)

	# mentioning major titles
	if not responses:
		content = message.content
		direct_mentions = []

		for member in message.mentions:
			member: discord.Member
			if str(member.id) in content:
				if not c.Person(discord_id = member.id).chat_ignore:
					direct_mentions.append(member)

		if direct_mentions and random.randint(1, 25) == 1:
			person = random.choice(direct_mentions)

			titles: list[c.Title] = t.get_titles(person, "major")

			if titles:
				text = "Did you mean..."
				for title in titles:
					ending = t.choice([
						"?", 3,
						"!", 1,
						"?!", 1,
					])
					if ending == "?!":
						text = f"{text}\nThe {title.name.upper()}{ending}"
					else:
						text = f"{text}\nThe {title.name}{ending}"

				await t.send_message(message, text = text, reply = True)


pass
