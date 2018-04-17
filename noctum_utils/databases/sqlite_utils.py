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


conn = database_connect('../../noctumDB.db')
cur = conn.cursor()
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

cur.execute("""	SELECT discord_id, name, prof1, prof1_level FROM wow_char_info LEFT JOIN wow_chars ON char_name=name
				UNION ALL
				SELECT discord_id, name, prof2, prof2_level FROM wow_char_info LEFT JOIN wow_chars ON char_name=name;""")
# [print(_) for _ in cur.fetchall()]

import operator
from tabulate import tabulate

rows = [list(row) for row in cur.fetchall()]

rows.sort(key = operator.itemgetter(3), reverse=True)
rows.sort(key = operator.itemgetter(2))

header = ""
row_output = []
for row in rows:
	if row[2] != header:
		header = row[2]
		row_output.append([])
		row_output.append([header.upper()])
	row[1] = row[1].title()
	row.pop(2)
	row.pop(0)
	row_output.append(row)
output = tabulate(row_output)

print(output)


conn.close()
