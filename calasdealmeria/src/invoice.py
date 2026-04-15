"""
Generador de recibos de arrendamiento en PDF.
Usa reportlab. Si no esta disponible muestra un error claro.
"""
import os
from datetime import date


MESES = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
         "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]


def _fmt_eur(v):
    try:
        s = f"{float(v or 0):,.2f} EUR"
        return s.replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception:
        return "0,00 EUR"


def generate_receipt(pago: dict, contrato: dict, inquilino: dict,
                     apartamento: dict, cfg: dict, output_path: str) -> str:
    """
    Genera un recibo PDF de arrendamiento.

    Returns: ruta absoluta del PDF generado.
    Raises: ImportError si reportlab no esta instalado.
            Exception con descripcion del error en caso de fallo.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.lib.colors import HexColor, black, white
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    except ImportError:
        raise ImportError(
            "La libreria 'reportlab' no esta instalada.\n"
            "Ejecuta:  pip install reportlab"
        )

    # ── Colors ──────────────────────────────────────────────────────
    NAVY   = HexColor("#1A2F4E")
    AMBER  = HexColor("#F6AD55")
    LIGHT  = HexColor("#EEF2F7")
    GRAY   = HexColor("#718096")
    DARK   = HexColor("#1A202C")

    # ── Styles ──────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', fontSize=22, textColor=white, leading=26,
                        fontName='Helvetica-Bold', alignment=TA_LEFT)
    h2 = ParagraphStyle('h2', fontSize=11, textColor=GRAY, leading=14,
                        fontName='Helvetica', alignment=TA_LEFT)
    label_s = ParagraphStyle('label', fontSize=8, textColor=GRAY,
                             fontName='Helvetica-Bold', spaceAfter=1,
                             leading=10, textTransform='uppercase')
    value_s = ParagraphStyle('value', fontSize=10, textColor=DARK,
                             fontName='Helvetica', leading=13)
    total_s = ParagraphStyle('total', fontSize=18, textColor=NAVY,
                             fontName='Helvetica-Bold', alignment=TA_RIGHT)
    footer_s = ParagraphStyle('footer', fontSize=8, textColor=GRAY,
                              fontName='Helvetica', alignment=TA_CENTER, leading=11)
    note_s = ParagraphStyle('note', fontSize=9, textColor=GRAY,
                            fontName='Helvetica-Oblique', leading=12)

    # ── Data ────────────────────────────────────────────────────────
    mes_num = pago.get('mes', 1) or 1
    mes_nombre = MESES[mes_num - 1] if 1 <= mes_num <= 12 else str(mes_num)
    anyo = pago.get('anyo', date.today().year)
    importe = pago.get('importe', 0) or 0
    fecha_pago = pago.get('fecha_pago') or str(date.today())
    try:
        d = date.fromisoformat(fecha_pago)
        fecha_pago_str = d.strftime("%d/%m/%Y")
    except Exception:
        fecha_pago_str = fecha_pago
    num_recibo = f"REC-{anyo}{mes_num:02d}-{pago.get('id', 0):04d}"

    inq_nombre = f"{inquilino.get('nombre', '')} {inquilino.get('apellidos', '')}".strip()
    inq_dni = inquilino.get('dni_nie', '') or ''
    inq_tel = inquilino.get('telefono', '') or ''
    inq_email = inquilino.get('email', '') or ''

    apt_nombre = apartamento.get('nombre', '') or ''
    apt_dir = apartamento.get('direccion', '') or ''

    arr_nombre = cfg.get('nombre_arrendador', '') or ''
    arr_nif = cfg.get('nif_arrendador', '') or ''
    arr_dir = cfg.get('direccion_arrendador', '') or ''
    arr_cp = cfg.get('cp_ciudad_arrendador', '') or ''
    arr_tel = cfg.get('telefono_arrendador', '') or ''
    arr_email = cfg.get('email_arrendador', '') or ''

    # ── Build document ──────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.8*cm,
        leftMargin=1.8*cm,
        topMargin=1.5*cm,
        bottomMargin=2*cm,
    )

    story = []
    page_w = A4[0] - 3.6*cm   # usable width

    # Header banner
    header_data = [[
        Paragraph("RECIBO DE<br/>ARRENDAMIENTO", h1),
        Paragraph(
            f"<b>N.° {num_recibo}</b><br/>"
            f"Fecha: {fecha_pago_str}<br/>"
            f"Periodo: {mes_nombre} {anyo}",
            ParagraphStyle('hdr_right', fontSize=10, textColor=white,
                           fontName='Helvetica', alignment=TA_RIGHT, leading=15)
        ),
    ]]
    header_table = Table(header_data, colWidths=[page_w * 0.55, page_w * 0.45])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('PADDING', (0, 0), (-1, -1), 16),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [NAVY]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.5*cm))

    # Amber accent line
    story.append(HRFlowable(width="100%", thickness=3, color=AMBER, spaceAfter=0.4*cm))

    # ── Parties table ────────────────────────────────────────────────
    def info_block(title, lines):
        parts = [Paragraph(title, ParagraphStyle(
            'sec_title', fontSize=9, textColor=white, fontName='Helvetica-Bold',
            alignment=TA_CENTER
        ))]
        for lbl, val in lines:
            if lbl:
                parts.append(Paragraph(lbl, label_s))
            parts.append(Paragraph(val or '—', value_s))
        return parts

    arr_block = info_block("ARRENDADOR", [
        ("Nombre", arr_nombre),
        ("NIF / NIE", arr_nif),
        ("Dirección", arr_dir),
        ("", arr_cp),
        ("Teléfono", arr_tel),
        ("Email", arr_email),
    ])
    inq_block = info_block("ARRENDATARIO", [
        ("Nombre", inq_nombre),
        ("DNI / NIE", inq_dni),
        ("Teléfono", inq_tel),
        ("Email", inq_email),
        ("", ""),
        ("", ""),
    ])

    parties = Table(
        [[arr_block, inq_block]],
        colWidths=[page_w * 0.5 - 0.3*cm, page_w * 0.5 - 0.3*cm],
        hAlign='LEFT',
    )
    parties.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), NAVY),
        ('BACKGROUND', (1, 0), (1, 0), HexColor("#253D58")),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('ROUNDEDCORNERS', [4, 4, 4, 4]),
        ('COLPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(parties)
    story.append(Spacer(1, 0.5*cm))

    # ── Apartment ────────────────────────────────────────────────────
    apt_data = [[
        Paragraph("INMUEBLE ARRENDADO", label_s),
        Paragraph(f"{apt_nombre}  —  {apt_dir}", value_s),
    ]]
    apt_table = Table(apt_data, colWidths=[page_w * 0.25, page_w * 0.75])
    apt_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E0")),
    ]))
    story.append(apt_table)
    story.append(Spacer(1, 0.5*cm))

    # ── Concept table ────────────────────────────────────────────────
    tipo = pago.get('tipo', 'alquiler') or 'alquiler'
    concepto = f"Renta de arrendamiento — {mes_nombre} {anyo}"
    if tipo != 'alquiler':
        concepto = f"{tipo.capitalize()} — {mes_nombre} {anyo}"
    metodo = pago.get('metodo', '') or ''

    concept_data = [
        [
            Paragraph("CONCEPTO", label_s),
            Paragraph("PERIODO", label_s),
            Paragraph("MÉTODO DE PAGO", label_s),
            Paragraph("IMPORTE", ParagraphStyle('lbl_r', fontSize=8, textColor=GRAY,
                      fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        ],
        [
            Paragraph(concepto, value_s),
            Paragraph(f"{mes_nombre} {anyo}", value_s),
            Paragraph(metodo or '—', value_s),
            Paragraph(f"<b>{_fmt_eur(importe)}</b>",
                      ParagraphStyle('val_r', fontSize=11, textColor=DARK,
                                     fontName='Helvetica-Bold', alignment=TA_RIGHT)),
        ],
    ]
    concept_table = Table(
        concept_data,
        colWidths=[page_w * 0.38, page_w * 0.18, page_w * 0.24, page_w * 0.20],
    )
    concept_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), LIGHT),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor("#CBD5E0")),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, HexColor("#CBD5E0")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(concept_table)
    story.append(Spacer(1, 0.3*cm))

    # ── Total ────────────────────────────────────────────────────────
    total_data = [[
        Paragraph("TOTAL PAGADO", label_s),
        Paragraph(f"<b>{_fmt_eur(importe)}</b>", total_s),
    ]]
    total_table = Table(total_data, colWidths=[page_w * 0.6, page_w * 0.4])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('LINEABOVE', (0, 0), (-1, 0), 2, AMBER),
        ('PADDING', (0, 0), (-1, -1), 12),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(total_table)
    story.append(Spacer(1, 0.8*cm))

    # ── Signature line ───────────────────────────────────────────────
    sig_data = [[
        Paragraph(
            f"<br/><br/>______________________________<br/>"
            f"Firma del arrendador<br/>{arr_nombre}",
            ParagraphStyle('sig', fontSize=9, textColor=DARK, fontName='Helvetica',
                           alignment=TA_CENTER, leading=13)
        ),
        Paragraph("", value_s),
        Paragraph(
            f"<br/><br/>______________________________<br/>"
            f"Firma del arrendatario<br/>{inq_nombre}",
            ParagraphStyle('sig2', fontSize=9, textColor=DARK, fontName='Helvetica',
                           alignment=TA_CENTER, leading=13)
        ),
    ]]
    sig_table = Table(sig_data, colWidths=[page_w * 0.4, page_w * 0.2, page_w * 0.4])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(sig_table)
    story.append(Spacer(1, 0.6*cm))

    # ── Footer ───────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#CBD5E0"), spaceAfter=0.2*cm))
    notas = pago.get('notas', '') or ''
    if notas:
        story.append(Paragraph(f"Notas: {notas}", note_s))
        story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Documento generado el {date.today().strftime('%d/%m/%Y')}  —  "
        f"Calas de Almeria - Gestion Inmobiliaria",
        footer_s
    ))

    doc.build(story)
    return output_path
