import asyncio
from datetime import datetime, date, timedelta
from utils.database_handler import DatabaseConnection
import discord
from classes import Person
from utils.bot_setup import bot
import utils.tools as t


async def trigger_reminder(reminder_id: int, guild: int, channel: int, message: int, remind_date: datetime, discord_id: int, text: str):
	person = Person(discord_id = discord_id)
	message: discord.Message = await bot.get_guild(guild).get_channel(channel).fetch_message(message)

	delta = datetime.now() - remind_date
	await asyncio.sleep(delta.total_seconds())

	await t.send_message(message, f"Hey {person.user.mention}, your reminder is here:\n{text}", reply = True, silent = False)

	with DatabaseConnection("reminders.db") as connection:
		cursor = connection.cursor()
		cursor.execute(
			'DELETE * FROM remind_date WHERE id = ?', (reminder_id,)
		)


async def reminder_checker():
	while True:
		with DatabaseConnection("reminders.db") as connection:
			cursor = connection.cursor()
			cursor.execute(
				'SELECT * FROM remind_date'
			)
			raw = cursor.fetchall()

		if not raw:
			await asyncio.sleep(60)

		for reminder in raw:
			reminder = list(reminder)
			reminder[4]: datetime = datetime.strptime(reminder[4], '%Y/%m/%d, %H:%M:%S')
			if reminder[4] < datetime.now() + timedelta(seconds = 90):
				# noinspection PyAsyncCall
				asyncio.create_task(trigger_reminder(*reminder))

		await asyncio.sleep(60)


def add_reminder(amount: int, timescale: str, sent: discord.Message, person: Person) -> datetime:
	now = datetime.now()
	future: datetime

	match timescale:
		case "minutes":
			future = now + timedelta(minutes = amount)
		case "hours":
			future = now + timedelta(hours = amount)
		case "days":
			future = now + timedelta(days = amount)
		case "weeks":
			future = now + timedelta(weeks = amount)
		case "months":
			future = now
			yrs = amount // 12
			amount = amount % 12
			if future.month + amount > 12:
				yrs = yrs + 1
				amount = amount + future.month - 12

			try:
				future = future.replace(year = future.year + yrs)
			except ValueError:  # if the date doesn't exist in the next year (feb 29) than it does it a day later
				future = future + (date(future.year + yrs, 1, 1) - date(future.year, 1, 1))

			future = future.replace(month = future.month + amount)
		case "years":
			future = now
			try:
				future = future.replace(year = future.year + amount)
			except ValueError:  # if the date doesn't exist in the next year (feb 29) than it does it a day later
				future = future + (date(future.year + amount, 1, 1) - date(future.year, 1, 1))
		case _:
			raise AssertionError

	with DatabaseConnection("reminders.db") as connection:
		cursor = connection.cursor()
		cursor.execute(
			'INSERT INTO remind_date('
			'guild_id,'
			'channel_id,'
			'message_id,'
			'date,'
			'discord_id'
			') VALUES (?, ?, ?, ?, ?)',
			(
				sent.guild.id,
				sent.channel.id,
				sent.id,
				future.strftime('%Y/%m/%d, %H:%M:%S'),
				person.user.id
			)
		)

	return future
