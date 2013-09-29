#!/usr/bin/python

from crontab import CronTab

cron = CronTab(tab='')
job = cron.new(command='python /home/gustavo/Desktop/Incubator/Incubator/take_photos.py', comment='Incubator cron')
job.hour.every(1)
job.enable()

print unicode(cron)