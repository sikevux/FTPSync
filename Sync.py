#!/usr/bin/env python2
# -*- encoding: utf-8 -*-

import sqlite3
import getpass
import time
from ftplib import FTP_TLS
import sys, getopt

def getfilelist(server, port, user, password, db):
	sqliteconnection = sqlite3.connect(db)
	sqlitecursor = sqliteconnection.cursor()

	sqlitecursor.execute('''CREATE TABLE IF NOT EXISTS files (date int, name text,  CONSTRAINT 'id_UNIQUE' UNIQUE ('name'))''')
	sqliteconnection.commit()


	ftpsconnection = FTP_TLS()
	ftpsconnection.connect(server, port)
	ftpsconnection.auth()
	ftpsconnection.prot_p()
	ftpsconnection.login(user, password)
	ftpsconnection.prot_p()

	rootfiles = ftpsconnection.nlst()

	for i in range(0,5):
		episodes = ftpsconnection.nlst(rootfiles[i])

		for episode in episodes:
			sqlitecursor.execute('''INSERT OR IGNORE INTO files VALUES ("%(date)d", "%(folder)s")''' % {'date': time.time(), 'folder': ("/" + rootfiles[i] + "/" + episode) } )
			sqliteconnection.commit()

	sqliteconnection.close()
	ftpsconnection.quit()
	ftpsconnection.close()


def getfiles(server, port, user, password, db):
	sqliteconnection = sqlite3.connect(db)
	sqlitecursor = sqliteconnection.cursor()

	sqlitecursor.execute('''CREATE TABLE IF NOT EXISTS latest (date int, CONSTRAINT 'id_UNIQUE' UNIQUE ('date'))''')
	sqliteconnection.commit()

	sqlitecursor.execute('''SELECT date FROM files WHERE date = (SELECT MAX(date) FROM files) LIMIT 1''')
	latestfile = sqlitecursor.fetchone()

	sqlitecursor.execute('''SELECT date FROM latest WHERE date = (SELECT MAX(date) FROM latest) LIMIT 1''')
	latestfetch = sqlitecursor.fetchone()

	if latestfetch is None:
		latestfetch = 0

	if latestfetch < latestfile:
		ftpsconnection = FTP_TLS()
		ftpsconnection.connect(server, port)
		ftpsconnection.auth()
		ftpsconnection.prot_p()
		ftpsconnection.login(user, password)
		ftpsconnection.prot_p()

		sqlitecursor.execute('''SELECT name FROM files WHERE date > %d''' % latestfetch)
		filestofetch = sqlitecursor.fetchall()

		for currfile in filestofetch:
        		ftpsconnection.cwd(currfile[0])
			filenames = ftpsconnection.nlst()

			for filename in filenames:
				print 'Now saving /mnt/folder' + currfile[0] + '/' + filename
				localfile = open('/mnt/folder' + currfile + '/' + filename, 'wb')
				ftpsconnection.retrbinary('RETR ' + filename, localfile.write)
				localfile.close()


	sqliteconnection.execute('''INSERT OR IGNORE INTO latest VALUES (%d)''' % time.time())
	sqliteconnection.commit()

	sqliteconnection.close()
	ftpsconnection.quit()
	ftpsconnection.close()

def main(argv):
	server = ''
	port = 22
	user = 'anonymous'
        password = 'anonymous'
	db = 'ftpsync.db'

	try:
		opts, args = getopt.getopt(argv, "s:p:u:d:", ["server=","port=","user=", "database="])
	except getopt.GetoptError:
		print 'Sync.py -s server -p port -u user'
		sys.exit(1);

	for opt, arg in opts:
	        if opt == '-h':
			print 'Sync.py -s server -p port -u user'
		elif opt in ("-s", "--server"):
			server = arg
		elif opt in ("-p", "--port"):
			port = arg
		elif opt in ("-u", "--user"):
			user = arg
			password = getpass.getpass()
		elif opt in ("-d", "--database"):
			db = arg

	getfiles(server, port, user, password, db)

if __name__ == "__main__":
        main(sys.argv[1:])


