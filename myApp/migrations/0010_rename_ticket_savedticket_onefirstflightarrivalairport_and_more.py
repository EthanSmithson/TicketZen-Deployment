# Generated by Django 5.0.6 on 2024-07-12 00:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0009_alter_savedticket_ticket'),
    ]

    operations = [
        migrations.RenameField(
            model_name='savedticket',
            old_name='ticket',
            new_name='oneFirstFlightArrivalAirport',
        ),
        migrations.AddField(
            model_name='savedticket',
            name='oneFirstFlightArrivalDate',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='oneFirstFlightDepartureAirport',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='oneFirstFlightDepartureDate',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='oneFlightTotalDuration',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='price',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='zeroFirstFlightArrivalAirport',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='zeroFirstFlightArrivalDate',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='zeroFirstFlightDepartureAirport',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='zeroFirstFlightDepartureDate',
            field=models.CharField(default='', max_length=1000000),
        ),
        migrations.AddField(
            model_name='savedticket',
            name='zeroFlightTotalDuration',
            field=models.CharField(default='', max_length=1000000),
        ),
    ]
