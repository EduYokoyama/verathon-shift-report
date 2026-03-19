from ._anvil_designer import Form1Template
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.tables as tables
from datetime import date

# ── Machine definitions ─────────────────────────────────────────────────────
MACHINES = [
  ("073",  "ASB-073",  "welder"),
  ("179",  "ASB-179",  "welder"),
  ("075",  "ASB-075",  "welder"),
  ("231",  "ASB-231",  "welder"),
  ("170",  "ASB-170",  "welder"),
  ("258",  "ASB-258",  "welder"),
  ("259",  "ASB-259",  "welder"),
  ("260",  "ASB-260",  "welder"),
  ("MV1",  "MV1",      "multivac"),
  ("MV2",  "MV2",      "multivac"),
]

TIME_OPTIONS = [
  "0", "0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5",
  "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0"
]

# Colour thresholds matching the original VBA exactly
def _pct_color(pct):
  """Return hex colour string for a 0‒1 percentage value."""
  if pct >= 1.0:
    return "#00FF00"   # bright green  (>= 100 %)
  elif pct >= 0.75:
    return "#009900"   # dark green    (>= 75 %)
  elif pct >= 0.30:
    return "#FFFF00"   # yellow        (>= 30 %)
  else:
    return "#0000CC"   # dark blue     (<  30 %)


class Form1(Form1Template):

  # ════════════════════════════════════════════════════════════════
  # INIT
  # ════════════════════════════════════════════════════════════════

  def __init__(self, **properties):
    self.init_components(**properties)
    self._panels   = {}   # machine_id → widget-dict
    self._pn_cache = {}   # machine_id → list[dict]
    self._iss_cache = {}  # machine_type → list[str]

    self._set_today()
    self._preload_lists()
    self._build_tabs()

  def _set_today(self):
    t = date.today()
    self.tb_month.text = str(t.month)
    self.tb_day.text   = str(t.day)
    self.tb_year.text  = str(t.year)
    self.rb_night.selected = True

  def _preload_lists(self):
    for mid, _, mtype in MACHINES:
      if mid not in self._pn_cache:
        self._pn_cache[mid] = anvil.server.call('get_part_numbers', mid)
      if mtype not in self._iss_cache:
        self._iss_cache[mtype] = anvil.server.call('get_issues', mtype)

    # ════════════════════════════════════════════════════════════════
    # BUILD UI — one tab per machine
    # ════════════════════════════════════════════════════════════════

  def _build_tabs(self):
    for mid, label, mtype in MACHINES:
      w = self._make_machine_tab(mid, mtype)
      self._panels[mid] = w
      self.tab_panel.add_tab(label, w['_root'])

  def _make_machine_tab(self, mid, mtype):
    """
        Builds the complete UI for one machine tab entirely in code.
        Returns a widget-dict  w  where  w['_root']  is the top-level panel.
        """
    w   = {}
    pns = [''] + [p['pn'] for p in self._pn_cache.get(mid, [])]
    iss = [''] + self._iss_cache.get(mtype, [])

    root = ColumnPanel(background='#0000AA', spacing_above='none',
                       spacing_below='none')

    # ── helper that adds a FlowPanel row to root ─────────────
    def row(*widgets, margin_top=4):
      fp = FlowPanel(spacing_above='none', spacing_below='none')
      for wgt in widgets:
        fp.add_component(wgt)
      root.add_component(fp)
      return fp

    def lbl(text, bold=False, color='white'):
      return Label(text=text, foreground=color, bold=bold,
                   spacing_above='none', spacing_below='none')

    def tb(ph='', w_=90, enabled=True, num=False):
      t = TextBox(placeholder=ph, width=w_, enabled=enabled,
                  spacing_above='none', spacing_below='none')
      if num:
        t.type = 'number'
      return t

    def dd(items, ph=''):
      return DropDown(items=items, placeholder=ph,
                      spacing_above='none', spacing_below='none')

    def chk(text, color='white'):
      return CheckBox(text=text, foreground=color, bold=True,
                      spacing_above='none', spacing_below='none')

    def btn(text, bg):
      return Button(text=text, background=bg, foreground='white',
                    bold=True, spacing_above='none', spacing_below='none')

    def bar(height=20):
      """A Label used as a colour progress bar."""
      return Label(text=' ', background='#333333',
                   height=height, width='0px',
                   spacing_above='none', spacing_below='none')

      # ── Row 0 : WO checkboxes + Changeover ───────────────────
    w['chk_wo1'] = chk("WO1")
    w['chk_wo2'] = chk("WO2")
    w['dd_cot']  = dd(TIME_OPTIONS, "Changeover (h)")
    row(w['chk_wo1'], lbl("      "), w['chk_wo2'],
        lbl("  Changeover (h):"), w['dd_cot'])

    # ── Row 1 : WO numbers + Run times ───────────────────────
    w['tb_wo1']   = tb("WO1 #", 80)
    w['dd_run1']  = dd(TIME_OPTIONS, "Run T1 (h)")
    w['tb_wo2']   = tb("WO2 #", 80,  enabled=False)
    w['dd_run2']  = dd(TIME_OPTIONS, "Run T2 (h)")
    row(lbl("WO1:"), w['tb_wo1'], lbl(" Run T(h):"), w['dd_run1'],
        lbl("    WO2:"), w['tb_wo2'], lbl(" Run T(h):"), w['dd_run2'])

    # ── Row 2 : Part numbers ──────────────────────────────────
    w['dd_pn1'] = dd(pns, "Part Number 1")
    w['dd_pn2'] = dd(pns, "Part Number 2")
    row(lbl("PN 1:"), w['dd_pn1'], lbl("   PN 2:"), w['dd_pn2'])

    # ── Row 3 : Geo / Mat / Planned Cases ────────────────────
    w['tb_geo1']       = tb("Geometry 1",   110, enabled=False)
    w['tb_mat1']       = tb("Material 1",    80, enabled=False)
    w['tb_plan_cases1']= tb("Plan Cases 1",  75, enabled=False, num=True)
    w['tb_geo2']       = tb("Geometry 2",   110, enabled=False)
    w['tb_mat2']       = tb("Material 2",    80, enabled=False)
    w['tb_plan_cases2']= tb("Plan Cases 2",  75, enabled=False, num=True)
    row(lbl("Geo:"), w['tb_geo1'], lbl(" Mat:"), w['tb_mat1'],
        lbl(" Plan:"), w['tb_plan_cases1'],
        lbl("  Geo:"), w['tb_geo2'], lbl(" Mat:"), w['tb_mat2'],
        lbl(" Plan:"), w['tb_plan_cases2'])

    # ── Row 4 : Actual cases ──────────────────────────────────
    w['tb_act_cases1'] = tb("Act Cases 1", 75, num=True)
    w['tb_act_cases2'] = tb("Act Cases 2", 75, enabled=False, num=True)
    row(lbl("Act Cases 1:"), w['tb_act_cases1'],
        lbl("   Act Cases 2:"), w['tb_act_cases2'])

    # ── Row 5a : Issues WO1 ───────────────────────────────────
    w['dd_issue_a'] = dd(iss, "Issue A")
    w['dd_lost_a']  = dd(TIME_OPTIONS, "Lost (h)")
    w['dd_issue_b'] = dd(iss, "Issue B")
    w['dd_lost_b']  = dd(TIME_OPTIONS, "Lost (h)")
    row(lbl("Issue A:"), w['dd_issue_a'], lbl(" Lost:"), w['dd_lost_a'],
        lbl("  Issue B:"), w['dd_issue_b'], lbl(" Lost:"), w['dd_lost_b'])

    # ── Row 5b : Issues WO2 ───────────────────────────────────
    w['dd_issue_c'] = dd(iss, "Issue C")
    w['dd_lost_c']  = dd(TIME_OPTIONS, "Lost (h)")
    w['dd_issue_d'] = dd(iss, "Issue D")
    w['dd_lost_d']  = dd(TIME_OPTIONS, "Lost (h)")
    row(lbl("Issue C:"), w['dd_issue_c'], lbl(" Lost:"), w['dd_lost_c'],
        lbl("  Issue D:"), w['dd_issue_d'], lbl(" Lost:"), w['dd_lost_d'])

    # ── Attainment bars ───────────────────────────────────────
    w['lbl_att1'] = lbl("Attainment 1 = 0.00 %")
    w['bar_att1'] = bar()
    w['lbl_att2'] = lbl("Attainment 2 = 0.00 %")
    w['bar_att2'] = bar()
    root.add_component(w['lbl_att1'])
    root.add_component(w['bar_att1'])
    root.add_component(w['lbl_att2'])
    root.add_component(w['bar_att2'])

    # ── Efficiency bars ───────────────────────────────────────
    w['lbl_eff1'] = lbl("Efficiency 1 = 0.00 %")
    w['bar_eff1'] = bar()
    w['lbl_eff2'] = lbl("Efficiency 2 = 0.00 %")
    w['bar_eff2'] = bar()
    root.add_component(w['lbl_eff1'])
    root.add_component(w['bar_eff1'])
    root.add_component(w['lbl_eff2'])
    root.add_component(w['bar_eff2'])

    # ── Row 6 : Totals ────────────────────────────────────────
    w['dd_runtotal']    = dd(TIME_OPTIONS, "Total Run T (h)")
    w['tb_cases_total'] = tb("Total Cases", 70, enabled=False, num=True)
    w['tb_lost_total']  = tb("Total Lost",  70, enabled=False, num=True)
    row(lbl("Total Run T:"), w['dd_runtotal'],
        lbl("  Total Cases:"), w['tb_cases_total'],
        lbl("  Total Lost:"),  w['tb_lost_total'])

    # ── Availability bar ──────────────────────────────────────
    w['lbl_avail'] = lbl("Availability = N/A", bold=True)
    w['bar_avail'] = bar(height=26)
    root.add_component(w['lbl_avail'])
    root.add_component(w['bar_avail'])

    # ── Row 7 : Hrs & Manpower ────────────────────────────────
    w['tb_est_hr1']  = tb("Est Hrs 1",  65, enabled=False, num=True)
    w['tb_act_hr1']  = tb("Act Hrs 1",  65, enabled=False, num=True)
    w['tb_plan_mp1'] = tb("Plan MP 1",  65, enabled=False, num=True)
    w['tb_act_mp1']  = tb("Act MP 1",   65, num=True)
    w['tb_est_hr2']  = tb("Est Hrs 2",  65, enabled=False, num=True)
    w['tb_act_hr2']  = tb("Act Hrs 2",  65, enabled=False, num=True)
    w['tb_plan_mp2'] = tb("Plan MP 2",  65, enabled=False, num=True)
    w['tb_act_mp2']  = tb("Act MP 2",   65, enabled=False, num=True)
    row(lbl("Est Hrs 1:"), w['tb_est_hr1'], lbl(" Act:"), w['tb_act_hr1'],
        lbl(" PlanMP:"), w['tb_plan_mp1'], lbl(" ActMP:"), w['tb_act_mp1'],
        lbl("  Est Hrs 2:"), w['tb_est_hr2'], lbl(" Act:"), w['tb_act_hr2'],
        lbl(" PlanMP:"), w['tb_plan_mp2'], lbl(" ActMP:"), w['tb_act_mp2'])

    # ── Row 8 : OT / Late start / Early leave ─────────────────
    w['dd_ot'] = dd(TIME_OPTIONS, "Overtime (h)")
    w['dd_ls'] = dd(TIME_OPTIONS, "Late Start (h)")
    w['dd_el'] = dd(TIME_OPTIONS, "Early Leave (h)")
    row(lbl("OT:"), w['dd_ot'],
        lbl("  Late Start:"), w['dd_ls'],
        lbl("  Early Leave:"), w['dd_el'])

    # ── Divider ───────────────────────────────────────────────
    root.add_component(lbl("─── NEXT SHIFT ───", bold=True, color='#FFFF00'))

    # ── Row 9 : Next shift ────────────────────────────────────
    w['tb_next_wo']  = tb("Next WO",  80)
    w['dd_pn_next']  = dd(pns, "Next PN")
    w['tb_next_geo'] = tb("Next Geo", 110, enabled=False)
    w['tb_next_mat'] = tb("Next Mat",  80, enabled=False)
    row(lbl("Next WO:"), w['tb_next_wo'],
        lbl("  Next PN:"), w['dd_pn_next'],
        lbl("  Geo:"), w['tb_next_geo'],
        lbl("  Mat:"), w['tb_next_mat'])

    # ── Row 10 : Readiness checkboxes ─────────────────────────
    w['chk_tool']   = chk("Molding tool ready?")
    w['tb_tool']    = tb("Tool #", 80)
    w['chk_labels'] = chk("Labels ready?")
    w['chk_kit']    = chk("Kit ready?")
    row(w['chk_tool'], w['tb_tool'], w['chk_labels'], w['chk_kit'])

    # ── Row 11 : SAVE / LOAD buttons ──────────────────────────
    b_save = btn("💾 SAVE", "#009900")
    b_load = btn("📂 LOAD", "#555555")
    b_save.set_event_handler('click', lambda **e: self._save_machine(mid))
    b_load.set_event_handler('click', lambda **e: self._load_machine(mid))
    row(b_save, lbl("  "), b_load)

    # ── Wire change events ────────────────────────────────────
    w['chk_wo1'].set_event_handler('change',
                                   lambda **e: self._on_wo1_change(mid))
    w['chk_wo2'].set_event_handler('change',
                                   lambda **e: self._on_wo2_change(mid))
    w['dd_pn1'].set_event_handler('change',
                                  lambda **e: self._on_pn_change(mid, 1))
    w['dd_pn2'].set_event_handler('change',
                                  lambda **e: self._on_pn_change(mid, 2))
    w['dd_pn_next'].set_event_handler('change',
                                      lambda **e: self._on_pn_next_change(mid))
    for key in ('dd_run1','dd_run2','tb_act_mp1','tb_act_mp2',
                'tb_act_cases1','tb_act_cases2'):
      w[key].set_event_handler('change',
                               lambda **e, k=mid: self._recalc(k))
    for key in ('dd_runtotal','dd_lost_a','dd_lost_b',
                'dd_lost_c','dd_lost_d','dd_cot'):
      w[key].set_event_handler('change',
                               lambda **e, k=mid: self._recalc_avail(k))
    for ik, lk in (('dd_issue_a','dd_lost_a'),('dd_issue_b','dd_lost_b'),
                   ('dd_issue_c','dd_lost_c'),('dd_issue_d','dd_lost_d')):
      w[ik].set_event_handler('change',
                              lambda **e, k=mid, i=ik, l=lk: self._on_issue_chg(k, i, l))

      # Store internal state for rates
    w['_rate1'] = 0.0
    w['_ehrs1'] = 0.0
    w['_rate2'] = 0.0
    w['_ehrs2'] = 0.0
    w['_root']  = root
    return w

    # ════════════════════════════════════════════════════════════════
    # WO ENABLE / DISABLE  (mirrors chk073wo1_Click etc.)
    # ════════════════════════════════════════════════════════════════

  def _on_wo1_change(self, mid):
    w  = self._panels[mid]
    en = w['chk_wo1'].checked
    for k in ('tb_wo1','dd_run1','dd_pn1','tb_act_cases1',
              'dd_issue_a','dd_lost_a','dd_issue_b','dd_lost_b',
              'tb_act_mp1'):
      w[k].enabled = en
    if not en:
      for k in ('tb_wo1','tb_act_cases1'):
        w[k].text = ''
      for k in ('dd_run1','dd_pn1','dd_issue_a',
                'dd_issue_b','dd_lost_a','dd_lost_b'):
        w[k].selected_value = None
      self._recalc(mid)

  def _on_wo2_change(self, mid):
    w  = self._panels[mid]
    en = w['chk_wo2'].checked
    for k in ('tb_wo2','dd_run2','dd_pn2','tb_act_cases2',
              'dd_issue_c','dd_lost_c','dd_issue_d','dd_lost_d',
              'dd_cot','tb_act_mp2'):
      w[k].enabled = en
    if not en:
      for k in ('tb_wo2','tb_act_cases2'):
        w[k].text = ''
      for k in ('dd_run2','dd_pn2','dd_cot','dd_issue_c',
                'dd_issue_d','dd_lost_c','dd_lost_d'):
        w[k].selected_value = None
      self._recalc(mid)

    # ════════════════════════════════════════════════════════════════
    # PART NUMBER CHANGE  (mirrors list073pn1_Change etc.)
    # ════════════════════════════════════════════════════════════════

  def _on_pn_change(self, mid, wo):
    w  = self._panels[mid]
    pn = w[f'dd_pn{wo}'].selected_value
    if not pn:
      w[f'tb_geo{wo}'].text      = ''
      w[f'tb_mat{wo}'].text      = ''
      w[f'tb_plan_mp{wo}'].text  = ''
      w[f'_rate{wo}']            = 0.0
      w[f'_ehrs{wo}']            = 0.0
      return
    det = anvil.server.call('get_pn_details', mid, pn)
    if det:
      w[f'tb_geo{wo}'].text     = str(det.get('geometry',  ''))
      w[f'tb_mat{wo}'].text     = str(det.get('material',  ''))
      w[f'tb_plan_mp{wo}'].text = str(det.get('crew_size', ''))
      w[f'_rate{wo}']           = float(det.get('run_rate', 0))
      w[f'_ehrs{wo}']           = float(det.get('est_hrs',  0))
      self._recalc(mid)

  def _on_pn_next_change(self, mid):
    w  = self._panels[mid]
    pn = w['dd_pn_next'].selected_value
    if not pn:
      w['tb_next_geo'].text = ''
      w['tb_next_mat'].text = ''
      return
    det = anvil.server.call('get_pn_details', mid, pn)
    if det:
      w['tb_next_geo'].text = str(det.get('geometry', ''))
      w['tb_next_mat'].text = str(det.get('material', ''))

    # ════════════════════════════════════════════════════════════════
    # ISSUE CHANGE  (mirrors list073problemsa_Change etc.)
    # ════════════════════════════════════════════════════════════════

  def _on_issue_chg(self, mid, ik, lk):
    w = self._panels[mid]
    w[lk].enabled = bool(w[ik].selected_value)
    self._recalc_avail(mid)

    # ════════════════════════════════════════════════════════════════
    # CALCULATIONS  (mirrors txt073actcases1_Change, etc.)
    # ════════════════════════════════════════════════════════════════

  @staticmethod
  def _fv(v, default=0.0):
    try:
      return float(v) if v not in (None, '', 'None') else default
    except (ValueError, TypeError):
      return default

  def _recalc(self, mid):
    w = self._panels[mid]

    for wo in (1, 2):
      run      = self._fv(w[f'dd_run{wo}'].selected_value)
      act_mp   = self._fv(w[f'tb_act_mp{wo}'].text)
      rate     = w.get(f'_rate{wo}', 0.0)
      ehrs     = w.get(f'_ehrs{wo}', 0.0)

      # Actual hours (run × actual manpower)
      act_hrs = run * act_mp
      w[f'tb_act_hr{wo}'].text = str(round(act_hrs, 2))

      # Planned cases (rate × runtime)
      plan_cases = rate * run
      w[f'tb_plan_cases{wo}'].text = str(round(plan_cases))

      # Estimated hours (est_hrs_per_case × actual cases)
      act_cases = self._fv(w[f'tb_act_cases{wo}'].text)
      est_hrs   = ehrs * act_cases
      w[f'tb_est_hr{wo}'].text = str(round(est_hrs, 2))

      # Attainment
      att = min(act_cases / plan_cases, 1.0) if plan_cases > 0 else 0.0
      w[f'lbl_att{wo}'].text = f"Attainment {wo} = {att*100:.2f} %"
      self._set_bar(w[f'bar_att{wo}'], att)

      # Efficiency
      eff = min(est_hrs / act_hrs, 1.0) if act_hrs > 0 else 0.0
      w[f'lbl_eff{wo}'].text = f"Efficiency {wo} = {eff*100:.2f} %"
      self._set_bar(w[f'bar_eff{wo}'], eff)

      # Total cases
    c1 = self._fv(w['tb_act_cases1'].text)
    c2 = self._fv(w['tb_act_cases2'].text) if w['chk_wo2'].checked else 0.0
    w['tb_cases_total'].text = str(int(c1 + c2))

        self._recalc_avail(mid)

    def _recalc_avail(self, mid):
        w       = self._panels[mid]
        runtime = self._fv(w['dd_runtotal'].selected_value)

        lost = sum(self._fv(w[k].selected_value) for k in
                   ('dd_lost_a','dd_lost_b','dd_lost_c','dd_lost_d','dd_cot'))
        w['tb_lost_total'].text = str(round(lost, 1))

        if runtime <= 0:
            w['lbl_avail'].text = "Availability = N/A"
            return
        if lost > runtime:
            alert("⚠ Time lost is greater than run time — please correct.")
            return

        avail = 1.0 - (lost / runtime)
        w['lbl_avail'].text = f"Availability = {avail*100:.2f} %"
        self._set_bar(w['bar_avail'], avail)

    @staticmethod
    def _set_bar(bar_wgt, pct):
        """Colour and size a Label progress-bar widget."""
        bar_wgt.background = _pct_color(pct)
        bar_wgt.width      = f"{min(int(pct * 100), 100)}%"

    # ════════════════════════════════════════════════════════════════
    # COLLECT DATA FOR SAVE
    # ════════════════════════════════════════════════════════════════

    def _collect(self, mid):
        w  = self._panels[mid]
        fv = self._fv

        def pct_from_label(lbl_key):
            try:
                return float(w[lbl_key].text.split('=')[1]
                             .replace('%','').strip())
            except Exception:
                return 0.0

        return {
            'run_total':    fv(w['dd_runtotal'].selected_value),
            'cases_total':  fv(w['tb_cases_total'].text),
            'lost_total':   fv(w['tb_lost_total'].text),
            'availability': pct_from_label('lbl_avail'),
            'cot':          fv(w['dd_cot'].selected_value),
            'ot':           fv(w['dd_ot'].selected_value),
            'late_start':   fv(w['dd_ls'].selected_value),
            'early_leave':  fv(w['dd_el'].selected_value),
            'wo1':          w['tb_wo1'].text,
            'run1':         fv(w['dd_run1'].selected_value),
            'pn1':          w['dd_pn1'].selected_value or '',
            'geo1':         w['tb_geo1'].text,
            'mat1':         w['tb_mat1'].text,
            'plan_cases1':  fv(w['tb_plan_cases1'].text),
            'act_cases1':   fv(w['tb_act_cases1'].text),
            'issue_a':      w['dd_issue_a'].selected_value or '',
            'lost_a':       fv(w['dd_lost_a'].selected_value),
            'issue_b':      w['dd_issue_b'].selected_value or '',
            'lost_b':       fv(w['dd_lost_b'].selected_value),
            'attainment1':  pct_from_label('lbl_att1'),
            'efficiency1':  pct_from_label('lbl_eff1'),
            'est_hr1':      fv(w['tb_est_hr1'].text),
            'act_hr1':      fv(w['tb_act_hr1'].text),
            'plan_mp1':     fv(w['tb_plan_mp1'].text),
            'act_mp1':      fv(w['tb_act_mp1'].text),
            'wo2':          w['tb_wo2'].text if w['chk_wo2'].checked else '',
            'run2':         fv(w['dd_run2'].selected_value),
            'pn2':          w['dd_pn2'].selected_value or '',
            'geo2':         w['tb_geo2'].text,
            'mat2':         w['tb_mat2'].text,
            'plan_cases2':  fv(w['tb_plan_cases2'].text),
            'act_cases2':   fv(w['tb_act_cases2'].text),
            'issue_c':      w['dd_issue_c'].selected_value or '',
            'lost_c':       fv(w['dd_lost_c'].selected_value),
            'issue_d':      w['dd_issue_d'].selected_value or '',
            'lost_d':       fv(w['dd_lost_d'].selected_value),
            'attainment2':  pct_from_label('lbl_att2'),
            'efficiency2':  pct_from_label('lbl_eff2'),
            'est_hr2':      fv(w['tb_est_hr2'].text),
            'act_hr2':      fv(w['tb_act_hr2'].text),
            'plan_mp2':     fv(w['tb_plan_mp2'].text),
            'act_mp2':      fv(w['tb_act_mp2'].text),
            'next_wo':      w['tb_next_wo'].text,
            'next_pn':      w['dd_pn_next'].selected_value or '',
            'next_geo':     w['tb_next_geo'].text,
            'next_mat':     w['tb_next_mat'].text,
            'tool_number':  w['tb_tool'].text,
            'tool_ready':   w['chk_tool'].checked,
            'labels_ready': w['chk_labels'].checked,
            'kit_ready':    w['chk_kit'].checked,
        }

    # ════════════════════════════════════════════════════════════════
    # POPULATE UI FROM LOADED DATA
    # ════════════════════════════════════════════════════════════════

    def _populate(self, mid, data):
        w  = self._panels[mid]

        def sv(k, fallback=''):
            v = data.get(k, fallback)
            return '' if v is None else v

        def ft(v):
            """float → dropdown string  e.g.  1 → '1.0',  0 → '0' """
            try:
                f = float(v)
                if f == 0:      return '0'
                if f == int(f): return f'{int(f)}.0'
                return str(f)
            except Exception:
                return '0'

        # Enable WO1 first
        w['chk_wo1'].checked = True
        self._on_wo1_change(mid)

        w['dd_runtotal'].selected_value    = ft(sv('run_total', 0))
        w['tb_cases_total'].text           = str(sv('cases_total', ''))
        w['tb_lost_total'].text            = str(sv('lost_total',  ''))
        w['dd_cot'].selected_value         = ft(sv('cot', 0))
        w['dd_ot'].selected_value          = ft(sv('ot',  0))
        w['dd_ls'].selected_value          = ft(sv('late_start',  0))
        w['dd_el'].selected_value          = ft(sv('early_leave', 0))

        # WO1 fields
        w['tb_wo1'].text                   = str(sv('wo1'))
        w['dd_run1'].selected_value        = ft(sv('run1', 0))
        w['dd_pn1'].selected_value         = sv('pn1')
        self._on_pn_change(mid, 1)
        w['tb_act_cases1'].text            = str(sv('act_cases1', ''))
        w['dd_issue_a'].selected_value     = sv('issue_a')
        w['dd_lost_a'].selected_value      = ft(sv('lost_a', 0))
        w['dd_issue_b'].selected_value     = sv('issue_b')
        w['dd_lost_b'].selected_value      = ft(sv('lost_b', 0))
        w['tb_act_mp1'].text               = str(sv('act_mp1', ''))

        # WO2 fields (only if wo2 has a value)
        if sv('wo2'):
            w['chk_wo2'].checked = True
            self._on_wo2_change(mid)
            w['tb_wo2'].text               = str(sv('wo2'))
            w['dd_run2'].selected_value    = ft(sv('run2', 0))
            w['dd_pn2'].selected_value     = sv('pn2')
            self._on_pn_change(mid, 2)
            w['tb_act_cases2'].text        = str(sv('act_cases2', ''))
            w['dd_issue_c'].selected_value = sv('issue_c')
            w['dd_lost_c'].selected_value  = ft(sv('lost_c', 0))
            w['dd_issue_d'].selected_value = sv('issue_d')
            w['dd_lost_d'].selected_value  = ft(sv('lost_d', 0))
            w['tb_act_mp2'].text           = str(sv('act_mp2', ''))

        # Next shift
        w['tb_next_wo'].text               = str(sv('next_wo'))
        w['dd_pn_next'].selected_value     = sv('next_pn')
        self._on_pn_next_change(mid)
        w['tb_tool'].text                  = str(sv('tool_number'))
        w['chk_tool'].checked              = bool(data.get('tool_ready',   False))
        w['chk_labels'].checked            = bool(data.get('labels_ready', False))
        w['chk_kit'].checked               = bool(data.get('kit_ready',    False))

        # Trigger recalc to restore bars
        self._recalc(mid)
        self._recalc_avail(mid)

    # ════════════════════════════════════════════════════════════════
    # SAVE  (mirrors cmd073save_Click etc.)
    # ════════════════════════════════════════════════════════════════

    def _save_machine(self, mid):
        ds = self._date_shift()
        if not ds:
            return
        m, d, y, s = ds

        exists  = anvil.server.call('check_machine_exists', m, d, y, s, mid)
        today   = date.today()
        is_today = (str(today.month) == m and str(today.day) == d
                    and str(today.year) == y)

        if exists:
            if is_today:
                if not confirm(
                    f"Data for ASB-{mid} already exists for this shift.\n"
                    "Do you want to OVERWRITE it?",
                    dismissible=False
                ):
                    return
            else:
                # Past date — password required (mirrors PasswordProtectedSave)
                if not self._password_gate():
                    return
                if not confirm(
                    f"Overwrite existing data for ASB-{mid}?",
                    dismissible=False
                ):
                    return

        data = self._collect(mid)
        anvil.server.call('save_machine_report', m, d, y, s, mid, data)
        Notification(f"✅  ASB-{mid} saved!", style="success", timeout=3).show()

    def _password_gate(self):
        tb = TextBox(placeholder="Password", hide_text=True)
        ok = alert(
            content=tb,
            title="Password required to edit past data",
            buttons=[("Confirm", True), ("Cancel", False)],
            dismissible=False
        )
        if not ok:
            return False
        if anvil.server.call('check_password', tb.text):
            return True
        alert("❌  Incorrect password. Save cancelled.")
        return False

    # ════════════════════════════════════════════════════════════════
    # LOAD  (mirrors cmd073load_Click etc.)
    # ════════════════════════════════════════════════════════════════

    def _load_machine(self, mid):
        ds = self._date_shift()
        if not ds:
            return
        m, d, y, s = ds
        data = anvil.server.call('load_machine_report', m, d, y, s, mid)
        if not data:
            alert(f"No data found for ASB-{mid} on {m}/{d}/{y} — {s} shift.")
            return
        self._populate(mid, data)
        Notification(f"📂  ASB-{mid} loaded!", style="success", timeout=3).show()

    # ── Header LOAD ALL button ────────────────────────────────────
    def btn_load_all_click(self, **event_args):
        ds = self._date_shift()
        if not ds:
            return
        m, d, y, s = ds
        all_data = anvil.server.call('load_all_machines', m, d, y, s)
        if not all_data:
            alert("No data found for this date and shift.")
            return
        for mid, data in all_data.items():
            if mid in self._panels:
                self._populate(mid, data)
        Notification("📂  All machines loaded!", style="success", timeout=4).show()

    # ════════════════════════════════════════════════════════════════
    # PDF REPORT
    # ════════════════════════════════════════════════════════════════

    def btn_pdf_click(self, **event_args):
        ds = self._date_shift()
        if not ds:
            return
        m, d, y, s = ds
        with Notification("⏳  Generating PDF report…", style="info"):
            pdf = anvil.server.call('generate_pdf_report', m, d, y, s)
        if pdf:
            download(pdf)
        else:
            alert("No saved data found for this date and shift.")

    # ════════════════════════════════════════════════════════════════
    # UTILITIES
    # ════════════════════════════════════════════════════════════════

    def _date_shift(self):
        m = (self.tb_month.text or '').strip()
        d = (self.tb_day.text   or '').strip()
        y = (self.tb_year.text  or '').strip()
        if not (m and d and y):
            alert("Please enter Month, Day and Year.")
            return None
        if not all(x.isdigit() for x in (m, d, y)):
            alert("Month, Day and Year must be numbers only.")
            return None
        if int(m) < 1 or int(m) > 12:
            alert("Month must be between 1 and 12.")
            return None
        if int(d) < 1 or int(d) > 31:
            alert("Day must be between 1 and 31.")
            return None
        if   self.rb_night.selected:     s = "night"
        elif self.rb_day.selected:       s = "day"
        elif self.rb_afternoon.selected: s = "afternoon"
        else:
            alert("Please select a shift.")
            return None
        return m, d, y, s
