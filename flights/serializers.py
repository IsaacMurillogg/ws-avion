from rest_framework import serializers
from .models import FlightData

class FlightDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightData
        fields = '__all__' # O especifica los campos que quieres exponer:
                           # ['flight_id', 'latitude', 'longitude', 'altitude', 'speed', 'heading', 'timestamp']