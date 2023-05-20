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


with DatabaseConnection("data.db") as connection:
	cursor = connection.cursor()

	# - - - people - - -
	try:
		cursor.execute(
			f'CREATE TABLE people('
			f'discord_id integer primary key,'
			f'name text,'
			f'active text,'
			f'tag text,'
			f'color text,'
			f'change_name integer,'
			f'auto_tag integer,'
			f'chat_ignore integer)'
		)
	except sqlite3.OperationalError:
		print(f"people found")

	# - - - dice - - -
	try:
		cursor.execute(
			f'CREATE TABLE dice('
			f'die_id integer primary key,'
			f'name text,'
			f'owner_id integer,'
			f'roll text)'
		)
	except sqlite3.OperationalError:
		print(f"dice found")

	# - - - sheets - - -
	try:
		cursor.execute(
			f'CREATE TABLE sheets('
			f'sheet_id integer primary key,'
			f'owner_id integer,'
			f'character text,'
			f'sheet text,'
			f'last_warning timestamp)'
		)
	except sqlite3.OperationalError:
		print(f"sheets found")

	# - - - sheet rents - - -
	try:
		cursor.execute(
			f'CREATE TABLE sheet_rents('
			f'sheet_id integer primary key,'
			f'owner_id integer,'
			f'character text,'
			f'sheet text,'
			f'last_warning timestamp)'
		)
	except sqlite3.OperationalError:
		print(f"sheets found")

	# - - - statistics - - -
	try:
		cursor.execute(
			f'CREATE TABLE statistics('
			f'id integer primary key,'
			f'owner_id integer,'
			f'outcome integer,'
			f'size integer,'
			f'used integer,'
			f'roll_text text,'
			f'tag text,'
			f'date timestamp)'
		)
	except sqlite3.OperationalError:
		print(f"statistics found")

	# - - - table - - -
	try:
		cursor.execute(
			f'CREATE TABLE tables('
			f'table_name text primary key,'
			f'dm_id integer, role_id integer,'
			f'guest_id integer,'
			f'message_id integer)'
		)
	except sqlite3.OperationalError:
		print(f"tables found")

	# - - - role_bot - - -
	try:
		cursor.execute(
			f'CREATE TABLE role_bot('
			f'id integer primary key,'
			f'channel_id text,'
			f'message_id text,'
			f'emoji text, role_id text)'
		)
	except sqlite3.OperationalError:
		print(f"role_bot found")


pass
