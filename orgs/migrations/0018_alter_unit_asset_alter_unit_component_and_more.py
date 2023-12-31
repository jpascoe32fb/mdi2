# Generated by Django 4.1.1 on 2023-06-12 18:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orgs', '0017_alter_unit_asset_alter_unit_function'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='asset',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orgs.asset'),
        ),
        migrations.AlterField(
            model_name='unit',
            name='component',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orgs.component'),
        ),
        migrations.AlterField(
            model_name='unit',
            name='function',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orgs.function'),
        ),
    ]
