LOAD_1 = [
	"`` | L O A D I N G | ``",
	"`` \\ L O A D I N G / ``",
	"`` - L O A D I N G - ``",
	"`` / L O A D I N G \\ ``"
]

LOAD_2 = [
	"``LOADING (●)``",
	"``LOADING (○)``"
]

LOAD_3 = [
	"``.LOADING.......``",
	"``..LOADING......``",
	"``...LOADING.....``",
	"``....LOADING....``",
	"``.....LOADING...``",
	"``......LOADING..``",
	"``.......LOADING.``",
	"``........LOADING``",
	"``.......LOADING.``",
	"``......LOADING..``",
	"``.....LOADING...``",
	"``....LOADING....``",
	"``...LOADING.....``",
	"``..LOADING......``",
	"``.LOADING.......``",
	"``LOADING........``"
]

LOADERS = [
	LOAD_1, 1,
	LOAD_2, 1,
	LOAD_3, 1
]

SKILLS = ["init", "acrobatics", "animal", "arcana", "athletics", "deception", "history", "insight", "intimidation", "investigation", "medicine", "nature", "perception", "performance", "persuasion", "religion", "sleight", "stealth", "survival"]
PROF = ["prof", "exp"]
# noinspection SpellCheckingInspection
SAVES = ["strsave", "dexsave", "consave", "concsave", "intsave", "wissave", "chasave", "7thsave", "deathsave"]
ATTACKS = ["hit1", "hit2", "hit3", "hit4", "hit5", "hit6", "hvy1", "hvy2", "hvy3", "hvy4", "hvy5", "hvy6", "hit", "hvy"]
SPELL = ["spell3", "spell2", "spell1", "spell"]
SPELL_MOD = ["spellmod3", "spellmod2", "spellmod1", "spellmod"]
DAMAGE = ["dmg1_1h", "dmg2_1h", "dmg3_1h", "dmg4_1h", "dmg5_1h", "dmg6_1h", "dmg1_2h", "dmg2_2h", "dmg3_2h", "dmg4_2h", "dmg5_2h", "dmg6_2h", "dmg1", "dmg2", "dmg3", "dmg4", "dmg5", "dmg6", "dmg_1h", "dmg_2h", "dmg"]

C_SKILLS = ["c" + i for i in SKILLS]
C_SAVES = ["c" + i for i in SAVES]
C_ATTACKS = ["c" + i for i in ATTACKS[:5]]
# noinspection SpellCheckingInspection
C_DAMAGE = ["cdmg1_1h", "cdmg2_1h", "cdmg3_1h", "cdmg4_1h", "cdmg1_2h", "cdmg2_2h", "cdmg3_2h", "cdmg4_2h", "cdmg1", "cdmg2", "cdmg3", "cdmg4", "cdmg_1h", "cdmg_2h", "cdmg"]

SHEET_ROLLS = SKILLS + SAVES + C_SKILLS + C_SAVES + ATTACKS + C_ATTACKS

ABILITIES = ["str", "dex", "con", "int", "wis", "cha", "7th"]

DAMAGE_TYPES = {
	"slashing": "🪓",
	"piercing": "🗡️",
	"bludgeoning": "🔨",
	"cold": "❄️",
	"poison": "🐍",
	"acid": "🧪",
	"psychic": "🧠",
	"fire": "🔥",
	"necrotic": "💀",
	"radiant": "☀️",
	"force": "☄️",
	"thunder": "🔊",
	"lightning": "⚡",
	"healing": "❤️‍🩹"
}
