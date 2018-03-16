import psycopg2
import configparser


def pgsql_connect(config):
	conn = psycopg2.connect(
		database=config['PostgreSQL']['database'],
		user=config['PostgreSQL']['user'],
		password=config['PostgreSQL']['password'],
		host=config['PostgreSQL']['host'],
		port=config['PostgreSQL']['port'])
	return conn


def drop(conn, tablename):
	try:
		cur = conn.cursor()
		cur.execute("DROP TABLE " + tablename)
		conn.commit()
		cur.close()
	except:
		conn.commit()
		cur.close()

def initialize_db(conn):
	init_cur = conn.cursor()

	drop(conn, "ark_alerts")
	init_cur.execute("""CREATE TABLE ark_alerts (
		user_id bigint,
		dino text UNIQUE,
		level int);""")

	conn.commit()
	init_cur.close()


def create_table(conn, table_name, *columns):
	init_cur = conn.cursor()
	init_cur.execute("""CREATE TABLE {} ({});""".format(table_name, ','.join(columns)))
	conn.commit()
	init_cur.close()


def main():
	conn = pgsql_connect('../noctum.config')
	# initialize_db(conn)
	conn.close()

if __name__ == '__main__':
	main()