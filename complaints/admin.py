from django.contrib import admin
from .models import Complaint, Department, Area, Officer

admin.site.register(Complaint)
admin.site.register(Department)
admin.site.register(Area)
admin.site.register(Officer)