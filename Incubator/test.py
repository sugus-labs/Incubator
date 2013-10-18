import sqlite3
import pandas.io.sql as psql
from data_utils import retrieve_DBs, extract_data_from_DB
import pandas as pd
from pymongo import MongoClient
import datetime

mongo_client = MongoClient()
mongo_db = mongo_client.incubator
measures_collection = mongo_db.measures

local_path_SHT1xdb = "/home/weblord/Desktop/Incubator/Incubator/static/data/SHT1x.db"
#local_path_SHT1xdb = "/home/gustavo/Desktop/Incubator/Incubator/static/data/SHT1x.db"
SQL_execute_SHT1xdb = "select max(date), humi from READ"
index_SHT1xdb = "date"
SQL_remove_last_SHT1xdb = "select date, humi from READ"
SHT1x = [local_path_SHT1xdb, SQL_execute_SHT1xdb, index_SHT1xdb, SQL_remove_last_SHT1xdb]

local_path_thermodb = "/home/weblord/Desktop/Incubator/Incubator/static/data/thermo.db"
#local_path_thermodb = "/home/gustavo/Desktop/Incubator/Incubator/static/data/thermo.db"
SQL_execute_thermodb = "select max(DATE_LOG), TEMP_LOG from LOG"
index_thermodb = "DATE_LOG"
SQL_remove_last_thermodb = "select DATE_LOG, TEMP_LOG from LOG"
THERMO = [local_path_thermodb, SQL_execute_thermodb, index_thermodb, SQL_remove_last_thermodb]

def enter_row_to_mongodb(humi, temp, desired_date, dataframe_date):
	pass

DBs = [SHT1x, THERMO]

retrieve_DBs()

dataframes_sqlite = []
all_DBs_list = []

now = datetime.datetime.utcnow()
now_without_seconds = now.strftime("%Y-%m-%d %H:%M")
print "NOW:",now_without_seconds

for DB in DBs:	
	with sqlite3.connect(DB[0], detect_types=sqlite3.PARSE_DECLTYPES) as conn:
		all_db = psql.frame_query(DB[3], con=conn)
		all_db.index = pd.to_datetime(all_db.pop(DB[2]))
		# TODO: This is an approximation. We need data every 15 seconds minimum. In these moments SHT1x go 1:13 seconds 
		all_db = all_db.resample('15S', fill_method='bfill')
		#all_db_last = all_db.humi[now_without_seconds]
		
		#print all_db_last.tail(30)
		#print all_db.humi[all_db.count() - 1].iloc[0]
	all_DBs_list.append(all_db)
		#print all_db.humi[all_db.count() - 1].iloc[0]
		#print str(read_sqlite.index[0])
		#data
		#df1.ix['2012-01-01 01:00:00']
# last_row = all_DBs_list[0].count() - 1
#print all_DBs_list[0]
#print all_DBs_list[0].humi[all_DBs_list[0].count() - 1].iloc[0]
#print all_DBs_list[0].humi.tail(5)
#print all_DBs_list[1].TEMP_LOG.tail(5)
h = pd.concat([all_DBs_list[0], all_DBs_list[1]], axis=1)
#h2 = pd.ordered_merge(all_DBs_list[0], all_DBs_list[1],fill_method='ffill')
#print h.tail(10)
h2 = h.fillna(method='ffill')
print h2.tail(10)
print str(h2.index[h2.count() - 1])
#h2b = h2.drop(str([h2.index[h2.count() - 1]]))
#print h2b.tail(10)
print "HUMI: %.2f" % h2.humi[h2.count() - 1].iloc[0]
print "TEMP: %.2f" % h2.TEMP_LOG[h2.count() - 1].iloc[0]
#print h2.tail(5)
# print str(all_DBs_list[0].index[int(int(all_DBs_list[0].count()) - 1)])
# print all_DBs_list[1]
# print all_DBs_list[1].TEMP_LOG[all_DBs_list[1].count() - 1].iloc[0]

#print max(dataframes_sqlite[0].index, dataframes_sqlite[1].index)
#print "HUMI: %.2f" % dataframes_sqlite[0].humi.iloc[0]
#print "TEMP: %.2f" % dataframes_sqlite[1].TEMP_LOG.iloc[0]