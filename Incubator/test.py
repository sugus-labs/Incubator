import sqlite3
import pandas.io.sql as psql
from data_utils import retrieve_DBs, extract_data_from_DB
import pandas as pd

local_path_SHT1xdb = "/home/weblord/Desktop/Incubator/Incubator/static/data/SHT1x.db"
SQL_execute_SHT1xdb = "select max(date), humi from READ"
index_SHT1xdb = "max(date)"
SQL_remove_last_SHT1xdb = "select date, humi from READ"
SHT1x = [local_path_SHT1xdb, SQL_execute_SHT1xdb, index_SHT1xdb, SQL_remove_last_SHT1xdb]

local_path_thermodb = "/home/weblord/Desktop/Incubator/Incubator/static/data/thermo.db"
SQL_execute_thermodb = "select max(DATE_LOG), TEMP_LOG from LOG"
index_thermodb = "max(DATE_LOG)"
SQL_remove_last_thermodb = "select DATE_LOG, TEMP_LOG from LOG"
THERMO = [local_path_thermodb, SQL_execute_thermodb, index_thermodb, SQL_remove_last_thermodb]

DBs = [SHT1x, THERMO]

retrieve_DBs()

dataframes_sqlite = []
all_DBs_list = []
for DB in DBs:
	
	with sqlite3.connect(DB[0], detect_types=sqlite3.PARSE_DECLTYPES) as conn:
		#last_row = psql.frame_query(DB[1], con=conn)
		#last_row.index = pd.to_datetime(last_row.pop(DB[2]))
		#dataframes_sqlite.append(last_row)
		all_db = psql.frame_query(DB[3], con=conn)
	all_DBs_list.append(all_db)
		#print all_db.humi[all_db.count() - 1].iloc[0]
		#print str(read_sqlite.index[0])
		#data
		#df1.ix['2012-01-01 01:00:00']

print all_DBs_list[0]
print all_DBs_list[1]
#print max(dataframes_sqlite[0].index, dataframes_sqlite[1].index)
#print "HUMI: %.2f" % dataframes_sqlite[0].humi.iloc[0]
#print "TEMP: %.2f" % dataframes_sqlite[1].TEMP_LOG.iloc[0]