import anvil.server
import anvil.media
from anvil.tables import app_tables
import io


def _kpi_color(pct_value):
  from reportlab.lib import colors
  try:
    p = float(pct_value)
  except (TypeError, ValueError):
    return colors.white
  if p >= 100:
    return colors.HexColor('#00FF00')
  elif p >= 75:
    return colors.HexColor('#009900')
  elif p >= 30:
    return colors.HexColor('#FFFF00')
  else:
    return colors.HexColor('#0000CC')


def _yn(v):
  return "YES" if v else "NO"


def _p(val):
  try:
    return f"{float(val):.1f} %"
  except Exception:
    return "N/A"


def _v(val, default=''):
  if val is None or val == '':
    return default
  return str(val)


@anvil.server.callable
def generate_pdf_report(month, day, year, shift):
  from reportlab.lib.pagesizes import landscape, letter
  from reportlab.lib import colors
  from reportlab.lib.units import inch
  from reportlab.lib.styles import ParagraphStyle
  from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak

  key = f"{month}{day}{year}{shift}"
  shift_row = app_tables.shifts.get(shift_key=key)
  if not shift_row:
    return None

  reports = app_tables.machine_reports.search(shift=shift_row)
  report_map = {r['machine_id']: r for r in reports}
  if not report_map:
    return None

  MACHINE_ORDER = ["073", "179", "075", "231", "170", "258", "259", "260", "MV1", "MV2"]
  report_date = f"{month}/{day}/{year}"

  buffer = io.BytesIO()
  doc = SimpleDocTemplate(
    buffer,
    pagesize=landscape(letter),
    leftMargin=0.35 * inch,
    rightMargin=0.35 * inch,
    topMargin=0.40 * inch,
    bottomMargin=0.30 * inch,
  )

  C_HEADER = colors.HexColor('#001166')
  C_SUBHDR = colors.HexColor('#336699')
  C_ROWALT = colors.HexColor('#EEF3FF')
  C_LABEL = colors.HexColor('#CCDEFF')
  C_WHITE = colors.white

  title_sty = ParagraphStyle(
    'rpt_title',
    fontSize=14,
    fontName='Helvetica-Bold',
    alignment=1,
    textColor=C_WHITE,
    backColor=C_HEADER,
    spaceBefore=0,
    spaceAfter=6,
    leftIndent=6,
    rightIndent=6,
    leading=20,
  )

  W_LABEL = 1.85 * inch
  W_DATA = 3.00 * inch
  W_TOT = 2.45 * inch
  COL4 = [W_LABEL, W_DATA, W_DATA, W_TOT]

  def make_table(data, col_widths, extra_style):
    base = [
      ('FONTSIZE', (0, 0), (-1, -1), 8),
      ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
      ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
      ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
      ('ROWHEIGHT', (0, 0), (-1, -1), 16),
    ]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(base + extra_style))
    return t

  story = []
  machines = [m for m in MACHINE_ORDER if m in report_map]

  for idx, mid in enumerate(machines):
    r = report_map[mid]
    label = f"ASB-{mid}" if not mid.startswith("MV") else mid

    # Page title
    story.append(Paragraph(
      f"  Machine: {label}  |  Date: {report_date}  |  Shift: {shift.title()}",
      title_sty
    ))
    story.append(Spacer(1, 0.06 * inch))

    # Summary row
    avail_bg = _kpi_color(r['availability'])
    summary_data = [
      ['Total Run Time (h)', 'Total Cases', 'Total Lost (h)', 'Availability'],
      [_v(r['run_total'], '0'), _v(r['cases_total'], '0'), _v(r['lost_total'], '0'), _p(r['availability'])]
    ]
    summary_style = [
      ('BACKGROUND', (0, 0), (-1, 0), C_HEADER),
      ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
      ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
      ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
      ('BACKGROUND', (3, 1), (3, 1), avail_bg),
    ]
    story.append(make_table(summary_data, COL4, summary_style))
    story.append(Spacer(1, 0.05 * inch))

    # Timing row
    timing_data = [
      ['Changeover (h)', 'Overtime (h)', 'Late Start (h)', 'Early Leave (h)'],
      [_v(r['cot'], '0'), _v(r['ot'], '0'), _v(r['late_start'], '0'), _v(r['early_leave'], '0')]
    ]
    timing_style = [
      ('BACKGROUND', (0, 0), (-1, 0), C_SUBHDR),
      ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
      ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]
    story.append(make_table(timing_data, COL4, timing_style))
    story.append(Spacer(1, 0.05 * inch))

    # WO detail table
    att1_bg = _kpi_color(r['attainment1'])
    att2_bg = _kpi_color(r['attainment2'])
    eff1_bg = _kpi_color(r['efficiency1'])
    eff2_bg = _kpi_color(r['efficiency2'])

    wo_data = [
      ['Field', 'Work Order 1', 'Work Order 2', 'Combined'],
      ['WO Number', _v(r['wo1']), _v(r['wo2']), ''],
      ['Part Number', _v(r['pn1']), _v(r['pn2']), ''],
      ['Geometry', _v(r['geo1']), _v(r['geo2']), ''],
      ['Material', _v(r['mat1']), _v(r['mat2']), ''],
      ['Planned Cases', _v(r['plan_cases1'], '0'), _v(r['plan_cases2'], '0'), ''],
      ['Actual Cases', _v(r['act_cases1'], '0'), _v(r['act_cases2'], '0'), _v(r['cases_total'], '0')],
      ['Run Time (h)', _v(r['run1'], '0'), _v(r['run2'], '0'), ''],
      ['Issue A / C', _v(r['issue_a']), _v(r['issue_c']), ''],
      ['Lost A/C (h)', _v(r['lost_a'], '0'), _v(r['lost_c'], '0'), ''],
      ['Issue B / D', _v(r['issue_b']), _v(r['issue_d']), ''],
      ['Lost B/D (h)', _v(r['lost_b'], '0'), _v(r['lost_d'], '0'), _v(r['lost_total'], '0')],
      ['Attainment', _p(r['attainment1']), _p(r['attainment2']), ''],
      ['Efficiency', _p(r['efficiency1']), _p(r['efficiency2']), ''],
      ['Est. Spent Hrs', _v(r['est_hr1'], '0'), _v(r['est_hr2'], '0'), ''],
      ['Actual Spent Hrs', _v(r['act_hr1'], '0'), _v(r['act_hr2'], '0'), ''],
      ['Planned Manpower', _v(r['plan_mp1'], '0'), _v(r['plan_mp2'], '0'), ''],
      ['Actual Manpower', _v(r['act_mp1'], '0'), _v(r['act_mp2'], '0'), ''],
    ]

    wo_style = [
      ('BACKGROUND', (0, 0), (-1, 0), C_HEADER),
      ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
      ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
      ('BACKGROUND', (0, 1), (0, -1), C_LABEL),
      ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
      ('ROWBACKGROUNDS', (1, 1), (-1, -1), [C_WHITE, C_ROWALT]),
      ('BACKGROUND', (1, 12), (1, 12), att1_bg),
      ('BACKGROUND', (2, 12), (2, 12), att2_bg),
      ('BACKGROUND', (1, 13), (1, 13), eff1_bg),
      ('BACKGROUND', (2, 13), (2, 13), eff2_bg),
    ]
    story.append(make_table(wo_data, COL4, wo_style))
    story.append(Spacer(1, 0.05 * inch))

    # Next shift and readiness
    tool_bg = colors.HexColor('#00CC00') if r['tool_ready'] else colors.HexColor('#CC0000')
    label_bg = colors.HexColor('#00CC00') if r['labels_ready'] else colors.HexColor('#CC0000')
    kit_bg = colors.HexColor('#00CC00') if r['kit_ready'] else colors.HexColor('#CC0000')

    nxt_w = [1.1 * inch, 1.1 * inch, 1.6 * inch, 1.5 * inch, 1.0 * inch, 1.1 * inch, 0.9 * inch]
    nxt_data = [
      ['Next WO', 'Next PN', 'Next Geometry', 'Next Material', 'Tool Ready?', 'Labels Ready?', 'Kit Ready?'],
      [_v(r['next_wo']), _v(r['next_pn']), _v(r['next_geo']), _v(r['next_mat']),
       _yn(r['tool_ready']), _yn(r['labels_ready']), _yn(r['kit_ready'])]
    ]
    nxt_style = [
      ('BACKGROUND', (0, 0), (-1, 0), C_SUBHDR),
      ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
      ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
      ('BACKGROUND', (4, 1), (4, 1), tool_bg),
      ('BACKGROUND', (5, 1), (5, 1), label_bg),
      ('BACKGROUND', (6, 1), (6, 1), kit_bg),
      ('TEXTCOLOR', (4, 1), (6, 1), C_WHITE),
      ('FONTNAME', (4, 1), (6, 1), 'Helvetica-Bold'),
    ]
    story.append(make_table(nxt_data, nxt_w, nxt_style))

    if idx < len(machines) - 1:
      story.append(PageBreak())

  doc.build(story)
  buffer.seek(0)
  return anvil.media.from_file(
    buffer,
    content_type='application/pdf',
    name=f'ShiftReport_{month}_{day}_{year}_{shift}.pdf'
  )
