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

data = Hatching.objects.latest('id')
last_hatching_data = data.start_datetime
#print type(data.start_datetime)
end_date = last_hatching_data + timedelta(days=21)

retrieve_DBs()

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
			print DATA_JSON
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
	TEMP, HUMI = request_without_proxy(URL_list_measures)
	TEMP = TEMP[0:5]
	HUMI = HUMI[0:5]
	now = datetime.now(pytz.utc)
	days = (now - last_hatching_data).days
	#print days
	return render_to_response('Incubator/home.html', {'last_hatching_data': last_hatching_data, 'end_date': end_date, 'TEMP': TEMP,  'HUMI': HUMI, 'days': days})

def download_temp(request):
	return render(request, 'Incubator/home.html')

def download_humi(request):
	return render(request, 'Incubator/home.html')

def download_excel(request):
	return render(request, 'Incubator/home.html')

def new_hatching(request):
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
	retrieve_DBs()
	thermo_dataframe = extract_data_from_DB(datetime_format, local_path_thermodb, thermodb_utils_dict)
	today = date.today()
	#print type(thermo_dataframe)
	#print thermo_dataframe
	if request.method == 'POST':
		mins = request.REQUEST["mins"]
		start_day = request.REQUEST["start_day"]
		end_day = request.REQUEST["end_day"]
		print "mins: %s. start_day: %s. end_day: %s." % (mins, start_day, end_day)
		if start_day != end_day:
			start_datetime = last_hatching_data + timedelta(days=int(start_day) - 1)
			start_date = start_datetime.date()
			end_datetime = last_hatching_data + timedelta(days=int(end_day) - 1)
			end_date = end_datetime.date()
			#print "%s - %s" % (start_date, end_date
			day_thermo = thermo_dataframe['TEMP_LOG'][str(start_date):str(end_date)]
			#print days_thermo
		else:
			start_end_datetime = last_hatching_data + timedelta(days=int(start_day) - 1)
			start_end_date = start_datetime.date()
			#print "%s" % start_end_date
			day_thermo = thermo_dataframe['TEMP_LOG'][str(start_end_date)]
			#print days_thermo
		if mins != 0:	
			day_thermo = day_thermo.resample(mins + 'Min')
			#print hours_days_thermo

	if request.method == 'GET':
		day_thermo = thermo_dataframe['TEMP_LOG'][str(today)]
		day_thermo = day_thermo.resample('60Min')
		#print type(day_thermo)
		#print day_thermo
		#day_thermo_csv = day_thermo.to_csv("Incubator/static/data/day_thermo.csv", header=True)
		#temperatures = day_thermo[::(day_thermo.count()/10)]
	temps_timeseries = day_thermo
		#index_temperatures = day_thermo.index[::(day_thermo.count()/10)]
	index_temps_timeseries = day_thermo.index
	temperatures_list = zip(index_temps_timeseries, temps_timeseries)
	print type(temperatures)
	comparing_temps_from_dataframe_by_day(temps_timeseries, temp_param_MAX, temp_param_MIN, temp_MAX, temp_MIN, temp_limit_SUP, temp_limit_INF)
	return render_to_response('Incubator/temperatures.html', {'temperatures_list': temperatures_list})

def humidities(request):
	retrieve_DBs()
	SHT1x_dataframe = extract_data_from_DB(datetime_format, local_path_SHT1xdb, SHT1xdb_utils_dict)
	today = date.today()
	day_SHT1x = SHT1x_dataframe['humi'][str(today)]
	day_SHT1x_csv = day_SHT1x.to_csv("Incubator/static/data/day_SHT1x.csv", header=True)
	humidities_today = day_SHT1x[::(day_SHT1x.count()/10)]
	index_humidities_today = day_SHT1x.index[::(day_SHT1x.count()/10)]
	humidities_today_list = zip(index_humidities_today, humidities_today)
	return render_to_response('Incubator/humidities.html', {'humidities_today_list': humidities_today_list})

def retrieve_image(request, cam_number):
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
#def take_picture(request):