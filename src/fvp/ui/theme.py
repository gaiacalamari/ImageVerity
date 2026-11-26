"""Temi chiaro (predefinito) e scuro.

I dizionari C, LEVEL_COLORS e STATUS_COLORS vengono aggiornati sul posto quando si cambia tema, così i
widget che li leggono al momento del disegno o dell'aggiornamento seguono il tema senza essere ricreati.
I colori di stato sono riservati ai risultati e scelti per un contrasto sufficiente su entrambi gli sfondi.
"""
from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette

# Stile "workspace": neutri caldi, bordi sottili, angoli quasi vivi, un solo colore d'azione (quasi nero in chiaro,
# quasi bianco in scuro). I colori di stato restano riservati ai risultati.
LIGHT = {
    "base": "#fafaf9", "panel": "#ffffff", "panel2": "#f3f3f1", "rule": "#e2e2de", "rule_strong": "#c9c9c3",
    "text": "#18181b", "muted": "#5f5f66", "accent": "#18181b", "accent_hover": "#2e2e33", "accent_fg": "#fafaf9",
    "accent_soft": "#f0f0ee", "select": "#e6e6e2", "sidebar": "#f3f3f1", "zero": "#a1a1aa",
    "green": "#2e7d4f", "yellow": "#a87a05", "red": "#bd3a2e", "grey": "#7a7a82", "orange": "#c0620f",
    "blue": "#2f69ad",
}
DARK = {
    "base": "#141416", "panel": "#1a1a1d", "panel2": "#212125", "rule": "#2e2e33", "rule_strong": "#45454c",
    "text": "#e7e7ea", "muted": "#a0a0a8", "accent": "#e7e7ea", "accent_hover": "#ffffff", "accent_fg": "#141416",
    "accent_soft": "#232327", "select": "#2f2f36", "sidebar": "#18181b", "zero": "#5c5c64",
    "green": "#4f9d69", "yellow": "#d1aa3a", "red": "#cf5246", "grey": "#7c7c85", "orange": "#d9822b",
    "blue": "#5b8fd0",
}
C: dict[str, str] = dict(LIGHT)
LEVEL_COLORS: dict[str, str] = {}
STATUS_COLORS: dict[str, str] = {}
CURRENT = {"mode": "light"}


def _derive() -> None:
    LEVEL_COLORS.update({"evidenza_certa": C["red"], "anomalia_tecnica": C["orange"],
                         "indicatore_sospetto": C["yellow"], "risultato_probabilistico": C["blue"],
                         "non_determinabile": C["grey"], "informativo": C["muted"]})
    STATUS_COLORS.update({"verde": C["green"], "giallo": C["yellow"], "rosso": C["red"], "grigio": C["grey"]})


_derive()


def set_mode(mode: str) -> None:
    CURRENT["mode"] = "dark" if mode == "dark" else "light"
    C.clear()
    C.update(DARK if CURRENT["mode"] == "dark" else LIGHT)
    _derive()


def span(color_key: str, text: str, bold: bool = False) -> str:
    t = f"<b>{text}</b>" if bold else text
    return f"<span style='color:{C[color_key]}'>{t}</span>"


def mono_font(size: int = 10) -> QFont:
    for fam in ("JetBrains Mono", "Cascadia Mono", "Consolas", "DejaVu Sans Mono", "Menlo"):
        if fam in QFontDatabase.families():
            f = QFont(fam, size)
            break
    else:
        f = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        f.setPointSize(size)
    f.setStyleHint(QFont.StyleHint.Monospace)
    return f


UI_FAMILIES = ("Geist", "Segoe UI Variable Text", "Segoe UI", "SF Pro Text", "Helvetica Neue", "Noto Sans",
               "DejaVu Sans")


def ui_font(size: int = 10) -> QFont:
    """Carattere dell'interfaccia: il primo disponibile tra quelli sobri e leggibili, altrimenti quello di sistema."""
    fams = set(QFontDatabase.families())
    for fam in UI_FAMILIES:
        if fam in fams:
            return QFont(fam, size)
    f = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    f.setPointSize(size)
    return f


def palette() -> QPalette:
    p = QPalette()
    for role, key in ((QPalette.ColorRole.Window, "base"), (QPalette.ColorRole.WindowText, "text"),
                      (QPalette.ColorRole.Base, "panel"), (QPalette.ColorRole.AlternateBase, "panel2"),
                      (QPalette.ColorRole.Text, "text"), (QPalette.ColorRole.Button, "panel2"),
                      (QPalette.ColorRole.ButtonText, "text"), (QPalette.ColorRole.Highlight, "select"),
                      (QPalette.ColorRole.HighlightedText, "text"), (QPalette.ColorRole.ToolTipBase, "panel"),
                      (QPalette.ColorRole.ToolTipText, "text"), (QPalette.ColorRole.PlaceholderText, "muted")):
        p.setColor(role, QColor(C[key]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(C["grey"]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(C["grey"]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(C["grey"]))
    return p


def qss() -> str:
    c = C
    return f"""
QWidget {{ color:{c['text']}; font-size:10pt; }}
QMainWindow, QStackedWidget > QWidget {{ background:{c['base']}; }}
#Sidebar {{ background:{c['sidebar']}; border:none; border-right:1px solid {c['rule']}; outline:0; padding:6px 0; }}
#Sidebar::item {{ padding:7px 10px; margin:1px 8px; border:1px solid transparent; border-radius:3px; }}
#Sidebar::item:selected {{ background:{c['panel']}; border:1px solid {c['rule']}; color:{c['text']}; }}
#Sidebar::item:hover:!selected:enabled {{ background:{c['select']}; }}
#Sidebar::item:disabled {{ color:{c['muted']}; }}
#Brand {{ background:{c['sidebar']}; border-right:1px solid {c['rule']}; border-bottom:1px solid {c['rule']}; }}
#BrandMark {{ background:{c['accent']}; color:{c['accent_fg']}; font-weight:600; font-size:9pt; }}
#BrandName {{ font-size:11pt; font-weight:600; }}
#ContextBar {{ background:{c['base']}; border-bottom:1px solid {c['rule']}; }}
#PageTitle {{ font-size:16pt; font-weight:600; }}
#PageIntro, #Muted {{ color:{c['muted']}; }}
#Strict {{ color:{c['green']}; border:1px solid {c['green']}; border-radius:2px; padding:1px 6px; }}
#StrictOff {{ color:{c['yellow']}; border:1px solid {c['yellow']}; border-radius:2px; padding:1px 6px; }}
#Stat {{ background:{c['panel']}; border:1px solid {c['rule']}; border-radius:3px; }}
#StatValue {{ font-size:20pt; font-weight:600; }}
#NotImpl {{ background:{c['panel']}; border:1px dashed {c['rule_strong']}; border-radius:3px; padding:12px; color:{c['muted']}; }}
QScrollArea#PageScroll, QWidget#PageViewport, QWidget#PageViewport > QWidget {{ background:{c['base']}; border:none; }}
#HelpBox {{ background:{c['panel2']}; border:1px solid {c['rule']}; border-radius:3px; padding:10px 12px; }}
#HelpButton {{ padding:4px 10px; }}
#ModeButton {{ padding:4px 12px; font-weight:600; }}
#Lead {{ font-size:11pt; }}
#BigDrop {{ border:1px dashed {c['rule_strong']}; border-radius:3px; padding:28px; font-size:12pt; color:{c['text']}; background:{c['panel']}; }}
#Notice {{ background:{c['panel']}; border:1px solid {c['rule']}; border-radius:3px; padding:10px 12px; }}
#DropZone {{ background:{c['panel']}; border:1px dashed {c['rule_strong']}; border-radius:3px; padding:18px; color:{c['muted']}; }}
#ImageView {{ background:{c['panel']}; border:1px solid {c['rule']}; }}
QGroupBox {{ border:1px solid {c['rule']}; border-radius:3px; margin-top:16px; padding-top:8px; background:{c['panel']}; }}
QGroupBox::title {{ subcontrol-origin:margin; left:8px; padding:0 4px; color:{c['muted']}; }}
QPushButton {{ background:{c['panel']}; border:1px solid {c['rule_strong']}; border-radius:3px; padding:5px 12px; }}
QPushButton:hover {{ background:{c['panel2']}; }}
QPushButton:pressed, QPushButton:checked {{ background:{c['select']}; }}
QPushButton:disabled {{ color:{c['grey']}; background:{c['base']}; border-color:{c['rule']}; }}
QPushButton#Primary {{ background:{c['accent']}; border-color:{c['accent']}; color:{c['accent_fg']}; font-weight:600; }}
QPushButton#Primary:hover {{ background:{c['accent_hover']}; border-color:{c['accent_hover']}; }}
QPushButton#Primary:disabled {{ background:{c['panel2']}; border-color:{c['rule']}; color:{c['grey']}; }}
QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {{ background:{c['panel']}; border:1px solid {c['rule_strong']};
  border-radius:3px; padding:4px 6px; selection-background-color:{c['select']}; selection-color:{c['text']}; }}
QComboBox:disabled {{ color:{c['muted']}; }}
QLineEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QComboBox:focus {{ border-color:{c['accent']}; }}
QComboBox QAbstractItemView {{ background:{c['panel']}; border:1px solid {c['rule']}; selection-background-color:{c['select']}; }}
QTableView, QTreeView, QListView, QTextBrowser {{ background:{c['panel']}; border:1px solid {c['rule']}; border-radius:0;
  gridline-color:{c['rule']}; selection-background-color:{c['select']}; selection-color:{c['text']};
  alternate-background-color:{c['base']}; }}
QHeaderView::section {{ background:{c['panel']}; border:none; border-bottom:1px solid {c['rule']}; padding:6px 8px;
  color:{c['muted']}; font-weight:500; }}
QTabWidget::pane {{ border:none; border-top:1px solid {c['rule']}; background:{c['base']}; }}
QTabBar::tab {{ background:transparent; color:{c['muted']}; padding:7px 2px; margin-right:18px; border:none;
  border-bottom:2px solid transparent; }}
QTabBar::tab:selected {{ color:{c['text']}; border-bottom:2px solid {c['accent']}; }}
QTabBar::tab:hover:!selected {{ color:{c['text']}; }}
QProgressBar {{ background:{c['panel2']}; border:1px solid {c['rule']}; border-radius:2px; text-align:center; height:12px; }}
QProgressBar::chunk {{ background:{c['accent']}; }}
QSplitter::handle {{ background:{c['rule']}; }}
QScrollBar:vertical {{ background:transparent; width:9px; }} QScrollBar:horizontal {{ background:transparent; height:9px; }}
QScrollBar::handle {{ background:{c['rule_strong']}; border-radius:2px; min-height:24px; min-width:24px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width:0; height:0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background:transparent; }}
QToolTip {{ background:{c['panel']}; color:{c['text']}; border:1px solid {c['rule_strong']}; padding:4px 6px; }}
QStatusBar {{ background:{c['sidebar']}; border-top:1px solid {c['rule']}; color:{c['muted']}; }}
QCheckBox::indicator {{ width:14px; height:14px; }}
"""


def apply(app, mode: str) -> None:
    set_mode(mode)
    app.setFont(ui_font())
    app.setPalette(palette())
    app.setStyleSheet(qss())


def icon_path():
    """Icona del programma: accanto al pacchetto (sorgenti) o nella cartella dell'eseguibile (PyInstaller)."""
    import sys
    from pathlib import Path
    for base in (Path(__file__).parent, Path(getattr(sys, "_MEIPASS", "")) / "fvp" / "ui"):
        p = base / "assets" / "fvp.ico"
        if p.is_file():
            return p
    return None


def app_icon():
    from PySide6.QtGui import QIcon
    p = icon_path()
    return QIcon(str(p)) if p else QIcon()
