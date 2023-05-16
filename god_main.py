from bot_setup import bot
import asyncio


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


with open("token.txt", "r") as f:
	_lines_ = f.readlines()

TOKEN = _lines_[0].strip()

bot.run(TOKEN)
