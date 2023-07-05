# Generated by Django 4.1.1 on 2023-05-31 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0008_faultgroup_condition_closed_report_fault_group'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='faultgroup',
            name='name',
        ),
        migrations.AddField(
            model_name='faultgroup',
            name='fault',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='faultgroup',
            name='fault_group',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]