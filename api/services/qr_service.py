import segno
import os
from django.conf import settings

class QRService:
    @staticmethod
    def generate_access_qr(token, context="exam"):
        """
        Génère un QR code pour l'accès à une salle d'examen ou autre.
        """
        # Création du QR Code
        qr = segno.make(token, error='h')
        
        # Nom du fichier
        filename = f"qr_{context}_{token[:8]}.png"
        output_path = os.path.join(settings.MEDIA_ROOT, 'qr_codes', filename)
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Sauvegarde
        qr.save(output_path, scale=10, dark='#6366F1')
        
        return os.path.join('qr_codes', filename)
