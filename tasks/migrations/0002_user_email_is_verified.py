# Generated by Django 4.2.6 on 2024-03-26 02:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_is_verified',
            field=models.BooleanField(default=False),
        ),
    ]
