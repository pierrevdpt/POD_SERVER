import uuid
import qrcode
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PIL import Image
from globals import qrs, qrs_lock
import sys

arguments = sys.argv

if len(arguments) > 1:
    qrin = arguments[1]

if qrin == '':
    qrin = str(uuid.uuid4())



with qrs_lock:
        for qr in qrs:
            if qr['qrcode'] == qrin or qrin == "ALL" :

                img=qrcode.make(qr['qrcode'])
                img_resize = img.resize((128, 128))
                img_resize.save('qrcode.png')

                filename = qr['qrcode'] + ".pdf"
                pdf = canvas.Canvas(filename, pagesize=A4)
                pdf.drawImage(ImageReader('qrcode.png'), 175, 450, 128, 128)
                pdf.setFont('Helvetica', 14)
                pdf.rect(45, 765, 475, 50, stroke=1, fill=0)
                pdf.drawString(75, 430, f"Code unique : {qr['qrcode']}")
                pdf.drawString(50, 800, f"Rest home : {qr['rest_home_name']}")
                pdf.drawString(50, 775, f"secteur   : {qr['logistic_tag']}")
                pdf.drawString(400, 800, f"site      : {qr['site']}")
                pdf.save()
                
