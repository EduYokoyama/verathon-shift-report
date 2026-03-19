# Verathon Daily Shift Report — Anvil Web App

A full web-based replacement for the Excel/VBA shift reporting system used at Southmedic Inc.
Tracks 10 machines (ASB-073, 179, 075, 231, 170, 258, 259, 260, MV1, MV2) across Day / Afternoon / Night shifts.

---

## ✅ Features (1-to-1 parity with original VBA)

| Feature | Status |
|---|---|
| 10 machine tabs | ✅ |
| WO1 / WO2 enable-disable | ✅ |
| Part number → auto-fill Geo/Mat/Manpower | ✅ |
| Planned cases calculation (rate × runtime) | ✅ |
| Actual hours calculation (runtime × manpower) | ✅ |
| Estimated hours calculation | ✅ |
| Attainment % with colour bar | ✅ |
| Efficiency % with colour bar | ✅ |
| Machine Availability % with colour bar | ✅ |
| Issue dropdowns → enable lost-time fields | ✅ |
| Save per machine | ✅ |
| Load per machine | ✅ |
| Load ALL machines at once | ✅ |
| Overwrite warning (same-day) | ✅ |
| Password protection (past dates) | ✅ |
| PDF shift report (colour-coded, per machine) | ✅ |
| Works in any browser / on any device | ✅ |

---

## 🚀 How to Deploy (Step-by-Step)

### Step 1 — Create an Anvil account

Go to **[anvil.works](https://anvil.works)** and sign up for a free account.

### Step 2 — Import this repository

1. In the Anvil editor, click **"New App"**
2. Choose **"Clone from GitHub"**
3. Paste this repository URL:
   ```
   https://github.com/YOUR_USERNAME/verathon-shift-report
   ```
4. Click **"Clone"** — Anvil will import all files automatically.

### Step 3 — Create the Data Tables

After cloning, click the **"Data"** tab in the left sidebar.
Create these 5 tables with the exact column names and types below:

#### Table: `shifts`
| Column | Type |
|---|---|
| shift_key | Text |
| month | Text |
| day | Text |
| year | Text |
| shift | Text |

#### Table: `machine_reports`
| Column | Type | Column | Type |
|---|---|---|---|
| shift | Link → shifts | machine_id | Text |
| run_total | Number | cases_total | Number |
| lost_total | Number | availability | Number |
| cot | Number | ot | Number |
| late_start | Number | early_leave | Number |
| wo1 | Text | run1 | Number |
| pn1 | Text | geo1 | Text |
| mat1 | Text | plan_cases1 | Number |
| act_cases1 | Number | issue_a | Text |
| lost_a | Number | issue_b | Text |
| lost_b | Number | attainment1 | Number |
| efficiency1 | Number | est_hr1 | Number |
| act_hr1 | Number | plan_mp1 | Number |
| act_mp1 | Number | wo2 | Text |
| run2 | Number | pn2 | Text |
| geo2 | Text | mat2 | Text |
| plan_cases2 | Number | act_cases2 | Number |
| issue_c | Text | lost_c | Number |
| issue_d | Text | lost_d | Number |
| attainment2 | Number | efficiency2 | Number |
| est_hr2 | Number | act_hr2 | Number |
| plan_mp2 | Number | act_mp2 | Number |
| next_wo | Text | next_pn | Text |
| next_geo | Text | next_mat | Text |
| tool_number | Text | tool_ready | True/False |
| labels_ready | True/False | kit_ready | True/False |

#### Table: `part_numbers`
| Column | Type |
|---|---|
| machine_id | Text |
| pn | Text |
| geometry | Text |
| material | Text |
| crew_size | Number |
| run_rate | Number |
| est_hrs | Number |

#### Table: `issues_list`
| Column | Type |
|---|---|
| machine_type | Text |
| issue_name | Text |

#### Table: `app_config`
| Column | Type |
|---|---|
| key | Text |
| value | Text |

### Step 4 — Seed the initial data (issues + password)

1. In the Anvil editor, open the **"⌘ Terminal"** or go to the **"Uplink"** section
2. Click on **"ListsService"** in the server modules list
3. At the top of the file, you'll see `seed_initial_data()`
4. In the Anvil editor, open the **Interactive Console** (bottom panel) and run:
   ```python
   import anvil.server
   print(anvil.server.call('seed_initial_data'))
   ```
   This will populate:
   - All 14 welder issues
   - All 8 multivac issues
   - The default save password (`Verathon123`)

   **You can change the password later** by editing the `save_password` row in the `app_config` table directly.

### Step 5 — Add your Part Numbers

In the `part_numbers` table, add rows for each machine's part numbers.
Each row needs:

| Field | Example |
|---|---|
| machine_id | `073` |
| pn | `LPS1` |
| geometry | `LPS` |
| material | `ABS` |
| crew_size | `4` |
| run_rate | `120` ← cases per hour |
| est_hrs | `0.008` ← hours per case |

**Machine IDs to use:** `073`, `179`, `075`, `231`, `170`, `258`, `259`, `260`, `MV1`, `MV2`

You can also import a CSV directly into the table using the Anvil Data tab → **"⬆ Upload CSV"**.

### Step 6 — Run the app

Click the **▶ Run** button in the top toolbar.  
Your app opens in a new browser tab — share the URL with your team!

---

## 🎨 Colour Legend (same as VBA original)

| Colour | Meaning |
|---|---|
| 🟢 Bright Green | ≥ 100% (target met or exceeded) |
| 🟢 Dark Green | ≥ 75% (good) |
| 🟡 Yellow | ≥ 30% (warning) |
| 🔵 Dark Blue | < 30% (critical) |

---

## 🔐 Password for Past-Date Edits

The default password is: **`Verathon123`**

To change it: go to the `app_config` table in the Anvil Data tab and edit the `save_password` row.

---

## 📄 PDF Report

The PDF report generates one page per machine with:
- Summary totals (run time, cases, lost time, availability)
- Timing breakdown (changeover, OT, late start, early leave)
- Full WO1 / WO2 detail with colour-coded attainment and efficiency
- Next shift planning section
- Tool / Labels / Kit readiness (green = YES, red = NO)

---

## 📁 File Structure

```
verathon-shift-report/
├── anvil.yaml                          ← Anvil app manifest
├── README.md                           ← This file
├── client_code/
│   └── Form1/
│       ├── __init__.py                 ← Main form logic (all 10 machines)
│       └── _anvil_designer.py          ← Header UI (date, shift, buttons)
└── server_code/
    ├── DatabaseService.py              ← Save / Load / Check operations
    ├── ListsService.py                 ← Part numbers, issues, seed data
    └── ReportService.py                ← PDF generation (ReportLab)
```

---

## 🆚 Improvements Over the VBA Version

| VBA | This App |
|---|---|
| Excel only, Windows only | Works in any browser on any device |
| Screenshot-based PDF (blurry) | Proper formatted PDF with coloured cells |
| 515-column flat database row | Normalised relational tables |
| Single user at a time | Multiple users simultaneously |
| Manual backup | Anvil handles data persistence automatically |
| No access control | Password-protected past-date edits |

---

## 🛠 Troubleshooting

**"No data found" when loading**  
→ Make sure you selected the correct date and shift before clicking Load.

**Part number dropdown is empty**  
→ Add rows to the `part_numbers` table for that machine_id.

**Issues dropdown is empty**  
→ Run `seed_initial_data()` from the server console (Step 4 above).

**PDF downloads but is blank**  
→ No data has been saved for that date/shift yet. Save each machine first.

**"Incorrect password" when editing past data**  
→ Default password is `Verathon123`. Check the `app_config` table.
