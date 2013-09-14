from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse
import urllib2, urllib
import json

URL_TEMP = 'http://192.168.0.110:8000/TEMP'
URL_HUMI = 'http://192.168.0.110:8000/HUMI'
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

def measures(request):
	if request.method == 'GET':
		try:
			DATA = {}
			TEMP, HUMI = request_without_proxy(URL_list_measures)
			DATA['TEMP'] = TEMP[0:5]
			DATA['HUMI'] = HUMI[0:5]
			DATA_JSON = json.dumps(DATA)
			print DATA_JSON
			return HttpResponse("200 OK")
		except urllib2.HTTPError, e:
			return HttpResponse("404 - NOT FOUND")

def lights(request, light_number, command):
	print "LIGHT: %s. COMMAND: %s" % (light_number, command)
	return HttpResponse("200 OK")

def home(request):
	return render(request, 'Incubator/home.html')