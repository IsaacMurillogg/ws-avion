from rest_framework import viewsets, permissions
from .models import FlightData
from .serializers import FlightDataSerializer
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers # Para caché

class FlightDataViewSet(viewsets.ReadOnlyModelViewSet): # ReadOnly, ya que los datos se crean/actualizan por el cron
    queryset = FlightData.objects.all().order_by('-timestamp') # Más reciente primero
    serializer_class = FlightDataSerializer
    permission_classes = [permissions.AllowAny]

    @method_decorator(cache_page(60 * 1)) # Cache por 1 minuto
    @method_decorator(vary_on_headers("Authorization",)) # Si usas autenticación, la caché varía según el token
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @method_decorator(cache_page(60 * 1))
    @method_decorator(vary_on_headers("Authorization",))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)