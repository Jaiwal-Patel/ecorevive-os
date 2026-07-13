from django.contrib import admin

from .models import RoutePlan, RouteStop

admin.site.register(RoutePlan)
admin.site.register(RouteStop)
