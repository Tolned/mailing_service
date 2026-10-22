from django.views.generic import TemplateView
from django.utils import timezone
from mailings.models import Mailing, Client


class HomePageView(TemplateView):
    template_name = 'core/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()

        context['total_mailings'] = Mailing.objects.count()
        context['active_mailings'] = Mailing.objects.filter(
            start_time__lte=now,
            end_time__gte=now,
            status=Mailing.STATUS_STARTED
        ).count()
        context['unique_clients'] = Client.objects.count()
        return context