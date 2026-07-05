from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.templatetags.static import static

class Profile(models.Model):
	user=models.OneToOneField(User, on_delete=models.CASCADE)
	image=models.ImageField(upload_to='avatars/',null=True, blank=True)
	displayname=models.CharField(max_length=20 , null=True , blank =True)
	info=models.TextField(null=True , blank=True)

	def __str__(self):
		return str(self.user)

	@property
	def name(self):
		if self.displayname:
			name=self.displayname
		else:
			name=self.user.username
		return name   

	@property
	def avatar(self):
		try:
			avatar=self.image.url
		except:
			avatar=static('images/avatar.svg')
		return avatar

def create_profile(sender,**kwargs):
	if kwargs['created']:
		user_profile=Profile.objects.create(user=kwargs['instance'])
post_save.connect(create_profile, sender=User)
