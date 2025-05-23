# flights/services.py (con adaptaciones para OpenSky)

import requests
import os
import logging
from django.utils import timezone
from datetime import datetime
from .models import FlightData

logger = logging.getLogger(__name__)

EXTERNAL_API_URL = os.environ.get('EXTERNAL_API_URL')
EXTERNAL_API_KEY = os.environ.get('EXTERNAL_API_KEY') # No usado por OpenSky para /states/all

class FlightDataService:
    def __init__(self):
        if not EXTERNAL_API_URL:
            logger.error("EXTERNAL_API_URL no está configurada en las variables de entorno.")
        self.api_url = EXTERNAL_API_URL
        self.api_key = EXTERNAL_API_KEY

    def _fetch_data_from_external_api(self):
        if not self.api_url:
            logger.error("No se puede obtener datos: EXTERNAL_API_URL no está configurada.")
            return None

        headers = {} # OpenSky /states/all no necesita headers especiales
        # Si tu API real necesita una key en el header:
        # if self.api_key:
        #     headers['Authorization'] = f'Bearer {self.api_key}' # o 'X-API-Key': self.api_key

        try:
            logger.info(f"Fetching data from {self.api_url}")
            response = requests.get(self.api_url, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from API: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing JSON response from API: {e}")
            return None

    def _process_api_item(self, item_array): # OpenSky devuelve un array de datos
        """
        Procesa un solo ítem (array) de la respuesta de OpenSky.
        Orden de los campos en el array de OpenSky:
        [0] icao24, [1] callsign, [2] origin_country, [3] time_position, [4] last_contact,
        [5] longitude, [6] latitude, [7] baro_altitude, [8] on_ground, [9] velocity,
        [10] true_track, [11] vertical_rate, [12] sensors, [13] geo_altitude,
        [14] squawk, [15] spi, [16] position_source
        """
        try:
            icao24 = str(item_array[0]).strip() if item_array[0] else None
            if not icao24:
                logger.warning(f'Missing icao24 for item: {item_array}. Skipping.')
                return None

            # El timestamp de OpenSky es epoch en segundos
            raw_timestamp = item_array[3] if item_array[3] else item_array[4] # time_position o last_contact
            parsed_timestamp = None
            if raw_timestamp:
                try:
                    parsed_timestamp = datetime.fromtimestamp(int(raw_timestamp), tz=timezone.utc)
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse timestamp '{raw_timestamp}' for {icao24}.")
                    parsed_timestamp = timezone.now()
            else:
                parsed_timestamp = timezone.now()

            # Crear un diccionario con los datos crudos para el campo raw_data
            # Esto es útil porque el formato de OpenSky es un array posicional
            fields_names = [
                "icao24", "callsign", "origin_country", "time_position", "last_contact",
                "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
                "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
                "spi", "position_source"
            ]
            raw_data_dict = {fields_names[i]: item_array[i] for i in range(min(len(fields_names), len(item_array)))}


            return {
                'flight_id': icao24, # Usamos icao24 como identificador único
                'latitude': float(item_array[6]) if item_array[6] is not None else None,
                'longitude': float(item_array[5]) if item_array[5] is not None else None,
                'altitude': float(item_array[7] or item_array[13] or 0.0), # baro_altitude o geo_altitude
                'speed': float(item_array[9]) if item_array[9] is not None else None, # velocity
                'heading': float(item_array[10]) if item_array[10] is not None else None, # true_track
                'timestamp': parsed_timestamp,
                'raw_data': raw_data_dict # Guardamos el dict de datos crudos
            }
        except IndexError:
            logger.error(f'Error processing item due to IndexError (array too short?): {item_array}')
            return None
        except Exception as e:
            logger.error(f'Error processing item {item_array[0] if item_array else "N/A"}: {e}')
            return None

    def update_database_from_api(self):
        api_response = self._fetch_data_from_external_api()

        if api_response is None:
            return {'success': False, 'message': 'Failed to fetch data from API.', 'created': 0, 'updated': 0}

        # OpenSky devuelve los datos en la clave "states", que es una lista de listas
        api_data_list = api_response.get('states')

        if api_data_list is None : # Si 'states' no existe o es None
            logger.warning(f"API data does not contain 'states' key or it's None. Response: {str(api_response)[:500]}")
            return {'success': False, 'message': "API data does not contain 'states' key or it's None.", 'created': 0, 'updated': 0}

        if not isinstance(api_data_list, list): # Si 'states' no es una lista
             logger.warning(f"'states' key in API data is not a list: {type(api_data_list)}. Data: {str(api_data_list)[:200]}")
             return {'success': False, 'message': "'states' key in API data is not a list.", 'created': 0, 'updated': 0}

        if not api_data_list:
            logger.info('No data items received from API or extracted list is empty.')
            return {'success': True, 'message': 'No data items to process.', 'created': 0, 'updated': 0}

        created_count = 0
        updated_count = 0

        for item_array in api_data_list: # Iteramos sobre la lista de arrays de OpenSky
            if not isinstance(item_array, list): # Cada item debe ser una lista
                logger.warning(f"Skipping non-list item in 'states': {item_array}")
                continue

            processed_data = self._process_api_item(item_array)
            if not processed_data:
                continue

            flight_identifier = processed_data.pop('flight_id')

            try:
                obj, created = FlightData.objects.update_or_create(
                    flight_id=flight_identifier,
                    defaults=processed_data
                )
                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                logger.error(f"Error saving data for flight {flight_identifier} to DB: {e}")

        logger.info(f'Flight data update complete. {created_count} created, {updated_count} updated.')
        return {
            'success': True,
            'message': 'Data update process finished.',
            'created': created_count,
            'updated': updated_count
        }