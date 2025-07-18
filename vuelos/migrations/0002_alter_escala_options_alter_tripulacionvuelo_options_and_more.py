# Generated by Django 5.2.3 on 2025-07-14 04:09

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aviones', '0002_asiento'),
        ('core', '0002_pais_alter_localidad_options_provincia_and_more'),
        ('vuelos', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='escala',
            options={'verbose_name': 'Escala', 'verbose_name_plural': 'Escalas'},
        ),
        migrations.AlterModelOptions(
            name='tripulacionvuelo',
            options={'verbose_name': 'Tripulación de Vuelo', 'verbose_name_plural': 'Tripulaciones de Vuelo'},
        ),
        migrations.AlterModelOptions(
            name='vuelo',
            options={'ordering': ['fecha_salida_estimada'], 'verbose_name': 'Vuelo', 'verbose_name_plural': 'Vuelos'},
        ),
        migrations.RemoveField(
            model_name='vuelo',
            name='avion',
        ),
        migrations.RemoveField(
            model_name='vuelo',
            name='escala',
        ),
        migrations.AddField(
            model_name='tripulacionvuelo',
            name='activo',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='vuelo',
            name='avion_asignado',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='aviones.avion'),
        ),
        migrations.AddField(
            model_name='vuelo',
            name='cargado_por',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='vuelo',
            name='destino_principal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vuelos_destino', to='core.localidad'),
        ),
        migrations.AddField(
            model_name='vuelo',
            name='fecha_carga',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vuelo',
            name='fecha_llegada_estimada',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vuelo',
            name='fecha_salida_estimada',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vuelo',
            name='km_totales',
            field=models.PositiveIntegerField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='vuelo',
            name='origen_principal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='vuelos_origen', to='core.localidad'),
        ),
        migrations.AlterField(
            model_name='escala',
            name='destino',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='escalas_destino', to='core.localidad'),
        ),
        migrations.AlterField(
            model_name='escala',
            name='origen',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='escalas_origen', to='core.localidad'),
        ),
        migrations.AlterField(
            model_name='tripulacionvuelo',
            name='rol',
            field=models.CharField(choices=[('piloto', 'Piloto'), ('copiloto', 'Copiloto'), ('asistente', 'Asistente de vuelo'), ('jefe_cabina', 'Jefe de Cabina')], max_length=20),
        ),
        migrations.AlterUniqueTogether(
            name='tripulacionvuelo',
            unique_together={('vuelo', 'persona', 'rol')},
        ),
        migrations.CreateModel(
            name='EscalaVuelo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveIntegerField(default=1)),
                ('fecha_salida', models.DateTimeField()),
                ('fecha_llegada', models.DateTimeField()),
                ('km_estimados', models.PositiveIntegerField()),
                ('activo', models.BooleanField(default=True)),
                ('avion', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='aviones.avion')),
                ('destino', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='escala_vuelo_destino', to='core.localidad')),
                ('origen', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='escala_vuelo_origen', to='core.localidad')),
                ('vuelo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='escalas_vuelo', to='vuelos.vuelo')),
            ],
            options={
                'verbose_name': 'Escala de Vuelo',
                'verbose_name_plural': 'Escalas de Vuelo',
                'ordering': ['vuelo', 'orden'],
                'unique_together': {('vuelo', 'orden')},
            },
        ),
        migrations.CreateModel(
            name='TripulacionEscala',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rol', models.CharField(choices=[('piloto', 'Piloto'), ('copiloto', 'Copiloto'), ('asistente', 'Asistente de vuelo'), ('jefe_cabina', 'Jefe de Cabina')], max_length=20)),
                ('activo', models.BooleanField(default=True)),
                ('escala_vuelo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='tripulacion_escala', to='vuelos.escalavuelo')),
                ('persona', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.persona')),
            ],
            options={
                'verbose_name': 'Tripulación de Escala',
                'verbose_name_plural': 'Tripulaciones de Escala',
                'unique_together': {('escala_vuelo', 'persona', 'rol')},
            },
        ),
    ]
