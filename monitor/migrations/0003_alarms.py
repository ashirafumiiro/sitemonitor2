# Generated by Django 2.2.2 on 2019-08-04 12:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0002_auto_20190715_1955'),
    ]

    operations = [
        migrations.CreateModel(
            name='Alarms',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('dg_fail_to_start', models.IntegerField()),
                ('dg_common_fault', models.IntegerField()),
                ('dg_low_fuel', models.IntegerField()),
                ('dg_battery_low', models.IntegerField()),
                ('charging_alt_fail', models.IntegerField()),
                ('ac_mains_fail', models.IntegerField()),
                ('high_coolant_temp', models.IntegerField()),
                ('site_on_batteries', models.IntegerField()),
                ('mains_on_load', models.IntegerField()),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='monitor.Device')),
            ],
        ),
    ]