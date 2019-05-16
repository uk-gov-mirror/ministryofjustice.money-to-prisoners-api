# Generated by Django 2.0.13 on 2019-05-16 15:59

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('notification', '0011_event_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='seen_by',
            field=models.ManyToManyField(related_name='events_seen', to=settings.AUTH_USER_MODEL),
        ),
    ]
