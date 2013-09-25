# sudo pip install paramiko
from pylab import *
import os
import sqlite3
import paramiko
from datetime import datetime
import matplotlib.pyplot as plt

datetime_format = '%Y-%m-%d %H:%M:%S'

temp_param_MAX = 37.1
temp_param_MIN = 36.5
temp_MIN = 36.0
temp_MAX = 37.6
humi_param_MAX = 60.5
humi_param_MIN = 55.5
humi_MIN = 60.0
humi_MAX = 75.0

server = "192.168.0.110"
host_username = "pi"
host_password = "letmein"

# thermo.db is the sqlite3 DB that shows sht1x values. We will rename to SHT1x.db
# The format is: table|read|read|2|CREATE TABLE READ(date text, temp real, humi real)
local_path_SHT1xdb = "/home/weblord/Desktop/Incubator/Raspberry_files/SHT1x/SHT1x.db"
remote_path_SHT1xdb = "/home/pi/test/thermo.db"
SHT1xdb_utils_dict = {
	'table_name' : 'READ',
	'table_columns' : ['date', 'temp', 'humi']
}

# incubator.db is the sqlite3 DB that shows thermostate values. We will rename to thermo.db
# The format is: table|LOG|LOG|2|CREATE TABLE LOG (ID_LOG INTEGER PRIMARY KEY AUTOINCREMENT,DATE_LOG DATETIME DEFAULT CURRENT_TIMESTAMP,TEMP_LOG REAL, STATUS_LOG INT DEFAULT 0)
local_path_thermodb = "/home/weblord/Desktop/Incubator/Raspberry_files/thermo/thermo.db"
remote_path_thermodb = "/home/pi/test/thermostate/incubator.db"
thermodb_utils_dict = {
	'table_name' : 'LOG',
	'table_columns' : ['ID_LOG', 'DATE_LOG', 'TEMP_LOG', 'STATUS_LOG']
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
def extract_thermo_data(datetime_format, db_local_path, db_utils_dict):
	# Extract data from thermo.db
	thermo_conn = sqlite3.connect(db_local_path)
	cursor = thermo_conn.cursor()
	dates = []
	status = []
	temps = []

	for db_utils_dict['table_columns'] in cursor.execute('SELECT * FROM ' + db_utils_dict['table_name']):
		datetime_log = datetime.strptime(db_utils_dict['table_columns'][1], datetime_format)
		dates.append(datetime_log)
		temps.append(db_utils_dict['table_columns'][2])
		status.append(db_utils_dict['table_columns'][3])

	return dates, temps, status
	

def extract_SHT1x_data(datetime_format, db_local_path, db_utils_dict):
	SHT1x_conn = sqlite3.connect(db_local_path)
	cursor = SHT1x_conn.cursor()
	dates = []
	humis = []
	temps = []

	for db_utils_dict['table_columns'] in cursor.execute('SELECT * FROM ' + db_utils_dict['table_name']):
		datetime_log = datetime.strptime(db_utils_dict['table_columns'][0], datetime_format)
		dates.append(datetime_log)
		temps.append(db_utils_dict['table_columns'][1])
		humis.append(db_utils_dict['table_columns'][2])

	return dates, temps, humis

def generate_comparing_temperature_with_dates_and_save(thermo_dates, thermo_temps, SHT1x_dates, SHT1x_temps, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF):
	plt.plot(thermo_dates, thermo_temps, 'r', SHT1x_dates, SHT1x_temps,)
	plt.ylim(temp_limit_INF, temp_limit_SUP)
	plt.gcf().autofmt_xdate()
	legend( ('thermo', 'SHT1x') ,
        loc = 'upper right')
	plt.savefig('thermo_comparation.png', orientation='landscape')
	#plt.show()
	plt.close()

def generate_thermo_plot_and_save(thermo_dates, thermo_temps, thermo_status, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF):
	plt.title('Data from thermometer')
	# First subplot
	plt.subplot(2, 1, 1)
	yticks = ['BAD', 'GOOD']
	y=[0,1]
	plt.yticks(y,yticks)
	plt.plot(thermo_dates,thermo_status)
	plt.ylim(-0.1, 1.1)
	# Second subplot
	plt.subplot(2, 1, 2)
	plot_date(thermo_dates, thermo_temps, 'k-')
	plt.ylim(temp_limit_INF, temp_limit_SUP)
	plt.axhspan(temp_MIN, temp_MAX, facecolor='r', alpha=0.3)
	plt.axhspan(temp_param_MIN, temp_param_MAX, facecolor='r', alpha=0.8)
	plt.gcf().autofmt_xdate()
	plt.xlabel('time')
	plt.ylabel('Temperature')
	plt.savefig('thermo.png', orientation='landscape')
	#plt.show()
	plt.close()

def generate_SHT1x_plot_and_save(SHT1x_dates, SHT1x_temps, SHT1x_humis, humi_param_MAX, humi_param_MIN, humi_MAX, humi_MIN, temp_limit_SUP, temp_limit_INF):
	plt.title('Data from SHT1x')
	# First subplot
	plt.subplot(2, 1, 1)
	plt.plot(SHT1x_dates, SHT1x_humis)
	plt.axhspan(humi_MIN, humi_MAX, facecolor='r', alpha=0.3)
	plt.axhspan(humi_param_MIN, humi_param_MAX, facecolor='r', alpha=0.8)
	plt.ylabel('Humidity')
	# Second subplot
	plt.subplot(2, 1, 2)
	plot_date(SHT1x_dates, SHT1x_temps, 'k-')
	plt.ylim(temp_limit_INF, temp_limit_SUP)
	plt.axhspan(temp_MIN, temp_MAX, facecolor='r', alpha=0.3)
	plt.axhspan(temp_param_MIN, temp_param_MAX, facecolor='r', alpha=0.8)
	plt.gcf().autofmt_xdate()
	plt.xlabel('time')
	plt.ylabel('Temperature')	
	plt.savefig('SHT1x.png', orientation='landscape')
	#plt.show()
	plt.close()

retrieve_DBs()
thermo_dates, thermo_temps, thermo_status = extract_thermo_data(datetime_format, local_path_thermodb, thermodb_utils_dict)
SHT1x_dates, SHT1x_temps, SHT1x_humis = extract_SHT1x_data(datetime_format, local_path_SHT1xdb, SHT1xdb_utils_dict)
generate_comparing_temperature_with_dates_and_save(thermo_dates, thermo_temps, SHT1x_dates, SHT1x_temps, temp_param_MAX, temp_param_MIN, temp_MAX, temp_param_MIN, 43, 32)
generate_thermo_plot_and_save(thermo_dates, thermo_temps, thermo_status, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, 40, 35)
generate_SHT1x_plot_and_save(SHT1x_dates, SHT1x_temps, SHT1x_humis, humi_param_MAX, humi_param_MIN, humi_MAX, humi_MIN, 40, 35)


