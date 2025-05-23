# flights/services.py

import requests
import os
import logging
from django.utils import timezone as django_timezone
from datetime import datetime, timezone as dt_timezone
from .models import FlightData # Asegúrate de que FlightData esté importado
from django.db import transaction # Para operaciones atómicas

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
        if self.api_key:
            # Ejemplo: headers['Authorization'] = f'Bearer {self.api_key}'
            pass # Adapta según tu API
        params = None
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
        try:
            flight_identifier = str(item_array[0]).strip() if item_array[0] else None
            if not flight_identifier:
                logger.warning(f'Missing flight_id for item: {item_array}. Skipping.')
                return None
            raw_timestamp = item_array[3] if item_array[3] else item_array[4]
            parsed_timestamp = django_timezone.now()
            if raw_timestamp:
                try:
                    parsed_timestamp = datetime.fromtimestamp(int(raw_timestamp), tz=dt_timezone.utc)
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse timestamp '{raw_timestamp}' for {flight_identifier}. Using current time.")
            
            latitude_val = float(item_array[6]) if item_array[6] is not None else None
            longitude_val = float(item_array[5]) if item_array[5] is not None else None
            altitude_val = float(item_array[7] or item_array[13] or 0.0)
            speed_val = float(item_array[9]) if item_array[9] is not None else None
            heading_val = float(item_array[10]) if item_array[10] is not None else None
            
            fields_names = [
                "icao24", "callsign", "origin_country", "time_position", "last_contact",
                "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
                "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
                "spi", "position_source"
            ]
            raw_data_dict = {fields_names[i]: item_array[i] for i in range(min(len(fields_names), len(item_array)))}

            return {
                'flight_id': flight_identifier,
                'latitude': latitude_val,
                'longitude': longitude_val,
                'altitude': altitude_val,
                'speed': speed_val,
                'heading': heading_val,
                'timestamp': parsed_timestamp,
                'raw_data': raw_data_dict
            }
        except IndexError:
            logger.error(f'Error processing item due to IndexError (array too short?): {item_array}')
            return None
        except Exception as e:
            logger.error(f'Error processing item {item_array[0] if item_array and len(item_array)>0 else "N/A"}: {e}')
            return None

    @transaction.atomic # Envuelve la operación en una transacción de base de datos
    def update_database_from_api(self):
        api_response = self._fetch_data_from_external_api()

        if api_response is None:
            # No se borran los datos si no se pudo obtener nada de la API
            return {'success': False, 'message': 'Failed to fetch data from API. Database not modified.', 'created': 0, 'deleted': 0, 'processed': 0}

        # --- ADAPTAR ESTA PARTE A LA ESTRUCTURA DE RESPUESTA DE TU API ---
        api_data_list_full = api_response.get('states') # Ejemplo para OpenSky
        # ---------------------------------------------------------------

        if api_data_list_full is None:
            logger.warning(f"API data does not contain expected data key or it's None. Response: {str(api_response)[:500]}")
            # No se borran los datos si la estructura de la API no es la esperada
            return {'success': False, 'message': "API data structure not as expected. Database not modified.", 'created': 0, 'deleted': 0, 'processed': 0}

        if not isinstance(api_data_list_full, list):
            logger.warning(f"Expected data from API is not a list: {type(api_data_list_full)}. Data: {str(api_data_list_full)[:200]}")
            # No se borran los datos si la estructura de la API no es la esperada
            return {'success': False, 'message': "Expected data from API is not a list. Database not modified.", 'created': 0, 'deleted': 0, 'processed': 0}

        # --- Borrar todos los registros existentes de FlightData ---
        try:
            num_deleted, _ = FlightData.objects.all().delete()
            logger.info(f"Successfully deleted {num_deleted} existing flight data records.")
        except Exception as e:
            logger.error(f"Error deleting existing flight data records: {e}")
            # Decide si quieres continuar o fallar aquí. Por ahora, continuamos pero reportamos.
            return {'success': False, 'message': f"Error deleting existing flight data: {e}", 'created': 0, 'deleted': 0, 'processed': 0}
        # ---------------------------------------------------------

        if not api_data_list_full:
            logger.info('No data items received from API or extracted list is empty. All previous data deleted.')
            return {'success': True, 'message': 'No new data items to process. All previous data deleted.', 'created': 0, 'deleted': num_deleted, 'processed': 0}

        limit = 350
        api_data_list_limited = api_data_list_full[:limit]
        logger.info(f"Obtained {len(api_data_list_full)} items from API. Processing up to {len(api_data_list_limited)} items after deleting old data.")

        created_count = 0
        processed_in_batch = 0
        
        # Lista para bulk_create
        flights_to_create = []

        for item_data in api_data_list_limited:
            if not isinstance(item_data, list): # Adaptar si tu API devuelve lista de dicts
                logger.warning(f"Skipping non-list item in API data: {item_data}")
                continue

            processed_data = self._process_api_item(item_data)
            if not processed_data:
                continue
            
            # En lugar de update_or_create, creamos instancias para bulk_create
            flights_to_create.append(FlightData(**processed_data))
            processed_in_batch +=1

        # --- Insertar los nuevos registros usando bulk_create para eficiencia ---
        if flights_to_create:
            try:
                FlightData.objects.bulk_create(flights_to_create)
                created_count = len(flights_to_create)
                logger.info(f"Successfully bulk created {created_count} new flight data records.")
            except Exception as e:
                logger.error(f"Error bulk creating new flight data records: {e}")
                # Si bulk_create falla, la transacción debería hacer rollback debido a @transaction.atomic
                return {'success': False, 'message': f"Error bulk creating new flight data: {e}", 'created': 0, 'deleted': num_deleted, 'processed': processed_in_batch}
        # --------------------------------------------------------------------

        logger.info(f'Flight data update complete. Processed: {processed_in_batch}. Created: {created_count}. Previous Deleted: {num_deleted}.')
        return {
            'success': True,
            'message': 'Data update process finished (delete and reload).',
            'created': created_count,
            'deleted': num_deleted,
            'processed': processed_in_batch,
            'total_from_api': len(api_data_list_full)
        }