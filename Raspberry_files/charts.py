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

# Extract data from SHT1x.db
def extract_util_data_from_DB(DB_path, db_utils_dict):
	conn = sqlite3.connect(DB_path)
	cursor = conn.cursor()
	for db_utils_dict['table_columns'] in cursor.execute('SELECT * FROM ' + db_utils_dict['table_name']):
		print db_utils_dict['table_columns']
	return

# Extract data from thermo.db 
#SHT1x_conn = sqlite3.connect('/home/weblord/Documents/Rasp_Incubator/thermo/thermo.db')
#cursor = SHT1x_conn.cursor()
#for ID_LOG, DATE_LOG, TEMP_LOG, STATUS_LOG in cursor.execute('SELECT * FROM LOG'):
#	print DATE_LOG

#sht1x_data = extract_util_data_from_DB(local_path_sht1xdb, sht1xdb_utils_dict)
#thermo_data = extract_util_data_from_DB(local_path_thermodb, thermodb_utils_dict)

def thermo_charts(datetime_format):
	# Extract data from thermo.db
	thermo_conn = sqlite3.connect(local_path_thermodb)
	cursor = thermo_conn.cursor()
	dates = []
	status = []
	temps = []

	for ID_LOG, DATE_LOG, TEMP_LOG, STATUS_LOG in cursor.execute('SELECT * FROM LOG'):
		datetime_log = datetime.strptime(DATE_LOG, datetime_format)
		dates.append(datetime_log)
		temps.append(TEMP_LOG)
		status.append(STATUS_LOG)

	# plot
	plt.title('Data from thermometer')

	plt.subplot(2, 1, 1)
	yticks = ['BAD', 'PERFECT']
	y=[0,1]
	plt.yticks(y,yticks)
	plt.plot(dates,status)
	plt.ylim(-0.1, 1.1)

	plt.subplot(2, 1, 2)
	plot_date(dates, temps, 'k-')
	plt.ylim(35, 40)
	plt.axhspan(temp_MIN, temp_MAX, facecolor='r', alpha=0.3)
	plt.axhspan(temp_param_MIN, temp_param_MAX, facecolor='r', alpha=0.8)
	plt.gcf().autofmt_xdate()
	plt.xlabel('time')
	plt.ylabel('Temperature')
	plt.savefig('thermo.png', orientation='landscape')
	#plt.show()
	plt.close()

def SHT1x_charts(datetime_format):
	SHT1x_conn = sqlite3.connect(local_path_SHT1xdb)
	cursor = SHT1x_conn.cursor()
	dates = []
	humis = []
	temps = []

	for date, temp, humi in cursor.execute('SELECT * FROM READ'):
		datetime_log = datetime.strptime(date, datetime_format)
		dates.append(datetime_log)
		temps.append(temp)
		humis.append(humi)

	plt.title('Data from SHT1x')

	plt.subplot(2, 1, 1)
	plt.plot(dates, humis)
	plt.axhspan(humi_MIN, humi_MAX, facecolor='r', alpha=0.3)
	plt.axhspan(humi_param_MIN, humi_param_MAX, facecolor='r', alpha=0.8)
	plt.ylabel('Humidity')

	plt.subplot(2, 1, 2)
	plot_date(dates, temps, 'k-')
	plt.ylim(35, 40)
	plt.axhspan(temp_MIN, temp_MAX, facecolor='r', alpha=0.3)
	plt.axhspan(temp_param_MIN, temp_param_MAX, facecolor='r', alpha=0.8)
	plt.gcf().autofmt_xdate()
	plt.xlabel('time')
	plt.ylabel('Temperature')	
	plt.savefig('SHT1x.png', orientation='landscape')
	#plt.show()
	plt.close()

retrieve_DBs()
thermo_charts(datetime_format)
SHT1x_charts(datetime_format)