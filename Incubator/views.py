from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse
from Incubator.models import Hatching, HatchingForm
from django.forms.models import modelformset_factory
import urllib2, urllib
#import datetime
import json
from data_utils import *
import pytz
import cv2
import time
import pymongo
from mongo_save import save_in_mongo
import threading
from photos_cron import activate_photos_cron

activate_photos_cron()
print "CRON to take photos hourly activated"

mongo_thread = threading.Thread(target=save_in_mongo, args=())
mongo_thread.start()
print "Thread to save data in mongodb every 15 seconds activated"
#today_datetime = datetime.datetime.today()
#midnight_datetime = datetime.datetime(today_datetime.year, today_datetime.month, today_datetime.day)
#for measure in measures.find({"date": {"$gt": midnight_datetime}}):
#print measures

data = Hatching.objects.latest('id')
last_hatching_data = data.start_datetime
#print type(data.start_datetime)
end_date = last_hatching_data + timedelta(days=21)

#retrieve_DBs()

URL_BASIC = 'http://192.168.0.110:8000/'
URL_TEMP = URL_BASIC + 'TEMP'
URL_HUMI = URL_BASIC + 'HUMI'
URL_list_measures = [URL_TEMP, URL_HUMI]

URL_cam_1 = 'http://192.168.0.156/image.jpg'
URL_cam_2 = 'http://192.168.0.153/image.jpg'
URL_cam_3 = 'http://192.168.0.152/image.jpg'

URL_cams = ['', URL_cam_1, URL_cam_2, URL_cam_3]

def request_without_proxy(URL_list):
	request_data_list = []
	proxy_handler = urllib2.ProxyHandler({})
	opener = urllib2.build_opener(proxy_handler)
	for URL in URL_list:
		request = urllib2.Request(URL)
		request_data = opener.open(request).read()
		request_data_list.append(request_data)
	return request_data_list

def request_without_proxy_POST(URL, parameters):
	encoded_parameters = urllib.urlencode(parameters)
	proxy_handler = urllib2.ProxyHandler({})
	opener = urllib2.build_opener(proxy_handler)
	request = urllib2.Request(URL, encoded_parameters)
	request_data = opener.open(request).read()
	return request_data

def measures(request):
	if request.method == 'GET':
		try:
			DATA = {}
			TEMP, HUMI = request_without_proxy(URL_list_measures)
			DATA['TEMP'] = TEMP[0:5]
			DATA['HUMI'] = HUMI[0:5]
			DATA_JSON = json.dumps(DATA)
			#print DATA_JSON
			return HttpResponse(DATA_JSON)
		except urllib2.HTTPError, e:
			return HttpResponse("404 - NOT FOUND")

def lights(request, light_number, command):
	#print "LIGHT: %s. COMMAND: %s" % (light_number, command)
	if light_number == "ALL":
		if command == "ON":
			resp = request_without_proxy_POST(URL_BASIC + 'EGGSON', {})
		else:
			resp = request_without_proxy_POST(URL_BASIC + 'EGGSOFF', {})
	else:
		#POST http://192.168.0.110:8000/EGG/1/value/on
		resp = request_without_proxy_POST(URL_BASIC + 'EGG/' + light_number + '/value/' + command.lower(), {})
	return HttpResponse("200 OK")

def home(request):
	logging(request)
	# TODO: These two lines can do only in one
	today = date.today()
	now = datetime.now(pytz.utc)
	###
	days = (now - last_hatching_data).days
	last_hatching_data_date = last_hatching_data.date()
	two_days_ago = today - timedelta(days=2)
	if two_days_ago >= last_hatching_data_date:
		two_days_date = two_days_ago.strftime("%Y%m%d") + "0000"
	else:
		two_days_date = ""
	four_days_ago = today - timedelta(days=4)
	if four_days_ago >= last_hatching_data_date:
		four_days_date = four_days_ago.strftime("%Y%m%d") + "0000"
	else:
		four_days_date = ""
	six_days_ago = today - timedelta(days=6)
	if six_days_ago >= last_hatching_data_date:
		six_days_date = six_days_ago.strftime("%Y%m%d") + "0000"
	else:
		six_days_date = ""
	TEMP, HUMI = request_without_proxy(URL_list_measures)
	TEMP = TEMP[0:5]
	HUMI = HUMI[0:5]
	#print days -< days [0, 1, 2, ...]
	return render_to_response('Incubator/home.html', {'last_hatching_data': last_hatching_data, 'end_date': end_date, 'TEMP': TEMP,  'HUMI': HUMI, 'days': days,
		'two_days_date': two_days_date, 'four_days_date': four_days_date, 'six_days_date': six_days_date})

def download_temp(request):
	logging(request)
	return render(request, 'Incubator/home.html')

def download_humi(request):
	logging(request)
	return render(request, 'Incubator/home.html')

def download_excel(request):
	logging(request)
	return render(request, 'Incubator/home.html')

def new_hatching(request):
	logging(request)
	HatchingFormSet = modelformset_factory(Hatching)
	if request.method == 'POST':
		hatching_formset = HatchingFormSet(request.POST, request.FILES)
		#print hatching_formset.errors
		if hatching_formset.is_valid():
			hatching_formset.save()
	else:
		hatching_formset = HatchingFormSet()
	return render_to_response('Incubator/new_hatching.html', {'hatching_formset': hatching_formset})

def temperatures(request):
	logging(request)
	initial_time = time.time()
	retrieve_DBs()
	print "retrieve_DBs()", time.time() - initial_time
	initial_time = time.time()
	thermo_dataframe = extract_data_from_DB(datetime_format, local_path_thermodb, thermodb_utils_dict)
	print "extract_data_from_DB()", time.time() - initial_time
	initial_time = time.time()
	today = date.today()
	if request.method == 'POST':
		mins = request.REQUEST["mins"]
		start_day = request.REQUEST["start_day"]
		end_day = request.REQUEST["end_day"]
		#print "mins: %s. start_day: %s. end_day: %s." % (mins, start_day, end_day)
		if start_day != end_day:
			start_datetime = last_hatching_data + timedelta(days=int(start_day) - 1)
			start_date = start_datetime.date()
			end_datetime = last_hatching_data + timedelta(days=int(end_day) - 1)
			end_date = end_datetime.date()
			if today < end_datetime.date():
				day_thermo = thermo_dataframe['TEMP_LOG'][str(start_date):str(today)]
				title = 'from ' + str(start_date) + ' to ' + str(today)
			else:
				day_thermo = thermo_dataframe['TEMP_LOG'][str(start_date):str(end_date)]
				title = 'from ' + str(start_date) + ' to ' + str(end_date)
		else:
			start_end_datetime = last_hatching_data + timedelta(days=int(start_day) - 1)
			start_end_date = start_end_datetime.date()
			day_thermo = thermo_dataframe['TEMP_LOG'][str(start_end_date)]
			title = 'of ' + str(start_end_date)
		if mins != "0":	
			day_thermo = day_thermo.resample(mins + 'Min')
			title += ' every ' + mins + ' mins.'
		url_image = comparing_temps_from_dataframe_by_day(title, day_thermo, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF)
		url_image_json = json.dumps({'url_image': url_image}, sort_keys=True,indent=4, separators=(',', ': '))
		print url_image_json
		return HttpResponse(url_image_json, mimetype="application/json")

	if request.method == 'GET':
		new_initial = time.time()
		day_thermo = thermo_dataframe['TEMP_LOG'][str(today)]
		day_thermo2 = day_thermo
		day_thermo = day_thermo.resample('15Min')
		print "day_thermo.resample(15min)", time.time() - new_initial
		#print day_thermo2
		#day_thermo_csv = day_thermo.to_csv("Incubator/static/data/day_thermo.csv", header=True)
		title = 'of today, ' + str(today) + ' every 15 mins'
		index_temps_timeseries = day_thermo.index
		temperatures_list = zip(index_temps_timeseries, day_thermo)
		url_image = comparing_temps_from_dataframe_by_day(title, day_thermo, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF)
		print "comparing_temps_from_dataframe_by_day()", time.time() - initial_time
		return render_to_response('Incubator/temperatures.html', {'temperatures_list': temperatures_list, 'url_image': url_image})

def humidities(request):
	logging(request)
	initial_time = time.time()
	retrieve_DBs()
	print "retrieve_DBs()", time.time() - initial_time
	initial_time = time.time()
	SHT1x_dataframe = extract_data_from_DB(datetime_format, local_path_SHT1xdb, SHT1xdb_utils_dict)
	print "extract_data_from_DB()", time.time() - initial_time
	initial_time = time.time()
	today = date.today()
	if request.method == 'POST':
		mins = request.REQUEST["mins"]
		start_day = request.REQUEST["start_day"]
		end_day = request.REQUEST["end_day"]
		#print "mins: %s. start_day: %s. end_day: %s." % (mins, start_day, end_day)
		if start_day != end_day:
			start_datetime = last_hatching_data + timedelta(days=int(start_day) - 1)
			start_date = start_datetime.date()
			end_datetime = last_hatching_data + timedelta(days=int(end_day) - 1)
			end_date = end_datetime.date()
			if today < end_datetime.date():
				day_SHT1x = SHT1x_dataframe['humi'][str(start_date):str(today)]
				title = 'from ' + str(start_date) + ' to ' + str(today)
			else:
				day_SHT1x = SHT1x_dataframe['humi'][str(start_date):str(end_date)]
				title = 'from ' + str(start_date) + ' to ' + str(end_date)
		else:
			start_end_datetime = last_hatching_data + timedelta(days=int(start_day) - 1)
			start_end_date = start_end_datetime.date()
			day_SHT1x = thermo_dataframe['humi'][str(start_end_date)]
			title = 'of ' + str(start_end_date)
		if mins != "0":	
			day_SHT1x = day_SHT1x.resample(mins + 'Min')
			title += ' every ' + mins + ' mins.'
		url_image = comparing_humis_from_dataframe_by_day(title, day_SHT1x, humi_param_MAX, humi_param_MIN, humi_MAX, humi_MIN, humi_limit_SUP, humi_limit_INF)
		url_image_json = json.dumps({'url_image': url_image}, sort_keys=True,indent=4, separators=(',', ': '))
		print url_image_json
		return HttpResponse(url_image_json, mimetype="application/json")


	if request.method == 'GET':
		new_initial = time.time()
		day_SHT1x = SHT1x_dataframe['humi'][str(today)]
		day_SHT1x2 = day_SHT1x
		day_SHT1x = day_SHT1x.resample('15Min')
		print "day_SHT1x.resample(15min)", time.time() - new_initial
		#day_SHT1x_csv = day_SHT1x.to_csv("Incubator/static/data/day_SHT1x.csv", header=True)
		title = 'of today, ' + str(today) + ' every 15 mins'
		index_humidities_today = day_SHT1x.index
		humidities_list = zip(index_humidities_today, day_SHT1x)
		url_image = comparing_humis_from_dataframe_by_day(title, day_SHT1x, humi_param_MAX, humi_param_MIN, humi_MAX, humi_MIN, humi_limit_SUP, humi_limit_INF)
		print "comparing_humis_from_dataframe_by_day()", time.time() - initial_time
		return render_to_response('Incubator/humidities.html', {'humidities_list': humidities_list, 'url_image': url_image})

def retrieve_image(request, cam_number):
	logging(request)	
	lights(request, cam_number, 'on')
	time.sleep(2)
	localtime = time.localtime()
	time_now = time.strftime("%Y%m%d%H%M%S", localtime)
	try:
		proxy_handler = urllib2.ProxyHandler({})
		opener = urllib2.build_opener(proxy_handler)
		urllib2.install_opener(opener)
		image_path = 'Incubator/static/egg_images/image_%s_%s.jpg' % (cam_number, time_now)
		with open(image_path,'wb') as f:
			f.write(urllib2.urlopen(URL_cams[int(cam_number)]).read())
			f.close()
		#im = cv2.imread("image.jpg")
	except:
		print "No connection!"
	lights(request, cam_number, 'off')
	response_json = json.dumps({'url_image': image_path[10:]}, sort_keys=True,indent=4, separators=(',', ': '))
	return HttpResponse(response_json)

def logging(request):
	# Some logging
	log_time = time.time()
	COOKIES = request.COOKIES
	USER_AGENT = request.META['HTTP_USER_AGENT']
	ADDR = request.META['REMOTE_ADDR']
	POST = request.POST.lists()
	GET = request.GET.lists()
	path = request.path
	with open('logs.txt', 'a') as log_file:
		log_file.write('path: ' + str(path) + '\n' )
		log_file.write('timestamp: ' + str(log_time) + '\n' )
		log_file.write('GET: ' + str(GET) + '\n' )
		log_file.write('POST: ' + str(POST) + '\n' )
		log_file.write('cookies: '+ str(COOKIES) + '\n' )
		log_file.write('user agent: ' + str(USER_AGENT) + '\n' )
		log_file.write('remote address: ' + str(ADDR) + '\n-\n' )