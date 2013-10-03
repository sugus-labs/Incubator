# sudo pip install paramiko
from pylab import *
import os
import sqlite3
import paramiko
from datetime import datetime, timedelta, date
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import pytz
import pandas.io.sql as psql
from pandas import ExcelWriter
# TODO: Integrate DB directly from the django app!
import MySQLdb

db = MySQLdb.connect(host="localhost", # your host, usually localhost
                     user="root", # your username
                      passwd="letmein", # your password
                      db="Incubator") # name of the data base
cursor = db.cursor()
cursor.execute("SELECT start_datetime FROM Incubator_hatching ORDER BY id DESC LIMIT 1")
last_datetime = cursor.fetchone()
#print type(last_datetime[0])

degree_sign= u'\N{DEGREE SIGN}'

# TODO: No hardcoded please! It is unuseful. Only for DEBUG
# first_day = last_datetime[0].date()
# num_days = 21
# days_list = [ first_day + timedelta(days=x) for x in range(0,num_days) ]

MAD=pytz.timezone('Europe/Madrid')
datetime_format = '%Y-%m-%d %H:%M:%S'

temp_param_MAX = 37.5
temp_param_MIN = 37.4
temp_MIN = 37.0
temp_MAX = 38.0
humi_param_MAX = 60.5
humi_param_MIN = 55.5
humi_MIN = 55.0
humi_MAX = 70.0

temp_limit_INF = 36.8
temp_limit_SUP = 39
humi_limit_INF = 50
humi_limit_SUP = 75

server = "192.168.0.110"
host_username = "pi"
host_password = "letmein"

# thermo.db is the sqlite3 DB that shows sht1x values. We will rename to SHT1x.db
# The format is: table|read|read|2|CREATE TABLE READ(date text, temp real, humi real)
#local_path_SHT1xdb = "/home/gustavo/Desktop/Incubator/Incubator/static/data/SHT1x.db"
local_path_SHT1xdb = "/home/weblord/Desktop/Incubator/Incubator/static/data/SHT1x.db"
remote_path_SHT1xdb = "/home/pi/test/thermo.db"
SHT1xdb_utils_dict = {
	'table_name' : 'READ',
	'table_columns' : ['date', 'temp', 'humi']
}

# incubator.db is the sqlite3 DB that shows thermostate values. We will rename to thermo.db
# The format is: table|LOG|LOG|2|CREATE TABLE LOG (ID_LOG INTEGER PRIMARY KEY AUTOINCREMENT,DATE_LOG DATETIME DEFAULT CURRENT_TIMESTAMP,TEMP_LOG REAL, STATUS_LOG INT DEFAULT 0)
#local_path_thermodb = "/home/gustavo/Desktop/Incubator/Incubator/static/data/thermo.db"
local_path_thermodb = "/home/weblord/Desktop/Incubator/Incubator/static/data/thermo.db"
remote_path_thermodb = "/home/pi/test/thermostate/incubator.db"
thermodb_utils_dict = {
	'table_name' : 'LOG',
	'table_columns' : ['DATE_LOG', 'TEMP_LOG', 'STATUS_LOG']
}

def get_file_from_remote_host(remote_path_file, local_path_file, sftp_client):
	try:
		sftp_client.get(remote_path_file, local_path_file)
	except:
		print "Impossible to retrieve %s" % remote_path_file

def retrieve_DBs():
	ssh_client = paramiko.SSHClient()
	ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	#ssh_client.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
	ssh_client.connect(server, username=host_username, password=host_password)
	#stdin, stdout, stderr = ssh_client.exec_command('ls -l')
	#print stdout.readlines()
	sftp_client = ssh_client.open_sftp()
	get_file_from_remote_host(remote_path_SHT1xdb, local_path_SHT1xdb, sftp_client)
	get_file_from_remote_host(remote_path_thermodb, local_path_thermodb, sftp_client)
	sftp_client.close()
	ssh_client.close()

# Extract data from thermo DB
def extract_data_from_DB(datetime_format, db_local_path, db_utils_dict):
	with sqlite3.connect(db_local_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
	    dataframe_sqlite = psql.frame_query('select ' + db_utils_dict['table_columns'][0] + ', ' + db_utils_dict['table_columns'][1] + 
	    	', ' + db_utils_dict['table_columns'][2] + ' from ' + db_utils_dict['table_name'] , con=conn)
	    # TODO: change the hour to 2 hours more! -> http://pandas.pydata.org/pandas-docs/dev/generated/pandas.tseries.tools.to_datetime.html 
	    # This solution is a bit hacky ... and slow!!!   
	    dataframe_sqlite.index = pd.to_datetime(dataframe_sqlite.pop(db_utils_dict['table_columns'][0]))
	    dataframe_sqlite_UTC = dataframe_sqlite.tz_localize('UTC')
	    dataframe_sqlite_MAD = dataframe_sqlite_UTC.tz_convert(MAD)
	return dataframe_sqlite_MAD

def save_humi_from_dataframe_by_day(dataframe, string_day, humi_param_MAX, humi_param_MIN, humi_MAX, humi_MIN, humi_limit_SUP, humi_limit_INF):
	plt.title('Humidity of day %s' % string_day)
	today_plot = dataframe.humi[string_day]
	plt.ylim(humi_limit_INF, humi_limit_SUP)
	today_plot.plot()
	plt.axhspan(humi_param_MIN, humi_param_MAX, facecolor='g', alpha=0.2)
	plt.axhspan(humi_MIN, humi_MAX, facecolor='g', alpha=0.2)
 	today_plot_mean = today_plot.mean()
 	today_plot_std = today_plot.std()
 	today_plot_var = today_plot.var()
 	today_plot_min = today_plot.min()
 	today_plot_max = today_plot.max()
 	legend( ('Max: %.2f %%, Min: %.2f %%\nMean: %.2f %%\nStandard Deviation: %.2f %%\nVariance: %.2f %%' % (today_plot_max, today_plot_min, today_plot_mean, today_plot_std, today_plot_var), 'Recommended zone') , loc = 'upper right')
 	plt.ylabel('Humidity (%)')
	plt.xlabel('Hours')
	plt.savefig('static/data/humi_%s.png' % string_day, orientation='landscape')
	plt.close()

def save_temp_from_dataframe_by_day(dataframe, string_day, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF):
	plt.title('Temperature of day %s' % string_day)
	today_plot = dataframe.TEMP_LOG[string_day]
	plt.ylim(temp_limit_INF, temp_limit_SUP)
 	y=np.arange(temp_limit_INF, temp_limit_SUP, 0.2)
 	plt.grid()
 	plt.yticks(y)
	today_plot.plot()
	plt.axhspan(temp_param_MIN, temp_param_MAX, facecolor='g', alpha=0.2)
	plt.axhspan(temp_MIN, temp_MAX, facecolor='g', alpha=0.2)
	today_plot_mean = today_plot.mean()
	today_plot_std = today_plot.std()
	today_plot_var = today_plot.var()
 	today_plot_min = today_plot.min()
 	today_plot_max = today_plot.max()	
	legend( ('Max: %.2f %sC, Min: %.2f %sC\nMean: %.2f %sC\nStandard Deviation: %.2f %sC\nVariance: %.2f %sC' % (today_plot_max, degree_sign, today_plot_min, degree_sign, today_plot_mean, degree_sign, today_plot_std, degree_sign, today_plot_var, degree_sign), 'Recommended zone') , loc = 'upper right')
	plt.ylabel('Temperature (%sC)' % degree_sign)
	plt.xlabel('Hours')
	plt.savefig('static/data/temp_%s.png' % string_day, orientation='landscape')
	plt.close()

def comparing_temps_from_dataframe_by_day(dataframe_thermo, dataframe_SHT1x, string_day, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF):
	plt.title('Comparation of the temperatures of day %s' % string_day)
	today_plot_thermo = dataframe_thermo.TEMP_LOG[string_day]
	today_plot_SHT1x = dataframe_SHT1x.temp[string_day]
	plt.ylim(temp_limit_INF, temp_limit_SUP)
 	y=np.arange(temp_limit_INF, temp_limit_SUP, 0.2)
 	plt.grid()
 	plt.yticks(y)
	today_plot_thermo.plot()
	today_plot_SHT1x.plot()
	plt.axhspan(temp_param_MIN, temp_param_MAX, facecolor='g', alpha=0.2)
	plt.axhspan(temp_MIN, temp_MAX, facecolor='g', alpha=0.2)
	legend( ('thermo', 'SHT1x', 'Recommended zone') , loc = 'upper right')
	plt.ylabel('Temperature (%sC)' % degree_sign)
	plt.xlabel('Hours')
	plt.savefig('static/data/comparing_temps_%s.png' % string_day, orientation='landscape')
	plt.close()

def comparing_humi_temps_from_dataframe_by_day(dataframe_thermo, dataframe_SHT1x, string_day, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF, humi_limit_SUP, humi_limit_INF):
 	f, axarr = plt.subplots(2, sharex=True)
 	# First subplot
 	plt.subplot(2, 1, 1)
	today_plot_thermo = dataframe_thermo.TEMP_LOG[string_day]
 	plt.ylim(temp_limit_INF, temp_limit_SUP)
 	y=np.arange(temp_limit_INF, temp_limit_SUP, 0.2)
 	plt.grid()
 	plt.yticks(y)
	today_plot_thermo.plot()
	plt.axhspan(temp_param_MIN, temp_param_MAX, facecolor='g', alpha=0.2)
	plt.axhspan(temp_MIN, temp_MAX, facecolor='g', alpha=0.2)
	plt.ylabel('Temperature (C)')
	plt.xlabel('')
	# Second subplot
 	plt.subplot(2, 1, 2)
	today_plot_SHT1x_humi = dataframe_SHT1x.humi[string_day]
	today_plot_SHT1x_temp = dataframe_SHT1x.temp[string_day]
	plt.ylim(humi_limit_INF, humi_limit_SUP)
 	plt.grid()
	today_plot_SHT1x_humi.plot()
	plt.axhspan(humi_param_MIN, humi_param_MAX, facecolor='g', alpha=0.2)
	plt.axhspan(humi_MIN, humi_MAX, facecolor='g', alpha=0.2)
	plt.ylabel('Humidity (%)')
	plt.xlabel('Hours')
	# Pearson correlation: http://en.wikipedia.org/wiki/Pearson_product-moment_correlation_coefficient
	# 0 implies that there is no linear correlation between the variables.
	pearson_corr_index = today_plot_SHT1x_temp.corr(today_plot_SHT1x_humi)
	plt.suptitle('Correlation between temperature and humidity\n')
	plt.suptitle('\n\nCalculated Pearson correlation index: %.2f' % pearson_corr_index, color='b')
	plt.savefig('static/data/comparing_humi_temps_%s.png' % string_day, orientation='landscape')
	plt.close()

def extract_SHT1x_data_day_by_day(SHT1x_dataframe, days_list):
	# the 'with' statement dont work
	today = date.today()
	writer = ExcelWriter('static/data/SHT1x.xlsx')
    	for day in days_list:
    		if day <= today:
    			day_SHT1x = SHT1x_dataframe[str(day)]
        		day_SHT1x.to_excel(writer, sheet_name=str(day))
    	writer.save()

def extract_thermo_data_day_by_day(thermo_dataframe, days_list):
	# the 'with' statement dont work
	# replace dont work properly
	#thermo_dataframe_sustituted = thermo_dataframe.replace({'0': 'OFF', '1': 'ON'})
	#print thermo_dataframe_sustituted
	today = date.today()
	writer = ExcelWriter('static/data/thermo.xlsx')
    	for day in days_list:
    		if day <= today:
    			day_thermo = thermo_dataframe[str(day)]
        		day_thermo.to_excel(writer, sheet_name=str(day))
    	writer.save()

#retrieve_DBs()
#SHT1x_dataframe = extract_data_from_DB(datetime_format, local_path_SHT1xdb, SHT1xdb_utils_dict)
#thermo_dataframe = extract_data_from_DB(datetime_format, local_path_thermodb, thermodb_utils_dict)
#save_humi_from_dataframe_by_day(SHT1x_dataframe, '2013-10-03', humi_param_MAX, humi_param_MIN, humi_MAX, humi_MIN, humi_limit_SUP, humi_limit_INF)
#save_temp_from_dataframe_by_day(thermo_dataframe, '2013-10-03', temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF)
#comparing_temps_from_dataframe_by_day(thermo_dataframe, SHT1x_dataframe, '2013-09-29', temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF)
#comparing_humi_temps_from_dataframe_by_day(thermo_dataframe, SHT1x_dataframe, '2013-10-02', temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF, humi_limit_SUP, humi_limit_INF)

#extract_SHT1x_data_day_by_day(SHT1x_dataframe, days_list)
#extract_thermo_data_day_by_day(thermo_dataframe, days_list)

#print SHT1x_dataframe