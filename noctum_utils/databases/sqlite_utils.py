import sqlite3

def database_connect(database_path):
	return sqlite3.connect(database_path)


def create_table(cur, table_name, columns):
	"""
	Parameters

	cur = Database cursor object
	columns = List of strings for columns ex: ["user_id INTEGER NOT NULL PRIMARY KEY", "user_name TEXT UNIQUE"]
	"""
	try:
		cur.execute("CREATE TABLE {} ({});".format(table_name, ','.join(columns)))
	except sqlite3.OperationalError as e:
		print("SQLite Error: {}".format(e))


# conn = database_connect('../../noctumDB')
# cur = conn.cursor()
# create_table(cur, 'wow_chars', ['discord_id INTEGER NOT NULL',
# 								'char_name text NOT NULL',
# 								'char_class text',
# 								'race text',
# 								'level int',
# 								'UNIQUE (discord_id, char_name) ON CONFLICT REPLACE',
# 								'PRIMARY KEY (discord_id, char_name)'])
# conn.close()