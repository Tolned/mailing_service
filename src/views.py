from django.views.generic import DetailView, TemplateView
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db import transaction

from models import Mailing, Client, MailingAttempt


class MailingDetailView(DetailView):
    model = Mailing
    template_name = "mailing/detail.html"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.update_status()  # Пересчет статуса
        return obj


class HomePageView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Считаем общие и активные рассылки
        context["total_mailings"] = Mailing.objects.count()
        context["active_mailings"] = Mailing.objects.filter(status=Mailing.STATUS_STARTED).count()
        context["unique_clients"] = Client.objects.count()
        return context


def send_mailing(mailing_id):
    mailing = Mailing.objects.get(id=mailing_id)

    # 1. Проверка времени
    now = timezone.now()
    if not (mailing.start_time <= now <= mailing.end_time):
        raise ValueError("Отправка запрещена: текущее время вне окна рассылки.")

    if not mailing.is_active:
        raise ValueError("Рассылка заблокирована администратором.")

    recipients = mailing.recipients.all()
    attempts_to_create = []

    # 2. Отправка и сбор данных для batch
    for client in recipients:
        try:
            send_mail(
                subject=mailing.message.subject,
                message=mailing.message.body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[client.email],
                fail_silently=False,
            )
            attempts_to_create.append(
                MailingAttempt(mailing=mailing, status=MailingAttempt.STATUS_SUCCESS, server_response="OK")
            )
        except Exception as e:
            attempts_to_create.append(
                MailingAttempt(mailing=mailing, status=MailingAttempt.STATUS_FAIL, server_response=str(e))
            )

    # 3. Batch создание (согласно ТЗ)
    with transaction.atomic():
        MailingAttempt.objects.bulk_create(attempts_to_create)
