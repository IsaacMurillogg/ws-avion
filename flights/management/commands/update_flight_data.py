# flights/management/commands/update_flight_data.py

import logging
from django.core.management.base import BaseCommand
from flights.services import FlightDataService # Importa la clase del servicio

logger = logging.getLogger(__name__) # Logger para el comando

class Command(BaseCommand):
    help = 'Fetches flight data from external API and updates the database using FlightDataService'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting flight data update via service...'))
        logger.info("Management command 'update_flight_data' initiated.")

        service = FlightDataService()
        result = service.update_database_from_api()

        if result.get('success'):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Flight data update process finished. "
                    f"{result.get('created', 0)} created, "
                    f"{result.get('updated', 0)} updated."
                )
            )
            logger.info(f"Service execution successful: {result.get('message')} - Created: {result.get('created', 0)}, Updated: {result.get('updated', 0)}")
        else:
            error_message = result.get('message', 'Unknown error occurred in service.')
            self.stderr.write(self.style.ERROR(f"Error during flight data update: {error_message}"))
            logger.error(f"Service execution failed: {error_message}")

        self.stdout.write(self.style.SUCCESS('Flight data update command finished.'))