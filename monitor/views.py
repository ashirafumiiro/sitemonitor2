import requests
from django.shortcuts import render, reverse
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from rest_framework.response import Response
from .models import (MainsLogs, Device, GeneratorLogs, User, StatusInfo, Alarms, Customer, DeviceSettings,
                     Notification, NotificationsSettings, PreviousAlarms)
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError
from django.core.paginator import Paginator, EmptyPage
from django.core import serializers, exceptions as django_exceptions
from datetime import datetime, date
import json
from django.utils import timezone
#from dateutil.parser import parse
from django.utils.dateparse import parse_datetime
import pytz
from rest_framework.decorators import api_view
from rest_framework import status
from .api_serializers import DeviceSerializer, GenLogsSerializer, MainsLogsSerializer, NotificationSerializer, \
    AlarmsSerializer

import csv
from django.http import StreamingHttpResponse


# from django.core import serializers


def welcome(request):
    return HttpResponse("Welcome to Site monitor app Click<a href=\"monitor\">here</a> to continue")


def index(request):
    if 'customer_id' not in request.session.keys():
        return HttpResponseRedirect(reverse('monitor:login'))

    user = User.objects.get(pk=request.session['user_id'])
    customer_devices = Device.objects.filter(device_owner=user.customer.id)
    online_devices = 0
    for dev in customer_devices:
        if dev.check_status() == 'online':
            online_devices += 1
    context = {'devices': customer_devices, 'user': user, 'registered_devices': customer_devices.count(),
               'online_devices': online_devices}
    return render(request, 'monitor/home.html', context)


@csrf_exempt
def devices(request):
    # api handler
    if request.method == 'POST':
        customer_id = request.POST['customer_id']
        user = User.objects.get(pk=customer_id)
        customer_devices = Device.objects.filter(device_owner=user.customer.id)
        return JsonResponse({'devices': serializers.serialize('python', customer_devices)})

    if 'customer_id' not in request.session.keys():
        return HttpResponseRedirect(reverse('monitor:login'))

    user = User.objects.get(pk=request.session['user_id'])
    customer_devices = Device.objects.filter(device_owner=user.customer.id)
    #  determine if online using last log time. Must not be greater than 5 minutes
    #  devices = []
    return render(request, 'monitor/devices.html', {'devices': customer_devices})


def reports(request):
    if 'customer_id' not in request.session.keys():
        return HttpResponseRedirect(reverse('monitor:login'))

    return render(request, 'monitor/reports.html')


def account(request):
    if 'customer_id' not in request.session.keys():
        return HttpResponseRedirect(reverse('monitor:login'))

    user = User.objects.get(pk=request.session['user_id'])
    return render(request, 'monitor/accounts.html', {'user': user})


def login(request):
    if 'customer_id' in request.session.keys():
        return HttpResponseRedirect(reverse('monitor:index'))

    error = ''
    if request.method == 'POST':
        try:
            user = User.objects.get(email=request.POST['email'], password=request.POST['password'])

        except User.DoesNotExist:
            context = {'error': 'Invalid Username or password'}
            return render(request, 'monitor/login.html', context)
        else:  # user exists
            request.session['customer_id'] = user.customer.id
            request.session['user_id'] = user.id
            # redirect to home page dashboard
            return HttpResponseRedirect(reverse('monitor:index'))
    return render(request, 'monitor/login.html', {'error': error})


def logout(request):
    del request.session['customer_id']
    del request.session['user_id']
    return HttpResponseRedirect(reverse('monitor:login'))


def device(request, device_id):
    # API handling
    if 'api_key' in request.GET:  # must send api key in url
        data = {'mains_log': '', 'gen_log': '', 'status_log': '', 'alarms_log': ''}
        try:
            dev = Device.objects.get(serial_number=device_id)
        except Device.DoesNotExist:
            data['device'] = "not exist"
            return JsonResponse(data)

        mains_log = MainsLogs.objects.filter(device=dev).order_by('-id').first()
        gen_log = GeneratorLogs.objects.filter(device=dev).order_by('-id').first()
        alarms_log = Alarms.objects.filter(device=dev).order_by('-id').first()
        status_log = StatusInfo.objects.filter(device=dev).order_by('-id').first()
        if mains_log is not None:
            data['mains_log'] = serializers.serialize('python', [mains_log])[0]['fields']
        if gen_log is not None:
            data['gen_log'] = serializers.serialize('python', [gen_log])[0]['fields']
        if status_log is not None:
            data['status_log'] = serializers.serialize('python', [status_log])[0]['fields']
        if alarms_log is not None:
            data['alarms_log'] = serializers.serialize('python', [alarms_log])[0]['fields']
        data['device'] = serializers.serialize('python', [dev])[0]['fields']
        data['device']['status'] = dev.check_status()

        return JsonResponse(data, safe=False)

    context = {'device_id': device_id, 'mains_state': 'dot-red', 'gen_state': 'dot-red'}
    dev = Device.objects.get(serial_number=device_id)
    context['device'] = dev
    mains_log = MainsLogs.objects.filter(device=dev).order_by('-id').first()
    context['mains_log'] = mains_log
    if mains_log.l1nv > 0:
        context['mains_state'] = 'dot-green'
    context['alarms_log'] = Alarms.objects.filter(device=dev).order_by('-id').first()
    context['gen_log'] = GeneratorLogs.objects.filter(device=dev).order_by('-id').first()
    if context['gen_log'].l1nv > 0:
        context['gen_state'] = 'dot-green'
    context['status_info'] = StatusInfo.objects.filter(device=dev).order_by('-id').first()
    context['dse_status'] = ['Not connected', 'Connected']
    context['dse_mode'] = ["Stop", "Not available"]
    return render(request, 'monitor/device/dashboard.html', context)


def mains_update(request, device_id):
    dev = Device.objects.get(serial_number=device_id)
    mains_log = MainsLogs.objects.filter(device=dev).order_by('-id').first()
    mains_state = 'dot-red'
    if mains_log.l1nv > 0:
        mains_state = 'dot-green'
    return render(request, 'monitor/device/mains_update.html', {'mains_log': mains_log, 'mains_state': mains_state})


def gen_update(request, device_id):
    dev = Device.objects.get(serial_number=device_id)
    gen_log = GeneratorLogs.objects.filter(device=dev).order_by('-id').first()
    gen_state = 'dot-green'
    if gen_log.l1nv > 0:
        gen_state = 'dot-green'
    return render(request, 'monitor/device/gen_update.html', {'gen_log': gen_log, 'gen_state': gen_state})


def alarms_update(request, device_id):
    dev = Device.objects.get(serial_number=device_id)
    alarm_log = Alarms.objects.filter(device=dev).order_by('-id').first()
    mains_log = MainsLogs.objects.filter(device=dev).order_by('-id')[0:1]
    context = {'alarms_log': alarm_log, 'mains_alarm': 'dot'}
    if mains_log[0].l1nv > 100:
        context['mains_alarm'] = 'dot-green'
    else:
        context['mains_alarm'] = 'dot-red'
    return render(request, 'monitor/device/alarms_update.html', context)


def status_update(request, device_id):
    dev = Device.objects.get(serial_number=device_id)
    status_info = StatusInfo.objects.filter(device=dev).order_by('-id').first()
    context = {'status_info': status_info}
    return render(request, 'monitor/device/status_update.html', context)


def mains_logs(request, device_id):
    try:
        dev = Device.objects.get(serial_number=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'device': 'Device not found'})
    if 'count' in request.GET and 'page' in request.GET:
        page = request.GET['page']
        count = request.GET['count']
        page_number = 1
        logs_number = 10
        try:
            page_number = int(page)
            logs_number = int(count)
        except ValueError:
            pass
        logs = MainsLogs.objects.all().order_by('-id')[0:1000]
        paginator = Paginator(logs, logs_number)
        if page_number > paginator.num_pages:
            page_number = paginator.num_pages
        page_data = serializers.serialize('python', paginator.get_page(page_number))
        mains_page_data = [log['fields'] for log in page_data]
        data = {'current_page': page_number, 'total_pages': paginator.num_pages, 'total_logs': logs_number,
                'logs': mains_page_data}
        return JsonResponse(data)

    logs = MainsLogs.objects.filter(device=dev).order_by('-id')[0:30]
    return render(request, 'monitor/device/mains_logs.html', {'mains_logs': logs})


def mains_logs_update(request, device_id):
    dev = Device.objects.get(serial_number=device_id)
    logs = MainsLogs.objects.filter(device=dev).order_by('-id')[0:30]
    return HttpResponse(logs)  # render(request, 'monitor/device/mains_logs.html', {'mains_logs': logs})


def gen_logs(request, device_id):
    try:
        dev = Device.objects.get(serial_number=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'device': 'Device not found'})
    if 'count' in request.GET and 'page' in request.GET:
        page = request.GET['page']
        count = request.GET['count']
        page_number = 1
        logs_number = 10
        try:
            page_number = int(page)
            logs_number = int(count)
        except ValueError:
            pass
        logs = GeneratorLogs.objects.filter(device=dev).order_by('-id')[0:1000]
        paginator = Paginator(logs, logs_number)
        if page_number > paginator.num_pages:
            page_number = paginator.num_pages
        page_data = serializers.serialize('python', paginator.get_page(page_number))
        gen_page_data = [log['fields'] for log in page_data]
        data = {'current_page': page_number, 'total_pages': paginator.num_pages, 'total_logs': logs_number,
                'logs': gen_page_data}
        return JsonResponse(data)

    dev = Device.objects.get(serial_number=device_id)
    logs = GeneratorLogs.objects.filter(device=dev).order_by('-id')[0:30]
    return render(request, 'monitor/device/gen_logs.html', {'gen_logs': logs})


def alarms_logs(request, device_id):
    try:
        dev = Device.objects.get(serial_number=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'device': 'Device not found'})
    page = 1
    count = 10
    if 'count' in request.GET and 'page' in request.GET:
        page = request.GET['page']
        count = request.GET['count']

    page_number = 1
    logs_number = 10
    try:
        page_number = int(page)
        logs_number = int(count)
    except ValueError:
        pass
    logs = Alarms.objects.filter(device=dev).order_by('-id')[0:1000]
    paginator = Paginator(logs, logs_number)
    if page_number > paginator.num_pages:
        page_number = paginator.num_pages
    page_data = serializers.serialize('python', paginator.get_page(page_number))
    alarms_page_data = [log['fields'] for log in page_data]
    data = {'current_page': page_number, 'total_pages': paginator.num_pages, 'total_logs': logs_number,
            'logs': alarms_page_data}
    return JsonResponse(data)


def status_logs(request, device_id):
    try:
        dev = Device.objects.get(serial_number=device_id)
    except Device.DoesNotExist:
        return JsonResponse({'device': 'Device not found'})
    page = 1
    count = 10
    if 'count' in request.GET and 'page' in request.GET:
        page = request.GET['page']
        count = request.GET['count']
    page_number = 1
    logs_number = 10
    try:
        page_number = int(page)
        logs_number = int(count)
    except ValueError:
        pass
    logs = StatusInfo.objects.filter(device=dev).order_by('-id')[0:1000]
    paginator = Paginator(logs, logs_number)
    if page_number > paginator.num_pages:
        page_number = paginator.num_pages
    page_data = serializers.serialize('python', paginator.get_page(page_number))
    alarms_page_data = [log['fields'] for log in page_data]
    data = {'current_page': page_number, 'total_pages': paginator.num_pages, 'total_logs': logs_number,
            'logs': alarms_page_data}
    return JsonResponse(data)


@csrf_exempt
def upload(request):
    response = 'empty'
    if request.method == 'POST':
        try:
            device_imei = request.POST['device_id']
            dev = Device.objects.get(device_imei=device_imei)
            if 'L1NV' in request.POST:  # Mains parameters
                #  response = 'Mains Parameters. ' + json.dumps(request.POST)
                try:
                    log = MainsLogs(device=dev, l1nv=request.POST['L1NV'], l2nv=request.POST['L2NV'],
                                    l3nv=request.POST['L3NV'], l1na=request.POST['L1NA'], l2na=request.POST['L2NA'],
                                    l3na=request.POST['L3NA'], l1l2v=request.POST['L1L2V'], l1l3v=request.POST['L1L3V'],
                                    l2l3v=request.POST['L2L3V'], frequency=request.POST['MFreq'],
                                    backup=request.POST['BackupV'], backup_load=request.POST['BackupLoad'])
                    log.save()
                    response = 'Saved Mains log'
                except Exception as ex:
                    response = "Error: " + str(ex)

            elif 'GL1NV' in request.POST:
                try:
                    log = GeneratorLogs(device=dev, l1nv=request.POST['GL1NV'], l2nv=request.POST['GL2NV'],
                                        l3nv=request.POST['GL3NV'], l1na=request.POST['GL1NA'],
                                        l2na=request.POST['GL2NA'],
                                        l3na=request.POST['GL3NA'], l1l2v=request.POST['GL1L2V'],
                                        l1l3v=request.POST['GL1L3V'], l2l3v=request.POST['GL2L3V'],
                                        frequency=request.POST['GF'], rpm=request.POST['GRPM'],
                                        run_hours=request.POST['GRH'], temperature=request.POST['GTEMP'],
                                        fuel_level=request.POST['FL'], battery_voltage=request.POST['GBatt'],
                                        alternator_voltage=request.POST['GAlt']
                                        )
                    log.save()
                    response = 'Saved Generator parameters'
                except Exception as ex:
                    response = "Error: " + str(ex)

            elif 'DSEStatus' in request.POST:
                boolean = ['False', 'True']
                try:
                    info = StatusInfo(device=dev, dse_status=request.POST['DSEStatus'],
                                      dse_mode=request.POST['DSEMode'],
                                      local_storage=boolean[int(float(request.POST['Local_Storage']))])
                    info.save()
                    response = 'Status update'
                except Exception as ex:
                    response = "Error. " + str(ex)

            elif 'DG_FSTART' in request.POST:
                try:
                    alarms = Alarms(
                        device=dev,
                        dg_fail_to_start=request.POST['DG_FSTART'],
                        dg_battery_low=request.POST['DG_BATT_LOW'],
                        dg_low_fuel=request.POST['LOW_FUEL'],
                        charging_alt_fail=request.POST['CHARG_ALT_F'],
                        ac_mains_fail=request.POST['MAINS_F'],
                        high_coolant_temp=request.POST['HiCoolantTemp'],
                        dse_emergency_stop=request.POST['EMStop'],
                        generator_low_voltage=request.POST['GenLow_V']
                    )
                    alarms.save()
                    response = 'Alarms update'
                except Exception as ex:
                    response = "Error. " + str(ex)

        except (Device.DoesNotExist, MultiValueDictKeyError):
            response = "Non verified user: " + request.POST['device_id']

    elif request.method == 'GET':
        try:
            device_imei = request.GET['device_id']
            dev = Device.objects.get(device_imei=device_imei)
            if 'L1NV' in request.GET:  # Mains parameters
                #  response = 'Mains Parameters. ' + json.dumps(request.GET)
                try:
                    log = MainsLogs(device=dev, l1nv=request.GET['L1NV'], l2nv=request.GET['L2NV'],
                                    l3nv=request.GET['L3NV'], l1na=request.GET['L1NA'], l2na=request.GET['L2NA'],
                                    l3na=request.GET['L3NA'], l1l2v=request.GET['L1L2V'], l1l3v=request.GET['L1L3V'],
                                    l2l3v=request.GET['L2L3V'], frequency=request.GET['MFreq'],
                                    backup=request.GET['BackupV'], backup_load=request.GET['BackupLoad'])
                    log.save()
                    response = 'Saved Mains log'
                except Exception as ex:
                    response = "Error: " + str(ex)

            elif 'GL1NV' in request.GET:
                try:
                    log = GeneratorLogs(device=dev, l1nv=request.GET['GL1NV'], l2nv=request.GET['GL2NV'],
                                        l3nv=request.GET['GL3NV'], l1na=request.GET['GL1NA'],
                                        l2na=request.GET['GL2NA'],
                                        l3na=request.GET['GL3NA'], l1l2v=request.GET['GL1L2V'],
                                        l1l3v=request.GET['GL1L3V'], l2l3v=request.GET['GL2L3V'],
                                        frequency=request.GET['GF'], rpm=request.GET['GRPM'],
                                        run_hours=request.GET['GRH'], temperature=request.GET['GTEMP'],
                                        fuel_level=request.GET['FL'], battery_voltage=request.GET['GBatt'],
                                        alternator_voltage=request.GET['GAlt']
                                        )
                    log.save()
                    response = 'Saved Generator parameters'
                except Exception as ex:
                    response = "Error: " + str(ex)

            elif 'DSEStatus' in request.GET:
                boolean = ['False', 'True']
                try:
                    info = StatusInfo(device=dev, dse_status=request.GET['DSEStatus'],
                                      dse_mode=request.GET['DSEMode'],
                                      local_storage=boolean[int(float(request.GET['Local_Storage']))])
                    info.save()
                    response = 'Status update'
                except Exception as ex:
                    response = "Error. " + str(ex)

            elif 'DG_FSTART' in request.GET:
                try:
                    alarms = Alarms(
                        device=dev,
                        dg_fail_to_start=request.GET['DG_FSTART'],
                        dg_battery_low=request.GET['DG_BATT_LOW'],
                        dg_low_fuel=request.GET['LOW_FUEL'],
                        charging_alt_fail=request.GET['CHARG_ALT_F'],
                        ac_mains_fail=request.GET['MAINS_F'],
                        high_coolant_temp=request.GET['HiCoolantTemp'],
                        dse_emergency_stop=request.GET['EMStop'],
                        generator_low_voltage=request.GET['GenLow_V']
                    )
                    alarms.save()
                    response = 'Alarms update'
                except Exception as ex:
                    response = "Error. " + str(ex)

        except (Device.DoesNotExist, MultiValueDictKeyError):
            response = "Non verified user: " + request.GET['device_id']
    return HttpResponse(response)


def graph_load(request):
    graph = request.GET['graph']
    if graph == 'mains':
        pass
    return HttpResponse(graph)


def paging(request):
    mains_logs_list = MainsLogs.objects.all()
    paginator = Paginator(mains_logs_list, 4)  # Show 25 contacts per page
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    return render(request, 'monitor/pagination.html', {'logs': logs})


def get_seconds(start_time, end_time):
    time_diff = start_time - end_time
    return time_diff.total_seconds()


def get_report(request):
    data = {"error": "no"}  # there is no error initially
    try:
        from_date = datetime.strptime(request.GET['date_from'], "%m/%d/%Y")
        to_date = datetime.strptime(request.GET['date_to'], "%m/%d/%Y")

        customer_id = request.session['customer_id']
        registered_devices = Device.objects.filter(device_owner=customer_id, registration_date__lte=to_date,
                                                   registration_date__gte=from_date)
        data['reg_dev'] = registered_devices.count()
        online_device = [dev for dev in registered_devices if dev.check_status() == 'online']
        data['online'] = len(online_device)
        data['offline'] = registered_devices.count() - len(online_device)

    except:
        data['error'] = "No parameters sent"
        return HttpResponse(json.dumps(data))

    return HttpResponse(json.dumps(data))


@csrf_exempt
def api_login(request):
    data = {'error': 'Invalid data', 'user': {}}
    if request.method == 'POST':
        try:
            user = User.objects.get(email=request.POST['email'], password=request.POST['password'])
        except User.DoesNotExist:
            data['error'] = 'Invalid Username or password'
        except MultiValueDictKeyError:
            pass
        else:  # user exists
            data['user']['customer_id'] = user.customer.id
            data['user']['user_id'] = user.id
            data['error'] = 'success'

    return JsonResponse(data)


def dashboard(request, customer_id):
    data = {'error': 'Invalid data', 'data': {}}
    try:
        user = User.objects.get(pk=customer_id)
        customer_devices = Device.objects.filter(device_owner=user.customer.id)
        data['data']['devices_count'] = customer_devices.count()
        online_devices = [dev for dev in customer_devices if dev.check_status() == 'online']
        data['data']['online_devices'] = len(online_devices)
        data['data']['offline_devices'] = customer_devices.count() - len(online_devices)
        data['data']['user'] = serializers.serialize('python', [user], fields=('username', 'email'))[0]['fields']
        data['error'] = 'success'
        ser = DeviceSerializer(customer_devices, many=True)
        data['devices'] = ser.data

    except MultiValueDictKeyError:
        pass

    except User.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)

    return JsonResponse(data)


@api_view(['GET'])
def get_devices(request, customer_id):
    if request.method == 'GET':
        try:
            user = User.objects.get(pk=customer_id)
            customer_devices = Device.objects.filter(device_owner=user.customer.id)
            serializer = DeviceSerializer(customer_devices, many=True)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response(status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_device(request, device_id):
    try:
        data = {'mains_log': '', 'gen_log': '', 'status_log': '', 'alarms_log': ''}
        dev = Device.objects.get(serial_number=device_id)
        # serializer = DeviceSerializer(dev)
        mains_log = MainsLogs.objects.filter(device=dev).order_by('-id').first()
        gen_log = GeneratorLogs.objects.filter(device=dev).order_by('-id').first()
        alarms_log = Alarms.objects.filter(device=dev).order_by('-id').first()
        status_log = StatusInfo.objects.filter(device=dev).order_by('-id').first()
        data['notifications'] = len(Notification.objects.filter(device=dev, viewed=False))
        if mains_log is not None:
            data['mains_log'] = serializers.serialize('python', [mains_log])[0]['fields']
        if gen_log is not None:
            data['gen_log'] = serializers.serialize('python', [gen_log])[0]['fields']
        if status_log is not None:
            data['status_log'] = serializers.serialize('python', [status_log])[0]['fields']
        if alarms_log is not None:
            data['alarms_log'] = serializers.serialize('python', [alarms_log])[0]['fields']
        data['device'] = serializers.serialize('python', [dev])[0]['fields']
        data['device']['status'] = dev.check_status()

        return JsonResponse(data, safe=False)
        #  return Response(serializer.data)
    except Device.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def api_mains_logs(request, device_id, page_num, limit):
    try:
        dev = Device.objects.get(serial_number=device_id)
        mains_logs_list = MainsLogs.objects.filter(device=dev).order_by('-id')
        paginator = Paginator(mains_logs_list, limit)
        page = paginator.get_page(page_num)
        page_data = MainsLogsSerializer(page.object_list, many=True)
        if page_num > paginator.num_pages: raise EmptyPage
        return JsonResponse({'logs':page_data.data, 'current': page.number, 'has_next': page.has_next(),
                             'num_pages': paginator.num_pages
                             })
    except Device.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)
    except EmptyPage:
        return Response(status.HTTP_404_NOT_FOUND)
    except:
        return Response(status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def api_alarms_logs(request, device_id, page_num, limit):
    try:
        dev = Device.objects.get(serial_number=device_id)
        alarms_logs_list = Alarms.objects.filter(device=dev).order_by('-id')
        paginator = Paginator(alarms_logs_list, limit)
        page = paginator.get_page(page_num)
        page_data = AlarmsSerializer(page.object_list, many=True)
        if page_num > paginator.num_pages: raise EmptyPage
        return JsonResponse({'logs':page_data.data, 'current': page.number, 'has_next': page.has_next(),
                             'num_pages': paginator.num_pages
                             })
    except Device.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)
    except EmptyPage:
        return Response(status.HTTP_404_NOT_FOUND)
    except:
        return Response(status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def api_gen_logs(request, device_id, page_num, limit):
    try:
        dev = Device.objects.get(serial_number=device_id)
        gen_logs_list = GeneratorLogs.objects.filter(device=dev).order_by('-id')
        paginator = Paginator(gen_logs_list, limit)
        page = paginator.get_page(page_num)
        page_data = GenLogsSerializer(page.object_list, many=True)
        if page_num > paginator.num_pages: raise EmptyPage
        return JsonResponse({'logs':page_data.data, 'current': page.number, 'has_next': page.has_next(),
                             'num_pages': paginator.num_pages
                             })

    except Device.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)
    except EmptyPage:
        return Response(status.HTTP_404_NOT_FOUND)
    except:
        return Response(status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_report(request, customer_id, export=0):
    try:
        customer = Customer.objects.get(pk=customer_id)
        customer_devices = Device.objects.filter(device_owner=customer)
        unread_notifications = Notification.objects.filter(customer=customer, viewed=0).count()
        online_devs = [dev for dev in customer_devices if dev.check_status() == 'online']
        offline_devs = [dev for dev in customer_devices if dev.check_status() == 'offline']
        sites_on_mains = [dev for dev in customer_devices if dev.on_mains() == True]
        sites_on_generator = [dev for dev in customer_devices if dev.on_generator() == True]
        sites_on_backup = [dev for dev in customer_devices if dev.on_backup() == True]
        data = {'online': len(online_devs),
                'offline': len(offline_devs),
                'on_mains': len(sites_on_mains),
                'on_generator': len(sites_on_generator),
                'on_backup': len(sites_on_backup),
                'unread_notifications': unread_notifications
                }
        if export == 1:
            statistics = []
            for key, value in data.items():
                statistics.append({'name': key, 'value': value})
            report_data = {'statistics': statistics,
                           'devices': DeviceSerializer(customer_devices, many=True).data,  # to be processed at ui
                           }
            return JsonResponse(report_data)

        return JsonResponse(data)
    except Customer.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def filter_devices(request, customer_id, category, page=1, count=20):
    try:
        customer = Customer.objects.get(pk=customer_id)
        devs = Device.objects.filter(device_owner=customer)
        if category == 'online':
            devs = [dev for dev in devs if dev.check_status() == 'online']
        if category == 'offline':
            devs = [dev for dev in devs if dev.check_status() == 'offline']
        if category == 'on_mains':
            devs = [dev for dev in devs if dev.on_mains() == True]
        if category == 'on_generator':
            devs = [dev for dev in devs if dev.on_generator() == True]
        if category == 'on_backup':
            devs = [dev for dev in devs if dev.on_backup() == True]
        paginator = Paginator(devs, count)
        get_page = paginator.get_page(page)
        page_data = DeviceSerializer(get_page.object_list, many=True)
        data = {
            'devices': page_data.data,
            'pages_cont': paginator.num_pages,
            'current_page': get_page.number
        }
        return JsonResponse(data)
    except Customer.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)
    except EmptyPage:
        return Response(status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def monitor_routine(request):
    sites = Device.objects.all()
    for site in sites:
        settings, settings_created = DeviceSettings.objects.get_or_create(device=site)
        alarms = Alarms.objects.filter(device=site).order_by('-id').first()  # get the last current alarm log
        previous_state, created = PreviousAlarms.objects.get_or_create(device=site)
        status_info = StatusInfo.objects.filter(device=site).order_by('-id').first()
        gen_params = GeneratorLogs.objects.filter(device=site).order_by("-id").first()

        if not created and settings.enable_notifications:
            if alarms:
                # Dg fail to start
                if get_alarm(alarms.dg_fail_to_start) != previous_state.dg_fail_to_start:
                    current_state = get_alarm(alarms.dg_fail_to_start)
                    if current_state == 1:
                        message = "Dg has failed to start"
                    else:
                        message = 'Dg fail to start cleared'

                    notification = Notification.objects.create(customer=site.device_owner, message=message,
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.dg_fail_to_start = current_state
                # Dg battery low
                if get_alarm(alarms.dg_battery_low) != previous_state.dg_battery_low:
                    current_state = get_alarm(alarms.dg_battery_low)
                    if current_state == 1:
                        message = "Dg Battery is low"
                    else:
                        message = 'Dg Battery is now normal'

                    notification = Notification.objects.create(customer=site.device_owner, message=message,
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.dg_battery_low = current_state

                if get_alarm(alarms.dg_low_fuel) != previous_state.dg_low_fuel:
                    current_state = get_alarm(alarms.dg_low_fuel)
                    if current_state == 1:
                        message = "Dg Fuel is low"
                    else:
                        message = 'Dg Fuel is now normal'

                    notification = Notification.objects.create(customer=site.device_owner, message=message,
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.dg_low_fuel = current_state

                if get_alarm(alarms.charging_alt_fail) != previous_state.charging_alt_fail:
                    current_state = get_alarm(alarms.charging_alt_fail)
                    if current_state == 1:
                        message = "Charging alternator has failed"
                    else:
                        message = 'charging alternator is back to normal'

                    notification = Notification.objects.create(customer=site.device_owner, message=message,
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.charging_alt_fail = current_state

                if get_alarm(alarms.high_coolant_temp) != previous_state.high_coolant_temp:
                    current_state = get_alarm(alarms.high_coolant_temp)
                    if current_state == 1:
                        message = "High coolant temperature"
                    else:
                        message = 'Coolant temperature back to normal'

                    notification = Notification.objects.create(customer=site.device_owner, message=message,
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.high_coolant_temp = current_state

                if get_alarm(alarms.dse_emergency_stop) != previous_state.dse_emergency_stop:
                    current_state = get_alarm(alarms.dse_emergency_stop)
                    if current_state == 1:
                        message = "Emergency stop activated"
                    else:
                        message = 'Emergency stop deactivated'

                    notification = Notification.objects.create(customer=site.device_owner, message=message,
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.dse_emergency_stop = current_state

                if get_alarm(alarms.generator_low_voltage) != previous_state.generator_low_voltage:
                    current_state = get_alarm(alarms.generator_low_voltage)
                    if current_state == 1:
                        message = "Generator has low voltage"
                    else:
                        message = 'Generator voltage back to normal'

                    notification = Notification.objects.create(customer=site.device_owner, message=message,
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.generator_low_voltage = current_state

                if get_alarm(alarms.ac_mains_fail) != previous_state.ac_mains_fail:
                    current_state = get_alarm(alarms.ac_mains_fail)
                    if current_state == 1:
                        message = "AC mains failed"
                    else:
                        message = 'AC mains back to normal'

                    notification = Notification.objects.create(customer=site.device_owner, message=message,
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.ac_mains_fail = current_state

            if status_info:
                if status_info.dse_status == 1 and previous_state.dse_disconnected == 1:
                    notification = Notification.objects.create(customer=site.device_owner, message="DSE Connected",
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.dse_disconnected = 0  # disable alarm coz dse is now on
                elif status_info.dse_status == 0 and previous_state.dse_disconnected == 0:
                    notification = Notification.objects.create(customer=site.device_owner, message="DSE disconnect",
                                                               is_critical=True, device=site)
                    notification.save()
                    previous_state.dse_disconnected = 1  # enable alarm coz dse is now off
            if gen_params:
                if site.on_generator():
                    if gen_params.alternator_voltage < gen_params.battery_voltage or gen_params.alternator_voltage > 15:
                        if not previous_state.charge_alt_error:
                            notification = Notification.objects.create(customer=site.device_owner,
                                                                       message="Charge alternator voltage Error",
                                                                       is_critical=True, device=site)
                            notification.save()
                            previous_state.charge_alt_error = 1
                    else:
                        if previous_state.charge_alt_error:
                            notification = Notification.objects.create(customer=site.device_owner,
                                                                       message="Charge alternator voltage Error Cleared",
                                                                       is_critical=True, device=site)
                            notification.save()
                            previous_state.charge_alt_error = 0

            if site.check_status() == 'online' and previous_state.site_state == 1:
                notification = Notification.objects.create(customer=site.device_owner, message="Site back online",
                                                           is_critical=True, device=site)
                notification.save()
                previous_state.site_state = 0
            elif site.check_status() == 'offline' and previous_state.site_state == 0:
                notification = Notification.objects.create(customer=site.device_owner, message="Site gone offline",
                                                           is_critical=True, device=site)
                notification.save()
                previous_state.site_state = 1

        previous_state.save()

    return Response("Routine Completed")


def get_alarm(alarm):
    if alarm == 1:  # alarm inactive
        return 0
    return 1  # else return active. however, 15 is for unimplemented. we need to consider it later


def get_state(state):
    if state == 'n/a':
        return False
    return state


@api_view(['GET'])
def get_notifications(request, customer_id, page=1, count= 10):
    try:
        customer = Customer.objects.get(pk=customer_id)
        notifications = Notification.objects.filter(customer=customer).order_by('-id')
        paginator = Paginator(notifications, count)
        get_page = paginator.get_page(page)
        page_data = NotificationSerializer(get_page.object_list, many=True)
        unread_notifications = len(notifications.filter(viewed=0))
        data = {
            'notifications': page_data.data,
            'pages_cont': paginator.num_pages,
            'current_page': get_page.number,
            'unread': unread_notifications
        }
        return JsonResponse(data)

    except Customer.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def search_device(request, customer_id, device_name):
    devs = Device.objects.filter(device_owner=customer_id, site_name__icontains=device_name)[0:25]
    dev_json = DeviceSerializer(devs, many=True)
    data = {
        'devices': dev_json.data,
        'pages_cont': 1,
        'current_page': 1
    }
    return JsonResponse(data)


def send_sms(phone='+256759990801', message="msg"):
    # Emmy = +256759990801
    url = 'https://api.africastalking.com/version1/messaging'
    key = '3cda7279d8cafa6207a6c2200c547ad8ea5ac3510030af79e652787b14be7c25'
    params = {'username': 'ashirafumiiro', 'to': phone,
              'message': message}

    x = requests.post(url, data=params, headers={'apiKey': key})
    print(x.status_code, 'type: ', type(x.status_code))
    print(x.reason, type(x.reason))

    return x.status_code == 201 and x.reason == 'Created'


@api_view(['GET'])
def send_messages(request):
    notifications = Notification.objects.filter(is_critical=True, sms_sent=False)

    for notification in notifications:
        res = send_sms(message=notification.site_name()+': '+notification.message)
        print("Response: ", res)
        if res:
            notification.sms_sent= True
            notification.save()

    return Response("Completed")


class Echo:
    """An object that implements just the write method of the file-like
    interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


def logs_download(request, device_id, logs_type, date_from, date_to):
    try:
        site = Device.objects.get(serial_number=device_id)
        date_from = date_from.split('-')
        date_to = date_to.split('-')
        logs = []
        #  eat = timezone('Africa/Kampala')

        from_date = pytz.timezone('Africa/Kampala').localize(datetime(int(date_from[0]), int(date_from[1]),
                                                                      int(date_from[2])))
        # , tzinfo=pytz.timezone('Africa/Kampala')
        to_date = pytz.timezone('Africa/Kampala').localize(datetime(int(date_to[0]), int(date_to[1]), int(date_to[2])))
        #  make_aware(from_date)

        if logs_type == 'mains':
            logs_m = MainsLogs.objects.filter(device=site, time__range=(from_date, to_date))
            logs = MainsLogsSerializer(logs_m, many=True).data
        elif logs_type == "generator":
            logs_g = GeneratorLogs.objects.filter(device=site, time__range=(from_date, to_date))
            logs = GenLogsSerializer(logs_g, many=True).data

        print("From", date_from, "To", to_date)
        # logs = json.loads(json.dumps(logs))
        # if not logs:
        #     return Response(status.HTTP_404_NOT_FOUND)

        rows = ([parse_datetime(log['time']).strftime("%Y-%m-%d %H:%M:%S"), log['l1nv'], log['l2nv'], log['l3nv'], log['l1l2v'],
                 log['l1l3v'], log['l2l3v'], log['l1na'], log['l2na'], log['l3na'], log['frequency'], log['backup'],
                 log['backup_load']] for log in logs)
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                         content_type="text/csv")
        response['Content-Disposition'] = 'attachment; filename="{}.csv"'.\
            format('-'.join(date_from)+"_to_"+'-'.join(date_to))
        return response

    except Device.DoesNotExist:
        return Response(status.HTTP_404_NOT_FOUND)
    except TypeError:
        return Response("Invalid Date")


def some_streaming_csv_view(request):
    """A view that streams a large CSV file."""
    # Generate a sequence of rows. The range is based on the maximum number of
    # rows that can be handled by a single sheet in most spreadsheet
    # applications.
    rows = (["Row {}".format(idx), str(idx)] for idx in range(65536))
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)
    response = StreamingHttpResponse((writer.writerow(row) for row in rows),
                                     content_type="text/csv")
    response['Content-Disposition'] = 'attachment; filename="somefilename.csv"'
    return response


@api_view(['POST'])
def password_change(request, user_id):
    if request.method == 'POST':
        old_password = request.POST['old_password']
        new_password = request.POST['new_password']
        try:
            user = User.objects.get(pk=user_id, password=old_password)
            user.password = new_password
            user.save()
            return Response(status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(status.HTTP_404_NOT_FOUND)
        except MultiValueDictKeyError:
            return Response(status.HTTP_502_BAD_GATEWAY)
    else:
        return Response(status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
def notifications_settings(request, user_id):
    if request.method == 'POST':
        try:
            user_settings, created = NotificationsSettings.objects.get_or_create(user_id=user_id)
            user_settings.email = request.POST['email']
            user_settings.phone = request.POST['phone_number']
            user_settings.sms_enable = request.POST['sms_receive']
            user_settings.email_enable = request.POST['email_receive']
            user_settings.save()

            return Response(status.HTTP_200_OK)
        except MultiValueDictKeyError:
            return Response(status.HTTP_502_BAD_GATEWAY)
        except django_exceptions.ValidationError:
            return Response(status.HTTP_204_NO_CONTENT)

    else:
        return Response(status.HTTP_404_NOT_FOUND)
