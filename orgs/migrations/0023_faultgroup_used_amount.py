# Generated by Django 4.1.1 on 2023-07-05 16:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0022_remove_condition_work_order_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='faultgroup',
            name='used_amount',
            field=models.PositiveIntegerField(blank=True, default=0, null=True),
        ),
    ]