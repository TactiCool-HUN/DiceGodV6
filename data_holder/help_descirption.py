# noinspection SpellCheckingInspection
help_list = [
	{
		"name": "ping",
		"call_type": "prefix",
		"calls": ["-ping", "-pong"],
		"short_description": "Pings the bot to see if it's online.",
		"long_description": "Pings the bot to see if it's online.",
		"example_uses": []
	},
	{
		"name": "roll",
		"call_type": "prefix",
		"calls": ["roll", "r", "e", "yeet"],
		"short_description": "Roll dice with the bot.",
		"long_description": """
A roll command consist of "roll"s or "add"s separated by either + or - signs.
A "roll" can be either static or sheet based.
- Static rolls are made up of a number of equal sized dice the following way: ``[number of dice]d[size of dice]``

- Sheet based rolls are from a set list of options that can be seen here (all sheet based rolls apply advantage and disadvantage by themselves if marked on the sheet):
- - ``init`` to roll initiative
- - ``[the first word of any skill-check]`` to roll a skill-check
- - ``[the first 3 letter of an ability score ("7th" for the last one)]save`` to trigger any saving throw,  ``concsave`` for concentration saves, or ``deathsave`` for death saving throws (which automatically applies successes and failures.
- - ``hit<a number between 1 and 5>`` to trigger your attack roll for said weapon slot leaving it empty triggers the 1st slot
- - ``hvy<a number between 1 and 5>`` as hit, but this subtracts your proficiency bonus from the roll while adding twice your proficiency to the damage.
- - ``dmg<a number between 1 and 5>`` to trigger your damage roll for said weapon slot leaving it empty triggers the 1st slot (it triggers the 1 handed if exists, if it doesn't it triggers the 2 handed damage)
- - ``dmg<a number between 1 and 5>_2h`` to trigger your 2 handed damage roll for said weapon slot leaving it empty triggers the 1st slot
- - ``spell<a number between 1 and 5>``to roll your spell attack roll, giving no number adds your first class's spellattack, 2 gives your 2nd class's, 3 gives the 3rd
- - ``[full or partial name of a spell]`` rolls the base level of the spell or auto scales cantrips to your active character


An "add" can be either static or sheet based.
- Static adds are just a basic number.

- Sheet based adds are a set list that can be seen here:
- - ``[the first 3 letter of an ability score ("7th" for the plus one)]`` for said ability's modifier
- - ``prof`` for proficiency bonus or ``exp`` for double your proficiency bonus
- - ``spellmod<a number between 1 and 5>`` to add your spell modifier, giving no number adds your first class's spellcasting modifier, 2 gives your 2nd class's, 3 gives the 3rd

Each "roll" can be argumented by using one or more of the following arguments:
- ``adv`` for advantage on the roll (aka keep the highest)
- ``dis`` for disadvantage on the roll (aka keep the lowest)
- ``emp`` it keeps the value farthest from the middle of the die size
- ``kh[number]`` to keep the highest x amount of rolls
- ``kl[number]`` to keep the lowest x amount of rolls
- ``min[number]`` the minimum each dice can roll
- ``max[number]`` the maximum each dice can roll
- ``crit`` to double the number of dice
- ``ex`` to make the die roll an "exploding" roll (does not work with adv, dis or emp).

Example of argumented rolls:
- ``-r 1d20adv``
- ``-r 3d10adv+dmg2_2hcrit``
- ``-r 3d20kh2dis``
If there are several arguments on a roll they'll be run in the following order: crit -> min/max -> kh/kl -> adv/dis/emp
The pairs in the previous line cannot be used together on a single roll.
If an argument is placed on an "add" it will affect the first "roll" on it's left.

You can use ``[number]x[rest of the roll text]`` to submit a roll several times and get organised but seperate results from it.
""",
		"example_uses": ["-r 1d20+5", "-r initadv+1d4", "-r 6x1d20adv+5"]
	},
	{
		"name": "coinflip",
		"call_type": "dynamic",
		"calls": ["-coin", "-coinflip", "/coinflip"],
		"short_description": "Flip a coin, see where it lands.",
		"long_description": "Flip a coin, see where it lands.",
		"example_uses": []
	},
	{
		"name": "character",
		"call_type": "dynamic",
		"calls": ["-pc", "-char", "-character", "/pc"],
		"short_description": "Connect your Google Sheet(tm) to Dice God. You can also: set, clear, update, or delete characters.",
		"long_description": """
Options:
- create:
- - Connect a new character's sheet.
- - Requires: char_name, sheet_name
- - Example: ``-pc create [character's name] [sheet's exact name]``

- update:
- - Update a character to use a new sheet.
- - Requires: char_name, sheet_name
- - Example: ``-pc update [character's name] [new sheet's exact name]``

- delete:
- - Delete a character you have.
- - Requires: char_name
- - Example: ``-pc delete [character's name]``

- set:
- - Set an existing character as your active character.
- - Requires: char_name
- - Example: ``-pc set [character's name]``

- clear:
- - Clear your active character.
- - Requires: -
- - Example: ``-pc clear``

- access:
- - Grant someone access to your character, they will be able to set the character and use sheet based commands.
- - Requires: char_name, person
- - Example: ```/pc command:access char_name:[character's name] person:[@ping of the person]```

- image:
- - Add an image to your character.
- - Requires: char_name, image_url
- - Example: ```/pc command:image char_name:[character's name] image_url:[url]```

- color:
- - Add a custom color for your character's rolls.
- - Requires: char_name, color (#000000 or 0x000000)
- - Example: ```/pc command:color char_name:[character's name] color:0x040053```
		""",
		"example_uses": []
	},
	{
		"name": "die",
		"call_type": "slash command",
		"calls": ["/die"],
		"short_description": "Create custom named dice, any complex roll. You can also: update, or delete already existing ones.",
		"long_description": """
Options:
- create:
- - Create a new custom die.
- - Requires: new_die_name, die_roll

- update:
- - Update your die with a new die roll or new name.
- - Requires: old_die_name
- - Optional: new_die_name, die_roll (requires at least one of these)

- delete:
- - Delete an existing die
- - Requires: old_die_name
		""",
		"example_uses": []
	},
	{
		"name": "settings",
		"call_type": "slash command",
		"calls": ["/settings"],
		"short_description": "Change your global settings for DiceGod, like name changing, roll tags, or chat ignore.",
		"long_description": """
Options:
- change_name:
- - While on whenever you set your character it will be displayed on your name. When you clear your character your name will be reset.

- auto_roll_tagging:
- - While your character is set your rolls will have a tag that is your character's name, allowing you to use the statistics command to filter it down to only the character's rolls.

- markov_chance:
- - Doesn't do anything rn sry :D

- chat_ignore:
- - While on Dice God will not react to your chat messages.

- color:
- - Sets the color next to your rolls, you must provide a hex code (either 0x123456, or #123456

- tag:
- - Manually set the tag for your rolls. "roll_auto_tagging" only overrides it on the next pc set or clear action.
		""",
		"example_uses": []
	},
	{
		"name": "condition",
		"call_type": "slash command",
		"calls": ["/condition"],
		"short_description": "Set exhaustion or conditions on your active character.",
		"long_description": "Set exhaustion or conditions on your active character.",
		"example_uses": []
	},
	{
		"name": "money_tracking",
		"call_type": "slash command",
		"calls": ["/money_tracking"],
		"short_description": "Add income or loss statements to your active character's Money Tracker.",
		"long_description": "Add income or loss statements to your active character's Money Tracker.",
		"example_uses": []
	},
	{
		"name": "spellpoint",
		"call_type": "slash command",
		"calls": ["/spellpoint"],
		"short_description": "Use, recover, or otherwise manipulate your spell points.",
		"long_description": "Use, recover, or otherwise manipulate your spell points.",
		"example_uses": []
	},
	{
		"name": "hurt / heal",
		"call_type": "prefix",
		"calls": ["-hurt", "-heal", "-healing"],
		"short_description": "You can damage or heal your active character.",
		"long_description": "You can write anything after the hurt or heal that you could use with a roll command, and the outcome will be automatically applied.",
		"example_uses": ["-hurt 5+1d4-prof"]
	},
	{
		"name": "temp",
		"call_type": "prefix",
		"calls": ["-temp"],
		"short_description": "Set your active character's temporary hit points.",
		"long_description": "You can write anything after the temp that you could use with a roll command, and the outcome will be automatically applied if you have no temporary hit points, if you have them a prompt will ask if you want to change or not.",
		"example_uses": ["-temp 5+1d4-prof"]
	},
	{
		"name": "rest",
		"call_type": "hybrid",
		"calls": ["-rest", "/rest"],
		"short_description": "Perform a long- or shortrest with your active character.",
		"long_description": """
- On a short rest you can use your hitdice to heal. This can be done the following way: ``-rest short 6d8`` this function automatically adds your constitution modifier for each hit dice.
- This will display an error if you:
- - Try to use anything else than your available hit dice.
- - Try to use more hit dice than available.

- A longrest does the following:
- - Lowers your exhaustion by 1.
- - Resets your current and temporary health.
- - Resets extra hp where it applies.
- - Resets your companion's current and temporary hit points.
- - Regains the appropiate amount of hit dice.
- - Resets your limited use abilities if they reset on a longrest (or shorter).
- - Resets your spell slots.
- - Resets death saves.

- A shortrest does the following:
- - Resets temporary health.
- - Resets death saves.
- - Resets your limited use abilities if they reset on a shortrest (or shorter).
- - Heals (if applicable).
- - Some short rest based class abilities.
		""",
		"example_uses": ["-rest", "-rest short"]
	},
	{
		"name": "list",
		"call_type": "slash command",
		"calls": ["/list"],
		"short_description": "List out your characters, inventory, spells, or dice.",
		"long_description": "You can list out characters, inventory, spells, and dice (aka shinies). In case of listing inventory you can use \"based_on\" to specify an item type.",
		"example_uses": []
	},
	{
		"name": "spell",
		"call_type": "hybrid",
		"calls": ["-spell", "-s", "/spell"],
		"short_description": "Get the full description and properties of a spell.",
		"long_description": "Get the full description and properties of a spell.\nYou can enter partial or full spell name. In case several spells are found a list will be returned with their names.",
		"example_uses": ["-s cure Wo", "-s light"]
	},
	{
		"name": "cast",
		"call_type": "hybrid",
		"calls": ["-cast", "-c", "/cast"],
		"short_description": "Get the full description of the spell and cast it from your active characters slots or points.",
		"long_description": "Get the full description of the spell and cast it from your active characters slots or points.\nThe slot or point will be automatically subtracted",
		"example_uses": ["-c cure Wo", "-c light"]
	},
	{
		"name": "statistics",
		"call_type": "slash command",
		"calls": ["/statistics"],
		"short_description": "Display your or others roll statistics.",
		"long_description": """
Display your or others roll statistics.
If you ping a person their rolls will be displayed, it defaults to yourself.
If you input a tag only rolls with that tag will be displayed.
If you turn on get_all_rolls, than all rolls will be displayed regardless of who rolled it (tags still apply)
If you turn ephemeral to private the return will only visible to you.
		""",
		"example_uses": []
	},
	{
		"name": "transfer",
		"call_type": "slash command",
		"calls": ["/transfer"],
		"short_description": "Transfers parts of your sheet to a new version so you don't have to copy pasta manually.",
		"long_description": "Transfers parts of your sheet to a new version so you don't have to copy pasta manually.\nOld and new sheet names both need to be exact.",
		"example_uses": []
	},
	{
		"name": "sort_inventory",
		"call_type": "slash command",
		"calls": ["/sort_inventory"],
		"short_description": "Sorts the active character's Inventory.",
		"long_description": "Sorts the active character's Inventory based on whatever type you choose.",
		"example_uses": []
	},
	{
		"name": "vote",
		"call_type": "prefix",
		"calls": ["-vote"],
		"short_description": "Create a vote for people to use!",
		"long_description": """
You can create votes with the following formating:
```
-vote
voters: [ping the people seperated by spaces]
vote type: pick [number between 0 and infinite, people will be able to choose this many option, 0 = any]
---
Write the text of your vote here
---
Write vote options here, each should be in it's own line and each option should look like this:
:emoji: - vote option text
		""",
		"example_uses": [
			"""-vote
voters: @Drakkenheim @tacticool_
vote type: pick 1
---
Is drakkenheim great?
---
:one: - yes!
:two: - no :c```"""
		]
	},
	{
		"name": "table",
		"call_type": "slash command",
		"calls": ["/table"],
		"short_description": "Manage access and settings for your tables as a GM.",
		"long_description": """
Permission options:
- Add people as players
- Add people as guests
- Remove people from the table

Settings:
- Toggle automatic addition of guests to your threads
		""",
		"example_uses": []
	},
	{
		"name": "create_table",
		"call_type": "slash command",
		"calls": ["/create_table"],
		"short_description": "Create a new table for yourself.",
		"long_description": "Create a new table for yourself.",
		"example_uses": []
	},
	{
		"name": "titles",
		"call_type": "slash command",
		"calls": ["/titles"],
		"short_description": "Request to see your or other's titles.",
		"long_description": "Request to see your or other's titles.",
		"example_uses": []
	},
	{
		"name": "draw",
		"call_type": "prefix",
		"calls": ["-draw", "-d"],
		"short_description": "Draw from a deck.",
		"long_description": "Draw from a deck created by the deck command.",
		"example_uses": ["-d french", "-d d20"]
	},
	{
		"name": "shuffle",
		"call_type": "prefix",
		"calls": ["-reshuffle", "-shuffle"],
		"short_description": "Shuffle a deck.",
		"long_description": "Reshuffle a deck created by the deck command.",
		"example_uses": ["-shuffle french", "-reshuffle d20"]
	},
	{
		"name": "deck",
		"call_type": "slash command",
		"calls": ["/deck"],
		"short_description": "Create, edit or destroy decks.",
		"long_description": """
Create New Deck:
- Allows you to create a new deck.

Edit Existin Deck:
- Allows you to edit a deck you created.

Add Art to Deck:
- Doesn't do shit cus I'm lazy.

Delete Deck:
- Allows you to delete a deck you created.
		""",
		"example_uses": ["/deck"]
	},
	{
		"name": "veterancy",
		"call_type": "slash command",
		"calls": ["/veterancy"],
		"short_description": "Allows you to get the veterancy rank of a person.",
		"long_description": "Allows you to get the veterancy rank of a person.",
		"example_uses": ["/veterancy", "/veterancy <@person>"]
	},
	{
		"name": "request_presence",
		"call_type": "slash command",
		"calls": ["/request_presence"],
		"short_description": "Requests to be in the presence of your god.",
		"long_description": "Requests DiceGod to be in your voice channel.",
		"example_uses": ["/request_presence"]
	},
	{
		"name": "leave",
		"call_type": "slash command",
		"calls": ["/leave"],
		"short_description": "Requests permission to leave your god's side.",
		"long_description": " Due to Discord limitations this will look as if Dicegod is leaving the voice channel.",
		"example_uses": ["/leave"]
	},
	{
		"name": "help",
		"call_type": "slash command",
		"calls": ["/help"],
		"short_description": "Display the command list or the documentation of each command.",
		"long_description": "Display the command list or the documentation of each command.",
		"example_uses": []
	}
]
