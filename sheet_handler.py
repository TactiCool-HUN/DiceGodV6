import settings as s
import classes as c
import math
import re


def get_skill(sheet_inc, skill_inc: str):
	sh = sheet_inc.google_sheet
	wks = sh.worksheet("BotRead")
	skills = wks.get("A8:D26")
	class_area = wks.get("A2:D5")

	add = 0
	adv = None
	minmax_type = None
	minmax_size = None
	prof = False
	pre_send = None

	for line in skills:
		while len(line) < 4:
			line.append("")

		if line[0].lower() == skill_inc:
			add = int(line[1])
			adv = line[2].lower()
			if adv == "fail":
				pre_send = "WARNING!\nThe skill check is set to \"FAIL\" the roll will still happen in case you need it."
			prof = line[3]
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
	pre_send = None

	for line in saves:
		while len(line) < 4:
			line.append("")

		if line[0] == looking_for:
			add = int(line[1])
			adv = line[2].lower()
			if adv == "fail":
				pre_send = "WARNING!\nThe skill check is set to \"FAIL\" the roll will still happen in case you need it."
			break

	if looking_for == "deathsave":
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

		temp = re.findall('extra \([0-9]+d[0-9]+ *[a-z]*\)', properties)  # extra damage
		if temp:
			temp = re.findall("[0-9]+d[0-9]+", temp[0])[0]
			dmg_type = re.findall("\[[a-z]+]", temp)[0]
			followups.append(c.Followup(s.DAMAGE_TYPES.get(dmg_type), f"{temp}[{dmg_type}]", "roll"))

	for feat in feats:
		if feat[0] == "Polearm Master" and int(feat[1]):
			temp_add = int(line[7])
			followups.append(c.Followup("🪄", f"1d4+{temp_add}[bludgeoning]", "roll"))
			break

	rogue_level = 0
	blood_level = 0
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

	return add, adv, followups


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
	pre_send = None

	for line in skills:
		while len(line) < 4:
			line.append("")

		if skill_inc[1:] in line[0].lower():
			while len(line) < 16:
				line.append("")

			add = int(line[8])
			adv = line[15].lower()
			if adv == "fail":
				pre_send = "WARNING!\nThe skill check is set to \"FAIL\" the roll will still happen in case you need it."
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
	pre_send = None

	for line in saves:
		while len(line) < 13:
			line.append("")

		if line[0].lower()[:3] == looking_for:
			add = int(line[5])
			adv = line[12].lower()
			if adv == "fail":
				pre_send = "WARNING!\nThe skill check is set to \"FAIL\" the roll will still happen in case you need it."
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
		slot = int(attack_inc[3])+6

	# noinspection SpellCheckingInspection
	followups.append(c.Followup("👋", f"cdmg{slot-6}", "roll"))
	# noinspection SpellCheckingInspection
	followups.append(c.Followup("\U0001F450", f"cdmg{slot-6}_2h", "roll"))

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
		temp = re.findall('flexible \([0-9]+d[0-9]+\)', properties)  # flexible attack
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

		temp = re.findall('extra \([0-9]+d[0-9]+ *[a-z]*\)', properties)  # extra damage
		if temp:
			temp = re.findall("[0-9]+d[0-9]+", temp[0])[0]
			dmg_type = re.findall("\[[a-z]+]", temp)[0]
			followups.append(c.Followup(s.DAMAGE_TYPES.get(dmg_type), f"{temp}[{dmg_type}]", "roll"))

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
		slot = int(dmg[3])+6

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

	return add


pass
