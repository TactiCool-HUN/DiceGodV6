from utils.bot_setup import prefix
import sheet_handler as sh
from utils import settings as s, tools as t
import classes as c
import discord.ext
import roller as r
import asyncio
import random
from icecream import ic
import re


async def roll_command(identifier: discord.Interaction | discord.ext.commands.Context, text: str, crit: bool = False):
	if isinstance(identifier, discord.Interaction):
		identifier: discord.Interaction
		try:
			await identifier.response.defer()
		except discord.errors.InteractionResponded:
			pass
	if text[:4] == "hurt":
		followups = [c.FollowupButton("✅", [text[4:], False, False], "heal_hurt"), c.FollowupButton("❎", None, "disable")]
		await t.send_message(identifier, text = f"Did you want to use ``{prefix}{text}``?", reply = True, followups = followups)
	elif text[:4] == "heal":
		followups = [c.FollowupButton("✅", [text[4:], True, False], "heal_hurt"), c.FollowupButton("❎", None, "disable")]
		await t.send_message(identifier, text = f"Did you want to use ``{prefix}{text}``?", reply = True, followups = followups)
	elif text[:4] == "rest":
		followups = [c.FollowupButton("✅", None, "rest"), c.FollowupButton("❎", None, "disable")]
		await t.send_message(identifier, f"Did you want to use ``{prefix}rest long``?", reply = True, followups = followups)
	elif text[:4] == "coin":
		followups = [c.FollowupButton("✅", None, "coin"), c.FollowupButton("❎", None, "disable")]
		await t.send_message(identifier, text = f"Did you want to use ``{prefix}coin``?", reply = True, followups = followups)
	else:
		loader = None
		try:
			if isinstance(identifier, discord.ext.commands.Context):
				loader = await t.load(identifier, f"-roll {text}")
				identifier: discord.ext.commands.Context
			else:
				identifier: discord.Interaction
			temp = re.split("x", text)
			if temp and temp[0].isnumeric():
				text = temp[1]
				temp = int(temp[0])
				if temp == 0:
					raise ValueError("I can't roll something zero times you dumdum")
				elif temp > 21:
					raise ValueError("That's like... a lot of rolls, I can't do that.")
				packs = []
				for i in range(temp):
					pack_maker = await asyncio.to_thread(r.text_to_pack, identifier, text, crit)
					temp2 = await pack_maker
					packs.append(temp2)
				await loader.delete()
				await t.send_multipack(packs, text)
			else:
				pack_maker = await asyncio.to_thread(r.text_to_pack, identifier, text, crit)
				pack = await pack_maker
				if loader:
					await loader.delete()
				await t.send_pack(pack)
		except Exception as e:
			try:
				if loader:
					await loader.delete()
			except AttributeError:
				pass
			await t.send_message(identifier, text = str(e))
			raise e


async def pc_command(identifier: discord.Interaction | discord.ext.commands.Context, command: str, char_name: str, sheet_name: str, image_url: str, person_inc: discord.Member, color: str):
	person = c.Person(identifier)
	if isinstance(identifier, discord.Interaction):
		identifier: discord.Interaction
		await identifier.response.defer()

	txt = "An error has occurred!\nNo command match found. Possible commands: ``create``, ``update``, ``set``, ``access``, ``clear``, ``delete``"
	silent = False
	followups = []

	match command:
		case "create":
			txt = "An error has occurred!"
			error = False
			if char_name is None:
				txt += "\nYou need to give a character name!"
				error = True
			elif t.exists(char_name, "char"):
				txt += f"\nThe character name {char_name} is in use.\nIf this is your character you can use ``-pc update {char_name} {sheet_name}`` to update to a new version of the sheet."
				error = True
			elif char_name[0].isnumeric():
				txt += f"\nThe character name cannot start with a number.\nMan, this is literally the only restriction, you character name can literally be a ``space`` and it'll work, please..."
				error = True

			if sheet_name is None:
				txt += "\nYou need to give a character sheet!"
				error = True
			elif not sh.ping_sheet(sheet_name):
				txt += "\nSheet name might be mistyped or the sheet is not connected to bot (notify Tacti)."
				error = True
			elif t.exists(sheet_name, "sheet_name"):
				txt += "\nThis sheet is already connected to a character."
				error = True

			if not error:
				sheet = c.Sheet(identifier, char_name, sheet_name, True)
				if color:
					sheet.color = color
					sheet.update()
				txt = f"Character successfully created!\nUse the ``-pc set {char_name}`` or the ``/pc`` command to set your new character!"
		case "update":
			txt = "An error has occurred!"
			error = False

			if char_name is None:
				txt += "\nYou need to give a character name!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True
			elif char_name[0].isnumeric():
				txt += f"\nThe character name cannot start with a number.\nMan, this is literally the only restriction, you character name can literally be a ``space`` and it'll work, please..."
				error = True
			
			sheet = c.Sheet(identifier, char_name)

			if sheet_name is None:
				txt += "\nYou need to give a character sheet!"
				error = True
			elif not sh.ping_sheet(sheet_name):
				txt += "\nSheet name might be mistyped or the sheet is not connected to bot (notify Tacti)."
				error = True
			elif t.exists(sheet_name, "sheet_name"):
				txt += "\nThis sheet is already connected to a character."
				error = True

			if sheet.user != sheet.owner and person.user.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot edit it!"
				error = True

			if not error:
				old_sheet = sheet.sheet
				sheet.sheet = sheet_name
				if color:
					sheet.color = color
				sheet.update()
				txt = f"{sheet.character}'s sheet is changed from ``{old_sheet}`` to ``{sheet.sheet}``."
				if sheet.user != sheet.owner and person.user.id in s.ADMINS:
					await t.send_message(sheet.owner, text = f"Admin privileges were used to edit the sheet of {sheet.character}")
		case "image":
			txt = "An error has occurred!"
			error = False

			if char_name is None or image_url is None:
				txt += "\nYou need to give both a character name and an image url!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True

			sheet = c.Sheet(identifier, char_name)

			if sheet.user != sheet.owner and person.user.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot edit it!"
				error = True
			if not error:
				sheet.set_picture(image_url)
				txt = f"Character image set, try it out with a roll!"
				if sheet.user != sheet.owner and person.user.id in s.ADMINS:
					await t.send_message(sheet.owner, text = f"Admin privileges were used to edit the sheet of {sheet.character}")
		case "color":
			txt = "An error has occurred!"
			error = False

			if char_name is None or color is None:
				txt += "\nYou need to give both a character name and a color hex-code!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True

			sheet = c.Sheet(identifier, char_name)

			if sheet.user != sheet.owner and person.user.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot edit it!"
				error = True
			if not error:
				if color == "clear":
					color = None
				elif color[0] == "#":
					color = f"0x{color[1:]}"
				sheet.color = color
				sheet.update()
				txt = f"Character color set, try it out with a roll!"
				if sheet.user != sheet.owner and person.user.id in s.ADMINS:
					await t.send_message(sheet.owner, text = f"Admin privileges were used to edit the sheet of {sheet.character}")
		case "set":
			txt = "An error has occurred!"
			error = False

			if char_name is None:
				txt += "\nYou need to give a character name!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True

			sheet = c.Sheet(identifier, char_name)

			if sheet.user != sheet.owner and person.user.id not in s.ADMINS and not t.is_rented(sheet, person.user):
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, and is not rented to you, you cannot set it!"
				error = True

			if not error:
				person.active = char_name
				if person.change_name:
					try:
						await person.user.edit(nick = person.set_name())
					except Exception as e:
						print(e)
				if person.auto_tag:
					person.tag = person.active
				person.update()
				txt = f"{char_name} successfully set as active character!"
				if sheet.user != sheet.owner:
					if t.is_rented(sheet, person.user):
						await t.send_message(sheet.owner, text = f"{sheet.user.user.mention} just set the character: {sheet.character}, because it is rented to them.")
					elif person.user.id in s.ADMINS:
						await t.send_message(sheet.owner, text = f"{sheet.user.user.mention} just set the character: {sheet.character}, because admins can just do that.")
				silent = True
				followups = [c.FollowupButton("🗑️", identifier.message, "delete_message", style=discord.ButtonStyle.grey)]
		case "clear":
			if person.change_name:
				try:
					await person.user.edit(nick = person.clear_name())
				except Exception as e:
					print(e)
			if person.auto_tag:
				person.tag = None
			person.active = None
			person.update()
			txt = f"Active character cleared."
			silent = True
			followups = [c.FollowupButton("🗑️", identifier.message, "delete_message", style=discord.ButtonStyle.grey)]
		case "delete":
			txt = "An error has occurred!"
			error = False

			if char_name is None:
				txt += "\nYou need to give a character name!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True
			
			sheet = c.Sheet(identifier, char_name)

			if sheet.user != sheet.owner and person.user.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot delete it!"
		
			if not error:
				if person.active == sheet_name:
					if person.change_name:
						try:
							await t.identifier_to_member(identifier).edit(nick = person.clear_name())
						except Exception as e:
							print(e)
					if person.auto_tag:
						person.tag = None
					person.active = None
					person.update()
				c.Sheet(identifier, char_name).delete()
				txt = random.choice([
					f"``{char_name}`` won't bother us anymore.",
					f"``{char_name}`` has been eliminated.",
					f"``{char_name}`` met their doom.",
					f"``{char_name}`` has been torn to a thousand pieces and fed to abyssal chickens.",
					f"``{person.user.display_name}`` has murdered ``{char_name}`` in cold blood! This cannot go unanswered, may the Dice God bring you bad luck when you most need it!|| ...oh, that's me.||"
				])
				if sheet.user != sheet.owner and person.user.id in s.ADMINS:
					await t.send_message(sheet.owner, text = f"An admin just deleted your character: {char_name}.\nYes they can do that.")
		case "access":
			txt = "An error has occurred!"
			error = False

			if char_name is None:
				txt += "\nYou need to give a character name!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True

			sheet = c.Sheet(identifier, char_name)

			if type(person_inc) != discord.Member:
				txt += "\nPerson was not properly mention!"
				error = True

			if sheet.user != sheet.owner and person.user.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot change it's rent status!"

			if not error:
				if t.is_rented(sheet, person_inc):
					with t.DatabaseConnection("data.db") as connection:
						cursor = connection.cursor()
						cursor.execute("DELETE FROM sheet_rents WHERE character = ? AND user_id = ?", (sheet.character, person_inc.id))
					person_inc = c.Person(discord_id = person_inc.id)
					if person_inc.active == sheet.character:
						try:
							await t.identifier_to_member(identifier).edit(nick = person.clear_name())
						except Exception as e:
							print(e)
						person.active = None
					if person_inc.tag == sheet.character:
						person_inc.tag = None
					person_inc.update()
					await t.send_message(person_inc, text = f"{sheet.character} is no longer rented to you.")
					txt = f"{sheet.character} is no longer rented to {person_inc.user.display_name}."
				else:
					with t.DatabaseConnection("data.db") as connection:
						cursor = connection.cursor()
						cursor.execute("INSERT INTO sheet_rents(owner_id, user_id, character) VALUES (?, ?, ?)", (person.user.id, person_inc.id, sheet.character))
					await t.send_message(person_inc, text = f"{sheet.character} is now rented to you. You can set and clear the character through Dice God but have no other permissions for it.\nSheet Owner: {sheet.owner.user.display_name}\nAccess Granted by: {t.identifier_to_member(identifier).name}")
					txt = f"{sheet.character} is now rented to {person_inc.display_name}."

	await t.send_message(identifier, text = txt, reply = True, followups = followups, silent = silent)


async def condition_command(interaction: discord.Interaction, condition, on_or_off, exhaustion_level):
	reply = await sh.set_condition(interaction, condition, on_or_off, exhaustion_level)
	if reply:
		await t.send_message(interaction, text = reply)


async def hp_command(ctx: discord.ext.commands.Context, amount, is_heal = None, is_companion = False):
	sent = await t.load(ctx)

	if is_heal is None:
		is_heal = re.split(" ", str(ctx.message.clean_content))[0].replace(prefix, "")
		if is_companion:
			# noinspection SpellCheckingInspection
			is_heal = is_heal == "cheal"
		else:
			is_heal = is_heal == "heal" or is_heal == "healing"
	person = c.Person(ctx)
	if person.active is None:
		await sent.delete()
		await t.send_message(ctx.message, text = "No active character found.", reply = True)
		return

	reply, followups = await sh.heal_hurt(ctx, is_heal, amount, is_companion)
	await sent.delete()
	await t.send_message(ctx, text = reply, reply = True, followups = followups)


async def rest_command(identifier: discord.Interaction | discord.ext.commands.Context, length = "long", hit_dice = None, sent = None):
	try:
		length = length.lower()
	except AttributeError:
		pass
	try:
		hit_dice = hit_dice.lower()
	except AttributeError:
		pass
	message = await sh.rest(identifier, length, hit_dice)
	if sent:
		await sent.delete()
	await t.send_message(identifier, text = message, reply = True)


async def spell_command(identifier: discord.Interaction | discord.ext.commands.Context, spell_name, sent = None):
	spell_out, found, _ = await sh.get_spell(identifier, spell_inc = spell_name)
	if sent:
		await sent.delete()

	if found == "exact":
		asyncio.create_task(t.send_message(identifier, embed = spell_out.create_embed(), reply = True, followups = spell_out.followups))
	elif found == "multiple":
		followups = []
		reply = f"The following spells include ``{spell_name}``:\n"
		for count, spell in enumerate(spell_out):
			spell_name = spell.name
			prep = spell.prepared
			if count < 9:
				num = f"[{count + 1}] "
			else:
				num = "[-] "
			if prep:
				reply = f"{reply}\n__**{num}{spell_name}** - On player spell list.__"
			else:
				reply = f"{reply}\n**{num}{spell_name}** - Not on player spell list."
			if count < 9:
				followups.append(c.FollowupButton(s.REACTION_NUMBERS[count], spell, "spell"))
		asyncio.create_task(t.send_message(identifier, text = reply, reply = True, followups = followups))
	else:
		asyncio.create_task(t.send_message(identifier, text = f"No spell matching ``{spell_name}`` found.", reply = True))


async def cast_command(identifier: discord.Interaction | discord.ext.commands.Context, spell_name, sent = None, spell_level = None, from_followup = False):
	if not c.Person(identifier).active:
		asyncio.create_task(t.send_message(identifier, text = "You don't have a character set.", reply = True))
		return
	if not from_followup:
		spell_out, found, _ = await sh.get_spell(identifier, spell_inc = spell_name)
	else:
		spell_out = spell_name
		found = "exact"
	if sent:
		await sent.delete()

	if found == "exact":
		reply = sh.cast_slot(identifier, spell_level)
		if reply[:6] == "Error!":
			await t.send_message(identifier, text = reply)
			return

		await t.send_message(identifier, embed = spell_out.create_embed(), followups = spell_out.followups)
		await roll_command(identifier, spell_out.followups[spell_level - int(spell_out.level[0]) + 1].data, False)

		if isinstance(identifier, discord.Interaction):
			await t.send_message(identifier, text = reply, ephemeral = True)
		else:
			await t.send_message(t.identifier_to_member(identifier), text = reply)
	elif found == "multiple":
		followups = []
		reply = f"The following spells include ``{spell_name}``:\n"
		for count, spell in enumerate(spell_out):
			spell_name = spell.name
			prep = spell.prepared
			if count < 9:
				num = f"[{count + 1}] "
			else:
				num = "[-] "
			if prep:
				reply = f"{reply}\n__**{num}{spell_name}** - On player spell list.__"
			else:
				reply = f"{reply}\n**{num}{spell_name}** - Not on player spell list."
			if count < 9:
				followups.append(c.FollowupButton(s.REACTION_NUMBERS[count], [spell, spell_level], "cast"))
		asyncio.create_task(t.send_message(identifier, text = reply, reply = True, followups = followups))
	else:
		asyncio.create_task(t.send_message(identifier, text = f"No spell matching ``{spell_name}`` found.", reply = True))


async def draw_card(ctx: discord.ext.commands.Context, deck: str):
	deck = deck.replace(" ", "")
	if deck[0].isnumeric():
		multiplier = ""
		counting = True
		deck_name = ""
		for char in deck:
			if counting:
				if char.isnumeric():
					multiplier = f"{multiplier}{char}"
				elif char == "x":
					counting = False
				else:
					raise ValueError("Bad deck name.")
			else:
				deck_name = f"{deck_name}{char}"
		deck = deck_name
		multiplier = int(multiplier)
	else:
		multiplier = 1

	deck = c.Deck(deck)

	cards = []
	for card in deck.cards:
		if card.in_draw:
			cards.append(card)

	empty = False
	cards_drawn = []
	for i in range(multiplier):
		if len(cards) == 0:
			empty = True
			break
		else:
			chosen_card: c.Card = random.choice(cards)

			temp = []
			for card in cards:
				if card.card_id == chosen_card.card_id:
					card.in_draw = 0
					card.update()
				else:
					temp.append(card)
			cards = temp

			cards_drawn.append(chosen_card.name)

	if cards_drawn:
		cards_drawn = '\n'.join(cards_drawn)
		await t.send_message(ctx, f"You draw:\n{cards_drawn}")
	if empty:
		await t.send_message(ctx, f"Deck empty (either no cards or all of them are drawn)!")


async def shuffle_deck(ctx: discord.ext.commands.Context, deck: str):
	deck = c.Deck(deck)

	for card in deck.cards:
		card.in_draw = 1

	deck.update()

	await t.send_message(ctx, "Deck shuffled.")


async def veterancy_command(interaction: discord.Interaction, person: discord.Member = None, change_rank = False):
	if person is None:
		person = c.Person(interaction)
	else:
		person = c.Person(person.id)

	guild = t.bot.get_guild(562373378967732226)
	hall_of_fame = guild.get_channel(911770517533507604)
	time_stopped = guild.get_channel(1171006228265193542)

	veterancy_points = 0

	messages: list[discord.Message] = [message async for message in hall_of_fame.history(limit = 200)]
	for message in messages:
		for mention in message.mentions:
			if mention.id == person.user.id:
				temp = re.findall("Duration \(irl\): [0-9]+ day", str(message.clean_content))
				if len(temp) == 0:
					veterancy_points += 1
					break
				if len(temp) != 1:
					await t.send_message(person, "Hall of Fame read failed.")
					return

				temp = re.findall("[0-9]+", temp[0])
				temp = int(temp[0])
				if temp >= 365:
					veterancy_points += 2
				else:
					veterancy_points += 1
				break

	messages: list[discord.Message] = [message async for message in time_stopped.history(limit = 200)]
	for message in messages:
		for mention in message.mentions:
			if mention.id == person.user.id:
				temp = re.findall("Duration \(irl\): [0-9]+ day", str(message.clean_content))
				if len(temp) == 0:
					veterancy_points += 1
					break
				if len(temp) != 1:
					await t.send_message(person, "Hall of Fame read failed.")
					return

				temp = re.findall("[0-9]+", temp[0])
				temp = int(temp[0])
				if temp >= 365:
					veterancy_points += 2
				else:
					veterancy_points += 1
				break

	# --------------------------------------------------------------------------

	if veterancy_points == 0:
		veterancy_rank = "Commoner"
		next_points = 1
	elif veterancy_points < 5:
		veterancy_rank = "Greenhorn"
		next_points = 5
	elif veterancy_points < 9:
		veterancy_rank = "Adventurer"
		next_points = 9
	elif veterancy_points < 13:
		veterancy_rank = "Hero"
		next_points = 13
	elif veterancy_points < 17:
		veterancy_rank = "Legend"
		next_points = 17
	elif veterancy_points < 21:
		veterancy_rank = "Mythic"
		next_points = 21
	else:
		veterancy_rank = "Planeswalker"
		next_points = "∞"

	await t.send_message(interaction, f"{person.user.display_name} is currently on the rank of {veterancy_rank} with {veterancy_points}/{next_points} towards the next tier.")

	if change_rank:
		roles: dict[str, discord.Role] = {
			"commoner": guild.get_role(1170854299786563735),
			"greenhorn": guild.get_role(562619225928105984),
			"adventurer": guild.get_role(562618251079712796),
			"hero": guild.get_role(695250745276235807),
			"legend": guild.get_role(869611219693236234),
			"mythic": guild.get_role(1170854863068991528),
			"planeswalker": guild.get_role(1170854843611615252)
		}
		veterancy_rank = veterancy_rank.lower()
		member: discord.Member = await guild.get_member(person.user.id)

		for key in roles:
			if key == veterancy_rank:
				await member.add_roles(roles[key])
			else:
				await member.remove_roles(roles[key])


pass
