from django.contrib import admin
from .models import Preference, Watchlist, Review
# Register your models here.
admin.site.register(Preference)
admin.site.register(Watchlist)
admin.site.register(Review)