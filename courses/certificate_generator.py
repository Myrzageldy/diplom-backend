import io
import os
import sys

import qrcode
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def _register_fonts():
    """Регистрирует шрифт с поддержкой кириллицы."""
    candidates = []

    if sys.platform == 'win32':
        font_dir = 'C:/Windows/Fonts'
        candidates = [
            (os.path.join(font_dir, 'arial.ttf'), os.path.join(font_dir, 'arialbd.ttf')),
            (os.path.join(font_dir, 'times.ttf'), os.path.join(font_dir, 'timesbd.ttf')),
        ]
    elif sys.platform == 'darwin':
        candidates = [
            ('/Library/Fonts/Arial.ttf', '/Library/Fonts/Arial Bold.ttf'),
        ]
    else:
        candidates = [
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
            ('/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
             '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'),
        ]

    for regular, bold in candidates:
        if os.path.exists(regular) and os.path.exists(bold):
            try:
                pdfmetrics.registerFont(TTFont('CertFont', regular))
                pdfmetrics.registerFont(TTFont('CertFont-Bold', bold))
                return 'CertFont', 'CertFont-Bold'
            except Exception:
                continue

    return 'Helvetica', 'Helvetica-Bold'


def generate_certificate_pdf(certificate):
    """
    Генерирует PDF-сертификат для объекта Certificate.
    Возвращает BytesIO с содержимым PDF.
    """
    regular, bold = _register_fonts()

    buffer = io.BytesIO()
    w, h = landscape(A4)  # 841.89 x 595.27 pt
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # ── Фон ─────────────────────────────────────────────────────────
    c.setFillColor(HexColor('#F0F4FF'))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Белая внутренняя область
    c.setFillColor(white)
    c.rect(24, 24, w - 48, h - 48, fill=1, stroke=0)

    # Внешняя рамка
    c.setStrokeColor(HexColor('#1D4ED8'))
    c.setLineWidth(5)
    c.rect(18, 18, w - 36, h - 36, fill=0)

    # Внутренняя рамка
    c.setStrokeColor(HexColor('#BFDBFE'))
    c.setLineWidth(1.5)
    c.rect(28, 28, w - 56, h - 56, fill=0)

    # ── Шапка (синяя полоса) ────────────────────────────────────────
    c.setFillColor(HexColor('#1D4ED8'))
    c.rect(18, h - 88, w - 36, 70, fill=1, stroke=0)

    c.setFillColor(white)
    c.setFont(bold, 26)
    c.drawCentredString(w / 2, h - 52, 'EDUPLATFORM KZ')

    c.setFont(regular, 11)
    c.drawCentredString(w / 2, h - 72, 'Образовательная платформа Казахстана')

    # ── Заголовок сертификата ───────────────────────────────────────
    c.setFillColor(HexColor('#1E3A8A'))
    c.setFont(bold, 44)
    c.drawCentredString(w / 2, h - 158, 'СЕРТИФИКАТ')

    c.setStrokeColor(HexColor('#93C5FD'))
    c.setLineWidth(1)
    c.line(w / 2 - 200, h - 168, w / 2 + 200, h - 168)

    # ── Тело ────────────────────────────────────────────────────────
    c.setFillColor(HexColor('#6B7280'))
    c.setFont(regular, 14)
    c.drawCentredString(w / 2, h - 210, 'Настоящим подтверждается, что')

    # Имя студента
    student_name = certificate.student.name
    c.setFillColor(HexColor('#1E3A8A'))
    c.setFont(bold, 34)
    c.drawCentredString(w / 2, h - 258, student_name)

    # Подчёркивание под именем
    name_w = c.stringWidth(student_name, bold, 34)
    c.setStrokeColor(HexColor('#3B82F6'))
    c.setLineWidth(1.2)
    c.line(w / 2 - name_w / 2, h - 267, w / 2 + name_w / 2, h - 267)

    c.setFillColor(HexColor('#6B7280'))
    c.setFont(regular, 14)
    c.drawCentredString(w / 2, h - 298, 'успешно завершил(а) курс')

    # Название курса
    course_title = certificate.course.certificate_title or certificate.course.title
    c.setFillColor(HexColor('#111827'))
    c.setFont(bold, 20)
    c.drawCentredString(w / 2, h - 338, f'«{course_title}»')

    # ── Нижняя часть ────────────────────────────────────────────────
    date_str = certificate.issued_at.strftime('%d.%m.%Y')

    # Левый блок — дата и номер
    c.setFont(regular, 11)
    c.setFillColor(HexColor('#9CA3AF'))
    c.drawString(52, 106, 'Дата выдачи:')
    c.setFillColor(HexColor('#111827'))
    c.setFont(bold, 11)
    c.drawString(152, 106, date_str)

    c.setFont(regular, 11)
    c.setFillColor(HexColor('#9CA3AF'))
    c.drawString(52, 86, 'Номер сертификата:')
    c.setFillColor(HexColor('#111827'))
    c.setFont(bold, 11)
    c.drawString(178, 86, certificate.certificate_number)

    # Центр — линия подписи
    c.setStrokeColor(HexColor('#D1D5DB'))
    c.setLineWidth(1)
    c.line(w / 2 - 90, 96, w / 2 + 90, 96)
    c.setFont(regular, 10)
    c.setFillColor(HexColor('#9CA3AF'))
    c.drawCentredString(w / 2, 82, 'Подпись преподавателя')
    c.drawCentredString(w / 2, 70, certificate.course.teacher.name)

    # ── QR-код ──────────────────────────────────────────────────────
    verify_url = f'http://localhost:3000/kk/verify/{certificate.certificate_number}'
    qr = qrcode.QRCode(version=1, box_size=5, border=2)
    qr.add_data(verify_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color='#1E3A8A', back_color='white')

    qr_buf = io.BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    c.drawImage(ImageReader(qr_buf), w - 168, 54, width=110, height=110)
    c.setFont(regular, 9)
    c.setFillColor(HexColor('#9CA3AF'))
    c.drawCentredString(w - 113, 46, 'Проверить подлинность')

    # ── Нижняя синяя полоса ─────────────────────────────────────────
    c.setFillColor(HexColor('#EFF6FF'))
    c.rect(18, 18, w - 36, 32, fill=1, stroke=0)
    c.setFillColor(HexColor('#BFDBFE'))
    c.setFont(regular, 8)
    c.drawCentredString(w / 2, 28, f'EduPlatform KZ  •  eduplatform.kz  •  {certificate.certificate_number}')

    c.save()
    buffer.seek(0)
    return buffer
