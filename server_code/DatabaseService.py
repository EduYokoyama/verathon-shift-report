"""
DatabaseService.py
Server-side save / load / check operations.
Mirrors the VBA save/load macros (cmd073save_Click, Load073Data, etc.)
"""
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server


# ── Internal helpers ────────────────────────────────────────────────────────

def _make_key(month, day, year, shift):
  """Build the same composite key the VBA used: '3182026night'"""
  return f"{month}{day}{year}{shift}"


def _get_or_create_shift(month, day, year, shift):
  key = _make_key(month, day, year, shift)
  row = app_tables.shifts.get(shift_key=key)
  if not row:
    row = app_tables.shifts.add_row(
      shift_key=key,
      month=str(month),
      day=str(day),
      year=str(year),
      shift=str(shift)
    )
  return row


# ── Public callables ────────────────────────────────────────────────────────

@anvil.server.callable
def save_machine_report(month, day, year, shift, machine_id, data):
  """
    Save (or overwrite) one machine's data for a given shift.
    Equivalent to Data073entry(), Data179entry() … etc.
    """
  shift_row = _get_or_create_shift(month, day, year, shift)

  existing = app_tables.machine_reports.get(
    shift=shift_row,
    machine_id=machine_id
  )
  if existing:
    existing.update(**data)
  else:
    app_tables.machine_reports.add_row(
      shift=shift_row,
      machine_id=machine_id,
      **data
    )
  return True


@anvil.server.callable
def load_machine_report(month, day, year, shift, machine_id):
  """
    Load one machine's saved data.
    Equivalent to Load073Data(), Load179Data() … etc.
    Returns a plain dict or None.
    """
  key       = _make_key(month, day, year, shift)
  shift_row = app_tables.shifts.get(shift_key=key)
  if not shift_row:
    return None

  report = app_tables.machine_reports.get(
    shift=shift_row,
    machine_id=machine_id
  )
  return dict(report) if report else None


@anvil.server.callable
def load_all_machines(month, day, year, shift):
  """
    Load every machine saved for a shift (used by LOAD ALL button).
    Equivalent to cmdload_Click() in the form.
    Returns  {machine_id: data_dict, …}
    """
  key       = _make_key(month, day, year, shift)
  shift_row = app_tables.shifts.get(shift_key=key)
  if not shift_row:
    return {}

  reports = app_tables.machine_reports.search(shift=shift_row)
  return {r['machine_id']: dict(r) for r in reports}


@anvil.server.callable
def check_machine_exists(month, day, year, shift, machine_id):
  """
    Returns True if data for this machine/shift already exists.
    Used to trigger overwrite-warning / password logic.
    """
  key       = _make_key(month, day, year, shift)
  shift_row = app_tables.shifts.get(shift_key=key)
  if not shift_row:
    return False
  report = app_tables.machine_reports.get(
    shift=shift_row,
    machine_id=machine_id
  )
  return report is not None


@anvil.server.callable
def check_password(entered):
  """
    Validate the overwrite password stored in app_config.
    Equivalent to PasswordProtectedSave() in the VBA module.
    """
  row = app_tables.app_config.get(key="save_password")
  if not row:
    return False
  return entered == row['value']
