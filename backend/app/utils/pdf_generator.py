import io
from datetime import datetime, timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether
)

def generate_pdf_report(assessment_data: dict) -> bytes:
    """Generates an executive cybersecurity risk and compliance assessment PDF report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#475569"),
        spaceAfter=12
    )
    heading2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1e293b"),
        spaceBefore=12,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155")
    )
    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Code'],
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#0f172a"),
        backColor=colors.HexColor("#f1f5f9")
    )
    alert_style = ParagraphStyle(
        'DocAlert',
        parent=styles['Normal'],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b")
    )

    story = []

    # Title & Metadata
    proj_name = assessment_data.get("project_name", "GenAI Application Assessment")
    aid = assessment_data.get("id", "N/A")
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    story.append(Paragraph(f"<b>Security & Compliance Assessment Report</b>", title_style))
    story.append(Paragraph(f"Project: <b>{proj_name}</b> | Assessment ID: {aid[:8]} | Date: {date_str}", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#0284c7"), spaceAfter=12))

    # Executive Summary Metrics Table
    risk_score = assessment_data.get("overall_risk_score", 0.0)
    risk_level = assessment_data.get("risk_level", "INFORMATIONAL")
    comp_score = assessment_data.get("compliance_score", 0.0)
    findings_count = assessment_data.get("findings_count", len(assessment_data.get("findings", [])))
    sev_breakdown = assessment_data.get("severity_breakdown", {})

    level_color = colors.HexColor("#dc2626") if risk_level in ("CRITICAL", "HIGH") else (
        colors.HexColor("#f59e0b") if risk_level == "MEDIUM" else colors.HexColor("#10b981")
    )

    metrics_data = [
        [
            Paragraph("<b>Overall Risk Score</b>", body_style),
            Paragraph("<b>Risk Level</b>", body_style),
            Paragraph("<b>Compliance Score</b>", body_style),
            Paragraph("<b>Total Findings</b>", body_style),
        ],
        [
            Paragraph(f"<b><font size='16'>{risk_score} / 100</font></b>", body_style),
            Paragraph(f"<b><font size='14' color='{level_color.hexval()}'>{risk_level}</font></b>", body_style),
            Paragraph(f"<b><font size='16'>{comp_score}%</font></b>", body_style),
            Paragraph(f"<b><font size='16'>{findings_count}</font></b>", body_style),
        ]
    ]

    t_metrics = Table(metrics_data, colWidths=[130, 130, 130, 130])
    t_metrics.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#f8fafc")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 10))

    # Severity Distribution Table
    sev_data = [
        [
            Paragraph("<b>Severity</b>", body_style),
            Paragraph("<b>Critical</b>", body_style),
            Paragraph("<b>High</b>", body_style),
            Paragraph("<b>Medium</b>", body_style),
            Paragraph("<b>Low</b>", body_style),
            Paragraph("<b>Informational</b>", body_style),
        ],
        [
            Paragraph("<b>Count</b>", body_style),
            Paragraph(str(sev_breakdown.get("CRITICAL", 0)), body_style),
            Paragraph(str(sev_breakdown.get("HIGH", 0)), body_style),
            Paragraph(str(sev_breakdown.get("MEDIUM", 0)), body_style),
            Paragraph(str(sev_breakdown.get("LOW", 0)), body_style),
            Paragraph(str(sev_breakdown.get("INFORMATIONAL", 0)), body_style),
        ]
    ]
    t_sev = Table(sev_data, colWidths=[90, 85, 85, 85, 85, 90])
    t_sev.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#e2e8f0")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ]))
    story.append(t_sev)
    story.append(Spacer(1, 14))

    # Reconnaissance / Architecture Summary
    story.append(Paragraph("<b>1. Architecture & Threat Boundaries</b>", heading2_style))
    recon = assessment_data.get("recon_summary", {})
    components = recon.get("components", ["Core GenAI Application"])
    boundaries = recon.get("trust_boundaries", ["Client to LLM Provider API"])
    
    comp_text = f"<b>Identified Components:</b> {', '.join(components[:8])}<br/><b>Trust Boundaries:</b> {', '.join(boundaries[:5])}"
    story.append(Paragraph(comp_text, body_style))
    story.append(Spacer(1, 12))

    # Findings Section
    story.append(Paragraph("<b>2. Key Security Findings & Evidence</b>", heading2_style))
    findings = assessment_data.get("findings", [])
    if not findings:
        story.append(Paragraph("<i>No security vulnerabilities detected across evaluated static rules.</i>", body_style))
    else:
        for f in findings[:10]: # Top 10 findings in PDF
            f_box = []
            fid = f.get("finding_id", "N/A")
            title = f.get("title", "Finding")
            sev = f.get("severity", "MEDIUM")
            f_color = "#dc2626" if sev == "CRITICAL" else ("#ea580c" if sev == "HIGH" else "#f59e0b")
            
            f_box.append(Paragraph(f"<b>[{fid}] {title}</b> — <font color='{f_color}'><b>{sev}</b></font>", body_style))
            desc = f.get("description", "")
            f_box.append(Paragraph(desc, body_style))
            
            # Evidence snippet
            evidences = f.get("evidences", [])
            if evidences:
                ev = evidences[0]
                loc = f"<b>Location:</b> {ev.get('file_path')}:{ev.get('line_start')}"
                f_box.append(Paragraph(loc, body_style))
                snip = ev.get("code_snippet")
                if snip:
                    clean_snip = snip[:200].replace("<", "&lt;").replace(">", "&gt;")
                    f_box.append(Paragraph(f"<font face='Courier'>{clean_snip}</font>", code_style))

            remed = f.get("remediation")
            if remed:
                f_box.append(Paragraph(f"<b>Remediation:</b> {remed}", body_style))

            f_box.append(Spacer(1, 6))
            story.append(KeepTogether(f_box))

    story.append(Spacer(1, 10))

    # Compliance Matrix Summary
    story.append(Paragraph("<b>3. Framework Compliance Highlights</b>", heading2_style))
    mappings = assessment_data.get("control_mappings", [])
    if mappings:
        cm_rows = [
            [
                Paragraph("<b>Framework</b>", body_style),
                Paragraph("<b>Control ID</b>", body_style),
                Paragraph("<b>Control Title</b>", body_style),
                Paragraph("<b>Status</b>", body_style),
            ]
        ]
        for cm in mappings[:12]:
            st = cm.get("status", "NOT_EVIDENCED")
            st_color = "#16a34a" if st == "IMPLEMENTED_WITH_EVIDENCE" else (
                "#dc2626" if st == "MISSING_WITH_EVIDENCE" else "#64748b"
            )
            cm_rows.append([
                Paragraph(cm.get("framework_id", ""), body_style),
                Paragraph(cm.get("control_id", ""), body_style),
                Paragraph(cm.get("control_title", "")[:35], body_style),
                Paragraph(f"<font color='{st_color}'><b>{st}</b></font>", body_style),
            ])
        t_cm = Table(cm_rows, colWidths=[90, 85, 230, 115])
        t_cm.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_cm)

    # Disclaimer Footer
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceAfter=8))
    story.append(Paragraph(
        "<b>Independent Academic Disclaimer:</b> This report is generated by an independent academic platform "
        "inspired by the OWASP GenAI Security Project Crosswalk concept. It does not constitute official certification, "
        "endorsement, or legal assurance under OWASP, NIST, ISO, or the EU AI Act.",
        alert_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
