#!/usr/bin/python

from crontab import CronTab
import sys

def activate_photos_cron():
	cron = CronTab('weblord')
	job = cron.new(command='/usr/bin/python /home/weblord/Desktop/Incubator/Incubator/take_photos.py', comment='Incubator cron')
	# 0 * * * * python /home/weblord/Desktop/Incubator/Incubator/take_photos.py # Incubator cron
	#job.minute.every(5)
	job.hour.every(1)
	job.minute.on(0)
	job.enable()
	#cron = CronTab(tab="@hourly /usr/bin/python /home/weblord/Desktop/Incubator/Incubator/take_photos.py")
	cron.write()
	# Test CRONS -> grep CRON /var/log/syslog
	print unicode(cron)
