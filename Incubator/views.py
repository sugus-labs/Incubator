from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse
from Incubator.models import Hatching, HatchingForm
from django.forms.models import modelformset_factory
import urllib2, urllib
import datetime
import json

data = Hatching.objects.latest('id')
last_hatching_data = data.start_datetime
#print type(data.start_datetime)
end_date = last_hatching_data + datetime.timedelta(days=21)

URL_BASIC = 'http://192.168.0.110:8000/'
URL_TEMP = URL_BASIC + 'TEMP'
URL_HUMI = URL_BASIC + 'HUMI'
URL_list_measures = [URL_TEMP, URL_HUMI]

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
	print "LIGHT: %s. COMMAND: %s" % (light_number, command)
	if light_number == "ALL":
		if command == "ON":
			resp = request_without_proxy_POST(URL_BASIC + 'EGGSON', {})
		else:
			resp = request_without_proxy_POST(URL_BASIC + 'EGGSOFF', {})
	# else:

	return HttpResponse("200 OK")

def home(request):
	TEMP, HUMI = request_without_proxy(URL_list_measures)
	TEMP = TEMP[0:5]
	HUMI = HUMI[0:5]
	return render_to_response('Incubator/home.html', {'last_hatching_data': last_hatching_data, 'end_date': end_date, 'TEMP': TEMP,  'HUMI': HUMI})

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
		print hatching_formset.errors
		if hatching_formset.is_valid():
			hatching_formset.save()
	else:
		hatching_formset = HatchingFormSet()
	return render_to_response('Incubator/new_hatching.html', {'hatching_formset': hatching_formset})