from pymongo import MongoClient
import urllib2
import time
import datetime
import json
import sqlite3
import pandas.io.sql as psql


mongo_client = MongoClient()
mongo_db = mongo_client.incubator
measures_collection = mongo_db.measures

local_path_SHT1xdb = "/home/weblord/Desktop/Incubator/Incubator/static/data/SHT1x.db"
SQL_execute_SHT1xdb = "select max(date), humi from READ"
SHT1x = [local_path_SHT1xdb, SQL_execute_SHT1xdb]

local_path_thermodb = "/home/weblord/Desktop/Incubator/Incubator/static/data/thermo.db"
SQL_execute_thermodb = "select max(DATE_LOG), TEMP_LOG from LOG"
THERMO = [local_path_thermodb, SQL_execute_thermodb]

DBs = [SHT1x, THERMO]

URL = 'http://localhost:8008/measures'

data_lost = []

def retrieve_last_row_from_DBS(DBs):
	dataframe_sqlite = []
	for DB in DBs:
		with sqlite3.connect(DB[0], detect_types=sqlite3.PARSE_DECLTYPES) as conn:
			dataframe_sqlite.append(psql.frame_query(DB[1], con=conn))
			#print dataframe_sqlite
			#	 max(date)      	  humi
			# 0  2013-10-15 16:48:15  51.02198
			#    max(DATE_LOG)        TEMP_LOG
			# 0  2013-10-15 16:49:09  37.375
	print max(dataframe_sqlite[0]['max(date)'], dataframe_sqlite[1]['max(DATE_LOG)'])
	return

def request_without_proxy(URL):
	proxy_handler = urllib2.ProxyHandler({})
	opener = urllib2.build_opener(proxy_handler)
	request = urllib2.Request(URL)
	request_data = opener.open(request).read()
	return request_data

def save_in_mongo():
	print "Saving all the data to mongodb"
	while(1):
		if data_lost:
			try:
				retrieve_DBs()
				retrieve_last_row_from_DBS(DBs)
			except:
				print "Impossible to retrive DB. Fix the problems in the net!"
				time.sleep(10)

		else:
			time.sleep(15)
		try:
			data = request_without_proxy(URL)
			json_data = json.loads(data)
			measure = {
				'date': datetime.datetime.utcnow(),
				'humi': json_data['HUMI'],
				'temp': json_data['TEMP']
			}
			measure_id = measures_collection.insert(measure)
		except:
			data_lost.append(datetime.datetime.utcnow())
		#print measure_id