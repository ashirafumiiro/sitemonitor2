from django.contrib import admin
from .models import (Device, Customer, User, Notification, NotificationsSettings, PreviousAlarms, DeviceSettings)


class DeviceAdmin(admin.ModelAdmin):
    fields = ['serial_number', 'site_name', 'device_imei', 'device_owner', 'registration_date']


class CustomerAdmin(admin.ModelAdmin):
    fields = ['name', 'access', 'devices']


class UserAdmin(admin.ModelAdmin):
    pass


admin.site.register(Device)
admin.site.register(Customer)
admin.site.register(User)
admin.site.register(PreviousAlarms)
admin.site.register(NotificationsSettings)
admin.site.register(Notification)
admin.site.register(DeviceSettings)