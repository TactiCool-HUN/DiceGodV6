import discord
from utils.bot_setup import bot
import commands as com
import utils.tools as t
import utils.settings as s
import asyncio
import re


class MessageCore:
	def __init__(self, message: discord.Message):
		self.user_message: discord.Message = message
		self.person = t.c.Person(message)
		self.queue = False
		self.crit = False


class FollowupButton(discord.ui.Button):
	def __init__(self, emoji, data, f_type, label = None, style: discord.ButtonStyle = discord.ButtonStyle.blurple, incremental = False):
		temp = bot.get_emoji(emoji)
		if temp:
			super().__init__(emoji = temp, style = style, label = label)
		else:
			super().__init__(emoji = emoji, style = style, label = label)
		self.core: MessageCore = None
		self.data = data
		self.f_type = f_type
		self.q_counter = 0
		self.og_label = self.label
		self.incremental = incremental

	async def callback(self, interaction: discord.Interaction):
		if self.core.person.user != interaction.user or self.core.person.user.id not in s.ADMINS:
			# noinspection SpellCheckingInspection
			await interaction.response.send_message("Sush!", ephemeral = True)
			return

		match self.f_type:
			case "reroll":
				asyncio.create_task(com.roll_command(self.core.user_message, self.data, crit = False))
				await interaction.response.defer()
			case "roll":
				if self.core.queue:
					if self.q_counter:
						self.q_counter += 1
						self.label = f"{self.og_label}[x{self.q_counter}]"
					else:
						self.q_counter += 1
						self.label = f"{self.og_label}[x{self.q_counter}]"
					await interaction.message.edit(view = self.view)
					await interaction.response.defer()
				else:
					await interaction.response.defer()
					asyncio.create_task(com.roll_command(self.core.user_message, self.data, crit = self.core.crit))
			case "queue":
				if self.core.queue:
					roll_txt = []
					self.core.queue = False
					await interaction.response.defer()
					self.style = discord.ButtonStyle.grey
					self.label = "off"
					for button in self.view.children:
						if button.q_counter == 0:
							continue
						if button.incremental:
							ind = button.data.index("d")
							temp = int(button.data[:ind])
							roll_txt.append(f"{temp * button.q_counter}{button.data[ind:]}")
						else:
							for _ in range(button.q_counter):
								roll_txt.append(button.data)
						button.label = button.og_label
						button.q_counter = 0
					await interaction.message.edit(view = self.view)
					asyncio.create_task(com.roll_command(self.core.user_message, "+".join(roll_txt), crit = self.core.crit))
				else:
					self.core.queue = True
					await interaction.response.defer()
					self.style = discord.ButtonStyle.green
					self.label = "on"
					await interaction.message.edit(view = self.view)
			case "crit":
				self.core.crit = not self.core.crit
				await interaction.response.defer()
				if self.core.crit:
					self.label = "on"
					await interaction.message.edit(view = self.view)
					# await interaction.response.send_message(f"Emoji rolls are critical for this roll!", ephemeral = True)
				else:
					self.label = "off"
					await interaction.message.edit(view = self.view)
					# await interaction.response.send_message(f"Emoji rolls are __not__ critical for this roll!", ephemeral = True)
			case "heal_hurt":
				await interaction.response.defer()
				asyncio.create_task(com.hp_command(self.core.user_message, self.data[0], self.data[1]))
				await interaction.message.delete()
			case "rest":
				await interaction.response.defer()
				sent = await t.load(self.core.user_message)
				asyncio.create_task(com.rest_command(self.core.user_message, length = "long", sent = sent))
				await interaction.message.delete()
			case "spell":
				await interaction.response.defer()
				asyncio.create_task(t.send_message(self.core.user_message, self.data.create_embed(), embed = True, reply = True, followups = self.data.followups))
				await interaction.message.delete()
			case "cast":
				await interaction.response.defer()
				sent = await t.load(self.core.user_message)
				await interaction.message.delete()
				asyncio.create_task(com.cast_command(self.core.user_message, self.data[0], sent, None, self.data[1], True))
			case "disable":
				await interaction.response.defer()
				if self.data:
					await t.send_message(self.core.user_message, self.data)
				for button in self.view.children:
					button.disabled = True
				await interaction.message.edit(view = self.view)
			case "delete_message":
				await interaction.response.defer()
				if self.data:
					try:
						await self.data.delete()
					except discord.errors.NotFound:
						pass
				await interaction.message.delete()
			case "add_inspiration":
				await interaction.response.defer()
				text = com.sh.change_inspiration(self.core.user_message, "add", 1)
				await t.send_message(self.core.user_message, text)
				self.disabled = True
				await interaction.message.edit(view = self.view)
			case "conditions":
				await interaction.response.defer()
				for button in self.view.children:
					button.disabled = True
				await interaction.message.edit(view = self.view)
				for condition in self.data:
					reply = await com.sh.set_condition(self.core.user_message, condition[0], condition[1], None)
					if reply:
						await t.send_message(self.core.user_message, reply, reply = True)
			case "coin":
				await interaction.response.defer()
				response_list = [
					f"{self.core.person.user.display_name} flipped a coin and it landed on... it's side?", 1,
					f"{self.core.person.user.display_name} flipped a coin and it landed on **heads**!", 49,
					f"{self.core.person.user.display_name} flipped a coin and it landed on **tails**!", 51
				]
				await t.send_message(self.core.user_message, t.choice(response_list))
				if self.data:
					await t.send_message(self.core.user_message, self.data)
				for button in self.view.children:
					button.disabled = True
				await interaction.message.edit(view = self.view)
			case "confirm_temphp":
				await interaction.response.defer()
				for button in self.view.children:
					button.disabled = True
				await interaction.message.edit(view = self.view)
				txt, _ = await com.sh.set_temp(self.core.user_message, self.data[0], True, self.data[1])
				await t.send_message(self.core.user_message, txt, reply = True)


class FollowupView(discord.ui.View):
	def __init__(self, message: discord.Message):
		super().__init__(timeout = 300)
		self.message_core = MessageCore(message = message)

	def add_item(self, item: FollowupButton):
		item.core = self.message_core
		super().add_item(item)


pass
