import discord

from utils.bot_setup import bot


def translate_to_symbols(text: str) -> str:
	# noinspection GrazieInspection, SpellCheckingInspection
	"""
	Translates written text into a glyphic abc made by u/Karn_the_friendly
	:param text: any english text + characters of: . , : ! ?
	:return:
	"""

	# here I'm using dictionaries as dictionaries (for letters)
	left = {
		'a': bot.get_emoji(1241830292545863885),
		'b': bot.get_emoji(1241830283989487727),
		'c': bot.get_emoji(1241830275496022056),
		'd': bot.get_emoji(1241830263768744026),
		'e': bot.get_emoji(1241830250766274623),
		'f': bot.get_emoji(1241830229333377165),
		'g': bot.get_emoji(1241830215404224622),
		'h': bot.get_emoji(1241830206503911495),
		'i': bot.get_emoji(1241830198425555045),
		'j': bot.get_emoji(1241830189789347931),
		'k': bot.get_emoji(1241830180893491280),
		'l': bot.get_emoji(1241830168796860546),
		'm': bot.get_emoji(1241830153743761599),
		'n': bot.get_emoji(1241829128873705623),
		'o': bot.get_emoji(1241814777228165173),
		'p': bot.get_emoji(1241814763714121769),
		'q': bot.get_emoji(1241814747738013756),
		'r': bot.get_emoji(1241814728926429235),
		's': bot.get_emoji(1241814698450620466),
		't': bot.get_emoji(1241814684814938293),
		'u': bot.get_emoji(1241814670981988404),
		'v': bot.get_emoji(1241814657090457672),
		'w': bot.get_emoji(1241814642402263152),
		'x': bot.get_emoji(1241814629307650148),
		'y': bot.get_emoji(1241814613910229054),
		'z': bot.get_emoji(1241814594541060237),
		' ': bot.get_emoji(1241838668206047375),
		'A': bot.get_emoji(1241867016537636934),
		'B': bot.get_emoji(1241867009902514216),
		'C': bot.get_emoji(1241867003417854002),
		'D': bot.get_emoji(1241866996950499368),
		'E': bot.get_emoji(1241866990285623369),
		'F': bot.get_emoji(1241866983750762567),
		'G': bot.get_emoji(1241866977438470144),
		'H': bot.get_emoji(1241866970794692618),
		'I': bot.get_emoji(1241866964499038269),
		'J': bot.get_emoji(1241866958077427722),
		'K': bot.get_emoji(1241866950125162658),
		'L': bot.get_emoji(1241866940172075178),
		'M': bot.get_emoji(1241866929925263410),
		'N': bot.get_emoji(1241866923336011776),
		'O': bot.get_emoji(1241866915484405811),
		'P': bot.get_emoji(1241866908932903013),
		'Q': bot.get_emoji(1241866902574334044),
		'R': bot.get_emoji(1241866896404512869),
		'S': bot.get_emoji(1241866889857077380),
		'T': bot.get_emoji(1241866883175813151),
		'U': bot.get_emoji(1241866876934684693),
		'V': bot.get_emoji(1241866868944277627),
		'W': bot.get_emoji(1241866861449052325),
		'X': bot.get_emoji(1241866686991171756),
		'Y': bot.get_emoji(1241866679693082645),
		'Z': bot.get_emoji(1241866668976771223),
		':': bot.get_emoji(1241880673216626839),
		'?': bot.get_emoji(1241880665918537789),
		'!': bot.get_emoji(1241880658754928700),
		'.': bot.get_emoji(1241880650978426920),
		',': bot.get_emoji(1241880637024112791),
	}

	right = {
		'a': bot.get_emoji(1241836618785230888),
		'b': bot.get_emoji(1241836611121971220),
		'c': bot.get_emoji(1241836562740678656),
		'd': bot.get_emoji(1241836554775695460),
		'e': bot.get_emoji(1241836548232581221),
		'f': bot.get_emoji(1241836541656170556),
		'g': bot.get_emoji(1241836534563340308),
		'h': bot.get_emoji(1241836527365914717),
		'i': bot.get_emoji(1241836519975555233),
		'j': bot.get_emoji(1241836512782581894),
		'k': bot.get_emoji(1241836500224839700),
		'l': bot.get_emoji(1241836493270552746),
		'm': bot.get_emoji(1241836485565743215),
		'n': bot.get_emoji(1241836479081086977),
		'o': bot.get_emoji(1241836471069966377),
		'p': bot.get_emoji(1241836464384250010),
		'q': bot.get_emoji(1241836457090351165),
		'r': bot.get_emoji(1241836450069352581),
		's': bot.get_emoji(1241836443412992100),
		't': bot.get_emoji(1241836436454637668),
		'u': bot.get_emoji(1241836429001228318),
		'v': bot.get_emoji(1241836421657137152),
		'w': bot.get_emoji(1241836414354587750),
		'x': bot.get_emoji(1241836408029577257),
		'y': bot.get_emoji(1241836399834173472),
		'z': bot.get_emoji(1241836388752556123),
		' ': bot.get_emoji(1241838626837495971),
		'A': bot.get_emoji(1241868147741688025),
		'B': bot.get_emoji(1241868141428998185),
		'C': bot.get_emoji(1241868135410171987),
		'D': bot.get_emoji(1241868129320304843),
		'E': bot.get_emoji(1241868123313803315),
		'F': bot.get_emoji(1241868116905037947),
		'G': bot.get_emoji(1241868036852420648),
		'H': bot.get_emoji(1241868028996751441),
		'I': bot.get_emoji(1241868022654701651),
		'J': bot.get_emoji(1241868015499350036),
		'K': bot.get_emoji(1241868008385679422),
		'L': bot.get_emoji(1241868002366849106),
		'M': bot.get_emoji(1241867995895169127),
		'N': bot.get_emoji(1241867988714520719),
		'O': bot.get_emoji(1241867981919617096),
		'P': bot.get_emoji(1241867974625984574),
		'Q': bot.get_emoji(1241867967873159219),
		'R': bot.get_emoji(1241867958024933377),
		'S': bot.get_emoji(1241867949594382347),
		'T': bot.get_emoji(1241867942929633361),
		'U': bot.get_emoji(1241867935966826506),
		'V': bot.get_emoji(1241867927934734479),
		'W': bot.get_emoji(1241867920943087619),
		'X': bot.get_emoji(1241867913523101748),
		'Y': bot.get_emoji(1241867905298206730),
		'Z': bot.get_emoji(1241867892803240047),
		':': bot.get_emoji(1241882103612833953),
		'?': bot.get_emoji(1241882097329901728),
		'!': bot.get_emoji(1241882091495624776),
		'.': bot.get_emoji(1241882085161959424),
		',': bot.get_emoji(1241882078631694437),
	}

	output_full = []
	words = text.split(' ')
	num_of_words = len(words)
	# this part first applies the dictionary
	# words have a line either on their left or right side which we need to keep track of
	for i, word in enumerate(words):
		output_word = []
		for letter in word:
			if i % 2:
				tmp = left.get(letter, False)
			else:
				tmp = right.get(letter, False)

			if tmp:
				tmp: discord.Emoji
				output_word.append(str(tmp))
			else:
				raise ValueError(f'translate_to_symbols() only take english characters and -->[ : ? ! . , ]<-- , character: >{letter}< is not within them')
		output_full.append(output_word)

	"""
	Now we have this:
	[|h, |e, |l, |l, |o],
	[w|, o|, r|, l|, d|],
	[|o, |n, |e],


	But need this:
	[|o, w|, |h],
	[|n, o|, |e],
	[|e, r|, |l],
	[|-, l|, |l],
	[|-, d|, |o],
	so we'll transpose it (not technically transpose more like rotate but eh...)
	"""

	longest_word_len: int = len(max(output_full, key = len))
	transposed = [[] for _ in range(longest_word_len)]  # just creates the empty lines
	for j, word in enumerate(reversed(output_full)):
		for i, letter in enumerate(word):  # puts the letters into the spaces
			transposed[i].append(letter)
		for i in range(len(word), longest_word_len):  # fills up the rest with empty
			if (j + num_of_words) % 2:
				transposed[i].append(str(right[' ']))
			else:
				transposed[i].append(str(left[' ']))

	transposed = [''.join(line) for line in transposed]  # put it back together
	return '\n'.join(transposed)


emoji_to_letter = {
	'1079': 'a',
	'1591': 'b',
	'2025': 'c',
	'2800': 'd',
	'3099': 'e',
	'3146': 'f',
	'3882': 'g',
	'3936': 'h',
	'3937': 'i',
	'4621': 'j',
	'5203': 'k',
	'5511': 'l',
	'5525': 'm',
	'5863': 'n',
	'6035': 'o',
	'6127': 'p',
	'6334': 'q',
	'6543': 'r',
	'7805': 's',
	'7896': 't',
	'7952': 'u',
	'8365': 'v',
	'8712': 'w',
	'8875': 'x',
	'8905': 'y',
	'9292': 'z',
	'1081': 'a',
	'1156': 'b',
	'1463': 'c',
	'1845': 'd',
	'2204': 'e',
	'2321': 'f',
	'2486': 'g',
	'4898': 'h',
	'4987': 'i',
	'5522': 'j',
	'5663': 'k',
	'6210': 'l',
	'6239': 'm',
	'6459': 'n',
	'6684': 'o',
	'7634': 'p',
	'7949': 'q',
	'8805': 'r',
	'8919': 's',
	'8939': 't',
	'8982': 'u',
	'9355': 'v',
	'9431': 'w',
	'9433': 'x',
	'9808': 'y',
	'9820': 'z',
	'1204': 'A',
	'1637': 'B',
	'2134': 'C',
	'2823': 'D',
	'3002': 'E',
	'3127': 'F',
	'3250': 'G',
	'3989': 'H',
	'4441': 'I',
	'5311': 'J',
	'5604': 'K',
	'5800': 'L',
	'5871': 'M',
	'6161': 'N',
	'6204': 'O',
	'6404': 'P',
	'6522': 'Q',
	'6969': 'R',
	'7194': 'S',
	'7246': 'T',
	'7976': 'U',
	'8008': 'V',
	'8415': 'W',
	'9461': 'X',
	'9567': 'Y',
	'9933': 'Z',
	'1042': 'A',
	'1311': 'B',
	'1521': 'C',
	'2226': 'D',
	'2569': 'E',
	'2619': 'F',
	'3211': 'G',
	'3225': 'H',
	'3234': 'I',
	'3306': 'J',
	'3483': 'K',
	'5207': 'L',
	'5299': 'M',
	'5459': 'N',
	'6027': 'O',
	'6622': 'P',
	'6724': 'Q',
	'7157': 'R',
	'8003': 'S',
	'8265': 'T',
	'8856': 'U',
	'9061': 'V',
	'9432': 'W',
	'9518': 'X',
	'9530': 'Y',
	'9840': 'Z',
	'3137': ':',
	'4614': '?',
	'6546': '!',
	'7646': '.',
	'8765': ',',
	'3138': ':',
	'4615': '?',
	'6547': '!',
	'7649': '.',
	'8764': ',',
}


def translate_to_text(text: str) -> str:
	"""
	Translates from a glyphic abc made by u/Karn_the_friendly into written text (reverse operation for translate_to_symbols())
	:param text: a bunch of emojis after each other that DiceGod generated with --cypher
	:return: hopefully proper english
	"""
	# this first line turns '<:2800:12><:9808:39><:1591:27>\n<:6210:46><:5511:47><:6239:15>'
	# into [['2800', '9808', '1591'], ['1079', '6684', '5511']]
	text = [[y.split(':')[0] for y in x[2:-1].split('><:')] for x in text.split('\n')]

	num_of_words: int = len(text[0])
	output = [[] for _ in range(num_of_words)]  # creates the empty matrix
	for line in text:
		for i in range(num_of_words):
			if line[i] not in ['0000', '9999']:
				output[num_of_words - i - 1].append(emoji_to_letter[line[i]])  # fills it up while rotating it

	output = [''.join(x) for x in output]  # put it back together as a string
	return ' '.join(output)


pass
