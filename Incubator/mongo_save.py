from pymongo import MongoClient
import urllib2
import time
import datetime
import json

mongo_client = MongoClient()
mongo_db = mongo_client.incubator
measures_collection = mongo_db.measures

URL = 'http://localhost:8008/measures'

def request_without_proxy(URL):
	proxy_handler = urllib2.ProxyHandler({})
	opener = urllib2.build_opener(proxy_handler)
	request = urllib2.Request(URL)
	request_data = opener.open(request).read()
	return request_data

while(1):
	time.sleep(15)
	data = request_without_proxy(URL)
	json_data = json.loads(data)
	measure = {
		'date': datetime.datetime.utcnow(),
		'humi': json_data['HUMI'],
		'temp': json_data['TEMP']
	}
	measure_id = measures_collection.insert(measure)
	#print measure_id