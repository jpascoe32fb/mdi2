# Generated by Django 4.1.1 on 2023-06-08 15:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0014_alter_report_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='component',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='orgs.component'),
        ),
    ]