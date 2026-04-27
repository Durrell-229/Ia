import uuid
from django.db import models
from django.utils.translation import gettext_lazy as _

# Listes basées sur le système éducatif béninois et standards internationaux
CLASSE_CHOICES = [
    ('PRIMAIRE', (
        ('CI', 'Cours d\'Initiation'),
        ('CP', 'Cours Préparatoire'),
        ('CE1', 'Cours Élémentaire 1'),
        ('CE2', 'Cours Élémentaire 2'),
        ('CM1', 'Cours Moyen 1'),
        ('CM2', 'Cours Moyen 2'),
    )),
    ('SECONDAIRE', (
        ('6E', '6ème'),
        ('5E', '5ème'),
        ('4E', '4ème'),
        ('3E', '3ème'),
        ('2NDE_A', '2nde A'),
        ('2NDE_C', '2nde C'),
        ('1ERE_A', '1ère A'),
        ('1ERE_C', '1ère C'),
        ('1ERE_D', '1ère D'),
        ('TLE_A', 'Terminale A'),
        ('TLE_C', 'Terminale C'),
        ('TLE_D', 'Terminale D'),
    )),
    ('UNIVERSITAIRE', (
        ('L1', 'Licence 1'),
        ('L2', 'Licence 2'),
        ('L3', 'Licence 3'),
        ('M1', 'Master 1'),
        ('M2', 'Master 2'),
    ))
]

MATIERE_CHOICES = [
    ('MATHS', 'Mathématiques'),
    ('PC', 'Physique-Chimie'),
    ('SVT', 'Sciences de la Vie et de la Terre'),
    ('FRANCAIS', 'Français'),
    ('ANGLAIS', 'Anglais'),
    ('HIST_GEO', 'Histoire et Géographie'),
    ('PHILO', 'Philosophie'),
    ('ESPAGNOL', 'Espagnol'),
    ('ALLEMAND', 'Allemand'),
    ('TIC', 'Technologie de l\'Information et de la Communication'),
]

# Liste exhaustive des pays
PAYS_CHOICES = [
    ('BJ', 'Bénin'), ('FR', 'France'), ('TG', 'Togo'), ('CI', 'Côte d\'Ivoire'),
    ('SN', 'Sénégal'), ('NG', 'Nigeria'), ('US', 'États-Unis'), ('CA', 'Canada'),
]
