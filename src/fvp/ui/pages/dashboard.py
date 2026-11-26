"""Risultati del caso, pensati per chi non è del mestiere.

A sinistra l'elenco dei file, ciascuno con una sola frase di esito. A destra, per il file scelto, i punti da
controllare scritti in parole semplici; cliccandone uno si apre la sua scheda (cosa significa, cosa fare, vista
collegata) con i dati tecnici nascosti dietro un pulsante. Nessuna tabella annidata, nessun numero superfluo.
"""
from __future__ import annotations

import html

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QCheckBox, QFrame, QHBoxLayout, QHeaderView, QLabel, QPushButton, QSplitter,
                               QStackedWidget, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from ...core import explain
from ...core.findings import Level, Status
from ..theme import C, LEVEL_COLORS, STATUS_COLORS
from ..widgets.common import Page
from ..widgets.findings_view import finding_html

ROLE = Qt.ItemDataRole.UserRole


def dot_icon(color: str, size: int = 10) -> QIcon:
    pm = QPixmap(size, size)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(color))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawEllipse(0, 0, size, size)
    p.end()
    return QIcon(pm)


def file_verdict(an: dict | None) -> tuple[str, str]:
    """Una frase di esito per il file e il colore corrispondente."""
    if not an:
        return "Non ancora analizzato", C["grey"]
    att = explain.attention(an["findings"])
    if att:
        n = len(att)
        return f"{n} {'punto' if n == 1 else 'punti'} da controllare", STATUS_COLORS[explain.overall(an).value]
    return "Nessun problema trovato", STATUS_COLORS[Status.GREEN.value]


def _browser(name: str) -> QTextBrowser:
    b = QTextBrowser()
    b.setObjectName(name)
    b.setOpenLinks(False)
    b.setFrameShape(QFrame.Shape.NoFrame)
    b.document().setDocumentMargin(0)
    return b


class DashboardPage(Page):
    title = "Risultati"
    lead = "Scegli un file a sinistra: a destra trovi cosa c'è da controllare, spiegato in parole semplici."
    intro = ("A sinistra ci sono i file del caso con una frase di esito: verde se i controlli non hanno trovato nulla, "
             "giallo o rosso se c'è qualcosa da controllare. A destra, per il file scelto, l'elenco dei punti da "
             "controllare; cliccandone uno si apre la sua scheda con cosa significa, cosa conviene fare e il "
             "collegamento alla pagina dove approfondire. I dati tecnici sono dietro il pulsante «Dati tecnici». "
             "I colori indicano dove guardare, non se un file è autentico: nessun risultato, da solo, dimostra che un "
             "file sia autentico o falsificato.")

    def __init__(self, state):
        super().__init__(state)
        self._index: dict[tuple[str, str], object] = {}
        self._quiet = False
        self._cur_finding = None
        self._tech = False

        self.summary = QLabel()
        self.summary.setObjectName("ResultSummary")
        self.summary.setTextFormat(Qt.TextFormat.RichText)
        self.summary.setWordWrap(True)
        self.root.addWidget(self.summary)

        split = QSplitter(Qt.Orientation.Horizontal)
        split.setObjectName("DetailSplit")
        split.setChildrenCollapsible(False)
        split.setHandleWidth(14)

        # elenco dei file
        self.files = QTreeWidget()
        self.files.setObjectName("FileList")
        self.files.setColumnCount(2)
        self.files.setHeaderLabels(["File", "Esito"])
        self.files.setRootIsDecorated(False)
        self.files.setUniformRowHeights(True)
        self.files.setIconSize(QSize(10, 10))
        self.files.setMinimumWidth(340)
        h = self.files.header()
        h.setStretchLastSection(False)
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.files.itemSelectionChanged.connect(self._file_selected)
        split.addWidget(self.files)

        # pannello del file: elenco dei punti, poi la scheda del punto scelto
        panel = QFrame()
        panel.setObjectName("Drawer")
        pv = QVBoxLayout(panel)
        pv.setContentsMargins(20, 16, 16, 16)
        self.stack = QStackedWidget()
        pv.addWidget(self.stack)

        self.empty = QLabel("Scegli un file nell'elenco a sinistra.")
        self.empty.setObjectName("Muted")
        self.empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(self.empty)

        fw = QWidget()
        fl = QVBoxLayout(fw)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(4)
        self.f_name = QLabel()
        self.f_name.setObjectName("FileTitle")
        self.f_name.setWordWrap(True)
        self.f_verdict = QLabel()
        self.f_verdict.setTextFormat(Qt.TextFormat.RichText)
        fl.addWidget(self.f_name)
        fl.addWidget(self.f_verdict)
        fl.addSpacing(14)
        self.points = _browser("Points")
        self.points.anchorClicked.connect(lambda url: self.show_finding(url.toString().split(":", 1)[1]))
        fl.addWidget(self.points, 1)
        self.show_all = QCheckBox("Mostra anche i controlli che non hanno trovato nulla")
        self.show_all.toggled.connect(lambda _on: self._render_points())
        fl.addWidget(self.show_all)
        self.stack.addWidget(fw)

        dw = QWidget()
        dl = QVBoxLayout(dw)
        dl.setContentsMargins(0, 0, 0, 0)
        self.back_btn = QPushButton("‹  Tutti i punti di questo file")
        self.back_btn.setObjectName("LinkButton")
        self.back_btn.clicked.connect(self.back)
        dl.addWidget(self.back_btn, 0, Qt.AlignmentFlag.AlignLeft)
        self.detail = _browser("DetailBody")
        dl.addWidget(self.detail, 1)
        row = QHBoxLayout()
        self.open_btn = QPushButton("Apri la pagina per approfondire")
        self.open_btn.setObjectName("Primary")
        self.open_btn.clicked.connect(self._open_current)
        self.tech_btn = QPushButton("Dati tecnici ▸")
        self.tech_btn.setCheckable(True)
        self.tech_btn.toggled.connect(self._toggle_tech)
        row.addWidget(self.open_btn)
        row.addWidget(self.tech_btn)
        row.addStretch(1)
        dl.addLayout(row)
        self.stack.addWidget(dw)

        split.addWidget(panel)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)
        split.setSizes([420, 640])
        self.root.addWidget(split, 1)

        state.case_changed.connect(self.refresh)
        state.analysis_changed.connect(self.refresh)
        state.exhibit_changed.connect(self._exhibit_changed)

    # ---------------------------------------------------------------- navigazione interna
    def apply_mode(self) -> None:
        self.refresh()

    def _open(self, page: str, art: str) -> None:
        self.state.show_map.emit(art or "")
        self.state.navigate.emit(page)

    def _open_current(self) -> None:
        f = self._cur_finding
        if f is not None and explain.related_page(f):
            self._open(explain.related_page(f), explain.related_map(f) or "")

    def back(self) -> None:
        self._cur_finding = None
        self.stack.setCurrentIndex(1 if self.state.exhibit_id else 0)

    def _toggle_tech(self, on: bool) -> None:
        self._tech = on
        self.tech_btn.setText("Dati tecnici ▾" if on else "Dati tecnici ▸")
        if self._cur_finding is not None:
            self.detail.setHtml(self._finding_page(self._cur_finding))

    def select_finding(self, finding_id: str, ex_id: str | None = None) -> None:
        """Apre la scheda di un risultato (sceglie prima il file, se indicato)."""
        if ex_id:
            self._select_file(ex_id)
        self.show_finding(finding_id)

    def show_finding(self, finding_id: str) -> None:
        f = self._index.get((self.state.exhibit_id or "", finding_id))
        if f is None:
            return
        self._cur_finding = f
        self.tech_btn.setChecked(False)
        self._tech = False
        self.detail.setHtml(self._finding_page(f))
        self.open_btn.setVisible(bool(explain.related_page(f)))
        self.stack.setCurrentIndex(2)

    def _finding_page(self, f) -> str:
        full = finding_html(f, link=False)
        if self._tech:
            return full
        cut = full.find("<p style='color:" + C["muted"] + ";margin:16px 0 6px 0'><b>Dati tecnici</b>")
        return full[:cut] if cut > 0 else full

    # ---------------------------------------------------------------- file
    def _select_file(self, ex_id: str) -> None:
        for i in range(self.files.topLevelItemCount()):
            it = self.files.topLevelItem(i)
            if it.data(0, ROLE) == ex_id:
                self.files.setCurrentItem(it)
                return

    def _file_selected(self) -> None:
        items = self.files.selectedItems()
        if not items:
            return
        ex_id = items[0].data(0, ROLE)
        if ex_id != self.state.exhibit_id:
            self._quiet = True
            self.state.set_exhibit(ex_id)
            self._quiet = False
        self._cur_finding = None
        self._render_points()
        self.stack.setCurrentIndex(1)

    def _exhibit_changed(self) -> None:
        if not self._quiet:
            self._select_file(self.state.exhibit_id or "")

    def _render_points(self) -> None:
        e = html.escape
        case, ex_id = self.state.case, self.state.exhibit_id
        if not (case and ex_id):
            return
        ex = case.exhibit(ex_id)
        an = case.analyses(ex_id)
        an = an[-1] if an else None
        verdict, color = file_verdict(an)
        findings = an["findings"] if an else []
        att = explain.attention(findings)
        self.f_name.setText(ex.original_name)
        self.f_verdict.setText(f"<span style='color:{color}'>●</span>&nbsp; <b>{e(verdict)}</b>")
        out = []
        if not an:
            out.append(f"<p style='color:{C['muted']}'>Avvia l'analisi da «Aggiungi i file».</p>")
        elif not att:
            out.append(f"<p>I controlli eseguiti su questo file non hanno trovato nulla da segnalare. "
                       f"<span style='color:{C['muted']}'>Non è una prova di autenticità: significa solo che "
                       f"nessun controllo ha dato un esito anomalo.</span></p>")
        for n, f in enumerate(att, 1):
            out.append(self._point_html(n, f))
        if self.show_all.isChecked() and an:
            shown = {f.id for f in att}
            basic = self.state.settings.ui_mode == "Basic"          # Basic: niente risultati solo informativi
            rest = [f for f in findings if f.id not in shown and not (basic and f.level == Level.INFO)]
            if rest:
                out.append(f"<p style='color:{C['muted']};margin-top:18px;margin-bottom:8px'><b>Altri controlli</b></p>")
                for f in sorted(rest, key=lambda x: explain.SEVERITY[x.level]):
                    out.append(f"<p style='margin-top:0;margin-bottom:6px'><a href='f:{e(f.id)}' style='text-decoration:none;"
                               f"color:{C['text']}'>{e(f.title)}</a> <span style='color:{C['muted']}'>· "
                               f"{e(explain.LEVEL_PLAIN[f.level].lower())}</span></p>")
        self.points.setHtml("".join(out))

    def _point_html(self, n: int, f) -> str:
        e = html.escape
        col = LEVEL_COLORS[f.level.value]
        return (f"<table width='100%' cellspacing='0' cellpadding='0' style='margin-bottom:18px'><tr>"
                f"<td width='28' valign='top' style='color:{C['muted']};font-weight:600'>{n}</td><td>"
                f"<a href='f:{e(f.id)}' style='text-decoration:none;color:{C['text']};font-weight:600'>"
                f"{e(f.title)}&nbsp;›</a>"
                f"<p style='margin-top:3px;margin-bottom:3px;color:{C['muted']}'>{e(explain.plain_explanation(f))}</p>"
                f"<span style='color:{col};font-size:9pt'>{e(explain.LEVEL_PLAIN[f.level])}</span>"
                f"<span style='color:{C['muted']};font-size:9pt'> · {e(explain.CATEGORY_LABELS[f.category])}</span>"
                f"</td></tr></table>")

    # ---------------------------------------------------------------- dati
    def refresh(self) -> None:
        case = self.state.case
        self.files.blockSignals(True)
        self.files.clear()
        self._index.clear()
        if not case:
            self.files.blockSignals(False)
            self.summary.setText("")
            self.stack.setCurrentIndex(0)
            return
        pairs = []
        for ex in case.exhibits():
            an = case.analyses(ex.id)
            pairs.append((ex, an[-1] if an else None))
        cs = explain.case_summary(pairs)
        bold = QFont(self.files.font())
        bold.setBold(True)
        for ex, an in pairs:
            verdict, color = file_verdict(an)
            it = QTreeWidgetItem([ex.original_name, verdict])
            it.setIcon(0, dot_icon(color))
            it.setForeground(1, QColor(color))
            it.setData(0, ROLE, ex.id)
            if an and explain.attention(an["findings"]):
                it.setFont(0, bold)
            self.files.addTopLevelItem(it)
            for f in (an["findings"] if an else []):
                self._index[(ex.id, f.id)] = f
        self.files.blockSignals(False)

        n_att = sum(1 for _e, a in pairs if a and explain.attention(a["findings"]))
        n_an = cs["analysed"]
        if not pairs:
            text = "Nessun file nel caso: aggiungili da «Aggiungi i file»."
        elif n_att:
            text = (f"<b>{n_att} file su {n_an}</b> hanno qualcosa da controllare."
                    + (f" In {cs['hidden_files']} è stato trovato un contenuto nascosto." if cs["hidden_files"] else ""))
        else:
            text = f"<b>Nessun problema trovato</b> nei {n_an} file analizzati."
        hashes = ("<span style='color:{0}'>●</span> I file non sono stati alterati dall'analisi."
                  .format(C["green"]) if cs["integrity_ok"] else
                  "<span style='color:{0}'>●</span> <b>Attenzione: alcuni file risultano cambiati durante "
                  "l'analisi.</b>".format(C["red"]))
        self.summary.setText(f"{text}&nbsp;&nbsp;&nbsp;<span style='color:{C['muted']}'>{hashes}</span>")

        # file da mostrare: quello attivo, altrimenti il primo con qualcosa da controllare
        cur = self.state.exhibit_id
        if not any(ex.id == cur for ex, _a in pairs):
            cur = next((ex.id for ex, a in pairs if a and explain.attention(a["findings"])),
                       pairs[0][0].id if pairs else None)
        keep = self._cur_finding.id if self._cur_finding is not None else None
        if cur:
            self._select_file(cur)
            if keep and (cur, keep) in self._index:
                self.show_finding(keep)
        else:
            self.stack.setCurrentIndex(0)
