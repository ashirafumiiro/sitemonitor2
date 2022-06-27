from django.urls import path, include
from . import views


app_name = 'monitor'
urlpatterns = [
    path('', views.index, name='index'),
    path('upload', views.upload, name='upload'),
    path('devices', views.devices, name='devices'),
    path('login', views.login, name='login'),
    path('api_login', views.api_login, name='api_login'),
    path('reports', views.reports, name='reports'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('reports/get_report', views.get_report, name='get_report'),
    path('graphs', views.graph_load, name='graphs'),
    path('account', views.account, name='account'),
    path('logout', views.logout, name='logout'),
    path('devices/<int:device_id>/', views.device, name='device'),
    path('devices/<int:device_id>/mains_update', views.mains_update, name='mains_update'),
    path('devices/<int:device_id>/gen_update', views.gen_update, name='gen_update'),
    path('devices/<int:device_id>/alarms_update', views.alarms_update, name='alarms_update'),
    path('devices/<int:device_id>/status_update', views.status_update, name='status_update'),
    path('devices/<int:device_id>/gen_logs', views.gen_logs, name='gen_logs'),
    path('devices/<int:device_id>/mains_logs', views.mains_logs, name='mains_logs'),
    path('devices/<int:device_id>/alarms_logs', views.alarms_logs, name='alarms_logs'),
    path('devices/<int:device_id>/status_logs', views.status_logs, name='status_logs'),
    path('devices/<int:device_id>/mains_logs_update', views.mains_logs_update, name='mains_logs_update'),
    path('paging', views.paging, name='paging'),
    path('api/<int:customer_id>/devices', views.get_devices, name='api_devices'),
    path('api/device/<int:device_id>', views.get_device, name='api_device'),
    path('api/dashboard/<int:customer_id>', views.dashboard, name='api_dashboard'),
    path('api/device/<int:device_id>/mains_logs/<int:page_num>/<int:limit>', views.api_mains_logs),
    path('api/device/<int:device_id>/gen_logs/<int:page_num>/<int:limit>', views.api_gen_logs),
    path('api/device/<int:device_id>/alarms_logs/<int:page_num>/<int:limit>', views.api_alarms_logs),
    path('api/reports/<int:customer_id>', views.get_report),
    path('api/reports/<int:customer_id>/<int:export>', views.get_report),
    path('api/devices/<int:customer_id>/<str:device_name>', views.search_device),
    path('api/devices/<int:customer_id>/<str:category>/<int:page>/<int:count>', views.filter_devices),
    path('routine', views.monitor_routine, name='routine'),
    path('send_sms', views.send_messages),
    #   path('api/notifications/<int:customer_id>', views.get_notifications),
    path('api/notifications/<int:customer_id>/<int:page>/<int:count>', views.get_notifications),
    path('api/logs/<int:device_id>/<str:logs_type>/<str:date_from>/<str:date_to>', views.logs_download),
    path('api/stream_data', views.some_streaming_csv_view),
    path('api/settings/notifications/<user_id>', views.notifications_settings),
    path('api/settings/password/<user_id>', views.password_change)

]
