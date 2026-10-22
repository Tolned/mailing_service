from django.core.management.base import BaseCommand
from django.utils import timezone
from mailings.models import Mailing
from mailings.services import send_mailing


class Command(BaseCommand):
    help = 'Отправляет рассылки, готовые к запуску'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        mailings = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            is_active=True
        )
        for mailing in mailings:
            try:
                send_mailing(mailing.id)
                self.stdout.write(self.style.SUCCESS(f'Рассылка {mailing.id} успешно отправлена'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Ошибка рассылки {mailing.id}: {e}'))