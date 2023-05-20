import classes as c
import discord.ext
import roller as r
import tools as t
import asyncio


async def roll_command(ctx, text):
	if text[:4] == "hurt" or text[:4] == "heal":
		raise NotImplemented
	elif text[:4] == "rest":
		raise NotImplemented
	else:
		loader = await t.load(ctx, f"-roll {text}")
		try:
			pack_maker = await asyncio.to_thread(r.text_to_pack, ctx, text)
			pack = await pack_maker
			await loader.delete()
			pack.send_pack()
		except Exception as e:
			try:
				await loader.delete()
			except discord.ext.commands.errors.MessageNotFound:
				pass
			raise Exception(e)


async def pc_command(ctx, command, char_name, sheet_name, interaction = None):
	person = c.Person(ctx)



pass
