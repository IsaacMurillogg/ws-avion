import requests
import os
import logging
from django.utils import timezone as django_timezone
from datetime import datetime, timezone as dt_timezone
from .models import FlightData

logger = logging.getLogger(__name__)

MODULE_EXTERNAL_API_URL = os.environ.get('EXTERNAL_API_URL')
MODULE_EXTERNAL_API_KEY = os.environ.get('EXTERNAL_API_KEY')

class FlightDataService:
    def __init__(self):
        self.api_url = MODULE_EXTERNAL_API_URL
        self.api_key = MODULE_EXTERNAL_API_KEY

        if not self.api_url:
            logger.error("FlightDataService initialized, but EXTERNAL_API_URL is not set/empty in environment.")

    def _fetch_data_from_external_api(self):
        if not self.api_url:
            logger.error("Cannot fetch data: api_url is not configured or is empty.")
            return None

        headers = {}
        # --- ADAPTAR AUTENTICACIÓN DE API AQUÍ ---
        if self.api_key:
            # Ejemplo: headers['Authorization'] = f'Bearer {self.api_key}'
            # Ejemplo para OpenSky (no necesita key para /states/all, pero si usaras otra cosa):
            # headers['X-API-Key'] = self.api_key # O como tu API lo requiera
            pass # OpenSky /states/all no necesita auth. Si tu API sí, descomenta y ajusta.

        params = None # Añade parámetros si tu API los necesita, ej: {'active': 'true'}

        try:
            logger.info(f"Fetching data from {self.api_url}")
            response = requests.get(self.api_url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching data from API: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing JSON response from API: {e}")
            return None

    def _process_api_item(self, item_array): # ADAPTADO PARA EL EJEMPLO DE OpenSky
        """
        Procesa un solo ítem (array) de la respuesta de OpenSky.
        [0] icao24, [1] callsign, ..., [3] time_position, ..., [5] longitude, [6] latitude, etc.
        ¡DEBES ADAPTAR ESTO COMPLETAMENTE A LA ESTRUCTURA DE TU API REAL!
        """
        try:
            # Ejemplo para OpenSky - ADAPTAR ESTOS ÍNDICES Y CAMPOS A TU API
            flight_identifier = str(item_array[0]).strip() if item_array[0] else None # icao24 para OpenSky
            if not flight_identifier:
                logger.warning(f'Missing flight_id (e.g., icao24) for item: {item_array}. Skipping.')
                return None

            # Timestamp (epoch en segundos para OpenSky)
            raw_timestamp = item_array[3] if item_array[3] else item_array[4] # time_position o last_contact
            parsed_timestamp = django_timezone.now() # Fallback
            if raw_timestamp:
                try:
                    parsed_timestamp = datetime.fromtimestamp(int(raw_timestamp), tz=dt_timezone.utc)
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse timestamp '{raw_timestamp}' for {flight_identifier}. Using current time.")
            
            # Ejemplo de campos para OpenSky - ADAPTAR
            latitude_val = float(item_array[6]) if item_array[6] is not None else None
            longitude_val = float(item_array[5]) if item_array[5] is not None else None
            altitude_val = float(item_array[7] or item_array[13] or 0.0) # baro_altitude o geo_altitude
            speed_val = float(item_array[9]) if item_array[9] is not None else None
            heading_val = float(item_array[10]) if item_array[10] is not None else None
            
            # Para guardar los datos crudos de OpenSky como un diccionario más legible
            fields_names = [
                "icao24", "callsign", "origin_country", "time_position", "last_contact",
                "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
                "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
                "spi", "position_source"
            ] # ADAPTAR SI LOS CAMPOS DE TU API SON DIFERENTES
            raw_data_dict = {fields_names[i]: item_array[i] for i in range(min(len(fields_names), len(item_array)))}

            return {
                'flight_id': flight_identifier,
                'latitude': latitude_val,
                'longitude': longitude_val,
                'altitude': altitude_val,
                'speed': speed_val,
                'heading': heading_val,
                'timestamp': parsed_timestamp,
                'raw_data': raw_data_dict # O simplemente `item_array` si prefieres el array original
            }
        except IndexError:
            logger.error(f'Error processing item due to IndexError (array too short?): {item_array}')
            return None
        except Exception as e:
            logger.error(f'Error processing item {item_array[0] if item_array and len(item_array)>0 else "N/A"}: {e}')
            return None

    def update_database_from_api(self):
        api_response = self._fetch_data_from_external_api()

        if api_response is None:
            return {'success': False, 'message': 'Failed to fetch data from API.', 'created': 0, 'updated': 0, 'processed': 0}

        # --- ADAPTAR ESTA PARTE A LA ESTRUCTURA DE RESPUESTA DE TU API ---
        # Ejemplo para OpenSky: los datos están en la clave "states", que es una lista de listas
        api_data_list_full = api_response.get('states')
        # Si tu API devuelve directamente una lista: api_data_list_full = api_response
        # Si está en otra clave: api_data_list_full = api_response.get('tu_clave_de_datos')
        # ---------------------------------------------------------------

        if api_data_list_full is None:
            logger.warning(f"API data does not contain expected data key or it's None. Response: {str(api_response)[:500]}")
            return {'success': False, 'message': "API data structure not as expected or data key is None.", 'created': 0, 'updated': 0, 'processed': 0}

        if not isinstance(api_data_list_full, list):
            logger.warning(f"Expected data from API is not a list: {type(api_data_list_full)}. Data: {str(api_data_list_full)[:200]}")
            return {'success': False, 'message': "Expected data from API is not a list.", 'created': 0, 'updated': 0, 'processed': 0}

        if not api_data_list_full:
            logger.info('No data items received from API or extracted list is empty.')
            return {'success': True, 'message': 'No data items to process.', 'created': 0, 'updated': 0, 'processed': 0}

        limit = 350
        api_data_list_limited = api_data_list_full[:limit]
        logger.info(f"Obtained {len(api_data_list_full)} items from API. Processing up to {len(api_data_list_limited)} items.")

        created_count = 0
        updated_count = 0
        processed_in_batch = 0

        for item_data in api_data_list_limited: # item_data será un array para OpenSky, o un dict para otras APIs
            # --- ADAPTAR ESTA VERIFICACIÓN SI TU API NO DEVUELVE UNA LISTA DE LISTAS ---
            if not isinstance(item_data, list): # Para OpenSky (lista de listas)
            # if not isinstance(item_data, dict): # Si tu API devuelve una lista de diccionarios
                logger.warning(f"Skipping non-list/dict item in API data: {item_data}")
                continue
            # ----------------------------------------------------------------------

            processed_data = self._process_api_item(item_data) # Pasa el item individual
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
                processed_in_batch +=1
            except Exception as e:
                logger.error(f"Error saving data for flight {flight_identifier} to DB: {e}")

        logger.info(f'Flight data update complete. Processed: {processed_in_batch}. Created: {created_count}. Updated: {updated_count}.')
        return {
            'success': True,
            'message': 'Data update process finished.',
            'created': created_count,
            'updated': updated_count,
            'processed': processed_in_batch,
            'total_from_api': len(api_data_list_full)
        }