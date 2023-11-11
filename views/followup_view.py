import discord.ext
from utils.bot_setup import bot
import commands as com
import utils.tools as t
import utils.settings as s
import asyncio


class MessageCore:
	def __init__(self, identifier: discord.Interaction | discord.ext.commands.Context):
		self.identifier = identifier
		self.person = t.c.Person(identifier)
		self.queue = False
		self.crit = False


class FollowupButton(discord.ui.Button):
	def __init__(self, emoji, data, f_type, label = None, style: discord.ButtonStyle = discord.ButtonStyle.blurple, incremental = False):
		temp = bot.get_emoji(emoji)
		if temp:
			super().__init__(emoji = temp, style = style, label = label)
		else:
			super().__init__(emoji = emoji, style = style, label = label)
		# noinspection PyTypeChecker
		self.core: MessageCore = None
		self.data = data
		self.f_type = f_type
		self.q_counter = 0
		self.og_label = self.label
		self.incremental = incremental

	async def callback(self, interaction: discord.Interaction):
		if self.view.myself is None:
			self.view.myself = interaction.message

		if self.core.person.user.id != interaction.user.id and interaction.user.id not in s.ADMINS:
			# noinspection SpellCheckingInspection
			await t.send_message(interaction, text = "Sush!", ephemeral = True)
			return

		match self.f_type:
			case "reroll":
				asyncio.create_task(com.roll_command(self.core.identifier, self.data, crit = False))
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
					asyncio.create_task(com.roll_command(self.core.identifier, self.data, crit = self.core.crit))
			case "roll_negative":
				pass
			case "queue":
				if self.core.queue:
					roll_txt = []
					self.core.queue = False
					await interaction.response.defer()
					self.style = discord.ButtonStyle.grey
					self.label = "off"
					for button in self.view.children:
						button: FollowupButton
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
					asyncio.create_task(com.roll_command(self.core.identifier, "+".join(roll_txt), crit = self.core.crit))
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
					self.style = discord.ButtonStyle.red
					await interaction.message.edit(view = self.view)
				else:
					self.label = "off"
					self.style = discord.ButtonStyle.grey
					await interaction.message.edit(view = self.view)
			case "heal_hurt":
				await interaction.response.defer()
				asyncio.create_task(com.hp_command(self.core.identifier, self.data[0], self.data[1]))
				await interaction.message.delete()
			case "rest":
				await interaction.response.defer()
				sent = await t.load(self.core.identifier)
				asyncio.create_task(com.rest_command(self.core.identifier, length = "long", sent = sent))
				await interaction.message.delete()
			case "spell":
				await interaction.response.defer()
				asyncio.create_task(t.send_message(self.core.identifier, embed = self.data.create_embed(), reply = True, followups = self.data.followups))
				await interaction.message.delete()
			case "cast":
				await interaction.response.defer()
				sent = await t.load(self.core.identifier)
				await interaction.message.delete()
				asyncio.create_task(com.cast_command(self.core.identifier, self.data[0], sent, self.data[1], True))
			case "disable":
				await interaction.response.defer()
				if self.data:
					await t.send_message(self.core.identifier, text = self.data)
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
				text = com.sh.change_inspiration(self.core.identifier, "add", 1)
				await t.send_message(self.core.identifier, text = text)
				self.disabled = True
				await interaction.message.edit(view = self.view)
			case "conditions":
				await interaction.response.defer()
				for button in self.view.children:
					button.disabled = True
				await interaction.message.edit(view = self.view)
				for condition in self.data:
					reply = await com.sh.set_condition(self.core.identifier, condition[0], condition[1], None)
					if reply:
						await t.send_message(self.core.identifier, text = reply, reply = True)
			case "coin":
				await interaction.response.defer()
				response_list = [
					f"{self.core.person.user.display_name} flipped a coin and it landed on... it's side?", 1,
					f"{self.core.person.user.display_name} flipped a coin and it landed on **heads**!", 49,
					f"{self.core.person.user.display_name} flipped a coin and it landed on **tails**!", 51
				]
				await t.send_message(self.core.identifier, text = t.choice(response_list))
				if self.data:
					await t.send_message(self.core.identifier, text = self.data)
				for button in self.view.children:
					button.disabled = True
				await interaction.message.edit(view = self.view)
			case "confirm_temphp":
				await interaction.response.defer()
				for button in self.view.children:
					button.disabled = True
				await interaction.message.edit(view = self.view)
				txt, _ = await com.sh.set_temp(self.core.identifier, self.data[0], True, self.data[1])
				await t.send_message(self.core.identifier, text = txt, reply = True)


class FollowupView(discord.ui.View):
	def __init__(self, identifier: discord.Interaction | discord.ext.commands.Context):
		super().__init__(timeout = 2 * 24 * 60 * 60)  # 2 days timeout
		self.message_core = MessageCore(identifier = identifier)
		self.myself = None

	def add_item(self, item: FollowupButton):
		item.core = self.message_core
		super().add_item(item)

	async def on_timeout(self) -> None:
		for button in self.children:
			button.disabled = True
		await self.myself.edit(view = self)


pass
