from discord.ext import commands
import discord

prefix = "--"
intents = discord.Intents().all()
bot = commands.Bot(command_prefix = prefix, intents = intents)

bot.remove_command("help")

with open("warning.txt", "w") as f:
	f.write("Unknown Error has occurred, please log the time and notify Tacti!")