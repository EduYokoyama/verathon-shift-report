from anvil import *


class Form1Template(anvil.Component):
    """
    Auto-generated designer template for Form1.
    All widgets added here are accessible via  self.<name>  in Form1.
    """

    def __init__(self, **properties):
        # ── Header Panel ─────────────────────────────────────────
        self._root = ColumnPanel(background='#001166', spacing_above='none')

        # Title
        title = Label(
            text='Verathon Daily Shift Report',
            font_size=20, bold=True,
            foreground='white',
            align='center',
            spacing_above='small', spacing_below='small'
        )
        self._root.add_component(title)

        # Date row
        date_row = FlowPanel(spacing_above='none', spacing_below='none')
        date_row.add_component(Label(text='Month:', foreground='white', bold=True))
        self.tb_month = TextBox(placeholder='mm', width=50,
                                spacing_above='none', spacing_below='none')
        date_row.add_component(self.tb_month)
        date_row.add_component(Label(text=' / Day:', foreground='white', bold=True))
        self.tb_day = TextBox(placeholder='dd', width=50,
                              spacing_above='none', spacing_below='none')
        date_row.add_component(self.tb_day)
        date_row.add_component(Label(text=' / Year:', foreground='white', bold=True))
        self.tb_year = TextBox(placeholder='yyyy', width=70,
                               spacing_above='none', spacing_below='none')
        date_row.add_component(self.tb_year)
        self._root.add_component(date_row)

        # Shift radio buttons
        shift_row = FlowPanel(spacing_above='none', spacing_below='none')
        self.rb_night     = RadioButton(text='🌙 Night',     group_name='shift',
                                        foreground='white', bold=True)
        self.rb_day       = RadioButton(text='☀ Day',        group_name='shift',
                                        foreground='white', bold=True)
        self.rb_afternoon = RadioButton(text='🌆 Afternoon', group_name='shift',
                                        foreground='white', bold=True)
        for rb in (self.rb_night, self.rb_day, self.rb_afternoon):
            shift_row.add_component(rb)
            shift_row.add_component(Label(text='  ', foreground='white'))
        self._root.add_component(shift_row)

        # Action buttons
        btn_row = FlowPanel(spacing_above='small', spacing_below='small')
        self.btn_load_all = Button(
            text='📂 LOAD ALL MACHINES',
            background='#336699', foreground='white', bold=True
        )
        self.btn_pdf = Button(
            text='📄 PDF REPORT',
            background='#006600', foreground='white', bold=True
        )
        btn_row.add_component(self.btn_load_all)
        btn_row.add_component(Label(text='   '))
        btn_row.add_component(self.btn_pdf)
        self._root.add_component(btn_row)

        # Tab panel  (machine tabs are added dynamically in Form1.__init__)
        self.tab_panel = TabPanel(spacing_above='none')
        self._root.add_component(self.tab_panel)

        # Southmedic footer
        footer = Label(
            text='Southmedic Inc. — Verathon Shift Report System',
            foreground='#AACCFF', font_size=9, align='center',
            spacing_above='small', spacing_below='small'
        )
        self._root.add_component(footer)

        # Wire header button events
        self.btn_load_all.set_event_handler('click', self.btn_load_all_click)
        self.btn_pdf.set_event_handler('click',      self.btn_pdf_click)

        # Expose root so Anvil knows what to render
        self.add_component(self._root)

    # ── Stub event handlers (overridden in Form1) ─────────────────
    def btn_load_all_click(self, **event_args): pass
    def btn_pdf_click(self, **event_args):      pass
