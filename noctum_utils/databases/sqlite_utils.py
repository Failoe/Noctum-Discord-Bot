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
		conn.commit()
	except sqlite3.OperationalError as e:
		print("SQLite Error: {}".format(e))


# conn = database_connect('../../noctumDB')
# cur = conn.cursor()
# cur.execute('drop table wow_char_info;')
# create_table(cur, 'wow_char_info', ['name text NOT NULL',
# 								'class text',
# 								'race text',
# 								'level int',
# 								'lastmodified text',
# 								'prof1 string',
# 								'prof1_level int',
# 								'prof2 string',
# 								'prof2_level int',
# 								'UNIQUE (name) ON CONFLICT REPLACE',
# 								'PRIMARY KEY (name)'])
# conn.close()
