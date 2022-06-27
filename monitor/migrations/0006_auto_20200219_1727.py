# Generated by Django 2.2.2 on 2020-02-19 14:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitor', '0005_auto_20200218_1830'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='site_serial',
            field=models.CharField(default='ETO/UG', max_length=30),
        ),
        migrations.AlterField(
            model_name='device',
            name='serial_number',
            field=models.IntegerField(unique=True),
        ),
    ]
