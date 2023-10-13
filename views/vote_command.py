import utils.tools as t
import classes as c
import discord.ext
import re
from ast import literal_eval


async def vote_command(identifier: discord.Interaction | discord.ext.commands.Context, text_dump_):
	text_dump = text_dump_.split("\n")
	index_1 = None
	index_2 = None

	for i, line in enumerate(text_dump):
		if line == "---" and index_1 is None:
			index_1 = i
		elif line == "---":
			index_2 = i
			break

	voting_options = text_dump[:index_1]
	vote_text = text_dump[index_1 + 1:index_2]

	vote = Vote(t.identifier_to_member(identifier), vote_text = "\n".join(vote_text))

	match len(voting_options):
		case 1:
			if "type: " in voting_options[0]:
				vote_type = re.findall("[0-9]+", voting_options[0])
				if vote_type:
					vote.vote_amount = int(vote_type[0])
			else:
				temp = voting_options[0].replace(" ", "")
				temp = re.split("><@", temp[9:-1])
				for element in temp:
					if element[0] == "&":
						roles = identifier.guild.roles
						members = []
						for role in roles:
							if role.id == int(element[1:]):
								members = role.members
								break
						for member in members:
							vote.voters.append(member.id)
					else:
						vote.voters.append(int(element))
		case 2:
			temp = voting_options[0].replace(" ", "")
			temp = re.split("><@", temp[9:-1])
			for element in temp:
				if element[0] == "&":
					roles = identifier.guild.roles
					members = []
					for role in roles:
						if role.id == int(element[1:]):
							members = role.members
							break
					for member in members:
						vote.voters.append(member.id)
				else:
					vote.voters.append(int(element))

			vote_type = re.findall("[0-9]+", voting_options[1])
			if vote_type:
				vote.vote_amount = int(vote_type[0])

	poll_options = text_dump[index_2 + 1:]
	for i, line in enumerate(poll_options):
		option = PollOption()
		temp = line.find("-")
		option.emoji = line[:temp].replace(" ", "")
		line_text = line[temp + 1:]
		if line_text[0] == " ":
			line_text = line_text[1:]
		option.option_text = line_text
		vote.poll_options.append(option)

	embed = vote.create_embed()

	if isinstance(identifier, discord.Interaction):
		await identifier.followup.send_message(embed = embed, view = VoteView(vote))
	else:
		await identifier.send(embed = embed, view = VoteView(vote))
	await identifier.message.delete()


class PollOption:
	def __init__(self):
		self.emoji: str = ""
		self.option_text: str = ""
		self.voters: list[int] = []


class Vote:
	def __init__(self, original_author, vote_amount = 0, vote_text = ""):
		self.original_author: discord.User = original_author
		self.voters: list[int] = []
		self.vote_amount: int = vote_amount
		self.poll_options: list[PollOption] = []
		self.vote_text: str = vote_text
		self.warning_sent: bool = False

	def get_vote_amount(self, user_id: int):
		amount = 0
		for option in self.poll_options:
			if user_id in option.voters:
				amount += 1

		return amount

	def create_embed(self) -> (discord.Embed, bool):
		everyone_voted = False
		person = c.Person(discord_id = self.original_author.id)
		embed = discord.Embed(
			title = f"Vote by {person.user.display_name}",
			description = self.vote_text,
			color = literal_eval(person.color)
		)

		for option in self.poll_options:
			if option.voters:
				temp = t.mention_texts(option.voters)
			else:
				temp = "None"

			embed.add_field(name = f"{option.emoji} - {option.option_text}", value = temp, inline = False)

		no_votes_ppl = self.voters[:]
		for option in self.poll_options:
			for being in option.voters:
				try:
					no_votes_ppl.remove(being)
				except ValueError:
					pass
		if no_votes_ppl:
			temp = t.mention_texts(no_votes_ppl)
		else:
			temp = "None"
			everyone_voted = True
		if not self.voters == []:
			embed.add_field(name = "No Vote", value = temp, inline = False)
		embed.set_author(name = person.user.display_name, icon_url = person.user.avatar.url)
		if self.vote_amount == 0:
			temp = "You may pick any number of options."
		else:
			temp = f"You may pick {self.vote_amount} of options."
		embed.set_footer(text = temp)

		return embed, everyone_voted


class VoteButton(discord.ui.Button):
	def __init__(self, vote: Vote, emoji = None, style = discord.ButtonStyle.blurple):
		super().__init__(emoji = emoji, style = style)
		self.vote: Vote = vote
		for index, option in enumerate(self.vote.poll_options):
			if option.emoji == f"<:{self.emoji.name}:{self.emoji.id}>" or option.emoji == self.emoji.name:
				self.poll_index = index
				break
		else:
			raise ValueError

	async def callback(self, interaction: discord.Interaction):
		warning = False
		if interaction.user.id in self.vote.voters or self.vote.voters == []:  # if person can vote
			if interaction.user.id in self.vote.poll_options[self.poll_index].voters:  # if person has no vote
				self.vote.poll_options[self.poll_index].voters.remove(interaction.user.id)
				embed, warning = self.vote.create_embed()
				await interaction.response.edit_message(embed = embed)
			else:
				if self.vote.vote_amount > 0:  # if there is vote limit
					if self.vote.get_vote_amount(interaction.user.id) >= self.vote.vote_amount:  # if they have too many votes
						await t.send_message(interaction, text = "You have too many votes here.", ephemeral = True)
					else:
						self.vote.poll_options[self.poll_index].voters.append(interaction.user.id)
						embed, warning = self.vote.create_embed()
						await interaction.response.edit_message(embed = embed)
				else:
					self.vote.poll_options[self.poll_index].voters.append(interaction.user.id)
					embed, warning = self.vote.create_embed()
					await interaction.response.edit_message(embed = embed)
		else:
			await t.send_message(interaction, text = "You cannot vote here.", ephemeral = True)

		if warning and not self.vote.warning_sent:
			self.vote.warning_sent = True
			await t.send_message(self.vote.original_author, f"Everyone voted on the vote you posted in {interaction.channel.name}!")


class VoteView(discord.ui.View):
	def __init__(self, vote: Vote):
		super().__init__(timeout = 7 * 24 * 60 * 60)  # 7 days
		for option in vote.poll_options:
			button = VoteButton(vote, emoji = option.emoji, style = discord.ButtonStyle.blurple)

			self.add_item(button)


pass
