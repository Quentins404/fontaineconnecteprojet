# ==========================================================
# Nom du projet : Station de remplissage
# Fichier      : main.py
# Version      : 1.7.0
# Auteur       : Pommet-Gravier Quentin
# Date         : 2026-01-28
# ==========================================================

import sys
import os
import re
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QFont, QMovie
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QSoundEffect

from style import button_style, scan_label_style, debug_button_style
from logger import log
from mysql_manager import MySQLManager
from logins import MYSQL_USER, MYSQL_PASSWORD

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(BASE_DIR, "assets")


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Station de remplissage")
        self.setFixedSize(1200, 800)

        try:
            self.db = MySQLManager()
            log("MYSQL", "Connexion OK")
        except Exception as e:
            self.db = None
            log("MYSQL", f"ERREUR connexion : {e}")
            QMessageBox.critical(self, "Erreur BDD", f"Impossible de se connecter à la base : {e}")

        self.last_qr = None
        self.debug_authenticated = False
        self.debug_visible = False
        self.debug_counter = 0
        self.debug_login_attempts = 0
        self.closing = False
        self.filling_active = False

        self.qr_buffer = ""
        self.qr_timer = QTimer()
        self.qr_timer.setSingleShot(True)
        self.qr_timer.timeout.connect(self.process_qr_buffer)

        self.start_sound = None
        self.close_sound = None

        self.init_ui()
        self.play_start_sound()
        log("SYSTEME", "Application démarrée")

    # ---------------- UI ----------------

    def init_ui(self):
        self.stack = QStackedLayout(self)
        self.page_home = self.build_home()
        self.page_fill = self.build_fill()
        self.page_done = self.build_done()
        self.stack.addWidget(self.page_home)
        self.stack.addWidget(self.page_fill)
        self.stack.addWidget(self.page_done)

    def build_home(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.logo = QLabel()
        logo_path = os.path.join(ASSETS, "logo.png")
        if os.path.exists(logo_path):
            self.logo.setPixmap(
                QPixmap(logo_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        self.logo.setAlignment(Qt.AlignCenter)

        total = 0
        if self.db:
            try:
                total = self.db.get_total()
            except Exception:
                log("MYSQL", "Impossible de récupérer le compteur global")

        self.counter_label = QLabel(f"Bouteilles scannées aujourd'hui : {total}")
        self.counter_label.setAlignment(Qt.AlignCenter)
        self.counter_label.setFont(QFont("Arial", 14, QFont.Bold))

        self.scan_label = QLabel(" Scannez votre QR code")
        self.scan_label.setAlignment(Qt.AlignCenter)
        self.scan_label.setFont(QFont("Arial", 18))
        self.scan_label.setStyleSheet(scan_label_style())

        self.capacity_box = QGroupBox("Choisissez la capacité")
        self.capacity_box.hide()

        self.total_label = QLabel("")
        self.qr_label = QLabel("")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.qr_label.setAlignment(Qt.AlignCenter)

        btn_layout = QHBoxLayout()
        for cap in ["1 L", "2 L", "5 L"]:
            btn = QPushButton(cap)
            btn.setStyleSheet(button_style())
            btn.setMinimumHeight(45)
            btn.clicked.connect(self.start_filling)
            btn_layout.addWidget(btn)

        box = QVBoxLayout()
        box.addWidget(self.total_label)
        box.addWidget(self.qr_label)
        box.addLayout(btn_layout)
        self.capacity_box.setLayout(box)

        self.debug_panel = QWidget()
        self.debug_panel.setStyleSheet("background:black;color:#00ff00;")
        self.debug_panel.hide()
        debug_layout = QVBoxLayout(self.debug_panel)
        btn_add_qr = QPushButton("Ajouter un QR code")
        btn_add_qr.setStyleSheet(debug_button_style())
        btn_add_qr.clicked.connect(self.add_qr_dialog)
        debug_layout.addWidget(btn_add_qr)

        layout.addWidget(self.logo)
        layout.addWidget(self.counter_label)
        layout.addWidget(self.scan_label)
        layout.addWidget(self.capacity_box)
        layout.addWidget(self.debug_panel)
        return page

    def build_fill(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        self.fill_label = QLabel(alignment=Qt.AlignCenter)
        gif_path = os.path.join(ASSETS, "spinner.gif")
        if os.path.exists(gif_path):
            self.fill_movie = QMovie(gif_path)
            self.fill_label.setMovie(self.fill_movie)

        txt = QLabel(" Remplissage en cours...", alignment=Qt.AlignCenter)
        txt.setStyleSheet("font-size:28px;font-weight:bold;color:#1a73e8;")

        layout.addWidget(self.fill_label)
        layout.addWidget(txt)
        return page

    def build_done(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(" Bouteille remplie\nMerci !", alignment=Qt.AlignCenter))
        return page

    # ---------------- LOGIQUE ----------------

    def process_qr_buffer(self):
        if self.qr_buffer:
            log("SCAN", f"QR scanné : {self.qr_buffer}")
            self.fake_scan(self.qr_buffer)
            self.qr_buffer = ""

    def fake_scan(self, qr_id):
        if not self.db:
            log("MYSQL", "DB non disponible")
            return
        if not re.fullmatch(r"\d{1,20}", qr_id):
            self.scan_label.setText("QR invalide")
            log("SCAN", f"QR invalide : {qr_id}")
            QMessageBox.critical(self, "Erreur Code", f"QR invalide : {qr_id}")
            return

        self.last_qr = qr_id
        try:
            if not self.db.qr_exists(qr_id):
                self.scan_label.setText("QR CODE INEXISTANT")
                self.capacity_box.hide()
                log("MYSQL", f"QR INEXISTANT : {qr_id}")
                QMessageBox.warning(self, "Erreur Code", f"QR code {qr_id} inexistant")
                return

            total, qr_count = self.db.get_counts(qr_id)
            self.scan_label.setText(f"QR détecté (ID {qr_id})")
            self.total_label.setText(f"Total remplissages : {total}")
            self.qr_label.setText(f"Avec ce QR : {qr_count}")

            global_total = self.db.get_total()
            self.counter_label.setText(f"Bouteilles scannées aujourd'hui : {global_total}")
            self.capacity_box.show()
            log("SCAN", f"QR OK : {qr_id}, total {total}, global {global_total}")

        except Exception as e:
            log("MYSQL", f"Erreur scan QR : {e}")
            QMessageBox.critical(self, "Erreur BDD", f"Erreur base de données : {e}")

    def start_filling(self):
        if not self.last_qr or self.filling_active:
            return
        self.filling_active = True
        self.stack.setCurrentWidget(self.page_fill)
        if hasattr(self, "fill_movie"):
            self.fill_movie.start()
        log("SYSTEME", f"Démarrage remplissage QR {self.last_qr}")
        QTimer.singleShot(5000, self.finish_filling)

    def finish_filling(self):
        try:
            self.db.increment(self.last_qr)
            total = self.db.get_total()
            self.counter_label.setText(f"Bouteilles scannées aujourd'hui : {total}")
            log("SYSTEME", f"Fin remplissage QR {self.last_qr}, total {total}")
        except Exception as e:
            log("MYSQL", f"Erreur increment : {e}")
            QMessageBox.critical(self, "Erreur BDD", f"Erreur base de données : {e}")

        if hasattr(self, "fill_movie"):
            self.fill_movie.stop()

        self.stack.setCurrentWidget(self.page_done)
        QTimer.singleShot(3000, self.reset_home)

    def reset_home(self):
        self.scan_label.setText(" Scannez votre QR code")
        self.capacity_box.hide()
        self.last_qr = None
        self.filling_active = False
        self.stack.setCurrentWidget(self.page_home)
        log("SYSTEME", "Retour à l'accueil")

    # ---------------- DEBUG ----------------

    def add_qr_dialog(self):
        if not self.debug_authenticated:
            while self.debug_login_attempts < 3:
                user, ok1 = QInputDialog.getText(self, "Erreur Auth", "Utilisateur MySQL :")
                if not ok1 or user != MYSQL_USER:
                    self.debug_login_attempts += 1
                    log("DEBUG", f"Auth échouée ({self.debug_login_attempts})")
                    continue
                pwd, ok2 = QInputDialog.getText(self, "Erreur Auth", "Mot de passe :", QLineEdit.Password)
                if not ok2 or pwd != MYSQL_PASSWORD:
                    self.debug_login_attempts += 1
                    log("DEBUG", f"Auth échouée ({self.debug_login_attempts})")
                    continue
                self.debug_authenticated = True
                log("DEBUG", "Authentification réussie")
                break
            else:
                QMessageBox.critical(self, "Erreur Auth", "Trop de tentatives échouées !")
                log("DEBUG", "Accès debug bloqué après 3 échecs")
                return

        while True:
            qr_id, ok = QInputDialog.getText(self, "Erreur Code", "ID QR (1-20 chiffres) :")
            if not ok:
                log("DEBUG", "Ajout QR annulé")
                return
            if not re.fullmatch(r"\d{1,20}", qr_id):
                QMessageBox.critical(self, "Erreur Code", "ID invalide (1-20 chiffres).")
                log("DEBUG", f"ID invalide : {qr_id}")
                continue
            try:
                if self.db.qr_exists(qr_id):
                    QMessageBox.critical(self, "Erreur Code", "QR code déjà existant.")
                    log("DEBUG", f"QR déjà existant : {qr_id}")
                    continue
                self.db.ensure_qr(qr_id)
                log("DEBUG", f"QR ajouté manuellement : {qr_id}")
                QMessageBox.information(self, "Succès", f"QR {qr_id} ajouté.")

                # Oui/Non pour ajouter un autre
                msg = QMessageBox(self)
                msg.setWindowTitle("Ajouter un autre?")
                msg.setText("Voulez-vous ajouter un autre QR ?")
                msg.setIcon(QMessageBox.Question)
                oui_btn = msg.addButton("Oui", QMessageBox.YesRole)
                non_btn = msg.addButton("Non", QMessageBox.NoRole)
                msg.exec_()
                if msg.clickedButton() == oui_btn:
                    continue
                else:
                    log("DEBUG", "Fin menu ajout QR")
                    return
            except Exception as e:
                QMessageBox.critical(self, "Erreur BDD", str(e))
                log("MYSQL", f"Erreur ajout QR : {e}")
                return

    # ---------------- EVENTS ----------------

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_D:
            self.debug_counter += 1
            if self.debug_counter >= 3:
                self.debug_visible = not self.debug_visible
                self.debug_panel.setVisible(self.debug_visible)
                self.debug_counter = 0
                log("DEBUG", f"Debug panel {'ouvert' if self.debug_visible else 'fermé'}")
            return
        text = event.text()
        if text.isdigit():
            self.qr_buffer += text
            self.qr_timer.start(400)

    # ---------------- SON ----------------

    def play_start_sound(self):
        path = os.path.join(ASSETS, "start.wav")
        if os.path.exists(path):
            self.start_sound = QSoundEffect(self)
            self.start_sound.setSource(QUrl.fromLocalFile(path))
            self.start_sound.setVolume(0.5)
            self.start_sound.play()
            log("SYSTEME", "Son d'ouverture joué")


# ---------------- MAIN ----------------

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = App()
    window.show()
    sys.exit(app.exec_())