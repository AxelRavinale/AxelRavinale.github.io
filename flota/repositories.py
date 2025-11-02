from .models import Avion

class AvionRepository:

    @staticmethod
    def listar_todos():
        return Avion.objects.filter(activo=True)

    @staticmethod
    def obtener_por_id(pk):
        try:
            return Avion.objects.get(pk=pk, activo=True)
        except Avion.DoesNotExist:
            return None

    @staticmethod
    def crear(data):
        return Avion.objects.create(**data)

    @staticmethod
    def actualizar(avion, data):
        for attr, value in data.items():
            setattr(avion, attr, value)
        avion.save()
        return avion

    @staticmethod
    def eliminar(avion):
        avion.activo = False
        avion.save()
        return avion
