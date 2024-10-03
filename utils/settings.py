LOAD_1 = "`` - L O A D I N G - ``"
LOAD_2 = "``. . . LOADING . . .``"

LOADERS = [
	LOAD_1, 1,
	LOAD_2, 1
]

SKILLS = ["init", "acrobatics", "animal", "arcana", "athletics", "deception", "history", "insight", "intimidation", "investigation", "medicine", "nature", "perception", "performance", "persuasion", "religion", "sleight", "stealth", "survival"]
PROF = ["prof", "exp"]
# noinspection SpellCheckingInspection
SAVES = ["strsave", "dexsave", "consave", "concsave", "intsave", "wissave", "chasave", "7thsave", "deathsave"]
ATTACKS = ["hit1", "hit2", "hit3", "hit4", "hit5", "hit6", "hvy1", "hvy2", "hvy3", "hvy4", "hvy5", "hvy6", "hit", "hvy"]
SPELL_ATTACK = ["spell3", "spell2", "spell1", "spell"]
SPELL_MOD = ["spellmod3", "spellmod2", "spellmod1", "spellmod"]
DAMAGE = ["dmg1_1h", "dmg2_1h", "dmg3_1h", "dmg4_1h", "dmg5_1h", "dmg6_1h", "dmg1_2h", "dmg2_2h", "dmg3_2h", "dmg4_2h", "dmg5_2h", "dmg6_2h", "dmg1", "dmg2", "dmg3", "dmg4", "dmg5", "dmg6", "dmg_1h", "dmg_2h", "dmg"]

C_SKILLS = ["c" + i for i in SKILLS]
C_SAVES = ["c" + i for i in SAVES]
C_ATTACKS = ["chit1", "chit2", "chit3", "chit4", "chit"]
# noinspection SpellCheckingInspection
C_DAMAGE = ["cdmg1_1h", "cdmg2_1h", "cdmg3_1h", "cdmg4_1h", "cdmg1_2h", "cdmg2_2h", "cdmg3_2h", "cdmg4_2h", "cdmg1", "cdmg2", "cdmg3", "cdmg4", "cdmg_1h", "cdmg_2h", "cdmg"]

ABILITIES = ["str", "dex", "con", "int", "wis", "cha", "7th"]

SHEET_ROLLS = SKILLS + PROF + SAVES + ATTACKS + SPELL_ATTACK + SPELL_MOD + DAMAGE + C_SKILLS + C_SAVES + C_ATTACKS + C_DAMAGE + ABILITIES

DAMAGE_TYPES = {
	"piercing": "🗡️",
	"bludgeoning": "🔨",
	"slashing": "🪓",
	"acid": "🧪",
	"fire": "🔥",
	"necrotic": "💀",
	"poison": "🐍",
	"cold": "❄️",
	"radiant": "☀️",
	"force": "☄️",
	"thunder": "🔊",
	"lightning": "⚡",
	"psychic": "🧠",
	"healing": "❤️‍🩹"
}

# noinspection SpellCheckingInspection
EMOJIS = ["✨", "❤️", "💖", "💜", "🐸", "<:idek:694605001502228540>", "<:zorablush:1021403403768844308>", "<:UwU:959931778905276456>", "<:Kyrihihihi:1058348961523576872>", "<:point:951578243415302235>", "<:diebish:694527515921743883>"]

SPELL_SCHOOL_ICONS = {"Abjuration": "https://media-waterdeep.cursecdn.com/attachments/2/707/abjuration.png", "Conjuration": "https://media-waterdeep.cursecdn.com/attachments/2/708/conjuration.png", "Divination": "https://media-waterdeep.cursecdn.com/attachments/2/709/divination.png", "Enchantment": "https://media-waterdeep.cursecdn.com/attachments/2/702/enchantment.png", "Evocation": "https://media-waterdeep.cursecdn.com/attachments/2/703/evocation.png", "Illusion": "https://media-waterdeep.cursecdn.com/attachments/2/704/illusion.png", "Necromancy": "https://media-waterdeep.cursecdn.com/attachments/2/720/necromancy.png", "Transmutation": "https://media-waterdeep.cursecdn.com/attachments/2/722/transmutation.png"}
SPELL_SCHOOL_COLORS = {"Abjuration": 0x8ccafb, "Conjuration": 0xf3bf59, "Divination": 0xadc7d6, "Enchantment": 0xf299d9, "Evocation": 0xe17b65, "Illusion": 0xcfa4fd, "Necromancy": 0xbaf48e, "Transmutation": 0xcb9863}

LETTERS = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "aa", "ab", "ac", "ad", "ae", "af", "ag", "ah", "ai", "aj", "ak", "al", "am", "an", "ao", "ap", "aq", "ar", "as", "at", "au", "av", "aw"]
REACTION_NUMBERS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
ALT_REACTION_NUMBERS = ['<:one_red:966321422949564426>', '<:two_red:966321444487307324>', '<:three_red:966321458685030421>', '<:four_red:966321473960677438>', '<:five_red:966321493027979336>', '<:six_red:966321513135497336>', '<:seven_red:966321535294009374>', '<:eight_red:966321551991509032>', '<:nine_red:966321567401406514>']

ADMINS = [282869456664002581]
BAN_LIST = [145980699961196544, 145978284201476099]
VERSION_CONTROL = "50005"

DICE_OVERRIDE = [False, -1, ""]
