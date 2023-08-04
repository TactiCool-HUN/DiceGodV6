from discord import RawReactionActionEvent, Role, Message
from utils.bot_setup import bot
from utils.database_handler import DatabaseConnection
import re
import utils.tools as t


class EmojiRole:
	def __init__(self, emoji_role_raw):
		self.emoji_role_id: int = emoji_role_raw[0]
		self.guild_id: int = emoji_role_raw[1]
		self.channel_id: int = emoji_role_raw[2]
		self.message_id: int = emoji_role_raw[3]
		self.emoji: str = emoji_role_raw[4]
		self.role_id: int = emoji_role_raw[5]

		if self.emoji[0] == "<" and self.emoji[-1] == ">":
			temp = re.split(":", self.emoji[1:-1])
			self.emoji_name = temp[1]
			self.emoji_id = int(temp[2])
		else:
			self.emoji_name = ""
			self.emoji_id = 0


async def emoji_role_command(reaction: RawReactionActionEvent):
	with DatabaseConnection("emoji_role.db") as connection:
		cursor = connection.cursor()
		cursor.execute("SELECT * FROM emoji_role WHERE guild_id = ?", (reaction.guild_id,))
		raw = cursor.fetchall()

	if not raw:
		return "empty"
	else:
		for temp in raw:
			temp = EmojiRole(temp)
			if temp.channel_id == reaction.channel_id and temp.message_id == reaction.message_id:
				if temp.emoji == reaction.emoji.name:
					break
				elif temp.emoji_id == reaction.emoji.id:
					break
		else:
			return "empty"

		role: Role = bot.get_guild(temp.guild_id).get_role(temp.role_id)
		user = reaction.member
		for role_ in user.roles:
			if role_.id == temp.role_id:
				await user.remove_roles(role)
				await t.send_message(user, text = f"You no longer have the ``{role.name}`` role.\nReason: you removed it yourself.")
				break
		else:
			await user.add_roles(role)
			await t.send_message(user, text = f"You now have the ``{role.name}`` role.\nReason: you added it yourself.")

		channel = await user.guild.fetch_channel(temp.channel_id)
		message: Message = await channel.fetch_message(temp.message_id)
		await message.remove_reaction(temp.emoji, user)


pass
