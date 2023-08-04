from utils.bot_setup import prefix
import sheet_handler as sh
from utils import settings as s, tools as t
import classes as c
import discord.ext
import roller as r
import asyncio
import random
import re


async def roll_command(ctx, text, crit = False):
	if text[:4] == "hurt":
		await t.send_message_old(ctx, f"Did you want to use ``{prefix}{text}``?", reply = True,
								 followups = [c.FollowupButton("✅", [text[4:], False, False], "heal_hurt"), c.FollowupButton("❎", None, "disable")])
	elif text[:4] == "heal":
		await t.send_message_old(ctx, f"Did you want to use ``{prefix}{text}``?", reply = True,
								 followups = [c.FollowupButton("✅", [text[4:], True, False], "heal_hurt"), c.FollowupButton("❎", None, "disable")])
	elif text[:4] == "rest":
		await t.send_message_old(ctx, f"Did you want to use ``{prefix}rest long``?", reply = True, followups = [c.FollowupButton("✅", None, "rest"), c.FollowupButton("❎", None, "disable")])
	elif text[:4] == "coin":
		await t.send_message_old(ctx, f"Did you want to use ``{prefix}coin``?", reply = True, followups = [c.FollowupButton("✅", None, "coin"), c.FollowupButton("❎", None, "disable")])
	else:
		loader = await t.load(ctx, f"-roll {text}")
		try:
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
					pack_maker = await asyncio.to_thread(r.text_to_pack, ctx, text, crit)
					temp2 = await pack_maker
					packs.append(temp2)
				await loader.delete()
				await t.send_multipack(packs, text)
			else:
				pack_maker = await asyncio.to_thread(r.text_to_pack, ctx, text, crit)
				pack = await pack_maker
				await loader.delete()
				await t.send_pack(pack)
		except Exception as e:
			try:
				await loader.delete()
			except discord.ext.commands.errors.MessageNotFound:
				pass
			await ctx.reply(e)
			raise e


async def pc_command(ctx, command: str, char_name: str, sheet_name: str, image_url: str, person_inc: discord.Member, interaction: discord.Interaction = None):
	person = c.Person(ctx)
	await ctx.defer(ephemeral = False)

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
				c.Sheet(ctx, char_name, sheet_name, True)
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
			
			sheet = c.Sheet(ctx, char_name)

			if sheet_name is None:
				txt += "\nYou need to give a character sheet!"
				error = True
			elif not sh.ping_sheet(sheet_name):
				txt += "\nSheet name might be mistyped or the sheet is not connected to bot (notify Tacti)."
				error = True
			elif t.exists(sheet_name, "sheet_name"):
				txt += "\nThis sheet is already connected to a character."
				error = True

			if sheet.user != sheet.owner and ctx.author.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot edit it!"

			if not error:
				old_sheet = sheet.sheet
				sheet.sheet = sheet_name
				sheet.update()
				txt = f"{sheet.character}'s sheet is changed from ``{old_sheet}`` to ``{sheet.sheet}``."
				if sheet.user != sheet.owner and ctx.author.id in s.ADMINS:
					await t.send_dm(ctx, f"Admin privileges were used to edit the sheet of {sheet.character}", False, discord_id = sheet.owner.user.id)
		case "image":
			txt = "An error has occurred!"
			error = False

			if char_name is None or image_url is None:
				txt += "\nYou need to give both a character name and an image url!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True

			sheet = c.Sheet(ctx, char_name)

			if sheet.user != sheet.owner and ctx.author.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot edit it!"
			if not error:
				sheet.set_picture(image_url)
				txt = f"Character image set, try it out with a roll!"
				if sheet.user != sheet.owner and ctx.author.id in s.ADMINS:
					await t.send_dm(ctx, f"Admin privileges were used to edit the sheet of {sheet.character}", False, discord_id = sheet.owner.user.id)
		case "set":
			txt = "An error has occurred!"
			error = False

			if char_name is None:
				txt += "\nYou need to give a character name!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True

			sheet = c.Sheet(ctx, char_name)

			if sheet.user != sheet.owner and ctx.author.id not in s.ADMINS and not t.is_rented(sheet, person.user):
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, and is not rented to you, you cannot set it!"

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
						await t.send_dm(ctx, f"{sheet.user.user.mention} just set the character: {sheet.character}, because it is rented to them.", False, discord_id = sheet.owner.user.id)
					elif ctx.author.id in s.ADMINS:
						await t.send_dm(ctx, f"{sheet.user.user.mention} just set the character: {sheet.character}, because admins can just do that.", False, discord_id = sheet.owner.user.id)
				silent = True
				followups = [c.FollowupButton("🗑️", ctx.message, "delete_message", style=discord.ButtonStyle.grey)]
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
			followups = [c.FollowupButton("🗑️", ctx.message, "delete_message", style=discord.ButtonStyle.grey)]
		case "delete":
			txt = "An error has occurred!"
			error = False

			if char_name is None:
				txt += "\nYou need to give a character name!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True
			
			sheet = c.Sheet(ctx, char_name)

			if sheet.user != sheet.owner and ctx.author.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot delete it!"
		
			if not error:
				if person.active == sheet_name:
					if person.change_name:
						try:
							await ctx.author.edit(nick = person.clear_name())
						except Exception as e:
							print(e)
					if person.auto_tag:
						person.tag = None
					person.active = None
					person.update()
				c.Sheet(ctx, char_name).delete()
				txt = random.choice([
					f"``{char_name}`` won't bother us anymore.",
					f"``{char_name}`` has been eliminated.",
					f"``{char_name}`` met their doom.",
					f"``{char_name}`` has been torn to a thousand pieces and fed to abyssal chickens.",
					f"``{person.user.display_name}`` has murdered ``{char_name}`` in cold blood! This cannot go unanswered, may the Dice God bring you bad luck when you most need it!|| ...oh, that's me.||"
				])
				if sheet.user != sheet.owner and ctx.author.id in s.ADMINS:
					await t.send_dm(ctx, f"An admin just deleted your character: {char_name}.\nYes they can do that.", False, discord_id = sheet.owner.user.id)
		case "access":
			txt = "An error has occurred!"
			error = False

			if char_name is None:
				txt += "\nYou need to give a character name!"
				error = True
			elif not t.exists(char_name, "char"):
				txt += f"\nThere is no sheet under the character name {char_name}. Use ``-pc create`` to make a new PC."
				error = True

			sheet = c.Sheet(ctx, char_name)

			if type(person_inc) != discord.Member:
				txt += "\nPerson was not properly mention!"
				error = True

			if sheet.user != sheet.owner and ctx.author.id not in s.ADMINS:
				txt += f"\nThe character is {sheet.owner.user.mention}'s property, you cannot change it's rent status!"

			if not error:
				if t.is_rented(sheet, person_inc):
					with t.DatabaseConnection("data.db") as connection:
						cursor = connection.cursor()
						cursor.execute("DELETE FROM sheet_rents WHERE character = ? AND user_id = ?", (sheet.character, person_inc.id))
					person_inc = c.Person(discord_id = person_inc.id)
					if person_inc.active == sheet.character:
						try:
							await ctx.author.edit(nick = person.clear_name())
						except Exception as e:
							print(e)
						person.active = None
					if person_inc.tag == sheet.character:
						person_inc.tag = None
					person_inc.update()
					await t.send_dm(ctx, f"{sheet.character} is no longer rented to you.", False, discord_id = person_inc.user.id)
					txt = f"{sheet.character} is no longer rented to {person_inc.user.display_name}."
				else:
					with t.DatabaseConnection("data.db") as connection:
						cursor = connection.cursor()
						cursor.execute("INSERT INTO sheet_rents(owner_id, user_id, character) VALUES (?, ?, ?)", (person.user.id, person_inc.id, sheet.character))
					await t.send_dm(ctx, f"{sheet.character} is now rented to you. You can set and clear the character through Dice God but have no other permissions for it.\nSheet Owner: {sheet.owner.user.display_name}\nAccess Granted by: {ctx.author.name}", False, discord_id = person_inc.id)
					txt = f"{sheet.character} is now rented to {person_inc.name}."

	if interaction:
		await interaction.followup.send(txt, ephemeral = True)
	else:
		await t.send_message_old(ctx, txt, reply = True, followups = followups, silent = silent)


async def condition_command(interaction, ctx, condition, on_or_off, exhaustion_level):
	reply = await sh.set_condition(ctx, condition, on_or_off, exhaustion_level)
	if reply:
		await interaction.followup.send(reply)


async def hp_command(ctx, amount, is_heal = None, is_companion = False):
	sent = await t.load(ctx)

	if is_heal is None:
		is_heal = re.split(" ", ctx.message.clean_content)[0].replace(prefix, "")
		if is_companion:
			# noinspection SpellCheckingInspection
			is_heal = is_heal == "cheal"
		else:
			is_heal = is_heal == "heal" or is_heal == "healing"
	person = c.Person(ctx)
	if person.active is None:
		await sent.delete()
		await t.send_message_old(ctx, "No active character found.", reply = True)
		return

	reply, followups = await sh.heal_hurt(ctx, is_heal, amount, is_companion)
	await sent.delete()
	await t.send_message_old(ctx, reply, reply = True, followups = followups)


async def rest_command(ctx, length = "long", hit_dice = None, sent = None):
	try:
		length = length.lower()
	except AttributeError:
		pass
	try:
		hit_dice = hit_dice.lower()
	except AttributeError:
		pass
	message = await sh.rest(ctx, length, hit_dice)
	if sent:
		await sent.delete()
	await t.send_message_old(ctx, message, reply = True)


async def spell_command(ctx, spell_name, sent = None, interaction = None):
	spell_out, found, _ = await sh.get_spell(ctx, spell_inc = spell_name)
	if sent:
		await sent.delete()

	if found == "exact":
		if interaction:
			if spell_out.followups:
				view = t.FollowupView(ctx)
				for i in spell_out.followups:
					view.add_item(i)
			else:
				view = None
			await interaction.followup.send(embed = spell_out.create_embed(), reply = True, view = view)
		else:
			asyncio.create_task(t.send_message_old(ctx, spell_out.create_embed(), reply = True, embed = True, followups = spell_out.followups))
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
		if interaction:
			if followups:
				view = t.FollowupView(ctx)
				for i in followups:
					view.add_item(i)
			else:
				view = None
			await interaction.followup.send(reply, reply = True, view = view)
		else:
			asyncio.create_task(t.send_message_old(ctx, reply, reply = True, followups = followups))
	else:
		if interaction:
			await interaction.followup.send(f"No spell matching ``{spell_name}`` found.", reply = True)
		else:
			asyncio.create_task(t.send_message_old(ctx, f"No spell matching ``{spell_name}`` found.", reply = True))


async def cast_command(ctx, spell_name, sent = None, interaction = None, spell_level = None, from_followup = False):
	if not c.Person(ctx).active:
		asyncio.create_task(t.send_message_old(ctx, "You don't have a character set.", reply = True))
		return
	if not from_followup:
		spell_out, found, _ = await sh.get_spell(ctx, spell_inc = spell_name)
	else:
		spell_out = spell_name
		found = "exact"
	if sent:
		await sent.delete()

	if found == "exact":
		if interaction:
			reply = sh.cast_slot(ctx, spell_level)
			if reply[:6] == "Error!":
				await interaction.followup.send(reply)
				return
			else:
				await t.send_dm(ctx, reply, silent = True)

			if spell_out.followups:
				view = t.FollowupView(ctx)
				for i in spell_out.followups:
					view.add_item(i)
			else:
				view = None
			await interaction.followup.send(embed = spell_out.create_embed(), view = view)
			await roll_command(ctx, spell_out.followups[spell_level - int(spell_out.level[0]) + 1].data, False)
		else:
			reply = sh.cast_slot(ctx, spell_level)
			if reply[:6] == "Error!":
				await t.send_message_old(ctx, reply, reply = True, silent = True)
				return
			else:
				await t.send_dm(ctx, reply, silent = True)
			asyncio.create_task(t.send_message_old(ctx, spell_out.create_embed(), reply = True, embed = True, followups = spell_out.followups, silent = True))
			await roll_command(ctx, spell_out.followups[spell_level - int(spell_out.level[0]) + 1].data, False)
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
		if interaction:
			if followups:
				view = t.FollowupView(ctx)
				for i in followups:
					view.add_item(i)
			else:
				view = None
			await interaction.followup.send(reply, view = view)
		else:
			asyncio.create_task(t.send_message_old(ctx, reply, reply = True, followups = followups, silent = True))
	else:
		if interaction:
			await interaction.followup.send(f"No spell matching ``{spell_name}`` found.", reply = True)
		else:
			asyncio.create_task(t.send_message_old(ctx, f"No spell matching ``{spell_name}`` found.", reply = True, silent = True))


pass
