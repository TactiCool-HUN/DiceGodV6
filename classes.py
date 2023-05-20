from ast import literal_eval
from bot_setup import bot
import settings as s
import tools as t
import datetime
import discord
import asyncio
import re


class Person:
	def __init__(self, ctx = None, discord_id = None):
		if not ctx and not discord_id:
			raise ValueError

		if ctx:
			self.user = ctx.author
		else:
			self.user = bot.get_user(discord_id)

		self.active = None
		self.tag = None
		self.color = "0"
		self.change_name = 1
		self.auto_tag = 1
		self.chat_ignore = 0

		if t.exists(self.user.id, "person"):
			self.load()
		else:
			self.create()

	def create(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				f"INSERT INTO people(discord_id, name, active, tag, color, change_name, auto_tag, chat_ignore)"
				f"VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
				(self.user.id, self.user.name, self.active, self.tag, self.color, self.change_name, self.auto_tag, self.chat_ignore)
			)

		self.load()

	def load(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(f"SELECT * FROM people WHERE discord_id = ?", (self.user.id,))
			raw = cursor.fetchall()[0]

		self.active = raw[2]
		self.tag = raw[3]
		self.color = raw[4]
		self.change_name = bool(raw[5])
		self.auto_tag = bool(raw[6])
		self.chat_ignore = bool(raw[7])

	def update(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				f"UPDATE people SET name = ?, active = ?, tag = ?, color = ?, change_name = ?, auto_tag = ?, chat_ignore = ?"
				f"WHERE discord_id = {self.user.id}",
				(self.user.name, self.active, self.tag, self.color, self.change_name, self.auto_tag, self.chat_ignore)
			)

	def add_roll(self, outcome, size, used, roll_text):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				f"INSERT INTO statistics(owner_id, outcome, size, used, roll_text, tag, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
				(self.user.id, outcome, size, int(used), roll_text, self.tag, datetime.datetime.now())
			)

	def get_rolls(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(f"SELECT * FROM statistics WHERE owner_id = ?", (self.user.id,))
			raw = cursor.fetchall()
		return raw

	def set_name(self):
		self.clear_name()
		return f"{self.user.name} [{self.active}]"

	def clear_name(self):
		if re.findall(" \[.*]", self.user.name):
			return self.user.name.replace(re.findall(" \[.*]", self.user.name)[0], "")


class Sheet:
	def __init__(self, ctx, new = False, character = None, sheet = None):
		self.character = character
		self.sheet = sheet
		self.google_sheet = None
		self.last_warning = datetime.datetime.now() - datetime.timedelta(days = 2)

		if new:
			self.create(ctx)
		else:
			self.character = Person(ctx).active
			self.load(ctx)

	def create(self, ctx):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				f"INSERT INTO sheets(owner_id, character, sheet, last_warning)"
				f"VALUES (?, ?, ?, ?)",
				(ctx.author.id, self.character, self.sheet, self.last_warning)
			)

		self.load(ctx)

	def load(self, ctx):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(f"SELECT * FROM sheets WHERE character = ?", (self.character,))
			raw = cursor.fetchall()[0]

		if raw[1] == ctx.author.id:
			self.sheet = raw[3]
			self.last_warning = datetime.datetime.strptime(raw[4], "%Y-%m-%d %H:%M:%S.%f")
		else:
			pass  # test if rented?

	def update(self):
		with t.DatabaseConnection("data.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				f"UPDATE sheets SET sheet = ?, last_warning = ? WHERE character = {self.character}",
				(self.character, self.sheet, self.last_warning)
			)

	def get_sheet(self, sa):
		self.google_sheet = sa.open(self.sheet)


class Pack:
	def __init__(self, ctx, single_rolls, roll_raw):
		self.ctx = ctx
		self.single_rolls = []
		self.single_rolls += single_rolls
		self.followups = [Followup("\U0001F504", roll_raw, "roll")]
		for roll in single_rolls:
			self.followups += roll.followups

	def add_single_roll(self, single_rolls):
		self.single_rolls += single_rolls
		for roll in single_rolls:
			self.followups += roll.followups

	def send_pack(self, is_reply = True, secret = False):
		person = Person(self.ctx)
		result = 0
		complex_roll = ""
		has_dynamic = False
		all_damage_types = ""
		roll_display_pack = []
		all_roll_notes = []

		for roll in self.single_rolls:
			if roll.pre_send:
				for text in roll.pre_send:
					if roll.pre_send == "lol" and person.user.id == 875753704685436938:
						tts = True
					else:
						tts = False
					asyncio.create_task(t.send_message(self.ctx, text, reply = True, silent = True, tts = tts))

			all_roll_notes += roll.roll_note

			for damage in roll.damage_type:
				all_damage_types += s.DAMAGE_TYPES.get(damage)

			match roll.speciality:
				case "init":
					pass
				case "deathsave":
					pass

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

		asyncio.create_task(t.send_message(self.ctx, embed, is_reply, True, self.followups, False, secret, True))


class SingleRoll:
	def __init__(self, raw_text, inc_type, name = None, dice_number = 0, die_size = 0, add = 0, dynamic = False, pre_send = None, damage_type = None, roll_note = None, followups = None):
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
			self.pre_send = [pre_send]
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

		raw_text = raw_text[1:]
		match inc_type:
			case "vanilla roll":
				temp = re.findall("[0-9]+d[0-9]+", raw_text)
				self.dice_number = int(re.split("d", temp[0])[0])
				self.die_size = int(re.split("d", temp[0])[1])

				temp = re.split("[0-9]+d[0-9]+", raw_text)[1]
				try:
					damage_type = re.findall("\[[a-z]+]", raw_text)[0]
					self.damage_type.append(damage_type[1:-1])
				except IndexError:
					pass
				self.args = RollArgs(temp)
			case "vanilla add":
				add = re.findall("[0-9]+", raw_text)[0]
				try:
					damage_type = re.findall("\[[a-z]+]", raw_text)[0]
					self.damage_type.append(damage_type[1:-1])
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


class Followup:
	def __init__(self, emoji, data, f_type):
		temp = bot.get_emoji(emoji)
		if temp:
			self.emoji = temp
		else:
			self.emoji = emoji
		self.data = data
		self.type = f_type


class RollArgs:
	def __init__(self, text = None):
		self.adv = None
		self.keep_type = None
		self.keep_quantity = None
		self.minmax_type = None
		self.minmax_size = None
		self.crit = False
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
		temp = re.findall("kh|kl", text)
		if temp:
			self.keep_type = temp[0]
			self.keep_quantity = int(re.findall("kh[0-9]+|kl[0-9]+", text)[0][2:])
		temp = re.findall("max|min", text)
		if temp:
			self.minmax_type = temp[0]
			self.minmax_size = int(re.findall("max[0-9]+|min[0-9]+", text)[0][3:])

	def create_args_display(self):
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

		args = f"{a_disp}{k_disp}{m_disp}{c_disp}"
		if args:
			args = f" {args}"
		return args


pass
