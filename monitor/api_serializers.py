from rest_framework import serializers
from .models import Device, User, MainsLogs, GeneratorLogs, Notification, Alarms, StatusInfo


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ('serial_number', 'site_name', 'site_serial', 'device_imei', 'device_owner', 'registration_date',
                  'check_status', 'on_mains', 'on_generator', 'on_backup')


class MainsLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainsLogs
        fields = (
            'time', 'l1nv', 'l2nv', 'l3nv', 'l1l2v', 'l1l3v', 'l2l3v', 'l1na', 'l2na', 'l3na',
            'frequency', 'backup', 'backup_load'
        )


class GenLogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratorLogs
        fields = (
            'time', 'l1nv', 'l2nv', 'l3nv', 'l1l2v', 'l1l3v', 'l2l3v', 'l1na', 'l2na', 'l3na',
            'frequency', 'rpm', 'fuel_level', 'battery_voltage', 'alternator_voltage', 'temperature', 'run_hours'
        )


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('time', 'message', 'viewed', 'site_name', 'device')


class AlarmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alarms
        fields = ('time', 'dg_fail_to_start', 'dg_low_fuel', 'dg_battery_low', 'charging_alt_fail', 'ac_mains_fail',
                  'high_coolant_temp', 'dse_emergency_stop', 'generator_low_voltage')


class StatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = StatusInfo
        fields = ('time', 'dse_status', 'dse_mode', 'local_storage')
