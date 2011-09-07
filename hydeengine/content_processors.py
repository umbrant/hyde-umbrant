from django.conf import settings

class PassthroughProcessor:

   @staticmethod
   def process(resource):       
	   resource.prerendered = True

