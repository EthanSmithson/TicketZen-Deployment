# Generated by Django 5.0.6 on 2024-07-06 20:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0008_alter_savedticket_ticket'),
    ]

    operations = [
        migrations.AlterField(
            model_name='savedticket',
            name='ticket',
            field=models.CharField(default='', max_length=1000000),
        ),
    ]
