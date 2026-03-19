"""
ListsService.py
Serves part-number and issues dropdown data to the client.
Equivalent to the Lists sheet lookups in the VBA (ListPn, FindIssues, DatabaseMath).
"""
import anvil.server
from anvil.tables import app_tables


@anvil.server.callable
def get_part_numbers(machine_id):
    """
    Return all part-number rows for a machine as a list of dicts.
    Equivalent to ListPn() in Module1.
    """
    rows = app_tables.part_numbers.search(machine_id=machine_id)
    return [dict(r) for r in rows]


@anvil.server.callable
def get_pn_details(machine_id, pn):
    """
    Return geometry, material, crew_size, run_rate, est_hrs for one PN.
    Equivalent to FindText() + DatabaseMath() in Module1.
    """
    row = app_tables.part_numbers.get(machine_id=machine_id, pn=pn)
    return dict(row) if row else None


@anvil.server.callable
def get_issues(machine_type):
    """
    Return the issues list for 'welder' or 'multivac'.
    Equivalent to FindIssues() in Module1.
    """
    rows = app_tables.issues_list.search(machine_type=machine_type)
    return [r['issue_name'] for r in rows]


@anvil.server.callable
def seed_initial_data():
    """
    One-time seed: populates issues_list and app_config with defaults.
    Run this once from the Anvil IDE after first deploy.
    """
    # ── Welder issues ────────────────────────────────────────────
    welder_issues = [
        "Horn Maks", "Nest Maks", "Flash", "Camera failures",
        "Weak weld value", "Failed load test", "Material not ready",
        "Sealer problems", "Automation problems", "Mold machine problems",
        "Engineering sampling/validation", "Lacking manpower",
        "Shims CO needed", "Routing cameras only"
    ]
    for issue in welder_issues:
        existing = app_tables.issues_list.get(
            machine_type='welder', issue_name=issue
        )
        if not existing:
            app_tables.issues_list.add_row(
                machine_type='welder', issue_name=issue
            )

    # ── Multivac issues ──────────────────────────────────────────
    multivac_issues = [
        "Materials", "Sealing gasket", "Chiller", "Bad forming",
        "Seal breach", "Printing issues", "Sensor issues",
        "Cutting station issues"
    ]
    for issue in multivac_issues:
        existing = app_tables.issues_list.get(
            machine_type='multivac', issue_name=issue
        )
        if not existing:
            app_tables.issues_list.add_row(
                machine_type='multivac', issue_name=issue
            )

    # ── Default password ─────────────────────────────────────────
    if not app_tables.app_config.get(key='save_password'):
        app_tables.app_config.add_row(key='save_password',
                                       value='Verathon123')

    return "✅  Seed data inserted successfully."
