# ==========================================================
# Nom du projet : Station de remplissage
# Fichier      : logger.py
# Version      : 1.0.2
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
import os
from datetime import datetime

# Dossier du projet
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

# Crée le dossier logs s'il n'existe pas
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log(action, details=""):
    """
    Écrit une ligne de log dans un fichier journalier.
    """
    date_str = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")

    log_file = os.path.join(LOG_DIR, f"{date_str}.log")

    line = f"[{time_str}] {action}"
    if details:
        line += f" | {details}"
    line += "\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(line)

    print("LOG:", line.strip())  # visible dans le terminal
