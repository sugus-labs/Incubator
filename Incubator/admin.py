from django.contrib import admin
from Incubator.models import Hatching

# class HatchingAdmin(admin.ModelAdmin):
# 	fields = ['name_of_hatching', 'number_of_eggs', 'start_datetime']
# admin.site.register(Hatching, HatchingAdmin)
admin.site.register(Hatching)