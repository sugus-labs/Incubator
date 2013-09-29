from django.db import models
from django.forms import ModelForm

class Hatching(models.Model):
	name_of_hatching = models.CharField(max_length=35,
		help_text = "Write a unique name to hatch. This name is important to save all the data")
	number_of_eggs = models.IntegerField(
		help_text = "Write the number of eggs to hatch.")
	start_datetime = models.DateTimeField(auto_now_add=True)
	#start_datetime = models.DateTimeField(
	#	help_text = "Select the day to start to hatch.")

	def __unicode__(self):
		return unicode(self.name_of_hatching)

class HatchingForm(ModelForm):
	class Meta:
		model = Hatching
		exclude = ('start_datetime')
