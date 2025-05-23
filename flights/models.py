from django.db import models

class FlightData(models.Model):
    flight_id = models.CharField(max_length=100, unique=True, help_text="Identificador único del vuelo/unidad")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    altitude = models.FloatField(null=True, blank=True, help_text="Altitud en metros o pies, según la API")
    speed = models.FloatField(null=True, blank=True, help_text="Velocidad")
    heading = models.FloatField(null=True, blank=True, help_text="Rumbo en grados")
    timestamp = models.DateTimeField(help_text="Fecha y hora de la última actualización de esta posición")
    raw_data = models.JSONField(null=True, blank=True, help_text="Datos crudos de la API para este vuelo")
    last_updated_by_system = models.DateTimeField(auto_now=True, help_text="Cuándo se actualizó este registro en nuestra BD")

    def __str__(self):
        return f"Flight {self.flight_id} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    class Meta:
        verbose_name = "Flight Data"
        verbose_name_plural = "Flight Data"
        ordering = ['-timestamp']