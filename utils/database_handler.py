import sqlite3


class DatabaseConnection:
	def __init__(self, host):
		self.connection = None
		self.host = f"data_holder/{host}"

	def __enter__(self):
		self.connection = sqlite3.connect(self.host)
		return self.connection

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.connection.commit()
		self.connection.close()


with DatabaseConnection("emoji_role.db") as connection:
	cursor = connection.cursor()

	# - - - emoji_role - - -
	try:
		cursor.execute(
			'CREATE TABLE emoji_role('
			'emoji_role_id integer primary key,'  # 0
			'guild_id integer,'  # 1
			'channel_id integer,'  # 2
			'message_id integer,'  # 3
			'emoji text,'  # 4
			'role_id integer)'  # 5
		)
	except sqlite3.OperationalError:
		print(f"emoji_roles found")

print("--------")

with DatabaseConnection("data.db") as connection:
	cursor = connection.cursor()

	# - - - people - - -
	try:
		cursor.execute(
			'CREATE TABLE people('
			'discord_id integer primary key,'
			'name text,'
			'active text,'
			'tag text,'
			'color text,'
			'change_name integer,'
			'auto_tag integer,'
			'markov_chance integer,'
			'chat_ignore integer,'
			'uwuify integer,'
			'tts_perms integer)'
		)
	except sqlite3.OperationalError:
		print(f"people found")

	# - - - dice - - -
	try:
		cursor.execute(
			'CREATE TABLE dice('
			'die_id integer primary key,'
			'name text,'
			'owner_id integer,'
			'roll text)'
		)
	except sqlite3.OperationalError:
		print(f"dice found")

	# - - - sheets - - -
	try:
		cursor.execute(
			'CREATE TABLE sheets('
			'sheet_id integer primary key,'
			'owner_id integer,'
			'character text,'
			'sheet text,'
			'char_image text,'
			'color text,'
			'last_warning timestamp)'
		)
	except sqlite3.OperationalError:
		print(f"sheets found")

	# - - - sheet rents - - -
	try:
		cursor.execute(
			'CREATE TABLE sheet_rents('
			'rent_id integer primary key,'
			'owner_id integer,'
			'user_id integer,'
			'character text)'
		)
	except sqlite3.OperationalError:
		print(f"sheet_rents found")

	# - - - statistics - - -
	try:
		cursor.execute(
			'CREATE TABLE statistics('
			'id integer primary key,'
			'owner_id integer,'
			'outcome integer,'
			'size integer,'
			'used integer,'
			'roll_text text,'
			'tag text,'
			'date timestamp)'
		)
	except sqlite3.OperationalError:
		print(f"statistics found")

	# - - - table - - -
	try:
		cursor.execute(
			'CREATE TABLE tables('
			'table_name text primary key,'  # 0
			'dm_id integer,'  # 1
			'role_id integer,'  # 2
			'guest_id integer,'  # 3
			'auto_guest_add integer,'  # 4
			'main_channel_id integer)'  # 5
		)
	except sqlite3.OperationalError:
		print(f"tables found")

	# - - - role_bot - - -
	try:
		cursor.execute(
			'CREATE TABLE role_bot('
			'id integer primary key,'
			'channel_id text,'
			'message_id text,'
			'emoji text, role_id text)'
		)
	except sqlite3.OperationalError:
		print(f"role_bot found")

	# - - - titles - - -
	try:
		cursor.execute(
			'CREATE TABLE titles('
			'id integer primary key,'
			'title text,'
			'rank text)'
		)
	except sqlite3.OperationalError:
		print(f"titles found")

	# - - - title-people connector - - -
	try:
		cursor.execute(
			'CREATE TABLE title_people('
			'id primary key,'
			'discord_id integer,'
			'title_id integer)'
		)
	except sqlite3.OperationalError:
		print(f"title-people found")

	# - - - alignment - - -
	try:
		pass
		"""cursor.execute(
			'CREATE TABLE alignment('
			'discord_id integer primary key,'
			'good integer,'
			'evil integer,'
			'law integer,'
			'chaos integer)'
		)"""
	except sqlite3.OperationalError:
		print(f"alignment found")

print("--------")

with DatabaseConnection("card_base.db") as connection:
	cursor = connection.cursor()

	# - - - decks - - -
	try:
		cursor.execute(
			'CREATE TABLE decks('
			'deck_id integer primary key,'
			'owner_id integer,'
			'name text)'
		)
	except sqlite3.OperationalError as e:
		print(f"decks found")

	# - - - cards - - -
	try:
		cursor.execute(
			'CREATE TABLE cards('
			'card_id integer primary key,'
			'deck_id integer,'
			'name text,'
			'in_draw integer,'
			'art_url text)'
		)
	except sqlite3.OperationalError as e:
		print(f"cards found")


pass
