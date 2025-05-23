from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FlightDataViewSet

router = DefaultRouter()
router.register(r'flightdata', FlightDataViewSet, basename='flightdata')

urlpatterns = [
    path('', include(router.urls)),
]