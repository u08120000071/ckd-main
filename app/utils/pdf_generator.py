import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.units import inch

def generate_diagnosis_pdf(diagnosis, patient, physician_name: str) -> io.BytesIO:
    """
    Generate a professional hospital-grade vector PDF diagnostic report.
    Returns a BytesIO stream containing the generated PDF binary data.
    """
    buffer = io.BytesIO()
    
    # 0.5 inch margins for standard neat clinical layouts
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Define custom premium typography & styling
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#ffffff'),
        spaceAfter=0,
        alignment=1 # Centered
    )
    
    section_heading_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=12,
        spaceAfter=6,
        borderPadding=2
    )
    
    label_style = ParagraphStyle(
        'CellLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#475569')
    )
    
    value_style = ParagraphStyle(
        'CellValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#0f172a')
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor('#334155')
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#334155'),
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    story = []
    
    # --- PAGE 1: HEADER & CLINICAL SCREENING RESULTS ---
    
    # Title Banner (Deep Slate Navy background)
    banner_data = [
        [Paragraph("CHRONIC KIDNEY DISEASE (CKD) CLINICAL REPORT", title_style)]
    ]
    banner_table = Table(banner_data, colWidths=[540])
    banner_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#1e293b')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 10))
    
    # Patient Demographic & Metadata Table
    meta_data = [
        [
            Paragraph("Patient Name:", label_style), Paragraph(patient.full_name, value_style),
            Paragraph("Patient Hospital ID:", label_style), Paragraph(patient.patient_id or "—", value_style)
        ],
        [
            Paragraph("Age / Gender:", label_style), Paragraph(f"{patient.age} yrs / {patient.gender}", value_style),
            Paragraph("Diagnosis Date:", label_style), Paragraph(diagnosis.created_at.strftime("%d %B %Y %H:%M") if diagnosis.created_at else datetime.now().strftime("%d %B %Y %H:%M"), value_style)
        ],
        [
            Paragraph("Contact Info:", label_style), Paragraph(patient.phone or "—", value_style),
            Paragraph("Attending Physician:", label_style), Paragraph(physician_name, value_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[90, 180, 110, 160])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 12))
    
    # Section: Renal Staging Metrics (KDIGO)
    story.append(Paragraph("1. Primary Renal Markers & KDIGO Risk Staging", section_heading_style))
    
    # KDIGO Color Coding Mapping
    risk_level = diagnosis.risk_level.lower().strip()
    if 'very high' in risk_level:
        risk_bg = colors.HexColor('#fef2f2')
        risk_text_color = colors.HexColor('#991b1b')
        risk_label = "VERY HIGH RISK"
    elif 'high' in risk_level:
        risk_bg = colors.HexColor('#fff7ed')
        risk_text_color = colors.HexColor('#c2410c')
        risk_label = "HIGH RISK"
    elif 'moderate' in risk_level:
        risk_bg = colors.HexColor('#fef3c7')
        risk_text_color = colors.HexColor('#b45309')
        risk_label = "MODERATE RISK"
    else:
        risk_bg = colors.HexColor('#ecfdf5')
        risk_text_color = colors.HexColor('#065f46')
        risk_label = "LOW RISK"
        
    kdigo_label_style = ParagraphStyle(
        'KdigoLabel',
        parent=value_style,
        fontName='Helvetica-Bold',
        textColor=risk_text_color
    )
    
    renal_data = [
        [
            Paragraph("eGFR Value", label_style),
            Paragraph("GFR Stage", label_style),
            Paragraph("Urine ACR", label_style),
            Paragraph("Albuminuria Stage", label_style),
            Paragraph("KDIGO Risk Category", label_style)
        ],
        [
            Paragraph(f"{diagnosis.egfr:.2f} mL/min/1.73 m²", value_style),
            Paragraph(f"{diagnosis.gfr_stage}", value_style),
            Paragraph(f"{diagnosis.urine_acr:.1f} mg/g", value_style),
            Paragraph(f"{diagnosis.albuminuria_stage}", value_style),
            Paragraph(risk_label, kdigo_label_style)
        ]
    ]
    renal_table = Table(renal_data, colWidths=[120, 90, 110, 110, 110])
    renal_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (4,1), (4,1), risk_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(renal_table)
    story.append(Spacer(1, 12))
    
    # Section: ML Decision Tree Prediction Staging
    story.append(Paragraph("2. Decision Tree Machine Learning Classifier", section_heading_style))
    
    ml_pred = diagnosis.ml_prediction.lower()
    if 'no' in ml_pred:
        ml_bg = colors.HexColor('#ecfdf5')
        ml_text_color = colors.HexColor('#047857')
        ml_outcome = "NO CKD DETECTED"
    else:
        ml_bg = colors.HexColor('#fef2f2')
        ml_text_color = colors.HexColor('#b91c1c')
        ml_outcome = "CKD DETECTED"
        
    ml_outcome_style = ParagraphStyle(
        'MlOutcome',
        parent=value_style,
        fontName='Helvetica-Bold',
        fontSize=11,
        textColor=ml_text_color
    )
    
    ml_data = [
        [
            Paragraph("Inference Engine Target", label_style),
            Paragraph("Diagnostic Classification", label_style),
            Paragraph("Inference Confidence Score", label_style)
        ],
        [
            Paragraph("UCI CKD Trained Classifier Model", value_style),
            Paragraph(ml_outcome, ml_outcome_style),
            Paragraph(f"{diagnosis.ml_confidence * 100:.1f}%", value_style)
        ]
    ]
    ml_table = Table(ml_data, colWidths=[200, 180, 160])
    ml_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (1,1), (1,1), ml_bg),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(ml_table)
    story.append(Spacer(1, 12))
    
    # Section: 12 Clinical Parameters Grid
    story.append(Paragraph("3. Expanded Urinalysis, Blood Chemistry & Vitals Grid", section_heading_style))
    
    def format_val(val, unit=""):
        return f"{val} {unit}" if val is not None else "—"
        
    params_data = [
        [
            Paragraph("Parameter Name", label_style), Paragraph("Patient Metric", label_style),
            Paragraph("Parameter Name", label_style), Paragraph("Patient Metric", label_style)
        ],
        [
            Paragraph("Blood Pressure:", label_style), Paragraph(format_val(diagnosis.blood_pressure, "mmHg"), value_style),
            Paragraph("Blood Urea (BUN):", label_style), Paragraph(format_val(diagnosis.blood_urea, "mg/dL"), value_style)
        ],
        [
            Paragraph("Hypertension:", label_style), Paragraph(format_val(diagnosis.hypertension), value_style),
            Paragraph("Serum Creatinine:", label_style), Paragraph(format_val(diagnosis.serum_creatinine, "mg/dL"), value_style)
        ],
        [
            Paragraph("Diabetes Mellitus:", label_style), Paragraph(format_val(diagnosis.diabetes_mellitus), value_style),
            Paragraph("Serum Sodium:", label_style), Paragraph(format_val(diagnosis.sodium, "mEq/L"), value_style)
        ],
        [
            Paragraph("Urine Specific Gravity:", label_style), Paragraph(format_val(diagnosis.specific_gravity), value_style),
            Paragraph("Serum Potassium:", label_style), Paragraph(format_val(diagnosis.potassium, "mEq/L"), value_style)
        ],
        [
            Paragraph("Albumin Level (Dipstick):", label_style), Paragraph(format_val(diagnosis.albumin, "+"), value_style),
            Paragraph("Hemoglobin Count:", label_style), Paragraph(format_val(diagnosis.hemoglobin, "g/dL"), value_style)
        ],
        [
            Paragraph("Sugar Level (Dipstick):", label_style), Paragraph(format_val(diagnosis.sugar_level), value_style),
            Paragraph("White Blood Cell (WBC):", label_style), Paragraph(format_val(diagnosis.white_blood_cell_count, "cells/mcL"), value_style)
        ],
        [
            Paragraph("Red Blood Cells (RBC):", label_style), Paragraph(format_val(diagnosis.red_blood_cells), value_style),
            Paragraph("Estimated eGFR:", label_style), Paragraph(format_val(round(diagnosis.egfr, 2), "mL/min"), value_style)
        ]
    ]
    params_table = Table(params_data, colWidths=[140, 130, 140, 130])
    params_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(params_table)
    
    # Add a page break to neatly split clinical metrics and Gemini AI recommendations
    story.append(PageBreak())
    
    # --- PAGE 2: GEMINI AI CLINICAL ASSISTANT & GUIDELINES ---
    
    story.append(banner_table) # Repeat header for visual continuity
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("4. Gemini AI Clinical Assistant Insights & Protocol", section_heading_style))
    
    if diagnosis.gemini_report:
        gemini = diagnosis.gemini_report
        
        # Medical Insights box
        story.append(Paragraph("<b>Medical Insights & Critical Findings:</b>", label_style))
        story.append(Paragraph(gemini.get('medical_insights', '—'), body_style))
        story.append(Spacer(1, 10))
        
        # Risk Analysis box
        story.append(Paragraph("<b>Pathophysiological Risk Analysis:</b>", label_style))
        story.append(Paragraph(gemini.get('risk_analysis', '—'), body_style))
        story.append(Spacer(1, 12))
        
        # Unpack bullet-point recommendations
        rec_data = []
        
        # Columns setup for precautions, lifestyle, and follow-up
        precautions_paragraphs = [Paragraph(f"• {item}", bullet_style) for item in gemini.get('suggested_precautions', [])]
        if not precautions_paragraphs:
            precautions_paragraphs = [Paragraph("No specific precautions suggested.", bullet_style)]
            
        lifestyle_paragraphs = [Paragraph(f"• {item}", bullet_style) for item in gemini.get('lifestyle_recommendations', [])]
        if not lifestyle_paragraphs:
            lifestyle_paragraphs = [Paragraph("No specific lifestyle modifications suggested.", bullet_style)]
            
        followup_paragraphs = [Paragraph(f"• {item}", bullet_style) for item in gemini.get('follow_up_recommendations', [])]
        if not followup_paragraphs:
            followup_paragraphs = [Paragraph("No specific follow-up protocol suggested.", bullet_style)]
            
        rec_data = [
            [
                Paragraph("Suggested Precautions", label_style),
                Paragraph("Lifestyle Advice", label_style),
                Paragraph("Follow-Up Protocol", label_style)
            ],
            [
                precautions_paragraphs,
                lifestyle_paragraphs,
                followup_paragraphs
            ]
        ]
        
        rec_table = Table(rec_data, colWidths=[180, 180, 180])
        rec_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(rec_table)
    else:
        story.append(Paragraph("Gemini AI clinical insights are not available for this record.", body_style))
        
    story.append(Spacer(1, 12))
    
    # Section: Final Recommendation & Physician Signature Block
    story.append(Paragraph("5. Primary Clinical Guideline & Recommendations", section_heading_style))
    story.append(Paragraph(diagnosis.recommendation, body_style))
    story.append(Spacer(1, 15))
    
    # Footer and Signature Block
    sig_data = [
        [
            Paragraph("<b>Medical Disclaimer:</b> This clinical summary is an educational decision-support tool. It has been generated by combining historical patient classification metrics, clinical KDIGO rules, and artificial intelligence models. Vitals must be checked and confirmed by a certified medical professional before clinical operations are enacted.", ParagraphStyle('Disclaimer', parent=styles['Normal'], fontSize=7.5, leading=10, textColor=colors.HexColor('#64748b'))),
            Paragraph("Physician Signature:<br/><br/>___________________________", ParagraphStyle('Signature', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, alignment=2))
        ]
    ]
    sig_table = Table(sig_data, colWidths=[360, 180])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('TOPPADDING', (0,0), (-1,-1), 10),
    ]))
    
    # Keep final block together
    story.append(KeepTogether(sig_table))

    # Build the document
    doc.build(story)
    
    buffer.seek(0)
    return buffer
