from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    ROLE_USER = 'user'
    ROLE_MANAGER = 'manager'
    ROLE_CHOICES = [(ROLE_USER, 'Пользователь'), (ROLE_MANAGER, 'Менеджер')]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_USER, verbose_name='Роль')
    is_blocked = models.BooleanField(default=False, verbose_name='Заблокирован')

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f"Профиль {self.user.username} ({self.get_role_display()})"


# Автоматическое создание профиля при регистрации
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)