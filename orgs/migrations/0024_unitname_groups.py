# Generated by Django 4.1.1 on 2023-10-19 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('orgs', '0023_faultgroup_used_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='unitname',
            name='groups',
            field=models.ManyToManyField(to='auth.group'),
        ),
    ]
