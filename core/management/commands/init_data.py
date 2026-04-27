from django.core.management.base import BaseCommand
from core.models import Matiere, Classe


class Command(BaseCommand):
    help = 'Initialise les données de base (matières, classes)'

    def handle(self, *args, **options):
        matieres_data = [
            {'nom': 'Mathématiques', 'code': 'MATH', 'couleur': '#6366F1'},
            {'nom': 'Physique-Chimie', 'code': 'PC', 'couleur': '#8B5CF6'},
            {'nom': 'Sciences de la Vie et de la Terre', 'code': 'SVT', 'couleur': '#10B981'},
            {'nom': 'Français', 'code': 'FR', 'couleur': '#F59E0B'},
            {'nom': 'Anglais', 'code': 'ANG', 'couleur': '#EF4444'},
            {'nom': 'Histoire-Géographie', 'code': 'HG', 'couleur': '#06B6D4'},
            {'nom': 'Philosophie', 'code': 'PHILO', 'couleur': '#EC4899'},
            {'nom': 'Informatique', 'code': 'INFO', 'couleur': '#14B8A6'},
        ]

        created_count = 0
        for data in matieres_data:
            _, created = Matiere.objects.get_or_create(code=data['code'], defaults=data)
            if created:
                created_count += 1

        classes_data = [
            {'nom': 'Sixième', 'niveau': 'primaire', 'annee_academique': '2025-2026'},
            {'nom': 'Cinquième', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Quatrième', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Troisième', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Seconde', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Première', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Terminale', 'niveau': 'secondaire', 'annee_academique': '2025-2026'},
            {'nom': 'Licence 1', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
            {'nom': 'Licence 2', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
            {'nom': 'Licence 3', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
            {'nom': 'Master 1', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
            {'nom': 'Master 2', 'niveau': 'universitaire', 'annee_academique': '2025-2026'},
        ]

        for data in classes_data:
            _, created = Classe.objects.get_or_create(nom=data['nom'], annee_academique=data['annee_academique'], defaults=data)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'{created_count} entrées créées avec succès.'))
