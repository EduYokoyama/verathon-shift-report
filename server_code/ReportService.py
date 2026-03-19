import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
"""
ReportService.py
Generates the per-shift PDF report using ReportLab.
Replaces the VBA screenshot-based cmdreport_Click() approach with a
proper formatted document containing colour-coded KPI cells.
"""
import anvil.server
import anvil.media
from anvil.tables import app_tables
import io


# ── Colour helper (mirrors VBA colour logic) ────────────────────────────────

def _kpi_color(pct_value):
  """
    pct_value is a raw percentage (0–100+).
    Returns a ReportLab HexColor matching the VBA progress-bar colours.
    """
  from reportlab.lib import colors
  try:
    p = float(pct_value)
  except (TypeError, ValueError):
    return colors.white
  if p >= 100:
    return colors.HexColor('#00FF00')   # bright green
  elif p >= 75:
    return colors.HexColor('#009900')   # dark green
  elif p >= 30:
    return colors.HexColor('#FFFF00')   # yellow
  else:
    return colors.HexColor('#0000CC')   # dark blue


def _yn(v):
  return "YES" if v else "NO"


def _v(val, default=''):
  """Safe value-to-string conversion."""
  if val is None or val == '' or (isinstance(val, float) and val == 0
                                  and default == ''):
    return default
  return str(val)


def _p(val):
  """Format a stored percentage number."""
  try:
    return f"{float(val):.1f} %"
  except (TypeError, ValueError):
    return "N/A"


# ── Main callable ────────────────────────────────────────────────────────────

@anvil.server.callable
def generate_pdf_report(month, day, year, shift):
  """
    Build a multi-page PDF shift report — one page per machine.
    Equivalent to cmdreport_Click() but produces real formatted tables
    instead of form screenshots.
    """
  from reportlab.lib.pagesizes import landscape, letter
  from reportlab.lib            import colors
  from reportlab.lib.units      import inch
  from reportlab.lib.styles     import getSampleStyleSheet, ParagraphStyle
  from reportlab.platypus       import (SimpleDocTemplate, Table, TableStyle,
  Paragraph, Spacer, PageBreak,
  HRFlowable)

  # ── Fetch data ────────────────────────────────────────────────
  key       = f"{month}{day}{year}{shift}"
  shift_row = app_tables.shifts.get(shift_key=key)
  if not shift_row:
    return None

  reports    = app_tables.machine_reports.search(shift=shift_row)
  report_map = {r['machine_id']: r for r in reports}
  if not report_map:
    return None

  MACHINE_ORDER = ["073","179","075","231","170",
                   "258","259","260","MV1","MV2"]
  report_date   = f"{month}/{day}/{year}"

  # ── Document setup ────────────────────────────────────────────
  buffer = io.BytesIO()
  doc    = SimpleDocTemplate(
    buffer,
    pagesize    = landscape(letter),
    leftMargin  = 0.35 * inch,
    rightMargin = 0.35 * inch,
    topMargin   = 0.40 * inch,
    bottomMargin= 0.30 * inch,
  )

  # Colours
  C_HEADER = colors.HexColor('#001166')
  C_SUBHDR = colors.HexColor('#336699')
  C_ROWALT = colors.HexColor('#EEF3FF')
  C_LABEL  = colors.HexColor('#CCDEFF')
  C_WHITE  = colors.white

  styles    = getSampleStyleSheet()
  title_sty = ParagraphStyle(
    'rpt_title',
    fontSize   = 14, fontName = 'Helvetica-Bold',
    alignment  = 1,
    textColor  = C_WHITE, backColor = C_HEADER,
    spaceBefore= 0, spaceAfter = 6,
    leftIndent = 6, rightIndent = 6,
    leading    = 20,
  )

  def section_hdr(text):
    return Paragraph(f"<b>{text}</b>", ParagraphStyle(
      'sec', fontSize=9, fontName='Helvetica-Bold',
      textColor=C_WHITE, backColor=C_SUBHDR,
      spaceBefore=4, spaceAfter=2, leading=13,
      leftIndent=4
    ))

    # ── Column widths (landscape letter ≈ 10.3 usable inches) ────
  W_LABEL = 1.85 * inch
  W_DATA  = 3.00 * inch   # WO1
  W_DATA2 = 3.00 * inch   # WO2
  W_TOT   = 2.45 * inch   # Totals

  COL4 = [W_LABEL, W_DATA, W_DATA2, W_TOT]
  COL2 = [W_LABEL + W_DATA, W_DATA2 + W_TOT]

  def make_table(data, col_widths, style_cmds):
    base = [
      ('FONTSIZE',   (0,0),(-1,-1), 8),
      ('ALIGN',      (0,0),(-1,-1), 'CENTER'),
      ('VALIGN',     (0,0),(-1,-1), 'MIDDLE'),
      ('GRID',       (0,0),(-1,-1), 0.4, colors.grey),
      ('ROWHEIGHT',  (0,0),(-1,-1), 16),
    ]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle(base + style_cmds))
    return t

    # ── Build story ───────────────────────────────────────────────
  story = []

  machines_in_report = [m for m in MACHINE_ORDER if m in report_map]

  for idx, mid in enumerate(machines_in_report):
    r     = report_map[mid]
    label = f"ASB-{mid}" if not mid.startswith("MV") else mid

    # ── Page title ────────────────────────────────────────────
    story.append(Paragraph(
      f"  Machine: {label}  |  Date: {report_date}  |  "
      f"Shift: {shift.title()}",
      title_sty
    ))
    story.append(Spacer(1, 0.06 * inch))

    # ── 1. Summary bar ────────────────────────────────────────
    avail_bg = _kpi_color(r['availability'])
    summ = make_table(
      [
        ['Total Run Time (h)', 'Total Cases', 'Total Lost (h)', 'Availability'],
        [_v(r['run_total'],'0'), _v(r['cases_total'],'0'),
         _v(r['lost_total'],'0'), _p(r['availability'])]
      ],
      COL4,
      [
        ('BACKGROUND', (0,0),(-1,0), C_HEADER),
        ('TEXTCOLOR',  (0,0),(-1,0), C_WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
        ('FONTNAME',   (0,1),(-1,1), 'Helvetica-Bold'),
        ('BACKGROUND', (3,1),(3,1), avail_bg),
      ]
    )
    story.append(summ)
    story.append(Spacer(1, 0.05 * inch))

    # ── 2. Timing bar ─────────────────────────────────────────
    timing = make_table(
      [
        ['Changeover (h)', 'Overtime (h)', 'Late Start (h)', 'Early Leave (h)'],
        [_v(r['cot'],'0'), _v(r['ot'],'0'),
         _v(r['late_start'],'0'), _v(r['early_leave'],'0')]
      ],
      COL4,
      [
        ('BACKGROUND', (0,0),(-1,0), C_SUBHDR),
        ('TEXTCOLOR',  (0,0),(-1,0), C_WHITE),
        ('FONTNAME',   (0,0),(-1,0), 'Helvetica-Bold'),
      ]
    )
    story.append(timing)
    story.append(Spacer(1, 0.05 * inch))

    # ── 3. WO detail table ────────────────────────────────────
    att1_bg = _kpi_color(r['attainment1'])
    att2_bg = _kpi_color(r['attainment2'])
    eff1_bg = _kpi_color(r['efficiency1'])
    eff2_bg = _kpi_color(r['efficiency2'])

    wo_data = [
      ['Field',             'Work Order 1',           'Work Order 2',    'Combined'],
      ['WO Number',         _v(r['wo1']),             _v(r['wo2']),      ''],
      ['Part Number',       _v(r['pn1']),             _v(r['pn2']),      ''],
      ['Geometry',          _v(r['geo1']),            _v(r['geo2']),     ''],
      ['Material',          _v(r['mat1']),            _v(r['mat2']),     ''],
      ['Planned Cases',     _v(r['plan_cases1'],'0'), _v(r['plan_cases2'],'0'), ''],
      ['Actual Cases',      _v(r['act_cases1'],'0'),  _v(r['act_cases2'],'0'),
       _v(r['cases_total'],'0')],
      ['Run Time (h)',      _v(r['run1'],'0'),        _v(r['run2'],'0'), ''],
      ['Issue A / C',       _v(r['issue_a']),         _v(r['issue_c']),  ''],
      ['Lost A / C (h)',    _v(r['lost_a'],'0'),      _v(r['lost_c'],'0'),''],
      ['Issue B / D',       _v(r['issue_b']),         _v(r['issue_d']),  ''],
      ['Lost B / D (h)',    _v(r['lost_b'],'0'),      _v(r['lost_d'],'0'),
       _v(r['lost_total'],'0')],
      ['Attainment',        _p(r['attainment1']),     _p(r['attainment2']), ''],
      ['Efficiency',        _p(r['efficiency1']),     _p(r['efficiency2']), ''],
      ['Est. Spent Hrs',    _v(r['est_hr1'],'0'),     _v(r['est_hr2'],'0'), ''],
      ['Actual Spent Hrs',  _v(r['act_hr1'],'0'),     _v(r['act_hr2'],'0'), ''],
            ['Planned Manpower',  _v(r['plan_mp1'],'0'),    _v(r['plan_mp2'],'0'),''],
            ['Actual Manpower',   _v(r['act_mp1'],'0'),     _v(r['act_mp2'],'0'),''],
        ]

        wo_cmds = [
            ('BACKGROUND',    (0,0), (-1,0), C_HEADER),
            ('TEXTCOLOR',     (0,0), (-1,0), C_WHITE),
            ('FONTNAME',      (0,0), (-1,0), 'Helvetica-Bold'),
            ('BACKGROUND',    (0,1), (0,-1), C_LABEL),
            ('FONTNAME',      (0,1), (0,-1), 'Helvetica-Bold'),
            ('ROWBACKGROUNDS',(1,1),(-1,-1), [C_WHITE, C_ROWALT]),
            # Attainment row (index 12)
            ('BACKGROUND', (1,12),(1,12), att1_bg),
            ('BACKGROUND', (2,12),(2,12), att2_bg),
            # Efficiency row (index 13)
            ('BACKGROUND', (1,13),(1,13), eff1_bg),
            ('BACKGROUND', (2,13),(2,13), eff2_bg),
        ]
        story.append(make_table(wo_data, COL4, wo_cmds))
        story.append(Spacer(1, 0.05 * inch))

        # ── 4. Next shift + readiness ─────────────────────────────
        tool_bg  = (colors.HexColor('#00CC00') if r['tool_ready']
                    else colors.HexColor('#CC0000'))
        label_bg = (colors.HexColor('#00CC00') if r['labels_ready']
                    else colors.HexColor('#CC0000'))
        kit_bg   = (colors.HexColor('#00CC00') if r['kit_ready']
                    else colors.HexColor('#CC0000'))

        nxt_data = [
            ['Next WO', 'Next PN', 'Next Geometry', 'Next Material',
             'Tool Ready?', 'Labels Ready?', 'Kit Ready?'],
            [_v(r['next_wo']), _v(r['next_pn']),
             _v(r['next_geo']), _v(r['next_mat']),
             _yn(r['tool_ready']), _yn(r['labels_ready']), _yn(r['kit_ready'])]
        ]
        nxt_w = [1.1*inch, 1.1*inch, 1.6*inch, 1.5*inch,
                 1.0*inch, 1.1*inch, 0.9*inch]
        nxt_cmds = [
            ('BACKGROUND', (0,0),(-1,0),  C_SUBHDR),
            ('TEXTCOLOR',  (0,0),(-1,0),  C_WHITE),
            ('FONTNAME',   (0,0),(-1,0),  'Helvetica-Bold'),
            ('BACKGROUND', (4,1),(4,1),   tool_bg),
            ('BACKGROUND', (5,1),(5,1),   label_bg),
            ('BACKGROUND', (6,1),(6,1),   kit_bg),
            ('TEXTCOLOR',  (4,1),(6,1),   C_WHITE),
            ('FONTNAME',   (4,1),(6,1),   'Helvetica-Bold'),
        ]
        story.append(make_table(nxt_data, nxt_w, nxt_cmds))

        # Page break between machines (not after the last one)
        if idx < len(machines_in_report) - 1:
            story.append(PageBreak())

    # ── Render & return ───────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)
    return anvil.media.from_file(
        buffer,
        content_type = 'application/pdf',
        name         = f'ShiftReport_{month}_{day}_{year}_{shift}.pdf'
    )
