# ==========================================================
# Nom du projet : Station de remplissage
# Fichier      : style.py
# Version      : 1.0.3
# Auteur       : Pommet-Gravier Quentin
# Date         : 2026-01-28
# Copyright    : © 2026 - Tous droits réservés
#
# Description  :
# Application graphique PyQt5 pour une station de
# remplissage avec scan QR, compteur global, compteur par QR,
# écran de remplissage animé, sauvegarde locale
# et panneau de debug caché.
# ==========================================================

def button_style():
    return """
    QPushButton {
        background-color: #00aa88;
        color: white;
        border-radius: 12px;
        padding: 10px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #008f72;
    }
    QPushButton:pressed {
        background-color: #006f59;
    }
    QPushButton:disabled {
        background-color: #9ad6c7;
        color: #eeeeee;
    }
    """

def scan_label_style():
    return """
    QLabel {
        border: 3px dashed #00aa88;
        border-radius: 15px;
        padding: 20px;
        background-color: #eafff9;
        font-weight: bold;
    }
    """

def debug_button_style():
    return """
    QPushButton {
        background-color: #222222;
        color: #00ff99;
        border: 1px solid #00ff99;
        border-radius: 6px;
        padding: 6px;
        font-size: 11px;
    }
    QPushButton:hover {
        background-color: #003322;
    }
    """