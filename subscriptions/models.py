import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class SubscriptionPlan(models.Model):
    class Level(models.TextChoices):
        FREE = 'FREE', 'Gratuit'
        PRO = 'PRO', 'Professionnel'
        ELITE = 'ELITE', 'Elite / École'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=Level.choices, default=Level.FREE)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    duration_days = models.IntegerField(default=30) # 0 pour illimité
    description = models.TextField(blank=True)
    features = models.JSONField(default=list) # Liste des avantages (ex: ["IA Illimitée", "Certificats PDF"])
    is_active = models.BooleanField(default=True)
    is_popular = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"

class UserSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.end_date and self.plan.duration_days > 0:
            self.end_date = timezone.now() + timedelta(days=self.plan.duration_days)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        if not self.end_date:
            return False
        return timezone.now() > self.end_date

    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
