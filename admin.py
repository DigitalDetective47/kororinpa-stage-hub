from django.contrib.admin import site

from .models import Submission

site.register(Submission)
