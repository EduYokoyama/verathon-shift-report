from ._anvil_designer import Form1Template
from anvil import *
import anvil.server
from datetime import date

MACHINES = [
  ("073", "ASB-073", "welder"),
  ("179", "ASB-179", "welder"),
  ("075", "ASB-075", "welder"),
  ("231", "ASB-231", "welder"),
  ("170", "ASB-170", "welder"),
  ("258", "ASB-258", "welder"),
  ("259", "ASB-259", "welder"),
  ("260", "ASB-260", "welder"),
  ("MV1", "MV1", "multivac"),
  ("MV2", "MV2", "multivac"),
]

TIME_OPTIONS = [
  "0", "0.5", "1.0", "1.5", "2.0", "2.5", "3.0", "3.5",
  "4.0", "4.5", "5.0", "5.5", "6.0", "6.5", "7.0", "7.5", "8.0"
]


def pct_color(pct):
  if pct >= 1.0:
    return "#00FF00"
  elif pct >= 0.75:
    return "#009900"
  elif pct >= 0.30:
    return "#FFFF00"
  else:
    return "#0000CC"


class Form1(Form1Template):
  def __init__(self, **properties):
    self.init_components(**properties)
    self._panels = {}
    self._panel_components = {}
    self._pn_cache = {}
    self._iss_cache = {}
    self._current_mid = None
    self._build_header()
    self._preload_lists()
    self._build_all_panels()
    self._show_machine("073")

  # ----------------------------------------------------------------
  # HEADER
  # ----------------------------------------------------------------

  def _build_header(self):
    self._outer = ColumnPanel(background='#001166')
    self.add_component(self._outer)

    self._outer.add_component(Label(
      text='Verathon Daily Shift Report',
      font_size=20,
      bold=True,
      foreground='white',
      align='center'
    ))

    date_row = FlowPanel()
    date_row.add_component(Label(text='Month:', foreground='white', bold=True))
    self._tb_month = TextBox(placeholder='mm', width=50)
    date_row.add_component(self._tb_month)
    date_row.add_component(Label(text='  Day:', foreground='white', bold=True))
    self._tb_day = TextBox(placeholder='dd', width=50)
    date_row.add_component(self._tb_day)
    date_row.add_component(Label(text='  Year:', foreground='white', bold=True))
    self._tb_year = TextBox(placeholder='yyyy', width=70)
    date_row.add_component(self._tb_year)
    self._outer.add_component(date_row)

    t = date.today()
    self._tb_month.text = str(t.month)
    self._tb_day.text = str(t.day)
    self._tb_year.text = str(t.year)

    shift_row = FlowPanel()
    self._rb_night = RadioButton(
      text='Night', group_name='shift', foreground='white', bold=True)
    self._rb_day_rb = RadioButton(
      text='Day', group_name='shift', foreground='white', bold=True)
    self._rb_afternoon = RadioButton(
      text='Afternoon', group_name='shift', foreground='white', bold=True)
    self._rb_night.selected = True
    shift_row.add_component(self._rb_night)
    shift_row.add_component(Label(text='   ', foreground='white'))
    shift_row.add_component(self._rb_day_rb)
    shift_row.add_component(Label(text='   ', foreground='white'))
    shift_row.add_component(self._rb_afternoon)
    self._outer.add_component(shift_row)

    machine_row = FlowPanel()
    machine_row.add_component(Label(text='Machine:', foreground='white', bold=True))
    self._dd_machine = DropDown(
      items=[label for _, label, _ in MACHINES],
      selected_value='ASB-073'
    )
    self._dd_machine.set_event_handler('change', self._on_machine_change)
    machine_row.add_component(self._dd_machine)
    self._outer.add_component(machine_row)

    btn_row = FlowPanel()
    btn_load_all = Button(
      text='LOAD ALL', background='#336699', foreground='white', bold=True)
    btn_pdf = Button(
      text='PDF REPORT', background='#006600', foreground='white', bold=True)
    btn_load_all.set_event_handler('click', self._btn_load_all_click)
    btn_pdf.set_event_handler('click', self._btn_pdf_click)
    btn_row.add_component(btn_load_all)
    btn_row.add_component(Label(text='   '))
    btn_row.add_component(btn_pdf)
    self._outer.add_component(btn_row)

    self._content_area = ColumnPanel()
    self._outer.add_component(self._content_area)

    self._outer.add_component(Label(
      text='Southmedic Inc.',
      foreground='#AACCFF',
      font_size=9,
      align='center'
    ))

  def _on_machine_change(self, **event_args):
    label = self._dd_machine.selected_value
    for mid, lbl, _ in MACHINES:
      if lbl == label:
        self._show_machine(mid)
        break

  def _show_machine(self, mid):
    self._content_area.clear()
    if mid in self._panel_components:
      self._content_area.add_component(self._panel_components[mid])
    self._current_mid = mid

  # ----------------------------------------------------------------
  # PRELOAD DATA
  # ----------------------------------------------------------------

  def _preload_lists(self):
    for mid, _, mtype in MACHINES:
      if mid not in self._pn_cache:
        self._pn_cache[mid] = anvil.server.call('get_part_numbers', mid)
      if mtype not in self._iss_cache:
        self._iss_cache[mtype] = anvil.server.call('get_issues', mtype)

  # ----------------------------------------------------------------
  # BUILD ALL PANELS
  # ----------------------------------------------------------------

  def _build_all_panels(self):
    for mid, label, mtype in MACHINES:
      w = self._build_panel(mid, mtype)
      self._panels[mid] = w
      self._panel_components[mid] = w['_root']

  # ----------------------------------------------------------------
  # BUILD ONE MACHINE PANEL
  # ----------------------------------------------------------------

  def _build_panel(self, mid, mtype):
    w = {}
    pns = [''] + [p['pn'] for p in self._pn_cache.get(mid, [])]
    iss = [''] + self._iss_cache.get(mtype, [])

    root = ColumnPanel(background='#0000AA')

    def add_row(*widgets):
      fp = FlowPanel()
      for wgt in widgets:
        fp.add_component(wgt)
      root.add_component(fp)

    def lbl(text, bold=False, color='white'):
      return Label(text=text, foreground=color, bold=bold)

    def tb(ph='', w_=90, enabled=True):
      return TextBox(placeholder=ph, width=w_, enabled=enabled)

    def dd(items, ph='', enabled=True):
      return DropDown(items=items, placeholder=ph, enabled=enabled)

    def chk(text):
      return CheckBox(text=text, foreground='white', bold=True)

    def bar():
      b = Label(text=' ', background='#333333', width='0%'); b.height = 20; return b

    w['chk_wo1'] = chk("WO1")
    w['chk_wo2'] = chk("WO2")
    w['dd_cot'] = dd(TIME_OPTIONS, "Changeover (h)", enabled=False)
    add_row(w['chk_wo1'], lbl("    "),
            w['chk_wo2'], lbl("  Changeover (h):"), w['dd_cot'])

    w['tb_wo1'] = tb("WO1 #", 80, enabled=False)
    w['dd_run1'] = dd(TIME_OPTIONS, "Run T1 (h)", enabled=False)
    w['tb_wo2'] = tb("WO2 #", 80, enabled=False)
    w['dd_run2'] = dd(TIME_OPTIONS, "Run T2 (h)", enabled=False)
    add_row(lbl("WO1:"), w['tb_wo1'], lbl(" Run T(h):"), w['dd_run1'],
            lbl("    WO2:"), w['tb_wo2'], lbl(" Run T(h):"), w['dd_run2'])

    w['dd_pn1'] = dd(pns, "Part Number 1", enabled=False)
    w['dd_pn2'] = dd(pns, "Part Number 2", enabled=False)
    add_row(lbl("PN 1:"), w['dd_pn1'], lbl("   PN 2:"), w['dd_pn2'])

    w['tb_geo1'] = tb("Geometry 1", 110, enabled=False)
    w['tb_mat1'] = tb("Material 1", 80, enabled=False)
    w['tb_plan_cases1'] = tb("Plan Cases 1", 75, enabled=False)
    w['tb_geo2'] = tb("Geometry 2", 110, enabled=False)
    w['tb_mat2'] = tb("Material 2", 80, enabled=False)
    w['tb_plan_cases2'] = tb("Plan Cases 2", 75, enabled=False)
    add_row(lbl("Geo:"), w['tb_geo1'], lbl(" Mat:"), w['tb_mat1'],
            lbl(" Plan:"), w['tb_plan_cases1'],
            lbl("  Geo:"), w['tb_geo2'], lbl(" Mat:"), w['tb_mat2'],
            lbl(" Plan:"), w['tb_plan_cases2'])

    w['tb_act_cases1'] = tb("Act Cases 1", 75, enabled=False)
    w['tb_act_cases2'] = tb("Act Cases 2", 75, enabled=False)
    add_row(lbl("Act Cases 1:"), w['tb_act_cases1'],
            lbl("   Act Cases 2:"), w['tb_act_cases2'])

    w['dd_issue_a'] = dd(iss, "Issue A", enabled=False)
    w['dd_lost_a'] = dd(TIME_OPTIONS, "Lost (h)", enabled=False)
    w['dd_issue_b'] = dd(iss, "Issue B", enabled=False)
    w['dd_lost_b'] = dd(TIME_OPTIONS, "Lost (h)", enabled=False)
    add_row(lbl("Issue A:"), w['dd_issue_a'], lbl(" Lost:"), w['dd_lost_a'],
            lbl("  Issue B:"), w['dd_issue_b'], lbl(" Lost:"), w['dd_lost_b'])

    w['dd_issue_c'] = dd(iss, "Issue C", enabled=False)
    w['dd_lost_c'] = dd(TIME_OPTIONS, "Lost (h)", enabled=False)
    w['dd_issue_d'] = dd(iss, "Issue D", enabled=False)
    w['dd_lost_d'] = dd(TIME_OPTIONS, "Lost (h)", enabled=False)
    add_row(lbl("Issue C:"), w['dd_issue_c'], lbl(" Lost:"), w['dd_lost_c'],
            lbl("  Issue D:"), w['dd_issue_d'], lbl(" Lost:"), w['dd_lost_d'])

    w['lbl_att1'] = lbl("Attainment 1 = 0.00 %")
    w['bar_att1'] = bar()
    w['lbl_att2'] = lbl("Attainment 2 = 0.00 %")
    w['bar_att2'] = bar()
    root.add_component(w['lbl_att1'])
    root.add_component(w['bar_att1'])
    root.add_component(w['lbl_att2'])
    root.add_component(w['bar_att2'])

    w['lbl_eff1'] = lbl("Efficiency 1 = 0.00 %")
    w['bar_eff1'] = bar()
    w['lbl_eff2'] = lbl("Efficiency 2 = 0.00 %")
    w['bar_eff2'] = bar()
    root.add_component(w['lbl_eff1'])
    root.add_component(w['bar_eff1'])
    root.add_component(w['lbl_eff2'])
    root.add_component(w['bar_eff2'])

    w['dd_runtotal'] = dd(TIME_OPTIONS, "Total Run T (h)")
    w['tb_cases_total'] = tb("Total Cases", 70, enabled=False)
    w['tb_lost_total'] = tb("Total Lost", 70, enabled=False)
    add_row(lbl("Total Run T:"), w['dd_runtotal'],
            lbl("  Total Cases:"), w['tb_cases_total'],
            lbl("  Total Lost:"), w['tb_lost_total'])

    w['lbl_avail'] = lbl("Availability = N/A", bold=True)
    w['bar_avail'] = Label(text=' ', background='#333333', width='0%'); w['bar_avail'].height = 26
    root.add_component(w['lbl_avail'])
    root.add_component(w['bar_avail'])

    w['tb_est_hr1'] = tb("Est Hrs 1", 65, enabled=False)
    w['tb_act_hr1'] = tb("Act Hrs 1", 65, enabled=False)
    w['tb_plan_mp1'] = tb("Plan MP 1", 65, enabled=False)
    w['tb_act_mp1'] = tb("Act MP 1", 65, enabled=False)
    w['tb_est_hr2'] = tb("Est Hrs 2", 65, enabled=False)
    w['tb_act_hr2'] = tb("Act Hrs 2", 65, enabled=False)
    w['tb_plan_mp2'] = tb("Plan MP 2", 65, enabled=False)
    w['tb_act_mp2'] = tb("Act MP 2", 65, enabled=False)
    add_row(lbl("Est Hrs 1:"), w['tb_est_hr1'],
            lbl(" Act:"), w['tb_act_hr1'],
            lbl(" PlanMP:"), w['tb_plan_mp1'],
            lbl(" ActMP:"), w['tb_act_mp1'],
            lbl("  Est Hrs 2:"), w['tb_est_hr2'],
            lbl(" Act:"), w['tb_act_hr2'],
            lbl(" PlanMP:"), w['tb_plan_mp2'],
            lbl(" ActMP:"), w['tb_act_mp2'])

    w['dd_ot'] = dd(TIME_OPTIONS, "Overtime (h)")
    w['dd_ls'] = dd(TIME_OPTIONS, "Late Start (h)")
    w['dd_el'] = dd(TIME_OPTIONS, "Early Leave (h)")
    add_row(lbl("OT:"), w['dd_ot'],
            lbl("  Late Start:"), w['dd_ls'],
            lbl("  Early Leave:"), w['dd_el'])

    root.add_component(lbl("--- NEXT SHIFT ---", bold=True, color='#FFFF00'))

    w['tb_next_wo'] = tb("Next WO", 80)
    w['dd_pn_next'] = dd(pns, "Next PN")
    w['tb_next_geo'] = tb("Next Geo", 110, enabled=False)
    w['tb_next_mat'] = tb("Next Mat", 80, enabled=False)
    add_row(lbl("Next WO:"), w['tb_next_wo'],
            lbl("  Next PN:"), w['dd_pn_next'],
            lbl("  Geo:"), w['tb_next_geo'],
            lbl("  Mat:"), w['tb_next_mat'])

    w['chk_tool'] = chk("Molding tool ready?")
    w['tb_tool'] = tb("Tool #", 80)
    w['chk_labels'] = chk("Labels ready?")
    w['chk_kit'] = chk("Kit ready?")
    add_row(w['chk_tool'], w['tb_tool'], w['chk_labels'], w['chk_kit'])

    btn_save = Button(text="SAVE", background="#009900",
                      foreground="white", bold=True)
    btn_load = Button(text="LOAD", background="#555555",
                      foreground="white", bold=True)
    btn_save.set_event_handler('click', self._make_save_handler(mid))
    btn_load.set_event_handler('click', self._make_load_handler(mid))
    add_row(btn_save, lbl("  "), btn_load)

    w['chk_wo1'].set_event_handler('change', self._make_wo1_handler(mid))
    w['chk_wo2'].set_event_handler('change', self._make_wo2_handler(mid))
    w['dd_pn1'].set_event_handler('change', self._make_pn_handler(mid, 1))
    w['dd_pn2'].set_event_handler('change', self._make_pn_handler(mid, 2))
    w['dd_pn_next'].set_event_handler('change', self._make_pn_next_handler(mid))
    w['dd_run1'].set_event_handler('change', self._make_recalc_handler(mid))
    w['dd_run2'].set_event_handler('change', self._make_recalc_handler(mid))
    w['tb_act_mp1'].set_event_handler('change', self._make_recalc_handler(mid))
    w['tb_act_mp2'].set_event_handler('change', self._make_recalc_handler(mid))
    w['tb_act_cases1'].set_event_handler('change', self._make_recalc_handler(mid))
    w['tb_act_cases2'].set_event_handler('change', self._make_recalc_handler(mid))
    w['dd_runtotal'].set_event_handler('change', self._make_avail_handler(mid))
    w['dd_lost_a'].set_event_handler('change', self._make_avail_handler(mid))
    w['dd_lost_b'].set_event_handler('change', self._make_avail_handler(mid))
    w['dd_lost_c'].set_event_handler('change', self._make_avail_handler(mid))
    w['dd_lost_d'].set_event_handler('change', self._make_avail_handler(mid))
    w['dd_cot'].set_event_handler('change', self._make_avail_handler(mid))
    w['dd_issue_a'].set_event_handler('change',
      self._make_issue_handler(mid, 'dd_issue_a', 'dd_lost_a'))
    w['dd_issue_b'].set_event_handler('change',
      self._make_issue_handler(mid, 'dd_issue_b', 'dd_lost_b'))
    w['dd_issue_c'].set_event_handler('change',
      self._make_issue_handler(mid, 'dd_issue_c', 'dd_lost_c'))
    w['dd_issue_d'].set_event_handler('change',
      self._make_issue_handler(mid, 'dd_issue_d', 'dd_lost_d'))

    w['_rate1'] = 0.0
    w['_ehrs1'] = 0.0
    w['_rate2'] = 0.0
    w['_ehrs2'] = 0.0
    w['_root'] = root
    return w

  # ----------------------------------------------------------------
  # EVENT HANDLER FACTORIES
  # ----------------------------------------------------------------

  def _make_wo1_handler(self, mid):
    def handler(**event_args):
      self._on_wo1_change(mid)
    return handler

  def _make_wo2_handler(self, mid):
    def handler(**event_args):
      self._on_wo2_change(mid)
    return handler

  def _make_pn_handler(self, mid, wo):
    def handler(**event_args):
      self._on_pn_change(mid, wo)
    return handler

  def _make_pn_next_handler(self, mid):
    def handler(**event_args):
      self._on_pn_next_change(mid)
    return handler

  def _make_recalc_handler(self, mid):
    def handler(**event_args):
      self._recalc(mid)
    return handler

  def _make_avail_handler(self, mid):
    def handler(**event_args):
      self._recalc_avail(mid)
    return handler

  def _make_issue_handler(self, mid, ik, lk):
    def handler(**event_args):
      self._on_issue_chg(mid, ik, lk)
    return handler

  def _make_save_handler(self, mid):
    def handler(**event_args):
      self._save_machine(mid)
    return handler

  def _make_load_handler(self, mid):
    def handler(**event_args):
      self._load_machine(mid)
    return handler

  def _btn_load_all_click(self, **event_args):
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
    Notification("All machines loaded!", style="success", timeout=4).show()

  def _btn_pdf_click(self, **event_args):
    ds = self._date_shift()
    if not ds:
      return
    m, d, y, s = ds
    with Notification("Generating PDF...", style="info"):
      pdf = anvil.server.call('generate_pdf_report', m, d, y, s)
    if pdf:
      download(pdf)
    else:
      alert("No saved data found for this date and shift.")

  # ----------------------------------------------------------------
  # WO ENABLE / DISABLE
  # ----------------------------------------------------------------

  def _on_wo1_change(self, mid):
    w = self._panels[mid]
    en = w['chk_wo1'].checked
    for k in ('tb_wo1', 'dd_run1', 'dd_pn1', 'tb_act_cases1',
              'dd_issue_a', 'dd_lost_a', 'dd_issue_b', 'dd_lost_b',
              'tb_act_mp1'):
      w[k].enabled = en
    if not en:
      for k in ('tb_wo1', 'tb_act_cases1'):
        w[k].text = ''
      for k in ('dd_run1', 'dd_pn1', 'dd_issue_a',
                'dd_issue_b', 'dd_lost_a', 'dd_lost_b'):
        w[k].selected_value = None
      self._recalc(mid)

  def _on_wo2_change(self, mid):
    w = self._panels[mid]
    en = w['chk_wo2'].checked
    for k in ('tb_wo2', 'dd_run2', 'dd_pn2', 'tb_act_cases2',
              'dd_issue_c', 'dd_lost_c', 'dd_issue_d', 'dd_lost_d',
              'dd_cot', 'tb_act_mp2'):
      w[k].enabled = en
    if not en:
      for k in ('tb_wo2', 'tb_act_cases2'):
        w[k].text = ''
      for k in ('dd_run2', 'dd_pn2', 'dd_cot', 'dd_issue_c',
                'dd_issue_d', 'dd_lost_c', 'dd_lost_d'):
        w[k].selected_value = None
      self._recalc(mid)

  # ----------------------------------------------------------------
  # PART NUMBER CHANGE
  # ----------------------------------------------------------------

  def _on_pn_change(self, mid, wo):
    w = self._panels[mid]
    wo_str = str(wo)
    pn = w['dd_pn' + wo_str].selected_value
    if not pn:
      w['tb_geo' + wo_str].text = ''
      w['tb_mat' + wo_str].text = ''
      w['tb_plan_mp' + wo_str].text = ''
      w['_rate' + wo_str] = 0.0
      w['_ehrs' + wo_str] = 0.0
      return
    det = anvil.server.call('get_pn_details', mid, pn)
    if det:
      w['tb_geo' + wo_str].text = str(det.get('geometry', ''))
      w['tb_mat' + wo_str].text = str(det.get('material', ''))
      w['tb_plan_mp' + wo_str].text = str(det.get('crew_size', ''))
      w['_rate' + wo_str] = float(det.get('run_rate', 0))
      w['_ehrs' + wo_str] = float(det.get('est_hrs', 0))
      self._recalc(mid)

  def _on_pn_next_change(self, mid):
    w = self._panels[mid]
    pn = w['dd_pn_next'].selected_value
    if not pn:
      w['tb_next_geo'].text = ''
      w['tb_next_mat'].text = ''
      return
    det = anvil.server.call('get_pn_details', mid, pn)
    if det:
      w['tb_next_geo'].text = str(det.get('geometry', ''))
      w['tb_next_mat'].text = str(det.get('material', ''))

  # ----------------------------------------------------------------
  # ISSUE CHANGE
  # ----------------------------------------------------------------

  def _on_issue_chg(self, mid, ik, lk):
    w = self._panels[mid]
    w[lk].enabled = bool(w[ik].selected_value)
    self._recalc_avail(mid)

  # ----------------------------------------------------------------
  # CALCULATIONS
  # ----------------------------------------------------------------

  def _fv(self, v, default=0.0):
    try:
      if v is None or v == '' or v == 'None':
        return default
      return float(v)
    except (ValueError, TypeError):
      return default

  def _recalc(self, mid):
    w = self._panels[mid]
    for wo in (1, 2):
      wo_str = str(wo)
      run = self._fv(w['dd_run' + wo_str].selected_value)
      act_mp = self._fv(w['tb_act_mp' + wo_str].text)
      rate = w.get('_rate' + wo_str, 0.0)
      ehrs = w.get('_ehrs' + wo_str, 0.0)

      act_hrs = run * act_mp
      w['tb_act_hr' + wo_str].text = str(round(act_hrs, 2))

      plan_cases = rate * run
      w['tb_plan_cases' + wo_str].text = str(round(plan_cases))

      act_cases = self._fv(w['tb_act_cases' + wo_str].text)
      est_hrs = ehrs * act_cases
      w['tb_est_hr' + wo_str].text = str(round(est_hrs, 2))

      if plan_cases > 0:
        att = min(act_cases / plan_cases, 1.0)
      else:
        att = 0.0
      att_pct = round(att * 100, 2)
      w['lbl_att' + wo_str].text = "Attainment " + wo_str + " = " + str(att_pct) + " %"
      self._set_bar(w['bar_att' + wo_str], att)

      if act_hrs > 0:
        eff = min(est_hrs / act_hrs, 1.0)
      else:
        eff = 0.0
      eff_pct = round(eff * 100, 2)
      w['lbl_eff' + wo_str].text = "Efficiency " + wo_str + " = " + str(eff_pct) + " %"
      self._set_bar(w['bar_eff' + wo_str], eff)

    c1 = self._fv(w['tb_act_cases1'].text)
    c2 = self._fv(w['tb_act_cases2'].text) if w['chk_wo2'].checked else 0.0
    w['tb_cases_total'].text = str(int(c1 + c2))
    self._recalc_avail(mid)

  def _recalc_avail(self, mid):
    w = self._panels[mid]
    runtime = self._fv(w['dd_runtotal'].selected_value)
    lost = (self._fv(w['dd_lost_a'].selected_value) +
            self._fv(w['dd_lost_b'].selected_value) +
            self._fv(w['dd_lost_c'].selected_value) +
            self._fv(w['dd_lost_d'].selected_value) +
            self._fv(w['dd_cot'].selected_value))
    w['tb_lost_total'].text = str(round(lost, 1))
    if runtime <= 0:
      w['lbl_avail'].text = "Availability = N/A"
      return
    if lost > runtime:
      alert("Time lost is greater than run time - please correct.")
      return
    avail = 1.0 - (lost / runtime)
    avail_pct = round(avail * 100, 2)
    w['lbl_avail'].text = "Availability = " + str(avail_pct) + " %"
    self._set_bar(w['bar_avail'], avail)

  def _set_bar(self, bar_wgt, pct):
    bar_wgt.background = pct_color(pct)
    px = min(int(pct * 100), 100)
    bar_wgt.width = str(px) + "%"

  # ----------------------------------------------------------------
  # COLLECT DATA FOR SAVE
  # ----------------------------------------------------------------

  def _collect(self, mid):
    w = self._panels[mid]

    def pct_from_lbl(key):
      try:
        return float(w[key].text.split('=')[1].replace('%', '').strip())
      except Exception:
        return 0.0

    return {
      'run_total':    self._fv(w['dd_runtotal'].selected_value),
      'cases_total':  self._fv(w['tb_cases_total'].text),
      'lost_total':   self._fv(w['tb_lost_total'].text),
      'availability': pct_from_lbl('lbl_avail'),
      'cot':          self._fv(w['dd_cot'].selected_value),
      'ot':           self._fv(w['dd_ot'].selected_value),
      'late_start':   self._fv(w['dd_ls'].selected_value),
      'early_leave':  self._fv(w['dd_el'].selected_value),
      'wo1':          w['tb_wo1'].text,
      'run1':         self._fv(w['dd_run1'].selected_value),
      'pn1':          w['dd_pn1'].selected_value or '',
      'geo1':         w['tb_geo1'].text,
      'mat1':         w['tb_mat1'].text,
      'plan_cases1':  self._fv(w['tb_plan_cases1'].text),
      'act_cases1':   self._fv(w['tb_act_cases1'].text),
      'issue_a':      w['dd_issue_a'].selected_value or '',
      'lost_a':       self._fv(w['dd_lost_a'].selected_value),
      'issue_b':      w['dd_issue_b'].selected_value or '',
      'lost_b':       self._fv(w['dd_lost_b'].selected_value),
      'attainment1':  pct_from_lbl('lbl_att1'),
      'efficiency1':  pct_from_lbl('lbl_eff1'),
      'est_hr1':      self._fv(w['tb_est_hr1'].text),
      'act_hr1':      self._fv(w['tb_act_hr1'].text),
      'plan_mp1':     self._fv(w['tb_plan_mp1'].text),
      'act_mp1':      self._fv(w['tb_act_mp1'].text),
      'wo2':          w['tb_wo2'].text if w['chk_wo2'].checked else '',
      'run2':         self._fv(w['dd_run2'].selected_value),
      'pn2':          w['dd_pn2'].selected_value or '',
      'geo2':         w['tb_geo2'].text,
      'mat2':         w['tb_mat2'].text,
      'plan_cases2':  self._fv(w['tb_plan_cases2'].text),
      'act_cases2':   self._fv(w['tb_act_cases2'].text),
      'issue_c':      w['dd_issue_c'].selected_value or '',
      'lost_c':       self._fv(w['dd_lost_c'].selected_value),
      'issue_d':      w['dd_issue_d'].selected_value or '',
      'lost_d':       self._fv(w['dd_lost_d'].selected_value),
      'attainment2':  pct_from_lbl('lbl_att2'),
      'efficiency2':  pct_from_lbl('lbl_eff2'),
      'est_hr2':      self._fv(w['tb_est_hr2'].text),
      'act_hr2':      self._fv(w['tb_act_hr2'].text),
      'plan_mp2':     self._fv(w['tb_plan_mp2'].text),
      'act_mp2':      self._fv(w['tb_act_mp2'].text),
      'next_wo':      w['tb_next_wo'].text,
      'next_pn':      w['dd_pn_next'].selected_value or '',
      'next_geo':     w['tb_next_geo'].text,
      'next_mat':     w['tb_next_mat'].text,
      'tool_number':  w['tb_tool'].text,
      'tool_ready':   w['chk_tool'].checked,
      'labels_ready': w['chk_labels'].checked,
      'kit_ready':    w['chk_kit'].checked,
    }

  # ----------------------------------------------------------------
  # POPULATE FROM LOADED DATA
  # ----------------------------------------------------------------

  def _populate(self, mid, data):
    w = self._panels[mid]

    def sv(k, fallback=''):
      v = data.get(k, fallback)
      return '' if v is None else v

    def ft(v):
      try:
        f = float(v)
        if f == 0:
          return '0'
        if f == int(f):
          return str(int(f)) + '.0'
        return str(f)
      except Exception:
        return '0'

    w['chk_wo1'].checked = True
    self._on_wo1_change(mid)

    w['dd_runtotal'].selected_value = ft(sv('run_total', 0))
    w['tb_cases_total'].text = str(sv('cases_total', ''))
    w['tb_lost_total'].text = str(sv('lost_total', ''))
    w['dd_cot'].selected_value = ft(sv('cot', 0))
    w['dd_ot'].selected_value = ft(sv('ot', 0))
    w['dd_ls'].selected_value = ft(sv('late_start', 0))
    w['dd_el'].selected_value = ft(sv('early_leave', 0))

    w['tb_wo1'].text = str(sv('wo1'))
    w['dd_run1'].selected_value = ft(sv('run1', 0))
    w['dd_pn1'].selected_value = sv('pn1')
    self._on_pn_change(mid, 1)
    w['tb_act_cases1'].text = str(sv('act_cases1', ''))
    w['dd_issue_a'].selected_value = sv('issue_a')
    w['dd_lost_a'].selected_value = ft(sv('lost_a', 0))
    w['dd_issue_b'].selected_value = sv('issue_b')
    w['dd_lost_b'].selected_value = ft(sv('lost_b', 0))
    w['tb_act_mp1'].text = str(sv('act_mp1', ''))

    if sv('wo2'):
      w['chk_wo2'].checked = True
      self._on_wo2_change(mid)
      w['tb_wo2'].text = str(sv('wo2'))
      w['dd_run2'].selected_value = ft(sv('run2', 0))
      w['dd_pn2'].selected_value = sv('pn2')
      self._on_pn_change(mid, 2)
      w['tb_act_cases2'].text = str(sv('act_cases2', ''))
      w['dd_issue_c'].selected_value = sv('issue_c')
      w['dd_lost_c'].selected_value = ft(sv('lost_c', 0))
      w['dd_issue_d'].selected_value = sv('issue_d')
      w['dd_lost_d'].selected_value = ft(sv('lost_d', 0))
      w['tb_act_mp2'].text = str(sv('act_mp2', ''))

    w['tb_next_wo'].text = str(sv('next_wo'))
    w['dd_pn_next'].selected_value = sv('next_pn')
    self._on_pn_next_change(mid)
    w['tb_tool'].text = str(sv('tool_number'))
    w['chk_tool'].checked = bool(data.get('tool_ready', False))
    w['chk_labels'].checked = bool(data.get('labels_ready', False))
    w['chk_kit'].checked = bool(data.get('kit_ready', False))
    self._recalc(mid)
    self._recalc_avail(mid)

  # ----------------------------------------------------------------
  # SAVE
  # ----------------------------------------------------------------

  def _save_machine(self, mid):
    ds = self._date_shift()
    if not ds:
      return
    m, d, y, s = ds
    exists = anvil.server.call('check_machine_exists', m, d, y, s, mid)
    today = date.today()
    is_today = (str(today.month) == m and
                str(today.day) == d and
                str(today.year) == y)
    if exists:
      if is_today:
        if not confirm("Data for ASB-" + mid + " already exists. Overwrite?",
                       dismissible=False):
          return
      else:
        if not self._password_gate():
          return
        if not confirm("Overwrite existing data for ASB-" + mid + "?",
                       dismissible=False):
          return
    data = self._collect(mid)
    anvil.server.call('save_machine_report', m, d, y, s, mid, data)
    Notification("ASB-" + mid + " saved!", style="success", timeout=3).show()

  def _password_gate(self):
    tb_pwd = TextBox(placeholder="Password")
    ok = alert(
      content=tb_pwd,
      title="Password required to edit past data",
      buttons=[("Confirm", True), ("Cancel", False)],
      dismissible=False
    )
    if not ok:
      return False
    if anvil.server.call('check_password', tb_pwd.text):
      return True
    alert("Incorrect password. Save cancelled.")
    return False

  # ----------------------------------------------------------------
  # LOAD
  # ----------------------------------------------------------------

  def _load_machine(self, mid):
    ds = self._date_shift()
    if not ds:
      return
    m, d, y, s = ds
    data = anvil.server.call('load_machine_report', m, d, y, s, mid)
    if not data:
      alert("No data found for ASB-" + mid + " on " + m + "/" + d + "/" + y)
      return
    self._populate(mid, data)
    Notification("ASB-" + mid + " loaded!", style="success", timeout=3).show()

  # ----------------------------------------------------------------
  # UTILITIES
  # ----------------------------------------------------------------

  def _date_shift(self):
    m = (self._tb_month.text or '').strip()
    d = (self._tb_day.text or '').strip()
    y = (self._tb_year.text or '').strip()
    if not (m and d and y):
      alert("Please enter Month, Day and Year.")
      return None
    if not (m.isdigit() and d.isdigit() and y.isdigit()):
      alert("Month, Day and Year must be numbers only.")
      return None
    if int(m) < 1 or int(m) > 12:
      alert("Month must be between 1 and 12.")
      return None
    if int(d) < 1 or int(d) > 31:
      alert("Day must be between 1 and 31.")
      return None
    if self._rb_night.selected:
      s = "night"
    elif self._rb_day_rb.selected:
      s = "day"
    elif self._rb_afternoon.selected:
      s = "afternoon"
    else:
      alert("Please select a shift.")
      return None
    return m, d, y, s
