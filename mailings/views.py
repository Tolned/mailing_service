from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect

from .models import Client, Message, Mailing, MailingAttempt
from .forms import ClientForm, MessageForm, MailingForm
from .services import send_mailing


class OwnerFilterMixin(LoginRequiredMixin):
    """Пользователь видит и редактирует только свои объекты, менеджер — все."""

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


class ClientUpdateView(OwnerFilterMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailings/client_form.html'
    success_url = reverse_lazy('mailings:client_list')


class ClientDeleteView(OwnerFilterMixin, DeleteView):
    model = Client
    template_name = 'mailings/client_confirm_delete.html'  # Убедитесь, что этот шаблон есть, или удалите этот класс, если удаление не требуется строго
    success_url = reverse_lazy('mailings:client_list')


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


class MessageUpdateView(OwnerFilterMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')


class MessageDeleteView(OwnerFilterMixin, DeleteView):
    model = Message
    template_name = 'mailings/message_confirm_delete.html'
    success_url = reverse_lazy('mailings:message_list')


# ============================================================
# РАССЫЛКИ
# ============================================================
class MailingListView(OwnerFilterMixin, ListView):
    model = Mailing
    template_name = 'mailings/mailing_list.html'
    context_object_name = 'mailings'
    paginate_by = 10

    # Примечание: Мы НЕ вызываем m.update_status() здесь в цикле,
    # так как это вызывает сохранение в БД при каждом просмотре страницы (ошибка N+1).
    # Статус должен вычисляться динамически через property в модели или при сохранении.


class MailingCreateView(OwnerFilterMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Новая рассылка'
        return context


class MailingUpdateView(OwnerFilterMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')


class MailingDeleteView(OwnerFilterMixin, DeleteView):
    model = Mailing
    template_name = 'mailings/mailing_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')


class MailingSendView(LoginRequiredMixin, DetailView):
    """Запуск рассылки вручную."""
    model = Mailing
    template_name = 'mailings/mailing_detail.html'

    def get(self, request, *args, **kwargs):
        mailing = self.get_object()

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
        context['active_mailings'] = mailings.filter(status=Mailing.STATUS_STARTED).count()
        context['total_clients'] = clients.count()
        context['total_attempts'] = attempts.count()
        context['success_attempts'] = attempts.filter(status=MailingAttempt.STATUS_SUCCESS).count()
        context['fail_attempts'] = attempts.filter(status=MailingAttempt.STATUS_FAIL).count()

        return context


from django.views.generic import UpdateView, DeleteView

# --- КЛИЕНТЫ ---
class ClientUpdateView(OwnerFilterMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = 'mailings/client_form.html'
    success_url = reverse_lazy('mailings:client_list')

class ClientDeleteView(OwnerFilterMixin, DeleteView):
    model = Client
    template_name = 'mailings/object_confirm_delete.html'
    success_url = reverse_lazy('mailings:client_list')

# --- СООБЩЕНИЯ ---
class MessageUpdateView(OwnerFilterMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = 'mailings/message_form.html'
    success_url = reverse_lazy('mailings:message_list')

class MessageDeleteView(OwnerFilterMixin, DeleteView):
    model = Message
    template_name = 'mailings/object_confirm_delete.html'
    success_url = reverse_lazy('mailings:message_list')

# --- РАССЫЛКИ ---
class MailingUpdateView(OwnerFilterMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = 'mailings/mailing_form.html'
    success_url = reverse_lazy('mailings:mailing_list')

class MailingDeleteView(OwnerFilterMixin, DeleteView):
    model = Mailing
    template_name = 'mailings/object_confirm_delete.html'
    success_url = reverse_lazy('mailings:mailing_list')