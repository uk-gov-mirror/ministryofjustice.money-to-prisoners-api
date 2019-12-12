# Generated by Django 2.0.13 on 2019-12-11 15:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0018_payment_status_rejected'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending'), ('failed', 'Failed'), ('taken', 'Taken'), ('rejected', 'Rejected'), ('expired', 'Expired')], db_index=True, default='pending', max_length=50),
        ),
    ]
