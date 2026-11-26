"""Riepilogo del caso: pochi numeri, una tabella dei file con i punti da verificare, dettagli a comparsa.

Ogni file del caso è una riga; sotto di essa (riga espandibile) ci sono i risultati che meritano attenzione, oppure
tutti i controlli eseguiti. Cliccando una riga si apre a destra il riquadro dei dettagli: cosa significa, cosa fare,
la vista collegata e i dati tecnici. Il riquadro si chiude con ✕ e non occupa spazio finché non serve.
"""
from __future__ import annotations

import html

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (QButtonGroup, QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton, QSplitter,
                               QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from ...core import explain
from ...core.findings import Level, Status
from ..theme import C, LEVEL_COLORS, STATUS_COLORS
from ..widgets.common import Page, fill_table, make_table
from ..widgets.findings_view import finding_html

ROLE = Qt.ItemDataRole.UserRole


class Stat(QWidget):
    def __init__(self, label: str):
        super().__init__()
        self.setObjectName("Stat")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(0)
        self.v = QLabel("0")
        self.v.setObjectName("StatValue")
        lab = QLabel(label)
        lab.setObjectName("Muted")
        lay.addWidget(self.v)
        lay.addWidget(lab)


class DashboardPage(Page):
    title = "Riepilogo"
    lead = "L'esito di ogni file del caso. Clicca una riga per vedere cosa significa e cosa fare."
    intro = ("L'esito di ogni file del caso. Ogni riga è un file: aprila per vedere i punti da verificare, oppure "
             "scegli «Tutti i controlli» per l'elenco completo. Cliccando una riga si apre a destra il riquadro dei "
             "dettagli, con la spiegazione in parole semplici, cosa conviene fare, il collegamento alla vista dove "
             "approfondire e i dati tecnici. I colori indicano dove guardare, non se un file è autentico: nessun "
             "risultato, da solo, dimostra che un file sia autentico o falsificato.")

    def __init__(self, state):
        super().__init__(state)
        self._index: dict[tuple[str, str], object] = {}
        self._quiet = False

        # numeri del caso
        kpi = QFrame()
        kpi.setObjectName("KpiBar")
        kl = QHBoxLayout(kpi)
        kl.setContentsMargins(0, 0, 0, 0)
        kl.setSpacing(0)
        self.s = {k: Stat(lbl) for k, lbl in (("files", "File analizzati"), ("red", "Richiedono attenzione"),
                                              ("yellow", "Da approfondire"), ("hidden", "Con contenuti nascosti"))}
        for w in self.s.values():
            kl.addWidget(w, 1)
        self.integrity = QLabel()
        self.integrity.setObjectName("KpiNote")
        self.integrity.setTextFormat(Qt.TextFormat.RichText)
        self.integrity.setWordWrap(True)
        kl.addWidget(self.integrity, 1)
        self.root.addWidget(kpi)

        # filtro
        bar = QHBoxLayout()
        bar.setSpacing(0)
        self.only = QPushButton("Da verificare")
        self.every = QPushButton("Tutti i controlli")
        grp = QButtonGroup(self)
        grp.setExclusive(True)
        for b in (self.only, self.every):
            b.setObjectName("Segment")
            b.setCheckable(True)
            grp.addButton(b)
            bar.addWidget(b)
        self.only.setChecked(True)
        self.only.toggled.connect(lambda _on: self.refresh())
        bar.addSpacing(16)
        self.count = QLabel()
        self.count.setObjectName("Muted")
        bar.addWidget(self.count)
        bar.addStretch(1)
        self.root.addLayout(bar)

        # tabella + riquadro dei dettagli
        self.split = QSplitter(Qt.Orientation.Horizontal)
        self.split.setChildrenCollapsible(False)
        self.split.setHandleWidth(10)
        self.split.setObjectName("DetailSplit")
        self.tree = QTreeWidget()
        self.tree.setObjectName("ResultsTree")
        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Esito", "File / risultato", "Area"])
        self.tree.setUniformRowHeights(True)
        self.tree.setIndentation(16)
        self.tree.setMinimumHeight(260)
        h = self.tree.header()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tree.itemSelectionChanged.connect(self._on_select)
        self.split.addWidget(self.tree)

        self.drawer = QFrame()
        self.drawer.setObjectName("Drawer")
        self.drawer.setMinimumWidth(380)
        dv = QVBoxLayout(self.drawer)
        dv.setContentsMargins(16, 10, 10, 14)
        head = QHBoxLayout()
        self.d_kicker = QLabel("Dettagli")
        self.d_kicker.setObjectName("Muted")
        head.addWidget(self.d_kicker)
        head.addStretch(1)
        close = QPushButton("✕")
        close.setObjectName("IconButton")
        close.setToolTip("Chiudi i dettagli")
        close.setAccessibleName("Chiudi i dettagli")
        close.clicked.connect(self.close_details)
        head.addWidget(close)
        dv.addLayout(head)
        self.detail = QTextBrowser()
        self.detail.setObjectName("DetailBody")
        self.detail.setOpenLinks(False)
        self.detail.setFrameShape(QFrame.Shape.NoFrame)
        dv.addWidget(self.detail, 1)
        self.open_btn = QPushButton("Apri la vista collegata")
        self.open_btn.setObjectName("Primary")
        self.open_btn.clicked.connect(self._open_current)
        dv.addWidget(self.open_btn, 0, Qt.AlignmentFlag.AlignLeft)
        self._target: tuple[str, str] | None = None
        self.split.addWidget(self.drawer)
        self.split.setStretchFactor(0, 3)
        self.split.setStretchFactor(1, 2)
        self.drawer.hide()
        self.root.addWidget(self.split, 1)

        # registro del caso, a richiesta
        self.log_btn = QPushButton("Registro del caso ▸")
        self.log_btn.setCheckable(True)
        self.log_btn.toggled.connect(self._toggle_log)
        self.root.addWidget(self.log_btn, 0, Qt.AlignmentFlag.AlignLeft)
        self.activity_box = QWidget()
        al = QVBoxLayout(self.activity_box)
        al.setContentsMargins(0, 0, 0, 0)
        self.activity = make_table(["Data e ora (UTC)", "Operatore", "Azione"])
        self.activity.setMaximumHeight(200)
        al.addWidget(self.activity)
        self.activity_box.hide()
        self.root.addWidget(self.activity_box)

        state.case_changed.connect(self.refresh)
        state.analysis_changed.connect(self.refresh)
        state.exhibit_changed.connect(self._exhibit_changed)

    # ---------------------------------------------------------------- comandi
    def apply_mode(self) -> None:
        self.refresh()

    def _toggle_log(self, on: bool) -> None:
        self.activity_box.setVisible(on)
        self.log_btn.setText("Registro del caso ▾" if on else "Registro del caso ▸")

    def close_details(self) -> None:
        self.tree.clearSelection()
        self.drawer.hide()

    def _open(self, page: str, art: str) -> None:
        self.state.show_map.emit(art or "")
        self.state.navigate.emit(page)

    def _open_current(self) -> None:
        if self._target:
            self._open(*self._target)

    def select_finding(self, finding_id: str, ex_id: str | None = None) -> None:
        """Seleziona un risultato nella tabella e ne apre i dettagli (passa a «Tutti i controlli» se serve)."""
        for attempt in (0, 1):
            if attempt:
                self.every.setChecked(True)
            for i in range(self.tree.topLevelItemCount()):
                top = self.tree.topLevelItem(i)
                if ex_id and top.data(0, ROLE)[1] != ex_id:
                    continue
                for j in range(top.childCount()):
                    it = top.child(j)
                    if it.data(0, ROLE)[2] == finding_id:
                        top.setExpanded(True)
                        self.tree.setCurrentItem(it)
                        self.tree.scrollToItem(it)
                        return

    # ---------------------------------------------------------------- dettagli
    def _on_select(self) -> None:
        items = self.tree.selectedItems()
        if not items:
            return
        key = items[0].data(0, ROLE)
        ex_id = key[1]
        if ex_id != self.state.exhibit_id:
            self._quiet = True                 # cambia il file attivo senza ricostruire la tabella
            self.state.set_exhibit(ex_id)
            self._quiet = False
        if key[0] == "f":
            f = self._index[(ex_id, key[2])]
            self.d_kicker.setText(self.state.case.exhibit(ex_id).original_name)
            self.detail.setHtml(finding_html(f, link=False))
            page = explain.related_page(f)
            self._target = (page, explain.related_map(f) or "") if page else None
        else:
            self.d_kicker.setText("File")
            self.detail.setHtml(self._exhibit_html(ex_id))
            self._target = None
        self.open_btn.setVisible(self._target is not None)
        self.drawer.show()

    def _exhibit_html(self, ex_id: str) -> str:
        e = html.escape
        case = self.state.case
        ex = case.exhibit(ex_id)
        an = case.analyses(ex_id)
        an = an[-1] if an else None
        ov = explain.overall(an)
        rows = "".join(
            f"<tr><td style='color:{STATUS_COLORS[st.value]}'>●</td><td>{e(explain.CATEGORY_LABELS[cat])}</td>"
            f"<td style='color:{C['muted']}'>{e(explain.STATUS_PLAIN[st].lower())}</td></tr>"
            for cat, st in explain.status_of(an).items() if st != Status.GREY)
        return (f"<h3 style='margin:0 0 4px 0'>{e(ex.original_name)}</h3>"
                f"<p style='margin:0 0 10px 0'><b style='color:{STATUS_COLORS[ov.value]}'>● "
                f"{e(explain.STATUS_PLAIN[ov]) if an else 'Non ancora analizzato'}</b></p>"
                f"<p>{e(explain.exhibit_summary(ex, an))}</p>"
                + (f"<p style='color:{C['muted']};margin:14px 0 2px 0'><b>Esito per area</b></p>"
                   f"<table cellpadding='3'>{rows}</table>" if rows else ""))

    def _exhibit_changed(self) -> None:
        if self._quiet:
            return
        ex_id = self.state.exhibit_id
        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            if top.data(0, ROLE)[1] == ex_id:
                top.setExpanded(True)
                self.tree.scrollToItem(top)
                return
        self.refresh()

    # ---------------------------------------------------------------- dati
    def refresh(self) -> None:
        case = self.state.case
        sel = self.tree.selectedItems()
        keep = sel[0].data(0, ROLE) if sel else None
        self.tree.blockSignals(True)
        self.tree.clear()
        self._index.clear()
        if not case:
            self.tree.blockSignals(False)
            self.drawer.hide()
            self.count.setText("Nessun caso aperto.")
            self.integrity.setText("")
            self.activity.setRowCount(0)
            for w in self.s.values():
                w.v.setText("0")
            return
        ent = case.audit.entries()[-30:][::-1]
        fill_table(self.activity, [[e["ts_utc"][:19].replace("T", " "), e["actor"], e["action"].replace("_", " ")]
                                   for e in ent], sortable=False)
        pairs = []
        for ex in case.exhibits():
            an = case.analyses(ex.id)
            pairs.append((ex, an[-1] if an else None))
        cs = explain.case_summary(pairs)
        self.s["files"].v.setText(str(cs["analysed"]))
        self.s["red"].v.setText(str(cs["red"]))
        self.s["yellow"].v.setText(str(cs["attention_files"] - cs["red"]))
        self.s["hidden"].v.setText(str(cs["hidden_files"]))
        self.integrity.setText(
            f"<span style='color:{C['green']}'>●</span> Impronte hash invariate in tutti i file" if cs["integrity_ok"]
            else f"<span style='color:{C['red']}'>●</span> <b>Alcuni file sono cambiati durante l'analisi</b>")

        only = self.only.isChecked()
        hide_info = self.state.settings.ui_mode == "Basic"
        bold = QFont(self.tree.font())
        bold.setBold(True)
        n_rows = n_att = 0
        to_select = None
        for ex, an in pairs:
            ov = explain.overall(an)
            findings = an["findings"] if an else []
            att = explain.attention(findings)
            shown = att if only else sorted(
                [f for f in findings if not (hide_info and f.level == Level.INFO)],
                key=lambda f: (not explain.needs_attention(f), explain.SEVERITY[f.level]))
            top = QTreeWidgetItem([f"●  {explain.STATUS_PLAIN[ov] if an else 'Non analizzato'}", ex.original_name,
                                   (f"{len(att)} da verificare" if att else explain.kind_of(an) if an else "")])
            top.setForeground(0, QColor(STATUS_COLORS[ov.value]))
            top.setFont(1, bold)
            top.setToolTip(1, explain.exhibit_summary(ex, an))
            top.setData(0, ROLE, ("ex", ex.id, ""))
            for f in shown:
                self._index[(ex.id, f.id)] = f
                ch = QTreeWidgetItem([explain.LEVEL_PLAIN[f.level], f.title, explain.CATEGORY_LABELS[f.category]])
                ch.setForeground(0, QColor(LEVEL_COLORS[f.level.value]))
                ch.setToolTip(1, explain.plain_explanation(f))
                ch.setData(0, ROLE, ("f", ex.id, f.id))
                top.addChild(ch)
                if keep == ("f", ex.id, f.id):
                    to_select = ch
            self.tree.addTopLevelItem(top)
            top.setExpanded(ex.id == self.state.exhibit_id or (only and bool(att) and len(pairs) <= 3))
            if keep == ("ex", ex.id, ""):
                to_select = top
            n_rows += len(shown)
            n_att += len(att)
        self.tree.blockSignals(False)
        self.count.setText(f"{len(pairs)} file · {n_att} punti da verificare" if only else
                           f"{len(pairs)} file · {n_rows} controlli")
        if to_select is not None:
            if to_select.parent():
                to_select.parent().setExpanded(True)
            self.tree.setCurrentItem(to_select)
        else:
            self.drawer.hide()
