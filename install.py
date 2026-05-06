#!/usr/bin/env python3
# ==========================================================
# install.py
# Script d'installation automatique des dépendances
# Compatible Windows / Linux
# Fait par POMMET-GRAVIER Quentin
# Version 1.0.3
# ==========================================================

import os
import sys
import subprocess
import platform

def run(cmd):
    print("\n▶", " ".join(cmd))
    subprocess.check_call(cmd)

def main():
    print("======================================")
    print(" Installation des dépendances - Station de remplissage ")
    print("======================================\n")

    print("Système détecté :", platform.system())
    print("Python :", sys.version)

    try:
        run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except:
        print("⚠ Impossible de mettre pip à jour")

    try:
        run([sys.executable, "-m", "pip", "install", "PyQt5"])
        run([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
    except Exception as e:
        print("❌ Erreur installation dépendances :", e)
        return

    try:
        run([sys.executable, "-c", "import mysql.connector; print('MySQL connector OK')"])
        run([sys.executable, "-c", "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"])
    except Exception as e:
        print("❌ Erreur test modules :", e)
        return

    print("\n✅ Installation terminée")
    print("   Lancez : python main.py\n")

if __name__ == "__main__":
    main()
