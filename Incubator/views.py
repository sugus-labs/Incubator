from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse
import urllib2, urllib
import json

URL_TEMP = 'http://192.168.0.110:8000/TEMP'
URL_HUMI = 'http://192.168.0.110:8000/HUMI'


def DATA(request):
	if request.method == 'GET':
		try:
			proxy_handler = urllib2.ProxyHandler({})
			opener = urllib2.build_opener(proxy_handler)
			req_TEMP = urllib2.Request(URL_TEMP)
			req_HUMI = urllib2.Request(URL_HUMI)
			TEMP = opener.open(req_TEMP).read()
			HUMI = opener.open(req_HUMI).read()
			DATA = {}
			DATA['TEMP'] = TEMP[0:5]
			DATA['HUMI'] = HUMI[0:5]
			DATA_JSON = json.dumps(DATA)
			print DATA_JSON
			#return render(request, 'mastermind/basic_game.html', {"balls_json": balls_json, "balls_db": balls_db, "attempts": range(attempts_num), "liquids_json": liquids_json })
			return HttpResponse(DATA_JSON)
		except urllib2.HTTPError, e:
			return HttpResponse("404 - NOT FOUND")

def home(request):
	return render(request, 'Incubator/home.html')