from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils import timezone

from .models import Client, Message, Mailing, MailingAttempt
from .forms import ClientForm, MessageForm, MailingForm
from .services import send_mailing


# ============================================================
# МИКСИН: Фильтрация по владельцу (обычный юзер видит только своё)
# ============================================================
class OwnerFilterMixin(LoginRequiredMixin):
    """Пользователь видит только свои объекты, менеджер — все."""

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.profile.role == 'manager':
            return qs
        return qs.filter(owner=self.request.user)

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


# ============================================================
# КЛИЕНТЫ
# ============================================================
class ClientListView(OwnerFilterMixin, ListView):
    model = Client
    template_name = 'mailings/client_list.html'
    context_object_name = 'clients'
    paginate_by = 10


class ClientCreateView(OwnerFilterMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailings/client_form.html'
    success_url = reverse_lazy('mailings:client_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Новый получатель'
        return context


# ============================================================
# СООБЩЕНИЯ
# ============================================================
class MessageListView(OwnerFilterMixin, ListView):
    model = Message
    template_name = 'mailings/message_list.html'
    context_object_name = 'messages'
    paginate_by = 10


class MessageCreateView(OwnerFilterMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Новое сообщение'
        return context


# ============================================================
# РАССЫЛКИ
# ============================================================
class MailingListView(OwnerFilterMixin, ListView):
    model = Mailing
    template_name = 'mailings/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    def get_queryset(self):
        qs = super().get_queryset()
        for m in qs:
            m.update_status()
        return qs


class MailingCreateView(OwnerFilterMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Новая рассылка'
        return context


class MailingSendView(LoginRequiredMixin, DetailView):
    """Запуск рассылки вручную."""
    model = Mailing
    template_name = 'mailings/mailing_detail.html'

    def get(self, request, *args, **kwargs):
        mailing = self.get_object()

        # Проверка владельца (менеджер может всё)
        if request.user.profile.role != 'manager' and mailing.owner != request.user:
            messages.error(request, 'У вас нет прав на эту рассылку.')
            return redirect('mailings:mailing_list')

        try:
            send_mailing(mailing.id)
            mailing.status = Mailing.STATUS_STARTED
            mailing.save(update_fields=['status'])
            messages.success(request, f'Рассылка #{mailing.pk} успешно запущена!')
        except ValueError as e:
            messages.error(request, str(e))
        except Exception as e:
            messages.error(request, f'Ошибка отправки: {e}')

        return redirect('mailings:mailing_list')


# ============================================================
# СТАТИСТИКА ПОЛЬЗОВАТЕЛЯ
# ============================================================
class UserStatsView(LoginRequiredMixin, TemplateView):
    template_name = 'mailings/user_stats.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        if user.profile.role == 'manager':
            mailings = Mailing.objects.all()
            clients = Client.objects.all()
        else:
            mailings = Mailing.objects.filter(owner=user)
            clients = Client.objects.filter(owner=user)

        attempts = MailingAttempt.objects.filter(mailing__in=mailings)

        context['total_mailings'] = mailings.count()
        context['active_mailings'] = mailings.filter(
            status=Mailing.STATUS_STARTED
        ).count()
        context['total_clients'] = clients.count()
        context['total_attempts'] = attempts.count()
        context['success_attempts'] = attempts.filter(
            status=MailingAttempt.STATUS_SUCCESS
        ).count()
        context['fail_attempts'] = attempts.filter(
            status=MailingAttempt.STATUS_FAIL
        ).count()

        return context