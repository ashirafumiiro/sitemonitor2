from django.db import models
#  from datetime import datetime
from django.utils import timezone


class Customer(models.Model):
    name = models.CharField(max_length=20, unique=True)
    access = models.CharField(max_length=5)  # True or False
    devices = models.IntegerField()
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class User(models.Model):
    username = models.CharField(max_length=20, unique=True)
    email = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=32)
    registration_date = models.DateTimeField(auto_now_add=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return self.username


class Device(models.Model):
    serial_number = models.IntegerField(unique=True)
    site_name = models.CharField(max_length=40, unique=True)
    site_serial = models.CharField(max_length=30, default="ETO/UG")
    device_imei = models.CharField(max_length=20)
    device_owner = models.ForeignKey(Customer, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.site_name

    def check_status(self):
        last_alarm = Alarms.objects.filter(device=self).order_by('-id').first()  # get the latest log for alarms
        #  time_diff = 100000000
        if last_alarm:
            time_diff = timezone.now() - last_alarm.time
            if (time_diff.total_seconds()/60) < 10:  # show online below this value
                return 'online'
        return 'offline'

    def on_mains(self):
        last_log = MainsLogs.objects.filter(device=self).order_by('-id').first()
        if last_log:
            if last_log.l1nv > 100 or last_log.l2nv > 100 or last_log.l3nv > 100:
                return True
        else:
            return 'n/a'
        return False

    def on_generator(self):
        last_log = GeneratorLogs.objects.filter(device=self).order_by('-id').first()
        if last_log:
            if last_log.l1nv > 100 or last_log.l2nv > 100 or last_log.l3nv > 100:
                return True
        else:
            return 'n/a'
        return False

    def on_backup(self):
        if (self.on_mains() == True) or (self.on_generator() == True):
            return False
        elif (self.on_mains() == 'n/a') or (self.on_generator() == 'n/a'):
            return 'n/a'

        return True


class StatusInfo(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    dse_status = models.IntegerField()
    dse_mode = models.IntegerField()
    local_storage = models.CharField(max_length=5)  # True of False

    def get_dse_status(self):
        if self.dse_status == 0:
            return "Not Connected"
        else:
            return "Connected"

    def get_dse_mode(self):
        pass


class MainsLogs(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    l1nv = models.FloatField()
    l2nv = models.FloatField()
    l3nv = models.FloatField()
    l1l2v = models.FloatField()
    l1l3v = models.FloatField()
    l2l3v = models.FloatField()
    l1na = models.FloatField()
    l2na = models.FloatField()
    l3na = models.FloatField()
    frequency = models.FloatField()
    backup = models.FloatField()
    backup_load = models.FloatField()


class GeneratorLogs(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    l1nv = models.FloatField()
    l2nv = models.FloatField()
    l3nv = models.FloatField()
    l1l2v = models.FloatField()
    l1l3v = models.FloatField()
    l2l3v = models.FloatField()
    l1na = models.FloatField()
    l2na = models.FloatField()
    l3na = models.FloatField()
    frequency = models.FloatField()
    rpm = models.FloatField()
    fuel_level = models.FloatField()
    battery_voltage = models.FloatField()
    alternator_voltage = models.FloatField()
    temperature = models.FloatField()
    run_hours = models.FloatField()


class Alarms(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    dg_fail_to_start = models.IntegerField()
    dg_low_fuel = models.IntegerField()
    dg_battery_low = models.IntegerField()
    charging_alt_fail = models.IntegerField()
    ac_mains_fail = models.IntegerField()
    high_coolant_temp = models.IntegerField()
    dse_emergency_stop = models.IntegerField()
    generator_low_voltage = models.IntegerField()

    def dg_fail_to_start_status(self):
        return self.get_status(self.dg_fail_to_start)

    def dg_low_fuel_status(self):
        return self.get_status(self.dg_low_fuel)

    def dg_battery_low_status(self):
        return self.get_status(self.dg_battery_low)

    def charging_alt_fail_status(self):
        return self.get_status(self.charging_alt_fail)

    def ac_mains_fail_status(self):
        # get previous voltage and check if it is not zero

        return self.get_status(self.ac_mains_fail)

    def high_coolant_temp_status(self):
        return self.get_status(self.high_coolant_temp)

    def dse_emergency_stop_status(self):
        return self.get_status(self.dse_emergency_stop)

    def generator_low_voltage_status(self):
        return self.get_status(self.generator_low_voltage)

    def get_status(self, alarm):
        if alarm == 1:  # alarm OK
            return 'dot-green'
        elif alarm == 15:  # not implemented
            return 'dot'
        else:
            return 'dot-red'


class PreviousAlarms(models.Model):  # store previous state of Alarm to enable notifications
    # in inactive state, these have to be 0/False
    device = models.OneToOneField(Device, on_delete=models.CASCADE)
    time = models.DateTimeField(auto_now_add=True)
    dg_fail_to_start = models.BooleanField(default=False)
    dg_low_fuel = models.BooleanField(default=False)
    dg_battery_low = models.BooleanField(default=False)
    charging_alt_fail = models.BooleanField(default=False)  # from panel
    ac_mains_fail = models.BooleanField(default=False)
    high_coolant_temp = models.BooleanField(default=False)
    dse_emergency_stop = models.BooleanField(default=False)
    generator_low_voltage = models.BooleanField(default=False)
    charge_alt_error = models.BooleanField(default=False)  # from voltage of cc being less than that of battery
    dse_disconnected = models.BooleanField(default=False)
    site_state = models.BooleanField(default=False)  # site went offline

    def __str__(self):
        return self.device.site_name


class Notification(models.Model):
    time = models.DateTimeField(auto_now_add=True)
    message = models.CharField(max_length=150)
    is_critical = models.BooleanField()  # for critical notifications, sms is enabled
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, default=1)
    sms_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    viewed = models.BooleanField(default=0)

    def __str__(self):
        return self.message

    def site_name(self):
        return self.device.site_name


class NotificationsSettings(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sms_enable = models.BooleanField(default=False)
    email_enable = models.BooleanField(default=False)
    email = models.CharField(max_length=50, default="")
    phone = models.CharField(max_length=20, default='')

    def __str__(self):
        return self.user.username


class DeviceSettings(models.Model):
    device = models.OneToOneField(Device, on_delete=models.CASCADE)
    enable_notifications = models.BooleanField(default=True)

    def __str__(self):
        return self.device.site_name


