from discord.app_commands import Choice
from discord import app_commands
from bot_setup import bot
import commands as com
import classes as c
import tools as t
import discord
import asyncio
import random


@bot.event
async def on_ready():
	print(f"{bot.user.name.upper()} is online!")

	try:
		synced = await bot.tree.sync()
		print(f"Synced {len(synced)} command(s)")
	except Exception as e:
		print(e)


@bot.event
async def on_message(ctx):
	if ctx.author != bot.user:
		asyncio.create_task(bot.process_commands(ctx))


@bot.command(name = 'thing')
async def _thingy(ctx):
	sent = await t.load(ctx)
	await asyncio.sleep(10)
	await sent.delete()
	# await ctx.send(f"lmao", tts = True)


@bot.command(name = "ping")
async def ping_command(ctx):
	response_list = [
		"pong", 48,
		"ping", 1,
		"Yes, yes. I'm here, just let me brew another coffee...", 1
	]
	result = t.choice(response_list)
	if result == "ping":
		await t.send_message(ctx, result, reply = True)
		await asyncio.sleep(2)
		await t.send_message(ctx, "oh, wait no\npong!", reply = True)
	else:
		await t.send_message(ctx, result, reply = True)


@bot.command(name = "pong")
async def pong_command(ctx):
	response_list = [
		"ping", 49,
		"You wrote \"pong\" instead of \"ping\" and now you feel special don't you?", 1
	]
	result = t.choice(response_list)
	await t.send_message(ctx, result, reply = True)


@bot.command(name = 'emoji')
async def emoji_command(emoji):
	print(emoji.message.content)


@bot.command(name = "kill")
async def kill_command(ctx, *, other = None):
	print(f'{ctx.author} said "{other}", how rude...')
	# noinspection SpellCheckingInspection
	await ctx.message.add_reaction("<:angycat:817122720227524628>")
	# noinspection SpellCheckingInspection
	response_list = [
		"Don't be so rude...", 1,
		"ruuuuude", 1,
		"You accidentally mispelled the \"-die\" command.", 1,
		f"-die {ctx.author.mention}", 1,
		f"Quit it {ctx.author.mention}!", 1
	]
	result = t.choice(response_list)
	if result[0] == "-":
		sent = await t.send_message(ctx, result, reply = True, is_return = True)
		sent = await sent.reply("Contacting Pinkertons, please do not leave your current area. (○)")
		for i in range(20):
			if i % 2 == 0:
				await sent.edit(content = "Contacting Pinkertons, please do not leave your current area. (●)")
			else:
				await sent.edit(content = "Contacting Pinkertons, please do not leave your current area. (○)")
			await asyncio.sleep(1)
		await sent.edit(content = "Connection established: Publishing address.")
		await asyncio.sleep(5)
		await sent.edit(content = "Connection established: Requesting agent.")
		await asyncio.sleep(6)
		await sent.edit(content = "Connection established: Agent granted.\nStandby for annihilation.")
	else:
		await t.send_message(ctx, result, reply = True)


@bot.command(name = "roll", aliases=["r", "e"])
async def _roll_command_(ctx, *, text):
	await com.roll_command(ctx, text)


@bot.command(name = "yeet")
async def _yeet_command_(ctx, *, text):
	if random.randint(1, 50) == 1:
		text = "I saw that it went off the table but I can't find it anywhere, you gotta roll a new one, we'll find it after session."
		await t.send_message(ctx, text, reply = True)
	elif random.randint(1, 12) == 1:
		followups = [c.Followup("✅", text, "roll"), c.Followup("❎", None, "disable")]
		# noinspection SpellCheckingInspection
		message = "You yeeted the die of the table, does it still count?"
		await t.send_message(ctx, message, reply = True, followups = followups)
	else:
		await com.roll_command(ctx, text)


@bot.command(name = "pc", aliases=["char", "character"])
async def pc_old(ctx, command, char_name = None, sheet_name = None):
	await com.pc_command(ctx, command, char_name, sheet_name)


@bot.tree.command(name = "pc", description = "Connect your Google Sheet(tm) to Dice God. You can also use this command to set a created characters, update them to a new sheet, or delete them.")
@app_commands.choices(command=[
	app_commands.Choice(name = "create", value = "create"),
	app_commands.Choice(name = "set", value = "set"),
	app_commands.Choice(name = "update", value = "update"),
	app_commands.Choice(name = "clear", value = "clear"),
	app_commands.Choice(name = "delete", value = "delete")])
@discord.app_commands.describe(char_name = "Give Character Name")
@discord.app_commands.describe(sheet_name = "Give Exact Google Sheet Name")
async def pc_slash(interaction: discord.Interaction, command: Choice[str], char_name: str = None, sheet_name: str = None):
	ctx = await bot.get_context(interaction)
	await com.pc_command(ctx, command.value, char_name, sheet_name, interaction)


with open("token.txt", "r") as f:
	_lines_ = f.readlines()

TOKEN = _lines_[0].strip()

bot.run(TOKEN)
