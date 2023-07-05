# Generated by Django 4.1.1 on 2023-06-12 17:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0015_alter_unit_component'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='asset',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='orgs.asset'),
        ),
        migrations.AlterField(
            model_name='unit',
            name='function',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='orgs.function'),
        ),
    ]