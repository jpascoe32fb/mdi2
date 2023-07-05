# Generated by Django 4.1.1 on 2023-01-21 19:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('severity', models.CharField(choices=[('LOW', 'LOW'), ('MEDIUM', 'MEDIUM'), ('HIGH', 'HIGH')], max_length=200, null=True)),
                ('technology', models.CharField(choices=[('Vibration - Special Test', 'Vibration - Special Test'), ('example - test', 'example - test')], max_length=200, null=True)),
                ('analyst', models.CharField(choices=[('Glen Hutto', 'Glen Hutto'), ('John Pascoe', 'John Pascoe')], max_length=200, null=True)),
                ('entry_date', models.DateTimeField(auto_now_add=True, null=True)),
                ('work_req', models.CharField(max_length=300, null=True)),
                ('work_order', models.CharField(max_length=300, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Function',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PlantTag',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, null=True)),
                ('asset', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='orgs.asset')),
                ('component', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='orgs.component')),
                ('funct', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='orgs.function')),
                ('plant_tag', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='orgs.planttag')),
            ],
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fault', models.CharField(max_length=200, null=True)),
                ('comment', models.CharField(max_length=500, null=True)),
                ('recommendation', models.CharField(max_length=500, null=True)),
                ('condition', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='orgs.condition')),
                ('unit', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='orgs.unit')),
            ],
        ),
    ]