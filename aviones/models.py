from django.db import models

class Avion(models.Model):
    num_avion = models.CharField(max_length=20, unique=True)
    modelo = models.CharField(max_length=50)
    filas = models.PositiveIntegerField()
    columnas = models.PositiveIntegerField()
    estado = models.CharField(max_length=50)  # Ej: operativo, mantenimiento
    km_recorridos = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.num_avion} ({self.modelo})"

    def generar_asientos(self):
        """
        Método para generar automáticamente los asientos del avión
        según las filas y columnas.
        """
        columnas = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # Soporta hasta 26 columnas
        for fila in range(1, self.filas + 1):
            for col in range(self.columnas):
                Asiento.objects.create(
                    avion=self,
                    fila=fila,
                    columna=columnas[col],
                    estado='libre'
                )


class Asiento(models.Model):
    ESTADOS = (
        ('libre', 'Libre'),
        ('reservado', 'Reservado'),
        ('ocupado', 'Ocupado'),
    )

    avion = models.ForeignKey(Avion, on_delete=models.CASCADE, related_name='asientos')
    fila = models.PositiveIntegerField()
    columna = models.CharField(max_length=2)
    estado = models.CharField(max_length=10, choices=ESTADOS, default='libre')

    def __str__(self):
        return f"Asiento {self.fila}{self.columna} - {self.avion.num_avion}"
