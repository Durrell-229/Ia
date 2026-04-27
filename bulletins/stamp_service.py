import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from pypdf import PdfReader, PdfWriter

def add_official_stamp(input_pdf_path, output_pdf_path, signature_img_path, stamp_img_path):
    """
    Superpose une signature et un cachet officiel sur la première page d'un PDF.
    """
    # 1. Créer le tampon en mémoire
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    
    # Positionnement du cachet (ex: en bas à droite)
    can.drawImage(stamp_img_path, 400, 100, width=120, height=120, mask='auto')
    
    # Positionnement de la signature (ex: légèrement au-dessus du cachet)
    can.drawImage(signature_img_path, 420, 150, width=100, height=50, mask='auto')
    
    can.save()
    packet.seek(0)
    
    # 2. Fusionner avec le PDF original
    new_pdf = PdfReader(packet)
    existing_pdf = PdfReader(open(input_pdf_path, "rb"))
    output = PdfWriter()
    
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    output.add_page(page)
    
    # Ajouter les autres pages si elles existent
    for i in range(1, len(existing_pdf.pages)):
        output.add_page(existing_pdf.pages[i])
        
    with open(output_pdf_path, "wb") as outputStream:
        output.write(outputStream)
