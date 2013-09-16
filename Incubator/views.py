from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse
import urllib2, urllib
import json

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
			DATA['TEMP'] = ' ' + TEMP[0:5] + ' *C '
			DATA['HUMI'] = HUMI[0:5] + ' % Hr'
			DATA_JSON = json.dumps(DATA)
			print DATA_JSON
			return HttpResponse(DATA_JSON)
		except urllib2.HTTPError, e:
			return HttpResponse("404 - NOT FOUND")

def lights(request, light_number, command):
	print "LIGHT: %s. COMMAND: %s" % (light_number, command)
	if light_number == "ALL":
		if command == "ON":
			# POST /EGGSON
			resp = request_without_proxy_POST(URL_BASIC + 'EGGSON', {})
		else:
			resp = request_without_proxy_POST(URL_BASIC + 'EGGSOFF', {})
			# POST /EGGSOFF
	# else:

	return HttpResponse("200 OK")

def home(request):
	return render(request, 'Incubator/home.html')