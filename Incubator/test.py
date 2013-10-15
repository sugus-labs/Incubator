import sqlite3
import pandas.io.sql as psql
from data_utils import retrieve_DBs, extract_data_from_DB
import pandas as pd

local_path_SHT1xdb = "/home/weblord/Desktop/Incubator/Incubator/static/data/SHT1x.db"
SQL_execute_SHT1xdb = "select max(date), humi from READ"
index_SHT1xdb = "max(date)"
SHT1x = [local_path_SHT1xdb, SQL_execute_SHT1xdb, index_SHT1xdb]

local_path_thermodb = "/home/weblord/Desktop/Incubator/Incubator/static/data/thermo.db"
SQL_execute_thermodb = "select max(DATE_LOG), TEMP_LOG from LOG"
index_thermodb = "max(DATE_LOG)"
THERMO = [local_path_thermodb, SQL_execute_thermodb, index_thermodb]

DBs = [SHT1x, THERMO]

retrieve_DBs()

dataframes_sqlite = []
for DB in DBs:
	with sqlite3.connect(DB[0], detect_types=sqlite3.PARSE_DECLTYPES) as conn:
		read_sqlite = psql.frame_query(DB[1], con=conn)
		read_sqlite.index = pd.to_datetime(read_sqlite.pop(DB[2]))
		dataframes_sqlite.append(read_sqlite)
print max(dataframes_sqlite[0].index, dataframes_sqlite[1].index)
print dataframes_sqlite[0].humi
print dataframes_sqlite[1].TEMP_LOG