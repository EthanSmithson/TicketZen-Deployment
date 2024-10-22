from django.contrib import admin
from .models import User, savedTicket, recentSearch

admin.site.register(User)
admin.site.register(savedTicket)
admin.site.register(recentSearch)
