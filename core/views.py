from django.views.generic import TemplateView
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.utils import timezone
from mailings.models import Mailing, Client


@method_decorator(cache_page(60 * 5), name='dispatch')  # Кеширование страницы на 5 минут
class HomePageView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        # 1. Общее количество всех созданных рассылок
        context['total_mailings'] = Mailing.objects.count()

        # 2. Количество активных рассылок
        # (текущая дата между start_time и end_time, и статус 'started')
        context['active_mailings'] = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            status='started'
        ).count()

        # 3. Количество уникальных получателей (общее число клиентов в системе)
        context['unique_clients'] = Client.objects.count()

        return context