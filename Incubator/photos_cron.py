#!/usr/bin/python

from crontab import CronTab
import sys

cron = CronTab(tab='* */3 * * * python /home/gustavo/Desktop/Incubator/Incubator/take_photos.py')
job = cron.new(command='python /home/gustavo/Desktop/Incubator/Incubator/take_photos.py', comment='Incubator cron')
job.hour.every(1)

sys.stdout.write(str(cron.render()))
cron.write()

print unicode(cron)