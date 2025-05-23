import logging
from django.core.management.base import BaseCommand
from flights.services import FlightDataService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fetches flight data from external API and updates the database using FlightDataService'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting flight data update via service...'))
        logger.info("Management command 'update_flight_data' initiated.")

        service = FlightDataService()
        result = service.update_database_from_api()

        if result.get('success'):
            total_api = result.get('total_from_api', 'N/A')
            processed = result.get('processed', 0)
            created = result.get('created', 0)
            updated = result.get('updated', 0)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Flight data update process finished. "
                    f"Total from API: {total_api}. Processed (limit applied): {processed}. "
                    f"Created: {created}. Updated: {updated}."
                )
            )
            logger.info(
                f"Service execution successful: {result.get('message')} - "
                f"Total API: {total_api}, Processed: {processed}, Created: {created}, Updated: {updated}"
            )
        else:
            error_message = result.get('message', 'Unknown error occurred in service.')
            self.stderr.write(self.style.ERROR(f"Error during flight data update: {error_message}"))
            logger.error(f"Service execution failed: {error_message}")

        self.stdout.write(self.style.SUCCESS('Flight data update command finished.'))