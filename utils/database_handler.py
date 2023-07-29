import sqlite3


class DatabaseConnection:
	def __init__(self, host):
		self.connection = None
		self.host = host

	def __enter__(self):
		self.connection = sqlite3.connect(self.host)
		return self.connection

	def __exit__(self, exc_type, exc_val, exc_tb):
		self.connection.commit()
		self.connection.close()


with DatabaseConnection("emoji_role.db") as connection:
	cursor = connection.cursor()

	# - - - emojis - - -
	try:
		cursor.execute(
			'CREATE TABLE emoji_role'
			'emoji_role_id integer primary key'
			'guild_id integer'
			'channel_id integer'
			'message_id integer'
			'emoji text'
			'role_id integer'
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
			'chat_ignore integer)'
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
			'table_name text primary key,'
			'dm_id integer,'
			'role_id integer,'
			'guest_id integer,'
			'auto_guest_add integer)'
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


pass
