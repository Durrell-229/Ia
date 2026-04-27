import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrateur')
        CONSEILLER = 'conseiller', _('Conseiller Pédagogique')
        PROFESSEUR = 'professeur', _('Professeur')
        ELEVE = 'eleve', _('Élève / Étudiant')

    class Niveau(models.TextChoices):
        PRIMAIRE = 'primaire', _('Primaire')
        SECONDAIRE = 'secondaire', _('Secondaire')
        UNIVERSITAIRE = 'universitaire', _('Universitaire')
        PROFESSIONNEL = 'professionnel', _('Formation Professionnelle')
        ENTREPRISE = 'entreprise', _('Entreprise')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('adresse email'), unique=True)
    first_name = models.CharField(_('prénom'), max_length=150)
    last_name = models.CharField(_('nom'), max_length=150)
    phone = models.CharField(_('téléphone'), max_length=30, blank=True)
    country = models.CharField(_('pays'), max_length=100, default='France')
    role = models.CharField(_('rôle'), max_length=20, choices=Role.choices, default=Role.ELEVE)
    niveau = models.CharField(_('niveau'), max_length=20, choices=Niveau.choices, blank=True)
    classe = models.CharField(_('classe / promotion'), max_length=100, blank=True)
    matricule = models.CharField(_('matricule'), max_length=50, blank=True, unique=True, null=True)
    avatar = models.ImageField(_('photo de profil'), upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(_('biographie'), blank=True)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    preferred_language = models.CharField(max_length=5, default='fr')
    dark_mode = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = _('utilisateur')
        verbose_name_plural = _('utilisateurs')
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def generate_matricule(self):
        if not self.matricule:
            prefix = self.role[:3].upper()
            year = timezone.now().year
            count = User.objects.filter(role=self.role).count() + 1
            self.matricule = f"{prefix}-{year}-{count:05d}"

    def save(self, *args, **kwargs):
        if not self.matricule:
            self.generate_matricule()
        
        # Accorder l'accès technique si le rôle est admin
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
            
        super().save(*args, **kwargs)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    birth_date = models.DateField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True)
    school = models.CharField(max_length=200, blank=True)
    specialite = models.CharField(max_length=200, blank=True)
    total_points = models.IntegerField(default=0)
    badges = models.JSONField(default=list)
    completed_exams = models.IntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    rank = models.IntegerField(default=0)

    def __str__(self):
        return f"Profil de {self.user.full_name}"
