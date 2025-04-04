from utils.bot_setup import bot
from utils import settings as s, tools as t
from views.followup_view import FollowupButton
import textwrap
import datetime
import discord.ext
import re


class Person:
	def __init__(self, identifier: discord.Interaction | discord.ext.commands.Context = None, discord_id = None):
		if not identifier and not discord_id:
			raise ValueError("Improper Person initiation.")

		if identifier is None:
			self.user: discord.User = bot.get_user(discord_id)
		else:
			self.user: discord.Member = t.identifier_to_member(identifier)

		self.active = None
		self.tag = None
		self.color = "0"
		self.change_name = 1
		self.auto_tag = 1
		self.markov_chance = 0
		self.chat_ignore = 0
		self.uwuify = 0
		self.tts_perms = ""

		if t.exists(self.user.id, "person"):
			self.load()
		else:
			self.create()

	def create(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"INSERT INTO people(discord_id, name, active, tag, color, change_name, auto_tag, markov_chance, chat_ignore, uwuify, tts_perms)"
				"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
				(self.user.id, self.user.display_name, self.active, self.tag, self.color, self.change_name, self.auto_tag, self.markov_chance, self.chat_ignore, self.uwuify, self.tts_perms)
			)

		self.load()

	def load(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM people WHERE discord_id = ?", (self.user.id,))
			raw = cursor.fetchall()[0]

		self.active = raw[2]
		self.tag = raw[3]
		self.color = raw[4]
		self.change_name = bool(raw[5])
		self.auto_tag = bool(raw[6])
		self.markov_chance = int(raw[7])
		self.chat_ignore = bool(raw[8])
		self.uwuify = bool(raw[9])
		self.tts_perms = raw[10]

	def update(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"UPDATE people SET name = ?, active = ?, tag = ?, color = ?, change_name = ?, auto_tag = ?, markov_chance = ?, chat_ignore = ?, uwuify = ?, tts_perms = ?"
				"WHERE discord_id = ?",
				(self.user.display_name, self.active, self.tag, self.color, self.change_name, self.auto_tag, self.markov_chance, self.chat_ignore, self.uwuify, self.tts_perms, self.user.id)
			)

	def add_roll(self, outcome, size, used, roll_text):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"INSERT INTO statistics(owner_id, outcome, size, used, roll_text, tag, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
				(self.user.id, outcome, size, int(used), roll_text, self.tag, datetime.datetime.now())
			)

	def get_rolls(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM statistics WHERE owner_id = ?", (self.user.id,))
			raw = cursor.fetchall()
		return raw

	def set_name(self):
		if "[" in self.user.display_name and "]" in self.user.display_name:
			temp = self.clear_name()
		else:
			temp = self.user.display_name
		return f"{temp} [{self.active}]"

	def clear_name(self):
		if re.findall(" \[.*]", self.user.display_name):
			return self.user.display_name.replace(re.findall(" \[.*]", self.user.display_name)[0], "")


class Sheet:
	def __init__(self, identifier: discord.Interaction | discord.ext.commands.Context, character: str = None, sheet: str = None, new: bool = False):
		self.user = Person(identifier)
		# noinspection PyTypeChecker
		self.owner: Person = None
		self.character = character
		self.sheet = sheet
		self.google_sheet = None
		self.char_image = None
		self.color = None
		self.last_warning = datetime.datetime.now() - datetime.timedelta(days = 2)

		if new:
			self.create(identifier)
		else:
			if not self.character:
				self.character = self.user.active
			self.load(identifier)

	def create(self, identifier: discord.Interaction | discord.ext.commands.Context) -> None:
		member = t.identifier_to_member(identifier)
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"INSERT INTO sheets(owner_id, character, sheet, last_warning)"
				"VALUES (?, ?, ?, ?)",
				(member.id, self.character, self.sheet, self.last_warning)
			)

		self.load(identifier)

	def load(self, identifier: discord.Interaction | discord.ext.commands.Context) -> None:
		member = t.identifier_to_member(identifier)
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM sheets WHERE character = ?", (self.character,))
			raw = cursor.fetchall()

		if not raw:
			raise IndexError("No character sheet found.")
		else:
			raw = raw[0]

		if raw[1] == member.id:  # check if owner
			self.owner = Person(discord_id = raw[1])
			self.user = self.owner
			self.sheet = raw[3]
			self.char_image = raw[4]
			self.color = raw[5]
			self.last_warning = datetime.datetime.strptime(raw[6], "%Y-%m-%d %H:%M:%S.%f")
		elif t.is_rented(self, member):  # check if rented
			self.owner = Person(discord_id = raw[1])
			self.sheet = raw[3]
			self.char_image = raw[4]
			self.color = raw[5]
			self.last_warning = datetime.datetime.strptime(raw[6], "%Y-%m-%d %H:%M:%S.%f")
		elif member.id in s.ADMINS:
			self.owner = Person(discord_id = raw[1])
			self.sheet = raw[3]
			self.char_image = raw[4]
			self.color = raw[5]
			self.last_warning = datetime.datetime.strptime(raw[6], "%Y-%m-%d %H:%M:%S.%f")

	def update(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				'UPDATE sheets SET sheet = ?, color = ?, last_warning = ? WHERE character = ?',
				(self.sheet, self.color, self.last_warning, self.character)
			)

	def delete(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("DELETE FROM sheets WHERE character = ?", (self.character,))

	def set_picture(self, url):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				'UPDATE sheets SET char_image = ?, last_warning = ? WHERE character = ?',
				(url, self.last_warning, self.character)
			)
		self.char_image = url

	def get_sheet(self, sa):
		self.google_sheet = sa.open(self.sheet)
		return self.google_sheet

	def get_version(self):
		if self.sheet == "MainV5":
			return s.VERSION_CONTROL
		else:
			return re.findall("V[0-9].[0-9][0-9].[0-9][0-9]", self.sheet)[0][1:].replace(".", "")


class Die:
	def __init__(self, name, owner_id = None, roll = None, new = False):
		self.die_id = None
		self.name = name
		self.owner_id = None
		self.roll = roll

		if new:
			self.create(owner_id)
		else:
			self.load()

	def create(self, owner_id):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("INSERT INTO dice(name, owner_id, roll) VALUES (?, ?, ?)", (self.name, owner_id, self.roll.replace(" ", "")))
		self.load()

	def load(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM dice WHERE name = ?", (self.name,))
			raw = cursor.fetchall()[0]
		self.die_id = raw[0]
		self.owner_id = raw[2]
		self.roll = raw[3]

	def update(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"UPDATE dice SET name = ?, owner_id = ?, roll = ? WHERE die_id = ?",
				(self.name, self.owner_id, self.roll, self.die_id)
			)

	def delete(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("DELETE FROM dice WHERE die_id = ?", (self.die_id,))


class Pack:
	def __init__(self, identifier: discord.Interaction | discord.ext.commands.Context, single_rolls, roll_raw):
		self.identifier = identifier
		self.single_rolls: list[SingleRoll] = []
		self.single_rolls += single_rolls
		self.followups = [FollowupButton("\U0001F504", roll_raw, "reroll")]
		for roll in single_rolls:
			self.followups += roll.followups

	def add_single_roll(self, single_rolls):
		self.single_rolls += single_rolls
		for roll in single_rolls:
			self.followups += roll.followups

	"""async def send_pack(self, is_reply = True, secret = False):
		person = Person(self.ctx)
		result = 0
		complex_roll = ""
		has_dynamic = False
		has_death = False
		all_damage_types = ""
		roll_display_pack = []
		all_roll_notes = []

		for roll in self.single_rolls:
			if roll.pre_send:
				for text in roll.pre_send:
					if "lol" in roll.pre_send and person.user.id == 875753704685436938:
						tts = True
					else:
						tts = False
					asyncio.create_task(t.send_message(self.ctx, text, reply = True, silent = False, tts = tts))

			all_roll_notes += roll.roll_note

			for damage in roll.damage_type:
				temp = s.DAMAGE_TYPES.get(damage)
				if temp not in all_damage_types:
					all_damage_types += temp

			match roll.speciality:
				case "init":
					asyncio.create_task(t.com.sh.init_resources(self.ctx))
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
						continue
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
			title = f"**Roll Result:** {t.num2word(result)} {all_damage_types}",
			description = complex_roll,
			color = literal_eval(person.color)
		)

		embed.timestamp = datetime.datetime.now()

		if has_dynamic:
			embed.set_author(name = person.active, icon_url = person.user.avatar.url)
		else:
			embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)

		for element in roll_display_pack:
			embed.add_field(name = element[0], value = element[1])

		if all_roll_notes:
			first = True
			footer = ""
			for roll_note in all_roll_notes:
				if first:
					footer = roll_note
					first = False
				else:
					footer = footer + " | " + roll_note

			embed.set_footer(text = footer)

		if has_death:
			await t.com.sh.set_deathsave(self.ctx, has_death, result)
		asyncio.create_task(t.send_message(self.ctx, embed, is_reply, True, self.followups, False, secret, True))"""


class SingleRoll:
	def __init__(self, raw_text, inc_type, name = None, dice_number = 0, die_size = 0, add = 0, dynamic = False, pre_send = None, damage_type = None, roll_note = None, followups: list[FollowupButton] = None, extra_crit_dice: int = 0, exploding: bool = False):
		self.raw_text = raw_text
		self.sign = raw_text[0]
		self.name = name
		self.dice_number = dice_number
		self.die_size = die_size
		self.add = add
		self.args = RollArgs()
		if followups:
			self.followups = followups
		else:
			self.followups = []
		self.dynamic = dynamic
		if pre_send:
			self.pre_send = pre_send
		else:
			self.pre_send = []
		if roll_note:
			self.roll_note = roll_note
		else:
			self.roll_note = []
		self.results = []
		self.die_result = 0
		self.full_result = 0
		if damage_type:
			self.damage_type = [damage_type]
		else:
			self.damage_type = []
		self.speciality = None
		self.extra_crit_dice: int = extra_crit_dice

		raw_text = raw_text[1:]
		match inc_type:
			case "vanilla roll":
				temp = re.findall("[0-9]+d[0-9]+", raw_text)
				self.dice_number = int(re.split("d", temp[0])[0])
				self.die_size = int(re.split("d", temp[0])[1])

				temp = re.split("[0-9]+d[0-9]+", raw_text)[1]
				try:
					damage_types = re.findall("\[[a-z]+]", raw_text)
					for dmg in damage_types:
						self.damage_type.append(dmg[1:-1])
				except IndexError:
					pass
				self.args = RollArgs(temp)
			case "vanilla add":
				add = re.findall("[0-9]+", raw_text)[0]
				try:
					damage_types = re.findall("\[[a-z]+]", raw_text)
					for dmg in damage_types:
						self.damage_type.append(dmg[1:-1])
				except IndexError:
					pass
				self.add = int(add)
				temp = raw_text[len(add):]
				self.args = RollArgs(temp)
			case "dynamic roll":
				pass  # yes this is pass sssh!
			case "dynamic add":
				pass  # yes this is pass sssh!

	def add_vanilla_add(self, raw_text):
		add = re.findall("[+-][0-9]+", raw_text)[0]
		self.add = self.add + int(add)
		temp = raw_text[len(add):]
		self.args.merge_args(temp)

		try:
			damage_type = re.findall("\[[a-z]+]", raw_text)[0]
			self.damage_type.append(damage_type[1:-1])
		except IndexError:
			pass

	def create_display(self):
		raise NotImplemented

	def create_name(self, short = False):
		args = self.args.create_args_display()
		if short:
			die = f"d{self.die_size}"

			add = ""

			damage_emoji = ""
		else:
			die = f"{self.dice_number}d{self.die_size}"

			if self.add > 0:
				add = f"+{self.add}"
			elif self.add < 0:
				add = str(self.add)
			else:
				add = ""

			damage_emoji = ""
			if self.damage_type:
				for damage in self.damage_type:
					damage_emoji = f"{damage_emoji}{s.DAMAGE_TYPES.get(damage)}"
				damage_emoji = f" {damage_emoji}"

		if self.dynamic:
			return f"{self.name} ({die}{args}{add}{damage_emoji})"
		else:
			return f"{die}{args}{add}{damage_emoji}"

	def add_results(self, results):
		for result in results:
			if result[1]:
				self.die_result += result[0]
		self.full_result = self.die_result + self.add


class RollArgs:
	def __init__(self, text = None):
		self.adv = None
		self.keep_type = None
		self.keep_quantity = None
		self.minmax_type = None
		self.minmax_size = None
		self.crit = False
		self.spell_level = None
		self.exploding = False
		self.elven = False
		if text:
			self.override_args(text.lower())

	def override_args(self, text):
		if re.findall("dis", text):
			self.adv = "dis"
		elif re.findall("adv", text):
			self.adv = "adv"
		elif re.findall("emp", text):
			self.adv = "emp"
		if re.findall("crit", text):
			self.crit = True
		temp = re.findall("kh|kl", text)
		if temp:
			self.keep_type = temp[0]
			self.keep_quantity = int(re.findall("kh[0-9]+|kl[0-9]+", text)[0][2:])
		temp = re.findall("max|min", text)
		if temp:
			self.minmax_type = temp[0]
			self.minmax_size = int(re.findall("max[0-9]+|min[0-9]+", text)[0][3:])
		temp = re.findall("lvl|level", text)
		if temp:
			temp = re.findall("lvl[1-9]|level[1-9]", text)[0]
			self.spell_level = int(re.findall("[1-9]", temp)[0])
		if re.findall("ex", text):
			self.exploding = True

	def merge_args(self, text):
		if not text:
			return
		if re.findall("dis", text):
			if self.adv == "adv":
				self.adv = None
			else:
				self.adv = "dis"
		elif re.findall("adv", text):
			if self.adv == "dis":
				self.adv = None
			else:
				self.adv = "adv"
		elif re.findall("emp", text):
			self.adv = "emp"
		if re.findall("crit", text):
			self.crit = True
		if re.findall("ex", text):
			self.exploding = True
		temp = re.findall("kh|kl", text)
		if temp:
			self.keep_type = temp[0]
			self.keep_quantity = int(re.findall("kh[0-9]+|kl[0-9]+", text)[0][2:])
		temp = re.findall("max|min", text)
		if temp:
			self.minmax_type = temp[0]
			self.minmax_size = int(re.findall("max[0-9]+|min[0-9]+", text)[0][3:])
		temp = re.findall("lvl|level", text)
		if temp:
			temp = re.findall("lvl[1-9]|level[1-9]", text)[0]
			self.spell_level = int(re.findall("[1-9]", temp)[0])

	def create_args_display(self):
		if self.exploding:
			e_disp = "ex"
		else:
			e_disp = ""
		if self.crit:
			c_disp = "crit"
		else:
			c_disp = ""
		if self.keep_type:
			k_disp = f"k{self.keep_type}{self.keep_quantity}"
		else:
			k_disp = ""
		if self.minmax_type:
			m_disp = f"{self.minmax_type}{self.minmax_size}"
		else:
			m_disp = ""
		if self.adv:
			a_disp = self.adv
		else:
			a_disp = ""

		args = f"{e_disp}{a_disp}{k_disp}{m_disp}{c_disp}"
		if args:
			args = f" {args}"

		return args


class Spell:
	def __init__(self, dump: list[str], prepared, pc_level = 0):
		self.name = dump[0]
		self.classes = dump[1].split(", ")
		self.prepared = prepared
		self.school = dump[2]
		self.level = dump[3]
		if self.level == "0th level":
			self.is_cantrip = True
		else:
			self.is_cantrip = False
		self.cast_time = dump[4]
		self.reaction_description = dump[5]
		if dump[6] == "1":
			self.is_ritual = True
		else:
			self.is_ritual = False
		self.cast_range = dump[7]
		self.duration = dump[8]
		if dump[9] == "1":
			self.is_concentration = True
		else:
			self.is_concentration = False
		self.components = Components()
		if "V" in dump[10]:
			self.components.verbal = True
		if "S" in dump[10]:
			self.components.somatic = True
		if "M" in dump[10]:
			self.components.material = True
			self.components.material_description = dump[11]
			if dump[12] == "1":
				self.components.is_material_significant = True
		self.description = dump[13]
		if dump[14] == "TRUE":
			if dump[15] == "TRUE":
				self.spell_attack = "melee"
			elif dump[16] == "TRUE":
				self.spell_attack = "ranged"
			else:
				self.spell_attack = True
		else:
			self.spell_attack = False
		self.saves = []
		for i, ability in enumerate(s.ABILITIES):
			if dump[17 + i] == "TRUE":
				self.saves.append(ability)
		self.damage_types = []
		for i, damage_type in enumerate(s.DAMAGE_TYPES):
			if dump[23 + i] == "TRUE":
				self.damage_types.append(damage_type)

		dmg_area_1 = dump[37:46]
		dmg_area_2 = dump[46:]

		self.followups = []
		for i, dmg in enumerate(dmg_area_1):
			if dmg:
				if self.is_cantrip:
					if pc_level > 16 and i == 3:
						emoji = "✨"
					elif pc_level > 10 and i == 2:
						emoji = "✨"
					elif pc_level > 4 and i == 1:
						emoji = "✨"
					elif pc_level < 5 and i == 0:
						emoji = "✨"
					else:
						emoji = s.REACTION_NUMBERS[i]
				else:
					emoji = s.REACTION_NUMBERS[i]
				self.followups.append(FollowupButton(emoji, f"{dmg}{self.get_damage_disp()}", "roll"))
		for i, dmg in enumerate(dmg_area_2):
			if dmg:
				if self.is_cantrip:
					if pc_level > 16 and i == 3:
						emoji = "✨"
					elif pc_level > 10 and i == 2:
						emoji = "✨"
					elif pc_level > 4 and i == 1:
						emoji = "✨"
					elif pc_level < 5 and i == 0:
						emoji = "✨"
					else:
						emoji = s.ALT_REACTION_NUMBERS[i]
				else:
					emoji = s.ALT_REACTION_NUMBERS[i]
				self.followups.append(FollowupButton(emoji, f"{dmg}{self.get_damage_disp()}", "roll"))
		if self.followups:
			self.followups = [FollowupButton("💥", None, "crit", label="off", style=discord.ButtonStyle.grey)] + self.followups

	def get_damage_disp(self):
		disp = ""
		for dmg_type in self.damage_types:
			disp = f"{disp}[{dmg_type}]"
		return disp

	def create_embed(self):
		if self.is_cantrip:
			lvl_school_disp = f"{self.school} Cantrip"
		else:
			lvl_school_disp = f"{self.level} {self.school}"

		if self.prepared:
			prepared_disp = "On player spell list."
		else:
			prepared_disp = "Not on player spell list."

		class_disp = ", ".join(self.classes)

		if self.reaction_description:
			reaction_disp = f" {self.reaction_description}"
		else:
			reaction_disp = ""

		if self.is_ritual:
			ritual_disp = " (ritual)"
		else:
			ritual_disp = ""

		if self.is_concentration:
			concentration_disp = " (concentration)"
		else:
			concentration_disp = ""

		roll_disp = None
		first_first = False
		second_first = False

		if len(self.followups) > 1:
			for followup in self.followups[1:]:
				if followup.emoji in s.REACTION_NUMBERS and not first_first:
					roll_disp = followup.data
					first_first = True
				elif followup.emoji in s.ALT_REACTION_NUMBERS and not second_first:
					roll_disp = f"{roll_disp} | {followup.data}"
					second_first = True
				if first_first and second_first:
					break

		embed = discord.Embed(
			title = self.name,
			description = f"{lvl_school_disp}\n*{prepared_disp}*\nClasses: {class_disp}",
			color = s.SPELL_SCHOOL_COLORS[self.school]
		)

		embed.set_thumbnail(url = s.SPELL_SCHOOL_ICONS[self.school])
		embed.add_field(
			name = "Properties",
			value = f"Cast time: {self.cast_time}{reaction_disp}{ritual_disp}\nRange: {self.cast_range}\nDuration: {self.duration}{concentration_disp}\nComponents: {self.components.create_disp()}",
			inline = False)
		per_page = 1000
		if len(self.description) > per_page:
			chunks = textwrap.wrap(self.description, per_page, break_long_words = False, replace_whitespace = False)
			self.followups.insert(0, FollowupButton("▶", chunks, "scroll"))
			self.followups.insert(0, FollowupButton("◀", chunks, "scroll"))
			embed.add_field(name = f"Description (1/{len(chunks)})", value = chunks[0], inline = False)
		else:
			embed.add_field(name = "Description", value = self.description, inline = False)
		if roll_disp:
			embed.set_footer(text = roll_disp)

		return embed


class Components:
	def __init__(self, verbal = False, somatic = False, material = False):
		self.verbal = verbal
		self.somatic = somatic
		self.material = material
		self.material_description = None
		self.is_material_significant = False

	def create_disp(self):
		disp = []
		if self.verbal:
			disp.append("V")
		if self.somatic:
			disp.append("S")
		if self.material:
			disp.append("M")

		disp = ", ".join(disp)

		if self.material:
			if self.is_material_significant:
				disp = f"{disp} __(significant material: {self.material_description})__"
			else:
				disp = f"{disp} ({self.material_description})"
		return disp


class Title:
	def __init__(self, title_id):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM titles WHERE id = ?", (title_id,))
			raw = cursor.fetchall()

		if raw:
			raw = raw[0]

			self.name = raw[1]
			self.rank = raw[2]

			with t.DatabaseConnection("data.db") as connection:
				cursor = connection.cursor()
				cursor.execute("SELECT * FROM title_people WHERE title_id = ?", (title_id,))
				raw2 = cursor.fetchall()

			self.people_id: list[int] = []
			for dc_id in raw2:
				self.people_id.append(dc_id[1])
		else:
			raise ValueError("No Title Found")


class Card:
	def __init__(self, card_id, name, in_draw, card_url = None, deck_id: int = None):
		self.card_id = card_id
		self.deck_id = deck_id
		self.name = name
		self.in_draw = in_draw
		self.card_url = card_url

	def update(self):
		with t.DatabaseConnection("card_base.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"UPDATE cards SET name = ?, in_draw = ?, art_url = ? WHERE card_id = ? ",
				(self.name, self.in_draw, self.card_url, self.card_id)
			)


class Deck:
	def __init__(self, name: str, owner_id = None, cards: list[Card] = None, new = False):
		self.deck_id = None
		self.name = name
		self.owner_id = owner_id
		self.cards: list[Card] = cards

		if new:
			self.create(owner_id)
		else:
			self.load()

	def create(self, owner_id):
		if owner_id:
			with t.DatabaseConnection("card_base.db") as connection:
				cursor = connection.cursor()
				cursor.execute("INSERT INTO decks(name, owner_id) VALUES (?, ?)", (self.name, owner_id))
			self.load()
		else:
			raise ValueError("Owner ID is none.")

		for card in self.cards:
			with t.DatabaseConnection("card_base.db") as connection:
				cursor = connection.cursor()
				cursor.execute(
					"INSERT INTO cards(deck_id, name, in_draw) VALUES (?, ?, 1)",
					(self.deck_id, card.name)
				)
		self.load()

	def load(self):
		with t.DatabaseConnection("card_base.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM decks WHERE name = ?", (self.name,))
			raw = cursor.fetchall()[0]
		self.deck_id = raw[0]
		self.owner_id = raw[1]

		with t.DatabaseConnection("card_base.db") as connection:
			cursor = connection.cursor()
			cursor.execute("SELECT * FROM cards WHERE deck_id = ?", (self.deck_id,))
			raw = cursor.fetchall()

		if raw:
			cards = []
			for card_raw in raw:
				card = Card(card_raw[0], card_raw[2], int(card_raw[3]), card_raw[4], self.deck_id)
				cards.append(card)
			self.cards = cards

	def update(self):
		with t.DatabaseConnection("card_base.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"UPDATE decks SET name = ?, owner_id = ? WHERE deck_id = ?",
				(self.name, self.owner_id, self.deck_id)
			)

		with t.DatabaseConnection("card_base.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"DELETE FROM cards WHERE deck_id = ?",
				(self.deck_id,)
			)

		for card in self.cards:
			with t.DatabaseConnection("card_base.db") as connection:
				cursor = connection.cursor()
				cursor.execute(
					"INSERT INTO cards(deck_id, name, in_draw, art_url) VALUES (?, ?, ?, ?)",
					(self.deck_id, card.name, card.in_draw, card.card_url)
				)

	def delete(self):
		with t.DatabaseConnection("card_base.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"DELETE FROM decks WHERE deck_id = ?",
				(self.deck_id,)
			)
		with t.DatabaseConnection("card_base.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				"DELETE FROM cards WHERE deck_id = ?",
				(self.deck_id,)
			)


pass
