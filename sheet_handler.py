from datetime import datetime
import settings as s
import classes as c
import tools as t
import roller as r
import gspread
import asyncio
import random
import math
import re

sa = gspread.service_account(filename = "service_account.json")


def ping_sheet(sheet_name):
	try:
		sh = sa.open(sheet_name)
	except gspread.SpreadsheetNotFound:
		return False
	wks = sh.worksheet("Setup")
	value = wks.acell('B2').value
	if value:
		return True
	else:
		return False


def transfer_inventory(old_sheet, new_sheet):
	sh = sa.open(old_sheet)
	old_spacing, old_area, old_empty_line = t.get_inventory_spaces(re.findall("V[0-9].[0-9][0-9].[0-9][0-9]", old_sheet)[0][1:].replace(".", ""))
	inventory_old = sh.worksheet("Inventory").get(old_area)
	new_spacing, new_area, new_empty_line = t.get_inventory_spaces(re.findall("V[0-9].[0-9][0-9].[0-9][0-9]", new_sheet)[0][1:].replace(".", ""))

	new_inventory_lines = []
	for line in inventory_old:
		temp = new_empty_line[:]
		while len(line) < len(old_empty_line):
			line.append('')

		for k in old_spacing:
			if k in ["count", "auto_fill"]:
				temp[new_spacing[k]] = line[old_spacing[k]] == "TRUE"
			else:
				value = line[old_spacing[k]]
				if value.isnumeric():
					value = int(value)
				temp[new_spacing[k]] = value
		new_inventory_lines.append(temp)

	while len(new_inventory_lines) < 300:
		new_inventory_lines.append(new_empty_line)

	sa.open(new_sheet).worksheet("Inventory").update(new_area, new_inventory_lines)


def transfer_money(old_sheet, new_sheet):
	sh = sa.open(old_sheet)
	wks = sh.worksheet("MoneyTracker")
	old_tracker = wks.get("A3:H1000")
	auto_c = wks.acell("B1").value
	wks = sa.open(new_sheet).worksheet("MoneyTracker")
	wks.update("A3:H1000", old_tracker)
	wks.update("B1", auto_c == "TRUE")


def sort_inventory(sheet_inc: c.Sheet, based_on: str, spaces: bool, reverse: bool):
	sh = sheet_inc.get_sheet(sa)
	spacing, area_og, empty_line = t.get_inventory_spaces(sheet_inc.get_version())
	sort_index = spacing[based_on]
	wks = sh.worksheet("Inventory")
	area = wks.get(area_og)

	temp = []
	for i, line in enumerate(area):
		if line[0] == "":
			continue
		temp.append(line)
	area = temp

	area = sorted(area, key = lambda item: item[sort_index], reverse = reverse)

	for i, line in enumerate(area):
		line[spacing["count"]] = line[spacing["count"]] == "TRUE"
		line[spacing["auto_fill"]] = line[spacing["auto_fill"]] == "TRUE"
		line[41] = None
		line[43] = None
		area[i] = line

	if spaces:
		temp = []
		prev_type = area[0][sort_index]
		for i, line in enumerate(area):
			if prev_type != line[sort_index]:
				temp.append(empty_line)
				prev_type = line[sort_index]
			temp.append(line)
		area = temp

	if len(area) > 300:
		return "Not enough space in inventory!"
	else:
		for _ in range(300 - len(area)):
			area.append(empty_line)

	wks.update(area_og, area)
	return None


async def init_resources(ctx):
	sheet = c.Sheet(ctx)
	sh = sheet.get_sheet(sa)
	wks = sh.worksheet("BotRead")
	class_area = wks.get("A2:D6")
	wks = sh.worksheet("LimitedUse")
	limited_area = wks.get("A1:AW53")

	monk_level = 0
	# sorcerer_level = 0

	for line in class_area:
		while len(line) < 4:
			line.append("")

		if line[0] == "Monk":
			monk_level = int(line[2])

	if monk_level > 19:
		for i in range(18):
			# noinspection SpellCheckingInspection
			if t.limited_calc_splitter(limited_area, i, "name", "value") == "kipoints" and t.limited_calc_splitter(limited_area, i, "current", "value") == "0":
				place = t.limited_calc_splitter(limited_area, i, "current", "place")
				wks.update(place, 4)


async def set_deathsave(ctx, natural, result) -> None:
	sheet = c.Sheet(ctx)
	sh = sheet.get_sheet(sa)
	main = sh.worksheet("Main")

	if natural == 20:
		setter = [[False, "", False, "", False], [False, "", False, "", False]]
		main.update("H21:L22", setter)
		main.update("AP14", 1)

		txt = random.choice([
			f"{sheet.character}'s instincts are on top today, fight or flight!",
			f"It's a miracle! {sheet.character}'s wounds close, do care though, death is still watching.",
			"Remember son, dying is gay.\n(flashback to childhood memories before suddenly pulled back to life)"
		])
		await t.send_message(ctx, txt, True)
		return
	else:
		if natural == 1:
			area_txt = "H22:L22"
			area = main.get(area_txt)[0]
			add = 2
		elif result > 9:
			area_txt = "H21:L21"
			area = main.get(area_txt)[0]
			add = 1
		else:
			area_txt = "H22:L22"
			area = main.get(area_txt)[0]
			add = 1

		if area[4] == "TRUE":
			current = 3
		elif area[2] == "TRUE":
			current = 2
		elif area[0] == "TRUE":
			current = 1
		else:
			current = 0

		number = min(current + add, 3)

		if natural == 1:
			if number == 2:
				txt = random.choice([
					"Death is knocking on your door, yet you refuse to answer.", 1,
				])
			else:
				txt = t.choice([
					f"LOL {sheet.character} has died from a nat 1. xD", 0.5,
					"Death is only temporary, yet you've still managed to disappoint~ (dies)", 2,
					"One cannot refuse the Reaper's calling. I hope you find rest soldier.", 3,
				])
		elif result > 9:
			if number == 1:
				txt = random.choice([
					f"{sheet.character} is slowly pulling themselves together.",
					"You visit a nearby bowling station and forget about the consequences."
				])
			elif number == 2:
				txt = random.choice([
					f"{sheet.character} is slowly pulling themselves together.",
					"You visit a nearby bowling station and forget about the consequences."
				])
			else:
				txt = random.choice([
					f"{sheet.character} is stable and resting, may god be with them.",
					"While waiting for your turn, your friend hits you in the head by accident and awake to reality once again. All is well as long as your friends are angry at you~"
				])
		else:
			if number == 1:
				txt = random.choice([
					f"{sheet.character} is slowly loosing their grasp on life.",
					"The Sheep gather under a tree, the end is drawing near."
				])
			elif number == 2:
				txt = random.choice([
					f"{sheet.character} is slowly loosing their grasp on life.",
					"The Sheep gather under a tree, the end is drawing near."
				])
			else:
				txt = t.choice([
					f"Look you can cast animate object on the guy! :D", 1,
					f"A corpse and tears hit the floor. You will be missed soldier!", 2,
					"The Wolf has found it's prey, and you go down alongside with it.", 2
				])

		if number == 3:
			setter = [[False, "", False, "", False], [False, "", False, "", False]]
			main.update("H21:L22", setter)
		else:
			setter = [[False, "", False, "", False]]

			for i in range(number):
				setter[0][(i * 2)] = True

			main.update(area_txt, setter)

		await t.send_message(ctx, txt, True)


def get_ability_mod(sheet_inc, ability_score: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	area = wks.get("A40:B46")

	for line in area:
		if line[0] == ability_score:
			return int(line[1])


def get_skill(sheet_inc, skill_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	skills = wks.get("A8:E26")
	class_area = wks.get("A2:D6")

	add = 0
	adv = None
	minmax_type = None
	minmax_size = None
	prof = False
	score_used = "7th"
	pre_send = []

	for line in skills:
		while len(line) < 4:
			line.append("")

		if line[0].lower() == skill_inc:
			add = int(line[1])
			adv = line[2].lower()
			if adv == "fail":
				pre_send.append("WARNING!\nThe skill check is set to \"FAIL\" the roll will still happen in case you need it.")
			prof = line[3]
			score_used = line[4]
			break

	for line in class_area:
		while len(line) < 4:
			line.append("")

		if line[1] == "Eloquence" and int(line[2]) > 2 and skill_inc in ["persuasion", "deception"]:
			minmax_type = "min"
			minmax_size = 10
		if line[0] == "Rogue" and int(line[2]) > 10 and prof:
			minmax_type = "min"
			minmax_size = 10
		if line[0] == "Mothfolk" and line[1] == "Royal" and score_used == "CHA":
			minmax_type = "min"
			minmax_size = 5
		if line[0] == "Barbarian" and int(line[2]) > 17 and score_used == "STR":
			pre_send.append(f"If the check's total is lower than {wks.acell('H22').value} (Strength score) you can use it in it's place.")

	if skill_inc == "init":
		speciality = "init"
	else:
		speciality = None

	return add, adv, minmax_type, minmax_size, pre_send, speciality


def get_prof(sheet_inc):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	return int(wks.acell("F4").value)


def get_save(sheet_inc, save_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	saves = wks.get("A29:D37")
	looking_for = save_inc.replace("save", "")

	add = 0
	adv = None
	pre_send = []

	for line in saves:
		while len(line) < 4:
			line.append("")

		if line[0] == looking_for:
			add = int(line[1])
			adv = line[2].lower()
			if adv == "fail":
				pre_send.append("WARNING!\nThe skill check is set to \"FAIL\" the roll will still happen in case you need it.")
			break

	if looking_for == "death":
		speciality = "deathsave"
	else:
		speciality = None

	return add, adv, pre_send, speciality


def get_attack(sheet_inc, attack_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	attacks = wks.get("G2:N7")
	feats = wks.get("A50:B200")
	class_area = wks.get("A2:D5")

	followups = [c.Followup("💥", None, "crit"), c.Followup("🇶", None, "queue")]

	if len(attack_inc) == 3:
		slot = 1
	else:
		slot = int(attack_inc[3])

	if attack_inc[:3] == "hvy":
		heavy = True
		hvy_extra_dmg = "+exp"
	else:
		heavy = False
		hvy_extra_dmg = ""

	followups.append(c.Followup("👋", f"dmg{slot}{hvy_extra_dmg}", "roll"))
	followups.append(c.Followup("\U0001F450", f"dmg{slot}_2h{hvy_extra_dmg}", "roll"))

	add = 0
	adv = None
	properties = None
	line = None
	extra_die = None

	for line in attacks:
		while len(line) < 8:
			line.append("")
		if int(line[0]) == slot:
			add = int(line[1])
			adv = line[2].lower()
			properties = line[3].lower()
			break

	if properties:
		temp = re.findall('flexible \([0-9]+d[0-9]+\)', properties)  # flexible attack
		if temp:
			temp = re.findall("[0-9]+d[0-9]+", temp[0])[0]
			dmg_type = line[6]
			if wks.acell("F2").value or re.findall('nimble', properties):  # two-weapon fighting
				temp_add = int(line[7])
			elif int(line[7]) < 0:
				temp_add = int(line[7])
			else:
				temp_add = 0

			if temp_add > 0:
				temp += "+" + str(temp_add)
			elif temp_add < 0:
				temp += temp_add

			followups.append(c.Followup("💪", f"flexible:{temp}[{dmg_type}]", "roll"))

		temp = re.findall('extra \([0-9]+d[0-9]+ *[a-z]*\)', properties)  # extra damage
		if temp:
			temp = re.findall('[0-9]+d[0-9]+ *[a-z]*', temp[0])[0]
			temp_roll = re.findall("[0-9]+d[0-9]+", temp)[0]
			try:
				dmg_type = re.findall("\[[a-z]+]", temp)[0]
			except IndexError:
				dmg_type = re.findall("[a-z]+", temp)[-1]
			followups.append(c.Followup(s.DAMAGE_TYPES.get(dmg_type, '✨'), f"{temp_roll}[{dmg_type}]", "roll"))

	for feat in feats:
		if feat[0] == "Polearm Master" and int(feat[1]):
			temp_add = int(line[7])
			followups.append(c.Followup("🪄", f"1d4+{temp_add}[bludgeoning]", "roll"))
			break

	rogue_level = 0
	blood_level = 0
	slain_level = 0
	runner_level = 0
	zealot_level = 0
	p_rogue_level = 0
	whisper_level = 0
	paladin_level = 0
	eldritch_level = 0
	hunter_r_level = 0

	for line in class_area:
		while len(line) < 4:
			line.append("")

		if line[0] == "Rogue":
			rogue_level = int(line[2])
		elif line[0] == "Proper Rogue":
			p_rogue_level = int(line[2])
		elif line[1] == "Zealot":
			zealot_level = int(line[2])
		elif line[0] == "Paladin":
			paladin_level = int(line[2])
		elif line[1] == "Hunter (r)":
			hunter_r_level = int(line[2])
			runner_level = int(line[2])
		elif line[1] == "Whispers":
			whisper_level = int(line[2])
		elif line[0] == "Runner":
			runner_level = int(line[2])
		elif line[0] == "Blood Hunter":
			blood_level = int(line[2])
		elif line[0] == "Warlock":
			warlock_invocations = wks.get("C50:D200")
			for invocation in warlock_invocations:
				if invocation[0] == "Eldritch Smite" and invocation[1]:
					eldritch_level = int(line[2])
		if line[1] == "Slain":
			slain_level = int(line[2])

	if rogue_level > 0:
		sneak_dmg = f"{math.ceil(rogue_level / 2)}d6"
		followups.append(c.Followup("\U0001F52A", sneak_dmg, "roll"))
	elif p_rogue_level > 0:
		if p_rogue_level > 17:
			size = 12
		elif p_rogue_level > 13:
			size = 10
		elif p_rogue_level > 6:
			size = 8
		else:
			size = 6
		sneak_dmg = f"{math.ceil(p_rogue_level / 2)}d{size}"
		followups.append(c.Followup("\U0001F52A", sneak_dmg, "roll"))

	if zealot_level > 2:
		temp = wks.acell("G14").value
		followups.append(c.Followup("🏵️", f"1d6+{math.floor(zealot_level / 2)}[{temp}]", "roll"))

	if paladin_level > 1:
		followups.append(c.Followup("🎆", "2d8[radiant]", "roll"))
		followups.append(c.Followup("🎇", "1d8[radiant]", "roll"))
	if paladin_level > 10:
		followups.append(c.Followup("🌠", "1d8[radiant]", "roll"))
	if slain_level > 17:
		extra_die = "1d6"
	elif slain_level > 6:
		extra_die = "1d4"

	if runner_level > 16:
		followups.append(c.Followup("🎯", "2d10", "roll"))
	elif runner_level > 10:
		followups.append(c.Followup("🎯", "2d8", "roll"))
	elif runner_level > 4:
		followups.append(c.Followup("🎯", "2d6", "roll"))

	if hunter_r_level > 5:
		followups.append(c.Followup("👁️", "1d6", "roll"))

	if whisper_level > 14:
		followups.append(c.Followup("🧠", "8d6[psychic]", "roll"))
	elif whisper_level > 9:
		followups.append(c.Followup("🧠", "5d6[psychic]", "roll"))
	elif whisper_level > 4:
		followups.append(c.Followup("🧠", "3d6[psychic]", "roll"))
	elif whisper_level > 2:
		followups.append(c.Followup("🧠", "2d6[psychic]", "roll"))

	if blood_level > 16:
		followups.append(c.Followup("🩸", "1d10", "roll"))
	elif blood_level > 10:
		followups.append(c.Followup("🩸", "1d8", "roll"))
	elif blood_level > 4:
		followups.append(c.Followup("🩸", "1d6", "roll"))
	elif blood_level > 1:
		followups.append(c.Followup("🩸", "1d4", "roll"))

	if eldritch_level > 8:
		followups.append(c.Followup(1071167194165170207, "6d8[force]", "roll"))
	elif eldritch_level > 6:
		followups.append(c.Followup(1071167194165170207, "5d8[force]", "roll"))
	elif eldritch_level > 4:
		followups.append(c.Followup(1071167194165170207, "4d8[force]", "roll"))
	elif eldritch_level > 2:
		followups.append(c.Followup(1071167194165170207, "3d8[force]", "roll"))
	elif eldritch_level > 0:
		followups.append(c.Followup(1071167194165170207, "2d8[force]", "roll"))

	if heavy:
		add = add - get_prof(sheet_inc)

	return add, adv, followups, extra_die


def get_damage(sheet_inc, damage_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	attacks = wks.get("G2:N7")

	if damage_inc[-3:] == "_2h":
		two_handed = True
		dmg = damage_inc.replace("_2h", "")
	else:
		if damage_inc[-3:] == "_1h":
			dmg = damage_inc.replace("_1h", "")
		else:
			dmg = damage_inc
		two_handed = False

	if len(dmg) == 3:
		slot = 1
	else:
		slot = int(dmg[3])

	for line in attacks:
		while len(line) < 8:
			line.append("")

		if int(line[0]) == slot:
			if two_handed:
				dmg = line[5]
				if not dmg:
					dmg = line[4]
			else:
				dmg = line[4]
				if not dmg:
					dmg = line[5]
			break

	damage_type = re.findall("[a-z]+", dmg)[-1]
	dmg = dmg.replace(damage_type, f"[{damage_type}]")

	return dmg


def get_c_skill(sheet_inc, skill_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("Companion")
	skills = wks.get("M24:AB41")

	add = 0
	adv = None
	pre_send = []

	for line in skills:
		while len(line) < 4:
			line.append("")

		if skill_inc[1:] in line[0].lower():
			while len(line) < 16:
				line.append("")

			add = int(line[8])
			adv = line[15].lower()
			if adv == "fail":
				pre_send.append("WARNING!\nThe skill check is set to \"FAIL\" the roll will still happen in case you need it.")
			break

	return add, adv, pre_send


def get_c_save(sheet_inc, save_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("Companion")
	saves = wks.get("B14:N20")
	looking_for = save_inc.replace("save", "")
	looking_for = looking_for[1:]

	add = 0
	adv = None
	pre_send = []

	for line in saves:
		while len(line) < 13:
			line.append("")

		if line[0].lower()[:3] == looking_for:
			add = int(line[5])
			adv = line[12].lower()
			if adv == "fail":
				pre_send.append("WARNING!\nThe skill check is set to \"FAIL\" the roll will still happen in case you need it.")
			break

	return add, adv, pre_send


def get_c_attack(sheet_inc, attack_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	attacks = wks.get("G9:N12")
	attack_inc = attack_inc[1:]

	followups = [c.Followup("💥", None, "crit"), c.Followup("🇶", None, "queue")]

	if len(attack_inc) == 3:
		slot = 7
	else:
		slot = int(attack_inc[3]) + 6

	# noinspection SpellCheckingInspection
	followups.append(c.Followup("👋", f"cdmg{slot - 6}", "roll"))
	# noinspection SpellCheckingInspection
	followups.append(c.Followup("\U0001F450", f"cdmg{slot - 6}_2h", "roll"))

	add = 0
	adv = None
	properties = None
	line = None

	for line in attacks:
		while len(line) < 8:
			line.append("")
		if int(line[0]) == slot:
			add = int(line[1])
			adv = line[2].lower()
			properties = line[3].lower()
			break

	if properties:
		temp = re.findall('flexible *\([0-9]+d[0-9]+\)', properties)  # flexible attack
		if temp:
			temp = re.findall("[0-9]+d[0-9]+", temp[0])[0]
			dmg_type = line[6]
			if wks.acell("F2").value:  # two-weapon fighting
				temp_add = int(line[7])
			elif int(line[7]) < 0:
				temp_add = int(line[7])
			else:
				temp_add = 0

			if temp_add > 0:
				temp += "+" + str(temp_add)
			elif temp_add < 0:
				temp += temp_add

			followups.append(c.Followup("💪", f"flexible:{temp}[{dmg_type}]", "roll"))

		temp = re.findall('extra *\([0-9]+d[0-9]+ *[a-z]*\)', properties)  # extra damage
		if temp:
			temp = re.findall("[0-9]+d[0-9]+", temp[0])[0]
			try:
				dmg_type = re.findall('\[[a-z]+]', temp)[0]
			except IndexError:
				dmg_type = line[6]
			dmg_type_disp = f"[{dmg_type}]"
			followups.append(c.Followup(s.DAMAGE_TYPES.get(dmg_type), f"{temp}{dmg_type_disp}", "roll"))

	return add, adv, followups


def get_c_damage(sheet_inc, damage_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	attacks = wks.get("G9:N12")
	damage_inc = damage_inc[1:]

	if damage_inc[-3:] == "_2h":
		two_handed = True
		dmg = damage_inc.replace("_2h", "")
	else:
		if damage_inc[-3:] == "_1h":
			dmg = damage_inc.replace("_1h", "")
		else:
			dmg = damage_inc
		two_handed = False

	if len(dmg) == 3:
		slot = 7
	else:
		slot = int(dmg[3]) + 6

	for line in attacks:
		while len(line) < 8:
			line.append("")

		if int(line[0]) == slot:
			if two_handed:
				dmg = line[5]
				if not dmg:
					dmg = line[4]
			else:
				dmg = line[4]
				if not dmg:
					dmg = line[5]
			break

	damage_type = re.findall("[a-z]+", dmg)[-1]
	dmg = dmg.replace(damage_type, f"[{damage_type}]")

	return dmg


def get_spell_attack(sheet_inc, spell_attack_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	spell_attacks = wks.get("G17:I19")

	if len(spell_attack_inc) == 3:
		slot = 1
	else:
		slot = int(spell_attack_inc[3])

	add = 0
	adv = None

	for line in spell_attacks:
		while len(line) < 5:
			line.append("")

		if int(line[0]) == slot:
			add = line[1]
			adv = line[2]
			break

	return add, adv


def get_spell_mod(sheet_inc, spell_mod_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	spell_attacks = wks.get("G17:J19")

	if len(spell_mod_inc) == 8:
		slot = 1
	else:
		slot = int(spell_mod_inc[3])

	add = 0

	for line in spell_attacks:
		while len(line) < 4:
			line.append("")

		if int(line[0]) == slot:
			add = line[3]
			break

	return int(add)


async def set_condition(ctx, condition, on_or_off, exhaustion_level):
	sheet = c.Sheet(ctx).sheet
	sh = sa.open(sheet)
	main = sh.worksheet("Main")
	if condition == "clear":
		all_false = [
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False],
			[False]
		]
		main.update("G26:G41", all_false)
		txt = "All conditions are cleared (except Exhaustion)"
		return txt
	else:
		if condition == "exhaustion":
			if exhaustion_level == "up":
				exhaustion_level = int(main.acell("K45").value) + 1
				if exhaustion_level == 7:
					txt = "You are already dead, where the hell do you want to go?"
					return txt
			elif exhaustion_level == "down":
				exhaustion_level = int(main.acell("K45").value) - 1
				if exhaustion_level == -1:
					txt = "You are already completely rested."
					return txt
			elif exhaustion_level is None:
				txt = "Please give exhaustion level."
				return txt
			exhaustion_level = int(exhaustion_level)
			main.update("K45", exhaustion_level)
			if exhaustion_level > 3:
				maximum = int(main.acell('AT14').value)
				current = int(main.acell("AP14").value)
				main.update("AP14", min(maximum, current))
			txt = f"Exhaustion set to ``{exhaustion_level}``!"
			return txt
		else:
			conditions = main.get("B26:G39")
			for i, con in enumerate(conditions):
				if con[0].lower() == condition:
					place = f"G{i + 26}"
					break
			else:
				return "Error (this error shouldn't come up tbh)"

			if on_or_off is None:
				on_or_off = main.acell(place).value
				if on_or_off == "FALSE":
					on_or_off = True
				else:
					on_or_off = False

			main.update(place, on_or_off)

			if condition == "unconscious" and on_or_off:
				main.update("AM27", True)
				add = "\n(this sets the ``Prone`` condition to ``True`` as well)"
			else:
				add = ""

			txt = f"Condition ``{condition.capitalize()}`` is now ``{on_or_off}``.{add}"
			return txt


def money(ctx, name, income_loss, platinum, gold, electrum, silver, copper, multiplier):
	sheet_name = c.Sheet(ctx).sheet
	sh = sa.open(sheet_name)
	active = sh.worksheet("MoneyTracker")
	area = active.get("A4:H201")
	transaction = [name, income_loss.capitalize(), platinum, gold, electrum, silver, copper, multiplier]
	active.update(f"A{len(area) + 4}:H{len(area) + 4}", [transaction])


def spell_point(ctx, command, amount, spell_level):
	sheet = c.Sheet(ctx)
	sh = sa.open(sheet.sheet)
	wks = sh.worksheet("Spells")
	area = wks.get("B2:S11")
	if area[0][0] == "Spellpoints":
		public = ""
		current = int(area[2][15])
		maximum = int(area[3][15])

		if spell_level:
			amount += int(area[spell_level][4])

		match command:
			case "use":
				current = current - amount
				if current < 0:
					return "You do not have enough spell points.", "Error."
				public = f"{sheet.character}'s spell points have been lowered by {amount}."
			case "recover":
				current = min(maximum, current + amount)
				public = f"{sheet.character} has recovered {amount} spell points."
			case "set":
				current = max(min(amount, maximum), 0)
				public = f"{sheet.character}'s spell points have been set to {current}."
			case "reset":
				current = maximum
				public = f"{sheet.character}'s spell points have been reset to maximum."

		private = f"You now have {current}/{maximum} spell points."

		wks.update("Q4", current)
		return public, private

	else:
		return "You do not have spell points set on your sheet", "Error."


async def heal_hurt(ctx, is_heal: bool, amount: str, is_companion: bool = False):
	if amount == "0":
		return "Why?", None

	sheet = c.Sheet(ctx).sheet
	sh = sa.open(sheet)
	if is_companion:
		wks = sh.worksheet("Companion")
		area = wks.get("AJ14:AV14")

		character = wks.acell("F2").value

		current = int(area[0][3])
		max_hp = int(area[0][9])
		temp = int(area[0][0])
		extra_hp_type = None
		extra_current = 0
		extra_max = 0
		extra_temp = 0
		main = sh.worksheet("Main")
		main_char = main.acell("AP17").value
	else:
		main = None
		main_char = None
		wks = sh.worksheet("Main")
		area = wks.get("AM14:AV19")

		character = c.Person(ctx).active

		current = int(area[0][3])
		max_hp = int(area[0][7])
		temp = int(area[0][0])

		extra_hp_type = area[3][3]
		if extra_hp_type in ["Arcane Ward"]:
			extra_current = int(area[5][3])
			extra_max = int(area[5][7])
			extra_temp = int(area[5][0])
		else:
			extra_current = 0
			extra_max = 0
			extra_temp = 0

	if not re.findall("[+-]", amount[0]):
		amount = f"+{amount}"
	splits_raw = re.findall("[+-][^+-]+", amount)
	amount = 0
	for split in splits_raw:
		pack_maker = await asyncio.to_thread(r.text_to_pack, ctx, split, False)
		pack = await pack_maker

		if pack.single_rolls:  # - - - - - - - - do the thing - - - - - - - -
			roll: c.SingleRoll = pack.single_rolls[0]
			if roll.damage_type:
				resistances_dict = {
					"piercing": "",
					"bludgeoning": "",
					"slashing": "",
					"acid": "",
					"fire": "",
					"necrotic": "",
					"poison": "",
					"cold": "",
					"radiant": "",
					"force": "",
					"thunder": "",
					"lightning": "",
					"psychic": ""
				}
				if is_companion:
					resistance_area = wks.get("AH28:AL42")
					for line in resistance_area:
						if line[4] != "- -":
							if line[0].lower() == "all":
								for k in resistances_dict:
									resistances_dict[k] = line[4].lower()[0]
							elif line[0].lower() == "all physical":
								for i, k in enumerate(resistance_area):
									if i < 3:
										resistances_dict[k] = line[4].lower()[0]
									else:
										break
							resistances_dict[line[0].lower()] = line[4].lower()[0]
					multi = 1
					for damage in roll.damage_type:
						res = resistances_dict[damage]
						match res:
							case "r":
								multi = 0.5
							case "i":
								multi = 0
							case "v":
								multi = 2
					if roll.sign == "+":
						amount += math.floor(int(roll.full_result) * multi)
					else:
						amount -= math.floor(int(roll.full_result) * multi)
				else:
					resistance_area = wks.get("AG30:AR44")
					for line in resistance_area:
						if line[10] != "":
							if line[0].lower() == "all":
								for k in resistances_dict:
									resistances_dict[k] = line[10].lower()[0]
							elif line[0].lower() == "all physical":
								for i, k in enumerate(resistance_area):
									if i < 3:
										resistances_dict[k] = line[10].lower()[0]
									else:
										break
							resistances_dict[line[0].lower()] = line[10].lower()[0]
					multi = 1
					for damage in roll.damage_type:
						res = resistances_dict[damage]
						match res:
							case "r":
								multi = 0.5
							case "i":
								multi = 0
							case "v":
								multi = 2
					if roll.sign == "+":
						amount += math.floor(int(roll.full_result) * multi)
					else:
						amount -= math.floor(int(roll.full_result) * multi)
			else:
				if roll.sign == "+":
					amount += int(roll.full_result)
				else:
					amount -= int(roll.full_result)
		else:
			return "An error has occurred, please notify Tacti\nInternal Error: rolling for heal/dmg failed", None

		if amount < 1:
			return "Amount came out as 0 or negative.", None

	update_current = False
	update_temp = False
	update_extra_current = False
	update_extra_temp = False
	from_the_dead = False
	overheal = False
	outright = False
	followups = []
	heal = 0  # just to silence warnings

	if is_heal:
		heal = amount
		responses = [f"{character} is healed for {heal}"]

		if current != max_hp:
			update_current = True
			if current == 0:
				from_the_dead = True
		current = current + heal
		if current > max_hp:
			overheal = True
			heal = current - max_hp
			current = max_hp
		else:
			heal = 0
	else:  # is_damage:
		dmg = amount
		responses = [f"{character} is hurt for {dmg}"]

		if extra_temp:
			extra_temp = extra_temp - dmg
			update_extra_temp = True
			if extra_temp < 0:
				dmg = -1 * extra_temp
				extra_temp = 0
			else:
				dmg = 0

		if extra_current and dmg:
			extra_current = extra_current - dmg
			update_extra_current = True
			if extra_current < 0:
				dmg = -1 * extra_current
				extra_current = 0
			else:
				dmg = 0

		if temp and dmg:
			temp = temp - dmg
			update_temp = True
			if temp < 0:
				dmg = -1 * temp
				temp = 0
			else:
				dmg = 0

		if current and dmg:
			current = current - dmg
			update_current = True
			if current < 0:
				dmg = -1 * current
				current = 0
			else:
				dmg = 0

		if dmg > max_hp:
			outright = True

	# - - - - - - - - - - - - - - - RESPONSE GENERATOR - - - - - - - - - - - - - - -

	if is_heal:
		if current == 0:  # on 0 hp
			responses.append("How did you manage to heal someone and still have them on literally zero hp?")
		elif current < max_hp / (5 + random.randint(0, 10)):  # below 5-15% hp
			responses.append(t.choice([
				"Even a small bit of hope can go a long way!", 1,
				"A small bit of light is all you need to find your way out of the dark.", 1,
			]))
		elif current < max_hp / 2:  # below half
			responses.append(t.choice([
				"They are still bloodied up, but have a bit more time in this fight.", 1,
				"This'll be enough to take a blow or two, although they are still not doing too well.", 1,
			]))
		elif current < max_hp - max_hp / (5 + random.randint(0, 10)):  # below 85-95% hp
			responses.append(t.choice([
				"Remember son, bleeding out is gay.", 1,
				"Still hurt, but at least not bleeding, am I right?", 1,
			]))
		elif current < max_hp:  # between 85-95% and 100%
			responses.append(t.choice([
				"Just scratches remain, nothing some rest can't handle...", 1,
				"Nicely healed, they'll be alright from here.", 1,
			]))
		else:  # on full hp
			responses.append(t.choice([
				"Fully patched up and ready to fight!", 1,
				"Back on full!", 1,
			]))

		if from_the_dead:
			responses.append(t.choice([
				"Don't forget to buy your healer a drink for this!", 1,
				f"Death had a near {character} experience.", 1,
				"From the brink of death they rise again!", 1,
			]))
	else:  # is_damage
		disable_secondary = False
		if update_extra_current or update_extra_temp:
			if extra_hp_type == "Arcane Ward":
				if extra_current == 0:
					if outright:
						responses.append(f"The attack annihilates {character}'s arcane barrier and their body hits the ground. Their magic floods out into the world, may they rest in peace.")
						disable_secondary = True
					elif amount > extra_max * 0.8:
						responses.append(f"With a small crack {character}'s ward suddenly shatters.",)
					else:
						responses.append("The arcane barrier dissipates into nothingness.")
				elif extra_current < extra_max / (5 + random.randint(0, 10)):  # below 5-15% hp
					if amount > extra_max * 0.8:
						responses.append(f"As the arcane ward is struck a small shockwave hits {character}. Luckily the ward held this time, yet it's cracks show that it will not do for long.")
					else:
						responses.append(t.choice([
							"Its always unsettling to hear it crackle, the ward won't hold much longer", 1,
							"The Arcane Ward is getting unstable, time to back off a bit.", 1,
						]))
				elif extra_current < extra_max / 2:  # below half
					responses.append(t.choice([
						"The ward is fading.", 1,
						"Arcane defenses are weakening.", 1,
					]))
				elif extra_current < extra_max - extra_max / (5 + random.randint(0, 10)):  # below 85-95% hp
					responses.append(t.choice([
						"The ward is fading.", 1,
						"Arcane defenses are weakening.", 1,
					]))
				elif extra_current < extra_max:  # between 85-95% and 100%
					responses.append("The arcane ward is doing it's job, no real harm yet.")
				else:  # on full hp
					responses.append("You Arcane Ward is still on maximum, this might be some kind of error as the bot detected damage being dealt to it.")
		if not disable_secondary:
			if update_temp:
				if temp == 0:
					responses.append(t.choice([
						"Where is your plot armor now?", 1,
						"Shields broken... let's hope the spirits are still high.", 1,
					]))
				elif temp < max_hp * (0.1 + random.randint(0, 5) * 0.01):  # below 10% max hp
					if temp > current:
						responses.append("Poor lad is more shields than health, not like either would be much...")
					else:
						responses.append("They have some temporary hitpoints to their name.")
				elif temp < max_hp / 2:
					responses.append("A patch of temporary hit points are still remain.")
				elif temp < max_hp:
					responses.append("Temporary hit points still going strong!")
				elif temp > 10:
					responses.append("They also possess and ungodly amount of temporary hit points.")
		if not disable_secondary:
			if update_current:
				if current == 0:
					if outright:
						responses.append(t.choice([
							"Look you can cast animate object on the guy! :D", 1,
							"A corpse and tears hit the floor. You will be missed soldier!", 1,
						]))
					elif amount > max_hp * 0.8:
						responses.append(t.choice([
							"Poor food never stood a chance...", 1,
							"Poor fool never stood a chance...", 1,
							"That went from 100 to 0 real quick.", 2,
						]))
					else:
						# noinspection SpellCheckingInspection
						responses.append(t.choice([
							"Down on the ground, but still breathing.", 1,
							"Someone needs to patch this lad up before they'll stand again.", 1,
							"I'm pretty sure that much blood is unhealthy on the outside... aaand there they fall...", 1,
						]))
				elif current < max_hp / (5 + random.randint(0, 10)):  # below 5-15% hp
					if amount > max_hp * 0.8:
						responses.append("How can one survive such a blow? Poor lad is barely alive.")
					else:
						responses.append(t.choice([
							"Our hero is looking death in the eyes...", 1,
							"Our hero is staring death in the eyes...", 1,
							"The reaper is sharpening his scythe.", 1,
							"The reaper is sharpening her scythe.", 1,
						]))
				elif current < max_hp / 2:  # below half
					responses.append(t.choice([
						"Uhh lad looks bloodied up!", 1,
						"Blood is flowing down their face, but a hero does not give up this easily.", 1,
						"Time to pay them back, blood for blood as they say...", 1,
					]))
				elif current < max_hp - max_hp / (5 + random.randint(0, 10)):  # below 85-95% hp
					responses.append(t.choice([
						"Got hit, took it. Carry on...", 1,
						f"{character} is not leaving this unanswered!", 1,
					]))
				elif current < max_hp:  # between 85-95% and 100%
					responses.append(t.choice([
						"Got some scratches, what now?", 1,
						f"\nDamage taken: {amount}\nFucks to give: 0", 1,
					]))
				else:  # on full hp
					responses.append(t.choice([
						"The guy just does not even care...", 1,
						"Healthy as always.", 1,
					]))

	if is_companion:
		if update_temp:
			wks.update("AJ14", temp)
			if main_char == character:
				main.update("AM19", temp)
		if update_current:
			wks.update("AM14", current)
			if main_char == character:
				main.update("AP19", current)
		if overheal:
			responses.append(f"\nThere is some healing remaining, press the shield emoji under this message to apply it as temporary hitpoints!\nCurrent temp hp: {temp} | Remaining healing: {heal}")
			followups.append(c.Followup("🛡️", [heal, is_companion], "confirm_temphp"))
	else:
		if update_extra_temp:
			wks.update("AM19", extra_temp)
		if update_extra_current:
			wks.update("AP19", extra_current)
		if update_temp:
			wks.update("AM14", temp)
		if update_current:
			wks.update("AP14", current)
			if current == 0:
				responses.append(f"\nYou just dropped to 0 hp, would you like me to set up your conditions?\n(the ✅ emoji will turn the prone and the unconscious conditions on)")
				followups.append(c.Followup("✅", [["unconscious", True]], "conditions"))
				followups.append(c.Followup("❎", None, "disable"))
			if from_the_dead:
				responses.append("\nYou just came back from 0 hit points, should I turn off the unconscious condition?")
				followups.append(c.Followup("✅", [["unconscious", False]], "conditions"))
				followups.append(c.Followup("❎", None, "disable"))
		if overheal:
			responses.append(f"\nThere is some healing remaining, press the shield emoji under this message to apply it as temporary hitpoints!\nCurrent temp hp: {temp} | Remaining healing: {heal}")
			followups.append(c.Followup("🛡️", [heal, is_companion], "confirm_temphp"))

	response = "\n".join(responses)

	return response, followups


async def set_temp(ctx, amount, force = False, is_companion = False):
	if amount == "0":
		return "Why?", None

	pack_maker = await asyncio.to_thread(r.text_to_pack, ctx, amount, False)
	pack = await pack_maker

	if pack.single_rolls:  # - - - - - - - - do the thing - - - - - - - -
		amount = 0
		for roll in pack.single_rolls:
			if roll.sign == "+":
				amount += roll.full_result
			else:
				amount -= roll.full_result
	else:
		return "An error has occurred, please notify Tacti\nInternal Error: rolling for heal/dmg failed", None

	if amount < 1:
		return "Amount came out as 0 or negative.", None

	sheet = c.Sheet(ctx).sheet
	sh = sa.open(sheet)
	if is_companion:
		wks = sh.worksheet("Companion")
		character = wks.acell("F2").value
		place = "AJ14"
	else:
		wks = sh.worksheet("Main")
		character = c.Person(ctx).active
		place = "AM14"

	if force:
		wks.update(place, amount)
		txt = f"{character}'s temporary hit points set to {amount}!"
		return txt, None
	else:
		current = wks.acell(place).value
		if int(current) == int(amount):
			txt = f"{character}'s temporary hit were already at {amount}!"
			return txt, None
		elif current == "0":
			wks.update(place, amount)
			txt = f"{character}'s temporary hit points set to {amount}!"
			return txt, None
		else:
			txt = f"{character} has temporary hit points at the moment.\nCurrent: {current}\nNew: {amount}\nDo you want to swap it?"
			followups = [c.Followup("✅", [amount, is_companion], "confirm_temphp"), c.Followup("❎", f"{character}'s temporary hit points have been left at {current}!", "disable")]
			return txt, followups


def change_inspiration(ctx, to_do, amount):
	sheet = c.Sheet(ctx)
	sh = sa.open(sheet.sheet)
	wks = sh.worksheet("Main")

	area = wks.get("AQ3:AU3")[0]
	current = int(area[0])
	maximum = int(area[4])

	if to_do == "add":
		set_to = min(current + amount, maximum)
		wks.update("AQ3", set_to)
		return f"Inspiration point added to {sheet.character}!\nCurrent inspiration: {set_to}/{maximum}"
	elif to_do == "subtract":
		set_to = min(current - amount, maximum)
		wks.update("AQ3", set_to)
		return f"Inspiration point removed from {sheet.character}!\nCurrent inspiration: {set_to}/{maximum}"
	elif to_do == "set":
		set_to = max(min(amount, maximum), 0)
		wks.update("AQ3", set_to)
		return f"Inspiration point set to {sheet.character}!\nCurrent inspiration: {set_to}/{maximum}"


async def rest(ctx, length: str, hit_dice: str):
	sheet = c.Sheet(ctx)
	sh = sa.open(sheet.sheet)
	main = sh.worksheet("Main")
	limited = sh.worksheet("LimitedUse")
	spells = sh.worksheet("Spells")
	responses = [f"{length.capitalize()}rest finished with {sheet.character}!"]

	if length == "long":  # | | | | | | | | | | | | | | | | | | | | long rest | | | | | | | | | | | | | | | | | | | |
		# - - - - - - - - - - exhaustion - - - - - - - - - -
		exhaustion = int(main.acell("K45").value)
		exhaustion = max(0, exhaustion - 1)
		main.update("K45", exhaustion)
		# - - - - - - - - - - current hp - - - - - - - - - -
		max_hp = main.acell("AT14").value
		main.update("AP14", max_hp)
		# - - - - - - - - - - temporary - - - - - - - - - -
		main.update("AM14", 0)
		main.update("AM19", 0)
		# - - - - - - - - - - extra hp - - - - - - - - - -
		if main.acell("AP17").value in ["Arcane Ward"]:
			extra_max = main.acell("AT19").value
			main.update("AP17", extra_max)
		# - - - - - - - - - - companion hp - - - - - - - - - -
		wks = sh.worksheet("Companion")
		max_hp = wks.acell("AS14").value
		wks.update("AM14", max_hp)
		wks.update("AJ14", 0)
		# - - - - - - - - - - hit dice - - - - - - - - - -
		area = main.get("AS24:AU27")
		for i, line in enumerate(area):
			ready_hd = int(line[0])
			max_hd = int(line[2])
			if ready_hd < max_hd:
				used = max_hd - ready_hd
				used = max(used - max(math.floor(max_hd / 2), 1), 0)
				main.update(f"AQ{24 + i}", used)
		# - - - - - - - - - - limited abilities - - - - - - - - - -
		area = limited.get("A1:AW53")
		for i in range(18):
			recharge = t.limited_calc_splitter(area, i, "recharge", "value")
			current = t.limited_calc_splitter(area, i, "current", "value")
			maximum = t.limited_calc_splitter(area, i, "maximum", "value")

			reset_able = re.findall("[0-9]+minute|minutes|hour|hours", recharge) != []
			reset_able = re.findall("1day|perday", recharge) != [] or reset_able
			# noinspection SpellCheckingInspection
			reset_able = reset_able or recharge in ["longrest", "shortrest", "startofturn"]
			if current < maximum and reset_able:
				current = t.limited_calc_splitter(area, i, "current", "place")
				limited.update(current, int(maximum))
		# - - - - - - - - - - spell slots - - - - - - - - - -
		cast_type = spells.acell("B2").value
		if cast_type == "Spell Slots":
			area = spells.get("F3:S11")
			block = []
			for count, line in enumerate(area):
				max_slots = int(line[0])
				block.append([])
				for _ in line[2:]:
					if max_slots > 0:
						block[count].append(True)
						max_slots -= 1
					else:
						block[count].append(False)
			spells.update("H3:S11", block)
		elif cast_type == "Spellpoints":
			spells.update("Q4", spells.acell("Q5").value)
		# - - - - - - - - - - death saves - - - - - - - - - -
		main.update("H21:M22", [[False, "", False, "", False], [False, "", False, "", False]])
	else:  # | | | | | | | | | | | | | | | | | | | | short rest | | | | | | | | | | | | | | | | | | | |
		# - - - - - - - - - - deft explorer - - - - - - - - - -
		temp = sh.worksheet("ClassFeatureCalc")
		if temp.acell("B233").value == "TRUE":
			temp = sh.worksheet("BotRead")
			temp = temp.get("A2:C4")
			for line in temp:
				while len(line) < 3:
					line.append("")
				if line[0] == "Ranger":
					temp = int(line[2])
					break
			if temp > 9:
				main.update("K45", max(0, int(main.acell("K45").value) - 1))
		# - - - - - - - - - - temporary - - - - - - - - - -
		main.update("AM14", 0)
		main.update("AM19", 0)
		# - - - - - - - - - - death saves - - - - - - - - - -
		main.update("H21:M22", [[False, "", False, "", False], [False, "", False, "", False]])
		# - - - - - - - - - - limited abilities - - - - - - - - - -
		area = limited.get("A1:AW53")
		for i in range(18):
			# noinspection SpellCheckingInspection
			if t.limited_calc_splitter(area, i, "name", "value") == "sorcerypoints":
				current = t.limited_calc_splitter(area, i, "current", "value")
				maximum = t.limited_calc_splitter(area, i, "maximum", "value")
				limited.update(t.limited_calc_splitter(area, i, "current", "place"), min(int(current) + 4, int(maximum)))
				continue

			recharge = t.limited_calc_splitter(area, i, "recharge", "value")
			current = t.limited_calc_splitter(area, i, "current", "value")
			maximum = t.limited_calc_splitter(area, i, "maximum", "value")

			reset_able = re.findall("[0-9]+minute|minutes", recharge) != []
			# noinspection SpellCheckingInspection
			reset_able = reset_able or recharge in ["shortrest", "startofturn", "1hour"]
			if current < maximum and reset_able:
				current = t.limited_calc_splitter(area, i, "current", "place")
				limited.update(current, int(maximum))

		setup = sh.worksheet("Setup")
		area = setup.get("Q5:AN7")
		for line in area:
			class_name = line[0]
			# subclass_name = line[11]
			try:
				level = int(line[23])
			except ValueError:
				continue

			if class_name == "Sorcerer" and level > 19:
				for i in range(18):
					if t.limited_calc_splitter(area, i, "name", "value") == "Sorcery Points":
						current = int(t.limited_calc_splitter(area, i, "current", "value"))
						current_place = t.limited_calc_splitter(area, i, "current", "place")
						maximum = int(t.limited_calc_splitter(area, i, "maximum", "value"))
						limited.update(current_place, min(maximum, current + 4))
						break
				# - - - - - - - - - - hit dice healing - - - - - - - - - -
				if hit_dice:
					con = int(main.acell("N6").value)
					pack_maker = await asyncio.to_thread(r.text_to_pack, ctx, hit_dice, False)
					pack = await pack_maker

					amount = 0
					if pack.single_rolls:  # - - - - - - - - do the thing - - - - - - - -
						for roll in pack.single_rolls:
							if roll.sign == "+":
								amount += (roll.full_result + con)
							else:
								amount -= (roll.full_result + con)
					else:
						return "An error has occurred, please notify Tacti\nInternal Error: rolling for short rest hit points failed"

					max_hp = main.acell("AT14").value
					current = main.acell("AP14").value

					ready_dice = main.get("AS22:AS25")
					max_dice = main.get("AU22:AU25")
					instances = hit_dice.split("+")
					for instance in instances:
						try:
							if int(instance.split("d")[1]) == 12:
								if instance.split("d")[0] > ready_dice[0][0]:
									return f"You don't have enough hit dice (available: {ready_dice[0][0]}d12)."
								else:
									num = int(max_dice[0][0]) - int(ready_dice[0][0]) + int(instance.split("d")[0])
									main.update("AQ22", num)
							elif int(instance.split("d")[1]) == 10:
								if instance.split("d")[0] > ready_dice[1][0]:
									return f"You don't have enough hit dice (available: {ready_dice[1][0]}d10)."
								else:
									num = int(max_dice[1][0]) - int(ready_dice[1][0]) + int(instance.split("d")[0])
									main.update("AQ23", num)
							elif int(instance.split("d")[1]) == 8:
								if instance.split("d")[0] > ready_dice[2][0]:
									return f"You don't have enough hit dice (available: {ready_dice[2][0]}d8)."
								else:
									num = int(max_dice[2][0]) - int(ready_dice[2][0]) + int(instance.split("d")[0])
									main.update("AQ24", num)
							elif int(instance.split("d")[1]) == 6:
								if instance.split("d")[0] > ready_dice[3][0]:
									return f"You don't have enough hit dice (available: {ready_dice[3][0]}d6)."
								else:
									num = int(max_dice[3][0]) - int(ready_dice[3][0]) + int(instance.split("d")[0])
									main.update("AQ25", num)
						except IndexError:
							return "Something went wrong with the hit dice healing."
					else:
						current_hp = min(int(amount) + int(current), int(max_hp))
						main.update("AM13", current_hp)
						responses.append(f"Healed {amount} hp, and is now on {current_hp}/{max_hp}")

	return "\n".join(responses)


async def get_spell(ctx, spell_inc, sheet = None, exact_search = False):  # gets text, returns spell class
	to_find = spell_inc.replace("_", "").replace(" ", "").lower()

	check_player = True

	if not sheet:
		try:
			try:
				sheet = c.Sheet(ctx)
				sh = sa.open(sheet.sheet)
			except IndexError:
				sh = sa.open("MainV5")
				check_player = False
		except gspread.exceptions.SpreadsheetNotFound:
			sh = sa.open("MainV5")
			check_player = False

	else:
		if sheet.google_sheet:
			sh = sheet.google_sheet
		else:
			sh = sa.open(sheet.sheet)
	spells_tab = sh.worksheet("SpellFull")
	all_spells = spells_tab.get("A1:BE750")
	pc_level = int(spells_tab.acell("BF2").value)

	for line in all_spells:
		while len(line) < 57:
			line.append("")

	found = None
	list_o_spells = []
	remainder = None

	if exact_search:
		for spell in all_spells:
			compare = spell[0].lower().replace(" ", "")
			if to_find[:len(compare)] == compare:
				list_o_spells.append(spell[0])
				found = "exact"
				remainder = to_find.replace(compare, "")
				break
	else:
		#  - - - - - phase one  - - - - - (looking for exact match)
		for spell in all_spells:
			if to_find == spell[0].lower().replace(" ", ""):
				list_o_spells.append(spell[0])
				found = "exact"
				print("found in phase one")
				break
		#  - - - - - phase two  - - - - - (looking at player spells)
		else:  # if not found
			for spell in all_spells:
				if to_find in spell[56].lower().replace(" ", ""):
					list_o_spells.append(spell[56])
			if len(list_o_spells) == 1 and check_player:
				found = "exact"
				print("found in phase two")
			else:
				list_o_spells = []
		#  - - - - - phase three - - - - - (looking at all spells)
				for spell in all_spells:
					if to_find in spell[0].lower().replace(" ", ""):
						list_o_spells.append(spell[0])
				if len(list_o_spells) == 1:
					found = "exact"
					print("found in phase three")
				elif len(list_o_spells) > 1:
					found = "multiple"
					print("found in phase three")

	match found:
		case "multiple":
			for i, spell in enumerate(list_o_spells):
				list_o_spells[i] = get_spell_class(all_spells, spell, pc_level)
			return list_o_spells, found, remainder
		case "exact":
			spell = get_spell_class(all_spells, list_o_spells[0], pc_level)
			return spell, found, remainder
	return None, found, remainder


def get_spell_class(all_spells, exact_spell, pc_level):
	spell = None
	for line in all_spells:
		if line[0] == exact_spell:
			spell = line[:-2]
			break

	prepared = False
	for line in all_spells:
		if line[56] == exact_spell:
			if line[55] == "TRUE":
				prepared = True
			break

	return c.Spell(spell, prepared, pc_level)


def cast_slot(ctx, spell_level):
	sheet = c.Sheet(ctx).sheet
	sh = sa.open(sheet)
	wks = sh.worksheet("Spells")
	area = wks.get("B2:S11")
	if area[0][0] == "Spell Slots":
		line = area[spell_level]
		for i, part in enumerate(line[6:]):
			if part == "FALSE":
				if i == 0:
					return "Error! You don't have the proper slot to cast at that level."
				wks.update(f"{s.LETTERS[6 + i]}{spell_level + 2}", False)
				break

		reply = ["Your remaining slots after casting:"]
		for i, line in enumerate(area):
			if i < 1:
				continue

			number_of_slots = 0
			for j, cell in enumerate(line):
				if j < 6:
					continue

				if cell == "TRUE":
					number_of_slots += 1

			if line[4] != "0":
				if int(line[2]) == spell_level:
					number_of_slots -= 1
				reply.append(f"Level {line[2]}: {number_of_slots}/{line[4]}")
		reply = "\n".join(reply)
	else:
		current = int(area[2][15])
		cost = int(area[spell_level][4])

		new = current - cost
		if new < 0:
			return "Error! You don't have enough spell points to cast at that level"

		wks.update("Q4", new)
		return f"You have {new}/{wks.acell('Q5').value} spell points remaining."

	return reply


def get_spell_list(ctx):
	sheet = c.Sheet(ctx)
	sh = sa.open(sheet.sheet)
	wks = sh.worksheet("Spells")
	area = wks.get("B15:D171")

	reply = []
	for line in area:
		if len(line) < 2:
			continue

		if line[0] == "TRUE":
			reply.append(f"__**{line[2]}** - prepared__")
		else:
			reply.append(f"**{line[2]}** - not prepared")

	return "\n".join(reply)


def get_inventory(sheet, based_on):
	sh = sa.open(sheet)
	wks = sh.worksheet("Inventory")
	area = wks.get("B12:AJ312")

	reply = []
	for line in area:
		if len(line) < 1:
			continue

		if based_on:
			if len(line) > 1:
				if line[5].lower().replace(" ", "") != based_on.lower().replace(" ", ""):
					continue

		if len(line) == 35:
			reply.append(f"{line[0]} (quantity: {line[-1]})")
		else:
			reply.append(line[0])

	return "\n".join(reply)


async def clear_sheet(interaction, ctx, sheet, player, dm):
	timer = 10
	sh = sa.open(sheet)
	link = sh.url
	temp = None

	progress = {
		"Overall": [0, 0],
		"Setup": [0, 23],
		"Features": [0, 1],
		"Main": [0, 18],
		"LimitedUse": [0, 2],
		"Spells": [0, 4],
		"Inventory": [0, 6],
		"MoneyTracker": [0, 1],
		"Notes": [0, 6],
		"Modifiers": [0, 1],
		"AbilityPicker": [0, 4],
		"Companion": [0, 16],
		"Spellbook": [0, 3],
		"SpellSearch": [0, 8]
	}
	start_time = datetime.now()

	sent = await t.clear_progress(player, sheet, progress, start_time)
	await interaction.followup.send("Clearing started.")
	# - - - - - - - - - - - - - - - - - - - - SETUP - - - - - - - - - - - - - - - - - - - -
	current = "Setup"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	filler = [
		['Name', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Player', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Sheet by TactiCool'],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
		[],
		['Race', '', '', '', '', '', '', '', '', '', 'Main Class', '', '', '', '', '', '', '', '', '', '', '', 'Subclass', '', '', '', '', '', '', '', '', '', '', '', '', 'Level', '', '', '', '', 'Main Score', '', '', '', 'OG'],
		['Variant', '', '', '', '', '', '', '', '', '', 'Multiclass I.', '', '', '', '', '', '', '', '', '', '', '', 'Subclass', '', '', '', '', '', '', '', '', '', '', '', '', 'Level', '', '', '', '', 'Main Score', '', '', '', 'OG'],
		['Post MotM race?', '', '', '', '', '', False, '', '', '', 'Multiclass II.', '', '', '', '', '', '', '', '', '', '', '', 'Subclass', '', '', '', '', '', '', '', '', '', '', '', '', 'Level', '', '', '', '', 'Main Score', '', '', '', 'OG'],
		[],
		['Ability Scores'],
		['Name', '', '', '', '', '', 'Strength', '', '', '', '', 'Dexterity', '', '', '', '', 'Constitution', '', '', '', '', 'Intelligence', '', '', '', '', 'Wisdom', '', '', '', '', 'Charisma', '', '', '', '', '7th Score', '', '', '', '', 'Name'],
		['Starting Value', '', '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 'Starting Value'],
		['Racial', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Manual', '', '', '', True],
		['Add (limited)', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Add (limited)'],
		['Add (unlimited)', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Add (unlimited)']
	]
	wks.update("B2:AV14", filler)
	wks.update("AU15:AU18", [[False], [False], ["max"], [False]])
	wks.update("H18", False)
	wks.update("M18", False)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 4, sent))
	await asyncio.sleep(timer)
	wks.update("R18", False)
	wks.update("W18", False)
	wks.update("AB18", False)
	wks.update("AG18", False)
	wks.update("AL18", False)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
	await asyncio.sleep(timer)
	wks.update("E21:L21", [[False, '', 'Class Choices', '', '', '', '', False]])
	wks.update("X21", False)
	wks.update("J23:J31", [['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO']])
	wks.update("X23:X31", [['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO']])
	filler = [
		['', '', '', '', '', '', '', '', '', '', '', False],
		[True, '', 'Base Health', '', '', '', '', '', '', '', 0],
		[],
		[True, '', 'Custom add (one time)', '', '', '', '', '', '', '', 0],
		[],
		[True, '', 'Custom add (per level)', '', '', '', '', '', '', '', 0],
		[],
		[True],
		[],
		[],
		[],
		['Official D&D']
	]
	wks.update("AK20:AV31", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
	await asyncio.sleep(timer)
	wks.update("E33:AQ33", [[False, 'Armor Proficiencies', '', '', '', '', '', '', '', 'Manual', '', '', False, 'Tool Proficiencies', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Auto EXP on all PROF ', '', '', '', '', '', '', False]])
	wks.update("I35:K43", [[False], [False], [False], [False], [], ['', False, 10], ['', False, 2], ['', False, 0], ['', False, 2]])
	wks.update("T35:T43", [['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO']])
	wks.update("AF35:AF43", [['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO']])
	filler = [
		['Thieves', '', '', '', '', '', 'AUTO'],
		['Herbalism', '', '', '', '', '', 'AUTO'],
		['Poisoner', '', '', '', '', '', 'AUTO'],
		['Disguise', '', '', '', '', '', 'AUTO'],
		['Vehicles (land)', '', '', '', '', '', 'AUTO'],
		['Vehicles (water)', '', '', '', '', '', 'AUTO'],
		['Vehicles (air)', '', '', '', '', '', 'AUTO'],
		['Forgery Kit', '', '', '', '', '', 'AUTO'],
		['[empty]', '', '', '', '', '', 'AUTO']
	]
	wks.update("AL35:AR43", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
	await asyncio.sleep(timer)
	wks.update("M51:M122", [[False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False]])
	wks.update("AC51:AC122", [[False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False]])
	# noinspection SpellCheckingInspection
	filler = [['Manual', '', '', False, 'Known Languages'], ['Language', '', '', '', '', '', '', '', '', '', 'Known'], ['Common', '', '', '', '', '', '', '', '', '', False], ['Abyssal', '', '', '', '', '', '', '', '', '', False], ['Celestial', '', '', '', '', '', '', '', '', '', False], ['Daelkyr', '', '', '', '', '', '', '', '', '', False], ['Deep Speech', '', '', '', '', '', '', '', '', '', False], ['Draconic', '', '', '', '', '', '', '', '', '', False], ['Dwarvish', '', '', '', '', '', '', '', '', '', False], ['Elvish', '', '', '', '', '', '', '', '', '', False], ['Giant', '', '', '', '', '', '', '', '', '', False], ['Gith', '', '', '', '', '', '', '', '', '', False], ['Gnomish', '', '', '', '', '', '', '', '', '', False], ['Goblin', '', '', '', '', '', '', '', '', '', False], ['Halfling', '', '', '', '', '', '', '', '', '', False], ['Infernal', '', '', '', '', '', '', '', '', '', False], ['Kraul', '', '', '', '', '', '', '', '', '', False], ['Leonin', '', '', '', '', '', '', '', '', '', False], ['Loxodon', '', '', '', '', '', '', '', '', '', False], ['Marquesian', '', '', '', '', '', '', '', '', '', False], ['Minotaur', '', '', '', '', '', '', '', '', '', False], ['Naush', '', '', '', '', '', '', '', '', '', False], ['Orc', '', '', '', '', '', '', '', '', '', False], ['Primordial', '', '', '', '', '', '', '', '', '', False], ['Quori', '', '', '', '', '', '', '', '', '', False], ['Riedran', '', '', '', '', '', '', '', '', '', False], ['Sylvan', '', '', '', '', '', '', '', '', '', False], ['Undercommon', '', '', '', '', '', '', '', '', '', False], ['Vedalken', '', '', '', '', '', '', '', '', '', False], ['Zemnian', '', '', '', '', '', '', '', '', '', False], ['Ivathi', '', '', '', '', '', '', '', '', '', False], ['Druidic', '', '', '', '', '', '', '', '', '', False], ["Thieves' Cant", '', '', '', '', '', '', '', '', '', False], ['Aarakocra', '', '', '', '', '', '', '', '', '', False], ['Auran', '', '', '', '', '', '', '', '', '', False], ['Aquan', '', '', '', '', '', '', '', '', '', False], ['Grung', '', '', '', '', '', '', '', '', '', False], ['Ivathi', '', '', '', '', '', '', '', '', '', False], ['[custom language]', '', '', '', '', '', '', '', '', '', False], ['[custom language]', '', '', '', '', '', '', '', '', '', False], ['[custom language]', '', '', '', '', '', '', '', '', '', False], [], ['Manual', '', '', False, 'Other Proficiencies'], ['Name', '', '', '', '', '', '', '', '', '', 'PROF'], ['Bagpipes', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Drum', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Flute', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Lyre', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Horn', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Pan Flute', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Shawn', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Viol', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Dice Set', '', '', '', '', '', '', '', '', '', 'AUTO'], ['Playing Card Set', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO'], ['[custom proficiency]', '', '', '', '', '', '', '', '', '', 'AUTO']]
	wks.update("AH49:AR122", filler)
	wks.update("E49", False)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 4, sent))
	await asyncio.sleep(timer)
	# - - - - - - - - - - - - - - - - - - - - FEATURES - - - - - - - - - - - - - - - - - - - -
	current = "Features"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	filler = [
		['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[],
		['Background', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Manual', '', '', '', False],
		[''],
		[],
		[],
		[],
		['Feats', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Manual', '', '', '', False],
		[''],
		[''],
		[''],
		[''],
		[''],
		[''],
		[''],
		[''],
		[''],
		[''],
		[],
		[],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[],
		[],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[],
		[],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -'],
		[], ['- - choose an option - -']
	]
	wks.update("B12:AV247", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	# - - - - - - - - - - - - - - - - - - - - MAIN - - - - - - - - - - - - - - - - - - - -
	current = "Main"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	wks.update("F20", False)
	wks.update("K12:K20", [['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO'], ['AUTO']])
	filler = [
		['Successes', '', '', '', '', '', False, '', False, '', False],
		['Failures', '', '', '', '', '', False, '', False, '', False],
		[],
		[],
		[],
		['Blinded', '', '', '', '', False, 'AUTO'],
		['Charmed', '', '', '', '', False, 'AUTO'],
		['Deafened', '', '', '', '', False, 'AUTO'],
		['Stunned', '', '', '', '', False, 'AUTO'],
		['Frightened', '', '', '', '', False, 'AUTO'],
		['Grappled', '', '', '', '', False, 'AUTO'],
		['Incapacitated', '', '', '', '', False, 'AUTO'],
		['Paralyzed', '', '', '', '', False, 'AUTO'],
		['Petrified', '', '', '', '', False, 'AUTO'],
		['Poisoned', '', '', '', '', False, 'AUTO'],
		['Prone', '', '', '', '', False, 'AUTO'],
		['Restrained', '', '', '', '', False, 'AUTO'],
		['Unconscious', '', '', '', '', False, 'AUTO'],
		['Invisible', '', '', '', '', False, 'AUTO'],
		['[custom]', '', '', '', '', False, 'AUTO'],
		['[custom]', '', '', '', '', False, 'AUTO'],
		['Reset', '', '', '', False, '', 'Adv/Immunity'],
		[],
		[],
		['Exhaustion', '', '', '', '', '', '', '', '', 0]
	]
	wks.update("B21:M45", filler)
	wks.update("Q13:Q32", [['DEX'], ['WIS'], ['INT'], ['STR'], ['CHA'], ['INT'], ['WIS'], ['CHA'], ['INT'], ['WIS'], ['INT'], ['WIS'], ['CHA'], ['CHA'], ['INT'], ['DEX'], ['DEX'], ['WIS'], [], [False]])
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 4, sent))
	await asyncio.sleep(timer)
	filler = [
		['AUTO', '', '', '', None, '', 'AUTO'],
		['AUTO'],
		['AUTO'],
		['AUTO'],
		['AUTO'],
		['AUTO'],
		['AUTO'],
		['AUTO'],
		['AUTO', '', '', '', 'AUTO'],
		['AUTO', '', '', '', 'Armor Type', '', '', '', '- -'],
		['AUTO'],
		['AUTO', '', '', '', '- -'],
		['AUTO', '', '', '', '', '', '', '', '', 0],
		['AUTO', '', '', '', 'Shield', '', '', '', False, 0],
		['AUTO'],
		['AUTO'],
		['AUTO'],
		['AUTO']
	]
	wks.update("AC13:AL30", filler)
	wks.update("AM14:AP19", [[0, '', '', 0], [], [], ['Display', '', '', '- -'], [], [0, '', '', 0]])
	wks.update("AQ22:AV27", [['', False, 'Reset', '', '', False], [], [0], [0], [0], [0]])
	filler = [
		['Manual', '', '', '', 'Reset', '', False],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any'],
		['- -', '', '', '', '', '', None, 'Any']
	]
	wks.update("AK29:AR44", filler)
	filler = [
		['Stealth'],
		[],
		['', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '']
	]
	wks.update("O39:X43", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
	await asyncio.sleep(timer)
	wks.update("AG54:AG56", [[''], [], ['']])
	filler = [
		['', '', '', '', '', '', '', '', '', '', '', 'Options from', '', '', '', 'Inventory'],
		['', '', '', '', '', '', '', '', '', '', '', '+1', '', False, '', None, '', '', False],
		[None, '', '', '', '', '', 'Prof', '', None, '', False, 'CHA', '', False, '', 'forced?', '', '', False],
		[None, '', '', '', '', '', 'Thrown', '', '', '', False, 'Hit', '', None, '', None, '', 'AUTO'],
		[],
		[],
		['', '', '', '', '', '', '', '', '', '', '', 'Ammo', '', '', '', '', '', -1, '', False],
		['', '', '', '', '', '', '', '', '', '', '', 'Loaded', '', '', ''],
		['', '', '', '', '', '', '', 'Short', '', '', True],
		['', '', '', '', '', '', '', '', '', '', '', '']
	]
	wks.update("E59:X68", filler)
	wks.update("E71:X89", filler)
	wks.update("AC59:AV68", filler)
	wks.update("AC71:AV89", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
	await asyncio.sleep(timer)
	filler = [
		['Unarmed Strike'],
		['', '', '', '', '', '', '', '', '', '', '', '+1', '', False, '', None, '', '', False],
		[None, '', '', '', '', '', 'Prof', '', None, '', '', 'CHA', '', False, '', 'forced?', '', '', False],
		[None, '', '', '', '', '', 'Thrown', '', '', '', False, 'Hit', '', None, '', None, '', 'AUTO'],
		[],
		[],
		[],
		[],
		['', '', '', '', '', '', '', 'Short', '', '', True],
		['', '', '', '', '', '', '', '', '', '', '', '']
	]
	wks.update("E83:X92", filler)
	filler = [
		['Name', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', '+1', '', False, '', None, '', '', False],
		['Type', '', '', '', '', '', '', '', '', 'Prof', '', '', '', False, 'CHA', '', False, '', 'forced?', '', '', False],
		['Style', '', '', '', '', '', '', '', '', 'Thrown', '', None, '', False, 'Hit', '', '', '', None, '', 'AUTO'],
		['Reach', '', '', '', '', '', '', 'Range', '', '', '', '', '', '', None, '', '', ''],
		['Properties', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Ammo', '', '', '', '', '', -1, '', False],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Loaded', ''],
		['Property Descriptions', '', '', '', '', '', '', '', '', '', 'Short', '', '', True],
		[None, '', '', '', '', '', '', '', '', '', '', '', '', '', '']
	]
	wks.update("B95:X104", filler)
	wks.update("AQ3", 0)
	filler = [
		[False, '', '', False, '', '', False, '', '', False, '', '', False],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', '']
	]
	wks.update("AH83:AU104", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 4, sent))
	# - - - - - - - - - - - - - - - - - - - - Limited Use - - - - - - - - - - - - - - - - - - - -
	current = "LimitedUse"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	filler = [
		[None, 'Name', '', '', ''],
		['Description', '', '', '', 'Source', '', '', '', ''],
		[''],
		['Current', '', '', '', '', '', '', 'Maximum', '', '', '', '', '', '', 'Recharge', '', '', '', ''],
		[],
		[None, 'Name', '', '', ''],
		['Description', '', '', '', 'Source', '', '', '', ''],
		[''],
		['Current', '', '', '', '', '', '', 'Maximum', '', '', '', '', '', '', 'Recharge', '', '', '', ''],
		[],
		[None, 'Name', '', '', ''],
		['Description', '', '', '', 'Source', '', '', '', ''],
		[''],
		['Current', '', '', '', '', '', '', 'Maximum', '', '', '', '', '', '', 'Recharge', '', '', '', ''],
		[],
		[],
		[],
		[],
		['Current', '', '', '', ''],
		[],
		[''],
		[],
		[],
		[],
		[],
		['Current', '', '', '', ''],
		[],
		[''],
		[],
		[],
		[],
		[],
		['Current', '', '', '', ''],
		[],
		[''],
		[],
		[],
		[],
		[],
		['Current', '', '', '', ''],
		[],
		[''],
		[],
		[],
		[],
		[],
		['Current', '', '', '', ''],
		[],
		[''],
		[],
		[],
		[],
		[],
		['Current', '', '', '', ''],
		[],
		['']
	]
	wks.update("B2:T57", filler)
	wks.update("Z2:AR57", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	await asyncio.sleep(timer)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	# - - - - - - - - - - - - - - - - - - - - Spells - - - - - - - - - - - - - - - - - - - -
	current = "Spells"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	match wks.acell("B2").value:
		case "Spell Slots":
			filler = [
				['Current', '', '', '', '', '', '', '', '', 'Reset', '', False],
				[False, False, False, False, False, False, False, False, False, False, False, False],
				[False, False, False, False, False, False, False, False, False, False, False, False],
				[False, False, False, False, False, False, False, False, False, False, False, False],
				[False, False, False, False, False, False, False, False, False, False, False, False],
				[False, False, False, False, False, False, False, False, False, False, False, False],
				[False, False, False, False, False, False, False, False, False, False, False, False],
				[False, False, False, False, False, False, False, False, False, False, False, False],
				[False, False, False, False, False, False, False, False, False, False, False, False],
				[False, False, False, False, False, False, False, False, False, False, False, False]
			]
			wks.update("H2:S11", filler)
		case "Spellpoints":
			wks.update("Q2:Q4", [[False], [], ['']])
	match wks.acell("B13").value:
		case "Spells (auto)":
			temp = "J15:L174"
			filler = [
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				[''],
				['List', '', 'All'],
				[''],
				[],
				['']
			]
		case "Spells":
			temp = "B15:L174"
			filler = [
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', ''],
				[False, '', '', '', '', '', '', '', 'List', '', 'All'],
				['', '', '', '', '', '', '', '', ''],
				[],
				['', '', '', '', '', '', '', '', '']
			]
	wks.update(temp, filler)
	wks.update("AH4:AH6", [['AUTO'], ['AUTO'], ['AUTO']])
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 4, sent))
	# - - - - - - - - - - - - - - - - - - - - INVENTORY - - - - - - - - - - - - - - - - - - - -
	current = "Inventory"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	await asyncio.sleep(timer)
	wks.update("I2", True)
	wks.update("C7", "GP")
	wks.update("R5:R7", [["AUTO"], [], [False]])
	wks.update("AA4:AG4", [[0, '', '', 0, '', '', 0]])
	wks.update("AL2:AN7", [[False, '', ''], [False, '', ''], [False, '', ''], [False, '', ''], [False, '', ''], [False, '', '']])
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
	await asyncio.sleep(timer)
	temp = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', True, '', '', '', None, '', None, '', False]
	filler = []
	for i in range(301):
		filler.append(temp)
	wks.update("B12:AU312", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	# - - - - - - - - - - - - - - - - - - - - MONEY TRACKER - - - - - - - - - - - - - - - - - - - -
	current = "MoneyTracker"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	temp = ['', '', '', '', '', '', '', '']
	filler = [
		[None, False],
		[],
		[None, None, 0, 0, 0, 0, 0]
	]
	for i in range(997):
		filler.append(temp)
	wks.update("A1:H1000", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	# - - - - - - - - - - - - - - - - - - - - NOTES - - - - - - - - - - - - - - - - - - - -
	current = "Notes"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	filler = [
		['Age', '', '', '', '', '', '', 'Alignment', '', '', '', ''],
		['Gender', '', '', '', ''],
		['Height', '', '', '', ''],
		['Weight', '', '', '', ''],
		[],
		['Personality Traits'],
		[''],
		[],
		[],
		[''],
		[],
		[],
		['Ideals'],
		[''],
		[],
		[],
		['Bonds'],
		[''],
		[],
		[],
		['Flaws'],
		[''],
		[],
		[],
		['Madnesses'],
		[''],
		[],
		['']
	]
	wks.update("B5:M33", filler)
	wks.update("S6", '')
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 2, sent))
	await asyncio.sleep(timer)
	wks.update("AQ7:AV18", [["Harptos"], [], [], [1], ["Month", '', '', '', '', False], ["Hammer"], ['Day', '', '', '', 1], [], [], [], [], [1]])
	wks.update("AT35", 10)
	temp = wks.get("B35:AV")
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 3, sent))
	await asyncio.sleep(timer)
	quest_row = 35
	people_row = 0
	places_row = 0
	other_row = 0
	end_rows = 0
	for i, line in enumerate(temp):
		if len(line) == 0:
			continue
		if line[0] == "- People -":
			people_row = 35 + i
		elif line[0] == "- Places -":
			places_row = 35 + i
		elif line[0] == "- Other Notes -":
			other_row = 35 + i
		if other_row != 0:
			end_rows += 1

	filler = [
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', False, '']
	]
	i = 0
	for i in range(people_row - quest_row - 3):
		wks.update(f"B{quest_row + 2 + i}:AP{quest_row + 2 + i}", filler)
		if i % 5 == 0 and i != 0:
			progress['Notes'][1] += 5
			asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
			await asyncio.sleep(timer)
	progress['Notes'][1] += i % 5
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, i % 5, sent))
	await asyncio.sleep(timer // (i % 5))

	filler = [
		['', '', '', '', '', '', '', '', '', 'Importance', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Standing', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', 'Notes', '', '', '', ''],
		[],
		['', '', '', '', '', '', '', '', '', 'Notes', '', '', '', '']
	]
	for i in range(((places_row - people_row) - 3) // 4):
		wks.update(f"B{people_row + 2 + i * 4}:AH{people_row + 5 + i * 4}", filler)
		if i % 5 == 0 and i != 0:
			progress['Notes'][1] += 5
			asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
			await asyncio.sleep(timer)
	progress['Notes'][1] += i % 5
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, i % 5, sent))
	await asyncio.sleep(timer // (i % 5))

	for i in range(((other_row - places_row) - 3) // 4):
		wks.update(f"B{places_row + 2 + i * 4}:AH{places_row + 5 + i * 4}", filler)
		if i % 5 == 0 and i != 0:
			progress['Notes'][1] += 5
			asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
			await asyncio.sleep(timer)
	progress['Notes'][1] += i % 5
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, i % 5, sent))
	await asyncio.sleep(timer // (i % 5))

	filler = []
	for _ in range(end_rows):
		filler.append([''])
	wks.update(f"B{other_row + 1}:B{other_row + end_rows}", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	# - - - - - - - - - - - - - - - - - - - - MODIFIERS - - - - - - - - - - - - - - - - - - - -
	current = "Modifiers"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	filler = [[False, '', '', '', False, '', '', '', False, '', '', '', 'TRUE', '', '', '', False, '', '', '', False, '', '', '', False, '', '', '', False, '', '', '', False]]
	for i in range(174):
		filler.append(['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''])
	filler.append([False, '', '', '', False, '', '', '', False, '', '', '', 'TRUE', '', '', '', False, '', '', '', False, '', '', '', False, '', '', '', False, '', '', '', False])
	wks.update("M3:AV178", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	# - - - - - - - - - - - - - - - - - - - - ABILITY PICKER - - - - - - - - - - - - - - - - - - - -
	current = "AbilityPicker"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	# noinspection SpellCheckingInspection
	filler = [
		['Archery', '', '', '', '', False],
		['Defense', '', '', '', '', False],
		['Dueling', '', '', '', '', False],
		['Great Weapon Fighting', '', '', '', '', False],
		['Protection', '', '', '', '', False],
		['Two-Weapon Fighting', '', '', '', '', False],
		['Blind Fighting', '', '', '', '', False],
		['Interception', '', '', '', '', False],
		['Superior Technique', '', '', '', '', False],
		['Thrown Weapon Fighting', '', '', '', '', False],
		['Unarmed Fighting', '', '', '', '', False],
		['Blessed Warrior', '', '', '', '', False],
		['Druidic Warrior', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		[],
		[],
		[],
		['Careful Spell', '', '', '', '', False],
		['Distant Spell', '', '', '', '', False],
		['Empowered Spell', '', '', '', '', False],
		['Extended Spell', '', '', '', '', False],
		['Heightened Spell', '', '', '', '', False],
		['Quickened Spell', '', '', '', '', False],
		['Seeking Spell', '', '', '', '', False],
		['Subtle Spell', '', '', '', '', False],
		['Transmuted Spell', '', '', '', '', False],
		['Twinned Spell', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		[],
		[],
		[],
		['Agonizing Blast', '', '', '', '', False],
		['Armor of Shadows', '', '', '', '', False],
		['Ascendant Step', '', '', '', '', False],
		['Aspect of the Moon', '', '', '', '', False],
		['Beast Speech', '', '', '', '', False],
		['Beguiling Influence', '', '', '', '', False],
		['Bewitching Whispers', '', '', '', '', False],
		['Bond of the Talisman', '', '', '', '', False],
		['Book of Ancient Secrets', '', '', '', '', False],
		['Chains of Carceri', '', '', '', '', False],
		['Cloak of Flies', '', '', '', '', False],
		["Devil's Sight", '', '', '', '', False],
		['Dreadful Word', '', '', '', '', False],
		['Eldritch Mind', '', '', '', '', False],
		['Eldritch Sight', '', '', '', '', False],
		['Eldritch Smite', '', '', '', '', False],
		['Eldritch Spear', '', '', '', '', False],
		['Eyes of the Rune Keeper', '', '', '', '', False],
		['Far Scribe', '', '', '', '', False],
		['Fiendish Vigor', '', '', '', '', False],
		['Gaze of Two Minds', '', '', '', '', False],
		['Ghostly Gaze', '', '', '', '', False],
		['Gift of the Depths', '', '', '', '', False],
		['Gift of the Ever-Living Ones', '', '', '', '', False],
		['Gift of Protectors', '', '', '', '', False],
		['Grasp of Hadar', '', '', '', '', False],
		['Improved Pact Weapon', '', '', '', '', False],
		['Investment of the Chain Master', '', '', '', '', False],
		['Lance of Lethargy', '', '', '', '', False],
		['Lifedrinker', '', '', '', '', False],
		['Maddening Hex', '', '', '', '', False],
		['Mask of Many Faces', '', '', '', '', False],
		['Master of Myriad Forms', '', '', '', '', False],
		['Minions of Chaos', '', '', '', '', False],
		['Mire the Mind', '', '', '', '', False],
		['Misty Visions', '', '', '', '', False],
		['One with Shadows', '', '', '', '', False],
		['Otherwordly Leap', '', '', '', '', False],
		['Protection of the Talisman', '', '', '', '', False],
		['Rebuke of the Talisman', '', '', '', '', False],
		['Relentless Hex', '', '', '', '', False],
		['Repelling Blast', '', '', '', '', False],
		['Sculptor of Flex', '', '', '', '', False],
		['Shroud of Shadow', '', '', '', '', False],
		['Sign of Ill Omen', '', '', '', '', False],
		['Thief of Five Fates', '', '', '', '', False],
		['Thirsting Blade', '', '', '', '', False],
		['Tomb of Levistus', '', '', '', '', False],
		["Trickster's Escape", '', '', '', '', False],
		['Undying Servitude', '', '', '', '', False],
		['Visions of Distant Realms', '', '', '', '', False],
		['Voice of the Chain Master', '', '', '', '', False],
		['Whispers of the Grave', '', '', '', '', False],
		['Witch Sight', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False],
		['[empty]', '', '', '', '', False]
	]
	wks.update("B4:G104", filler)
	wks.update("AU2", False)
	wks.update("AU24", False)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 3, sent))
	await asyncio.sleep(timer)
	wks.update("AU41", False)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	# - - - - - - - - - - - - - - - - - - - - COMPANION - - - - - - - - - - - - - - - - - - - -
	current = "Companion"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	wks.update("F2", '')
	wks.update("H9:AL10", [[10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10, '', '', '', '', 10]])
	filler = [
		['Use PC profs', '', '', '', False],
		[],
		['AUTO', '', '', '', '', None, '', 'AUTO'],
		['AUTO', '', '', '', '', None, '', 'AUTO'],
		['AUTO', '', '', '', '', None, '', 'AUTO'],
		['AUTO', '', '', '', '', None, '', 'AUTO'],
		['AUTO', '', '', '', '', None, '', 'AUTO'],
		['AUTO', '', '', '', '', None, '', 'AUTO'],
		['AUTO', '', '', '', '', None, '', 'AUTO']
	]
	wks.update("I12:P20", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 4, sent))
	await asyncio.sleep(timer)
	filler = [
		['', '', 'Add Prof', '', '', False],
		['', '', 'Add Dex', '', '', False],
		['', '', 'Dex Limit', '', '', '- -'],
		['13', '', 'Temp Add', '', '', '0']
	]
	wks.update("V12:AA16", filler)
	wks.update("T19:Z20", [[0, '', None, '', None, '', 'd6'], [None, '', '', '', '', '', 0]])
	filler = [
		[''],
		['', '', '', '', '', '', 0, '', '', 0],
		[],
		[''],
		[],
		['', '', '', '', '', '', 'Manual Health Base', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', 'Class Level Scaling', '', '', '', '', '', '', '', '- -'],
		['', '', '', '', '', '', 'Constitution Mod / level', '', '', '', '', '', '', '', False],
		['', '', '', '', '', '', 'Proficiency / level', '', '', '', '', '', '', '', False],
		['', '', '', '', '', '', 'Add Manual per Level', '', '', '', '', '', '', '', ''],
		['Forced', '', '', '', '', '', 'Add Manual Once', '', '', '', '', '', '', '', '']
	]
	wks.update("AD13:AR23", filler)
	# noinspection SpellCheckingInspection
	filler = [
		['Blinded', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'DEX', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', '', '', 'Health Setup'],
		['Charmed', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'WIS', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO'],
		['Deafened', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'INT', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Resistance / Immunity'],
		['Stunned', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'STR', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Name', '', '', '', 'Manual', '', '', 'Reset', '', False, 'Against'],
		['Frightened', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'CHA', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'All', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Grappled', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'INT', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'All Physical', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Incapacitated', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'WIS', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Piercing', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Paralyzed', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'CHA', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Bludgeoning', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Petrified', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'INT', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Slashing', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Poisoned', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'WIS', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Acid', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Prone', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'INT', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Fire', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Restrained', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'WIS', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Necrotic', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Unconcious', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'CHA', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Poison', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Invisible', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'CHA', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Cold', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['[custom]', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'INT', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Radiant', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['[custom]', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'DEX', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Force', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['[custom]', '', '', '', '', False, 'AUTO', '', '', '', '', None, '', '', '', '', '', 'DEX', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Thunder', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Reset', '', '', '', False, '', 'Adv/Immu', '', '', '', '', None, '', '', '', '', '', 'WIS', '', None, '', 'AUTO', '', '', '', '', None, '', 'AUTO', '', '', '', 'Lightning', '', '', '', '- -', '', '', '', '', '', 'Any'],
		['Exhaustion', '', '', '', '', '', '', 0, '', '', '', '', '', '', 'Reset', '', '', False, '', '', 'Use PC profs', '', '', '', '', False, '', '', '', '', '', '', 'Psychic', '', '', '', '- -', '', '', '', '', '', 'Any']
	]
	wks.update("B24:AR42", filler)
	# noinspection SpellCheckingInspection
	filler = [
		['', '', '', '', '', '', '', '', '', '', '', 'Perception', '', '', '', '', '', None, '', '', '', 'Darkvision', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', 'Investigation', '', '', '', '', '', None, '', '', '', 'Blindsight', '', '', '', '', '', '', '', '', 0, '', '', 'ft', '', 0, '', None, '', '', '', 0],
		['', '', '', '', '', '', '', '', '', '', '', 'Insight', '', '', '', '', '', None, '', '', '', 'Tremorsense', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', 'Stealth', '', '', '', '', '', None, '', '', '', 'Truesight', '', '', '', '', '', '', '', '', None, '', '', '', '', 0, '', None, '', '', '', 0]
	]
	wks.update("B45:AQ48", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
	await asyncio.sleep(timer)
	filler = [
		['Name', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', '+1', '', False, '', None, '', '', False],
		['Type', '', '', '', '', '', '', '', '', 'Prof', '', False, '', '', 'CHA', '', False, '', 'forced?', '', '', False],
		['Style', '', '', '', '', '', '', '', '', 'Thrown', '', '', '', False, 'Hit', '', '', '', None, '', 'AUTO'],
		['Reach', '', '', '', '', '', '', 'Range', '', '', '', '', '', '', None, '', '', ''],
		[None, '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Ammo', '', '', '', '', '', -1, '', False],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Loaded', '', '', ''],
		['Property Descriptions', '', '', '', '', '', '', '', '', '', 'Short', '', '', True],
		[None, '', '', '', '', '', '', '', '', '', '', '', '', '', '']
	]
	wks.update("B51:X60", filler)
	wks.update("B63:X72", filler)
	wks.update("Z51:AV60", filler)
	wks.update("Z63:AV72", filler)
	filler = [
		['Name', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Name', '', '', '', ''],
		['Description', '', '', '', 'Source', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Description', '', '', '', 'Source', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
		['Current', '', '', '', '', '', '', 'Maximum', '', '', '', '', '', '', 'Recharge', '', '', '', '', '', '', '', '', '', 'Current', '', '', '', '', '', '', 'Maximum', '', '', '', '', '', '', 'Recharge', '', '', '', ''],
		[],
		['Name', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Name', '', '', '', ''],
		['Description', '', '', '', 'Source', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Description', '', '', '', 'Source', '', '', '', ''],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
		['Current', '', '', '', '', '', '', 'Maximum', '', '', '', '', '', '', 'Recharge', '', '', '', '', '', '', '', '', '', 'Current', '', '', '', '', '', '', 'Maximum', '', '', '', '', '', '', 'Recharge', '', '', '', ''],
		[],
		[],
		[],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', ''],
		['', '', '', '', '', '', '']
	]
	wks.update("B74:AR99", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))
	await asyncio.sleep(timer)
	filler = [
		['Character Size', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Name', '', '', 'Arrow', '', '', 'Bolt', '', '', 'Bullet', '', '', '', False, '', False, '', False],
		['Medium', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Manual', '', '', 0, '', '', 0, '', '', 0],
		['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', 'Found', '', '', None, '', '', None, '', '', None, '', '', '', False, '', False, '', False],
		[],
		[False, '', '', '', '', '', 'Extra Carry Capacity', '', '', '', '', '', '', '']
	]
	wks.update("J102:AU106", filler)
	temp = ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', True, '', '']
	filler = []
	for i in range(31):
		filler.append(temp)
	wks.update("B111:AQ141", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 2, sent))
	# - - - - - - - - - - - - - - - - - - - - SPELLBOOK - - - - - - - - - - - - - - - - - - - -
	current = "Spellbook"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	wks.update("I3", False)
	filler = [
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', '']
	]
	wks.update("B7:D128", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 2, sent))
	await asyncio.sleep(timer)
	filler = [
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[],
		[],
		[],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', ''],
		[False, '', '']
	]
	wks.update("Z4:AB128", filler)
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 1, sent))
	# - - - - - - - - - - - - - - - - - - - - SPELLSEARCH - - - - - - - - - - - - - - - - - - - -
	current = "SpellSearch"
	print(sheet + ": " + current)
	wks = sh.worksheet(current)
	wks.update("AG3:AL5", [['', 'Use Filter', '', '', '', False], [False, 'B. Action', '', '', '', False], [False, 'Other', '', '', '', False]])
	wks.update("AH7:AH13", [['- -'], ['- -'], ['- -'], [], ['- -'], ['- -'], ['- -']])
	wks.update("F5:F15", [[False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False]])
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 3, sent))
	await asyncio.sleep(timer)
	wks.update("L5:L13", [[False], [False], [False], [False], [False], [False], [False], [False], [False]])
	wks.update("R5:R17", [[False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False]])
	wks.update("W5:W16", [[False], [False], [False], [], [], [False], [False], [False], [False], [False], [False], [False]])
	wks.update("AB5:AB18", [[False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False], [False]])
	wks.update("B20", '')
	asyncio.create_task(t.clear_progress(player, sheet, progress, start_time, current, 5, sent))

	text = f"Your new sheet is ready adventurer, best of luck out there!\n{sheet}\n<{link}>"
	await t.send_dm(ctx, text, False, player.id)
	if dm:
		text = f"One of your players got a new sheet, here is the access link:\n{sheet}\n<{link}>"
		await t.send_dm(ctx, text, False, dm.id)
	await interaction.followup.send("Done.")
	print("- - - - - - - - done - - - - - - - -")


pass
