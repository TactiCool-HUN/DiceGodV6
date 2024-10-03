import sheet_handler as sh
import classes as c
import utils.tools as t
import datetime
import gspread
import random
import re
import discord.ext

sa = gspread.service_account(filename = "data_holder/service_account.json")


async def text_to_pack(identifier: discord.Interaction | discord.ext.commands.Context, roll_txt, crit = False):
	if isinstance(roll_txt, str):
		roll_txt = roll_txt.replace(" ", "").lower()
	else:
		roll_txt = str(roll_txt)
	single_rolls = await text_to_singles(identifier, roll_txt)
	for i, roll in enumerate(single_rolls):
		if crit:
			roll.args.crit = True
		single_rolls[i] = random_roller(identifier, roll)

	return c.Pack(identifier, single_rolls, roll_txt)


async def text_to_singles(identifier: discord.Interaction | discord.ext.commands.Context, roll_txt: str) -> list[c.SingleRoll]:
	single_rolls = []

	if roll_txt[:9] == "flexible:":
		roll_txt = roll_txt[9:]
		flexible_warning = True
	else:
		flexible_warning = False

	if not re.findall("[+-]", roll_txt[0]):
		roll_txt = f"+{roll_txt}"

	splits_raw = re.findall("[+-][^+-]+", roll_txt)
	current_single = None
	extra_die = []
	sheet = None

	for split in splits_raw:
		if re.findall("[+-][0-9]+d[0-9]+[^+-]*", split):  # - - - - - vanilla roll - - - - -
			if current_single:
				single_rolls.append(current_single)
			current_single = c.SingleRoll(split, "vanilla roll")
		elif re.findall("[+-][0-9]+[^+-]*", split) and split[1:3] != "7t":  # - - - - - vanilla add - - - - -
			if current_single:
				current_single.add_vanilla_add(split)
			else:
				current_single = c.SingleRoll(split, "vanilla add")
		elif t.is_sheet_based(split[1:]):  # - - - - - sheet based - - - - -
			sheet_type, split_cut, args = t.is_sheet_based(split[1:])
			if not sheet:
				sheet = c.Sheet(identifier)
				sheet.get_sheet(sa)

			match sheet_type:
				case "SKILLS":
					if current_single:
						single_rolls.append(current_single)
					add, adv, minmax_type, minmax_size, pre_send, speciality = sh.get_skill(sheet, split_cut)
					current_single = c.SingleRoll(split, "dynamic roll", split_cut, 1, 20, add, True, pre_send)
					current_single.args.merge_args(f"{adv}{minmax_type}{minmax_size}")
					current_single.speciality = speciality
				case "PROF":
					if split_cut == "prof":
						multiplier = 1
					else:
						multiplier = 2

					add = sh.get_prof(sheet)

					if current_single:
						current_single.add += add * multiplier
						current_single.dynamic = True
						if not current_single.name:
							current_single.name = split_cut
					else:
						current_single = c.SingleRoll(split, "dynamic add", split_cut, add = add * multiplier)
				case "SAVES":
					if current_single:
						single_rolls.append(current_single)
					add, adv, pre_send, speciality, extra_die = sh.get_save(sheet, split_cut)
					current_single = c.SingleRoll(split, "dynamic roll", split_cut, 1, 20, add, True, pre_send)
					current_single.args.merge_args(adv)
					current_single.speciality = speciality
				case "ATTACKS":
					if current_single:
						single_rolls.append(current_single)
					add, adv, followups, extra_die, elven = sh.get_attack(sheet, split_cut)
					current_single = c.SingleRoll(split, "dynamic roll", split_cut, 1, 20, add, True, followups = followups)
					current_single.args.merge_args(adv)
					current_single.args.elven = elven
				case "DAMAGE":
					if current_single:
						single_rolls.append(current_single)
					temp, extra_crit_dice = sh.get_damage(sheet, split_cut)
					damage_singles = await text_to_singles(identifier, temp)
					for single in damage_singles:
						single.args.merge_args(args)
						single.dynamic = True
						single.name = split_cut
						single.extra_crit_dice = extra_crit_dice
					single_rolls = single_rolls + damage_singles
					current_single = None
				case "C_SKILLS":
					if current_single:
						single_rolls.append(current_single)
					add, adv, pre_send = sh.get_c_skill(sheet, split_cut)
					current_single = c.SingleRoll(split, "dynamic roll", split_cut, 1, 20, add, True, pre_send)
					current_single.args.merge_args(adv)
				case "C_SAVES":
					if current_single:
						single_rolls.append(current_single)
					add, adv, pre_send = sh.get_c_save(sheet, split_cut)
					current_single = c.SingleRoll(split, "dynamic roll", split_cut, 1, 20, add, True, pre_send)
					current_single.args.merge_args(adv)
				case "C_ATTACKS":
					if current_single:
						single_rolls.append(current_single)
					add, adv, followups = sh.get_c_attack(sheet, split_cut)
					current_single = c.SingleRoll(split, "dynamic roll", split_cut, 1, 20, add, True, followups = followups)
					current_single.args.merge_args(adv)
				case "C_DAMAGE":
					if current_single:
						single_rolls.append(current_single)
					temp = sh.get_c_damage(sheet, split_cut)
					damage_singles = await text_to_singles(identifier, temp)
					for single in damage_singles:
						single.args.merge_args(args)
						single.dynamic = True
						single.name = split_cut
						single_rolls.append(single)
					current_single = None
				case "SPELL_ATTACK":
					if current_single:
						single_rolls.append(current_single)
					add, adv, extra_die = sh.get_spell_attack(sheet, split_cut)
					current_single = c.SingleRoll(split, "dynamic roll", split_cut, 1, 20, add, True)
					current_single.args.merge_args(adv)
				case "SPELL_MOD":
					add = sh.get_spell_mod(sheet, split_cut)

					if current_single:
						current_single.add += add
						current_single.dynamic = True
						if not current_single.name:
							current_single.name = split_cut
					else:
						current_single = c.SingleRoll(split, "dynamic add", split_cut, add = add)
				case "ABILITIES":
					add = sh.get_ability_mod(sheet, split_cut)

					if current_single:
						current_single.add += add
						current_single.dynamic = True
						if not current_single.name:
							current_single.name = split_cut
					else:
						current_single = c.SingleRoll(split, "dynamic add", split_cut, add = add)

			try:
				current_single.args.merge_args(args)
			except AttributeError:
				pass
			try:
				damage_type = re.findall("\[[a-z]+]", args)[0]
				current_single.damage_type.append(damage_type[1:-1])
			except IndexError:
				pass
		elif t.is_die(split[1:]):  # - - - - - custom die - - - - -
			split_cut, args = t.is_die(split[1:])
			if current_single:
				single_rolls.append(current_single)
			die = c.Die(split_cut)
			die_rolls = await text_to_singles(identifier, die.roll)
			for roll in die_rolls:
				if not t.exists(roll.name, "die"):
					roll.name = die.name
				roll.args.merge_args(args)
				roll.dynamic = True
				roll.sign = t.sign_merger([roll.sign, split[0]])
				single_rolls.append(roll)
			current_single = None
		else:  # - - - - - spells - - - - -
			try:
				if not sheet:
					sheet = c.Sheet(identifier)
					sheet.get_sheet(sa)
			except IndexError:
				pass

			spell_out, found, remainder = await sh.get_spell(identifier, spell_inc = split[1:], sheet = sheet, exact_search = True)
			if found == "exact" and len(spell_out.followups) > 1:
				args = c.RollArgs(remainder)
				if args.spell_level:
					level = args.spell_level - int(spell_out.level[0]) + 1
				else:
					level = 1
				spell_rolls = await text_to_singles(identifier, spell_out.followups[level].data)
				for roll in spell_rolls:
					if not t.exists(roll.name, "die"):
						roll.name = spell_out.name
					roll.args.merge_args(remainder)
					roll.dynamic = True
					roll.sign = t.sign_merger([roll.sign, split[0]])
					single_rolls.append(roll)
				current_single = None
			else:
				raise ValueError("Either too many, or no spell match found.")

	if current_single:
		single_rolls.append(current_single)

	for die in extra_die:
		single_rolls += await text_to_singles(identifier, die)

	if flexible_warning:
		single_rolls[0].roll_note.append("Damage bonuses that solely apply to 1 or 2 handed attacks are NOT automatically added to Flexible damage rolls.")

	return single_rolls


def recurse_roller(amount: int, size: int, args: c.RollArgs) -> list[list[int, bool]]:
	results = []

	for _ in range(amount):
		roll_raw = random.randint(1, size)
		if args.minmax_type == "min":
			roll_raw = max(roll_raw, args.minmax_size)
		elif args.minmax_type == "max":
			roll_raw = min(roll_raw, args.minmax_size)

		if args.exploding and roll_raw == size:
			if size == 1:
				raise ValueError("No infinities, hmph.")
			results = results + [[roll_raw, True]] + recurse_roller(1, size, args)
		else:
			results = results + [[roll_raw, True]]

	if t.s.DICE_OVERRIDE[0]:
		results = [[t.s.DICE_OVERRIDE[1], True] for _ in results]

	return results


def random_roller(identifier: discord.Interaction | discord.ext.commands.Context, roll: c.SingleRoll):
	person = c.Person(identifier)
	args: c.RollArgs = roll.args
	pre_send = []

	if args.crit:
		amount = roll.dice_number * 2 + roll.extra_crit_dice
	else:
		amount = roll.dice_number

	if args.adv == "adv" and args.elven and roll.dice_number < 2:
		amount = 3
	elif (args.adv == "adv" or args.adv == "dis" or args.adv == "emp") and roll.dice_number == 1:
		amount = 2

	roll.results = []

	if amount > 250 or roll.die_size > 5000:
		amount = min(amount, 250)
		size = min(roll.die_size, 5000)
		pre_send.append("You madman...")
	else:
		size = roll.die_size

	my_date = datetime.date.today()
	if my_date.month == 4 and my_date.day == 1:
		for _ in range(amount):
			flip = random.randint(1, 2)
			if flip == 1:
				roll_raw = 1
			else:
				roll_raw = size
			if args.minmax_type == "min":
				roll_raw = max(roll_raw, args.minmax_size)
			elif args.minmax_type == "max":
				roll_raw = min(roll_raw, args.minmax_size)
			roll.results.append([roll_raw, True])
	else:  # ----- ----- ----- ----- actual random part ----- ----- ----- -----
		roll.results = roll.results + recurse_roller(amount, size, args)

	if args.keep_type:
		rolls_mid = [i[0] for i in roll.results]
		rolls_mid_sorted = sorted(rolls_mid, reverse = args.keep_type == "kh")
		top3 = rolls_mid_sorted[:args.keep_quantity]
		for e, x in enumerate(rolls_mid):
			if x in top3:
				roll.results[e][1] = True
				top3.remove(x)
			else:
				roll.results[e][1] = False

	match args.adv:
		case "adv":
			current = [0, 0]
			for i, result in enumerate(roll.results):
				if result[1] and result[0] > current[1]:
					current = [i, result[0]]
			for i, result in enumerate(roll.results):
				if i != current[0]:
					roll.results[i][1] = False
		case "dis":
			current = [0, roll.die_size + 1]
			for i, result in enumerate(roll.results):
				if result[1] and result[0] < current[1]:
					current = [i, result[0]]
			for i, result in enumerate(roll.results):
				if i != current[0]:
					roll.results[i][1] = False
		case "emp":
			midpoint = roll.die_size / 2
			current = [0, midpoint]
			for i, result in enumerate(roll.results):
				if result[1] and abs(midpoint - result[0]) > abs(midpoint - current[1]):
					current = [i, result[0]]
			for i, result in enumerate(roll.results):
				if i != current[0]:
					roll.results[i][1] = False

	if args.adv in ["adv", "dis"] and amount == 2:
		if (roll.results[0][0] == 1 and roll.results[1][0] == size) or (roll.results[0][0] == size and roll.results[1][0] == 1):
			pre_send.append("*Perfectly balanced as all things should be.*")
		elif roll.args.adv == "adv" and roll.results[0][0] == 1 and roll.results[1][0] == 1:
			random_things = [
				f"{random.randint(2, roll.die_size + 2)} chickens",
				f"{random.randint(2, roll.die_size + 2)} dice",
				f"{random.randint(2, roll.die_size + 2)} PCs",
				f"{random.randint(2, roll.die_size + 2)} pebbles",
				f"{random.randint(2, roll.die_size + 2)} fireflies",
				f"{random.randint(2, roll.die_size + 2)} liters of mayonnaise",
				f"your mom"
			]

			random1 = random_things.pop(random.randint(0, len(random_things) - 1))
			random2 = random_things.pop(random.randint(0, len(random_things) - 1))
			pre_send.append(f"Dayum, that's quite unlucky.\nMay I recommend sacrificing {random1} and {random2} by {random.randint(1, 12)}pm tomorrow?")
		elif roll.args.adv == "dis" and roll.results[0][0] == roll.die_size and roll.results[1][0] == roll.die_size:
			pre_send.append("Lady Luck smiles on you!")

	if size == 20 and roll.results[0][0] == 1 and roll.results[0][1] and person.user.id == 875753704685436938 and random.randint(1, 2) == 1:
		msg = t.choice([
			"lol", 3,
			"Well, no luck (take a guess who has it...)", 1,
			"Yep, Dani stole your luck again, sry...", 1
		])
		pre_send.append(msg)
	elif size == 20 and roll.results[0][0] == 20 and roll.results[0][1] and person.user.id == 875753704685436938 and random.randint(1, 2) == 1:
		if person.active == "Scorpio" and random.randint(1, 3) != 1:
			msg = t.choice([
				"Yria's amulet seem to be working?", 2,
				"WAIT!", 1
			])
		else:
			msg = t.choice([
				"Didn't think I'll live to see this day.", 1,
				"It's cheating to ask Dani to roll you nat20s.", 1,
				"And where did you steal this from?", 1
			])
		pre_send.append(msg)
	if size == 20 and roll.results[0][0] == 20 and person.user.id == 886672003396927530 and random.randint(1, 5) == 1:
		msg = f"Going around stealing Nika's luck again I see."
		pre_send.append(msg)
	elif size == 20 and roll.results[0][0] == 1 and person.user.id == 886672003396927530 and random.randint(1, 5) == 1:
		msg = f"Welcome to the other side!"
		pre_send.append(msg)
	if size == 20 and roll.dynamic:
		for item in roll.results:
			if (item[0] == 1 or item[0] == 20) and item[1]:
				roll.followups.append(c.FollowupButton("🍀", None, "add_inspiration", style=discord.ButtonStyle.green))

	if my_date.month == 4 and my_date.day == 1:
		pre_send = []

	if roll.full_result == 69:
		pre_send.append("Nice")

	if t.s.DICE_OVERRIDE[0]:
		pre_send.append(f"{t.s.DICE_OVERRIDE[2]}\n||This roll was predetermined by an Admin and is not actually random.||")

	roll.pre_send += pre_send
	roll.add_results(roll.results)
	t.s.DICE_OVERRIDE[0] = False
	return roll


pass
