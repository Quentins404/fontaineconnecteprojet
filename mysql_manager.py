import sys, os

# Permet d'importer `logins.py` depuis `assets/old`
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OLD_ASSETS_DIR = os.path.join(BASE_DIR, "assets", "old")
if OLD_ASSETS_DIR not in sys.path:
    sys.path.insert(0, OLD_ASSETS_DIR)

import mysql.connector
from logins import (
    MYSQL_HOST,
    MYSQL_DATABASE,
    MYSQL_USER,
    MYSQL_PASSWORD
)

class MySQLManager:
    def __init__(self):
        self.db = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )
        self.cursor = self.db.cursor(dictionary=True)
        self.init_tables()

    def init_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS qr_codes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            qr_id VARCHAR(64) UNIQUE NOT NULL,
            count INT DEFAULT 0
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INT PRIMARY KEY,
            total INT NOT NULL
        )
        """)

        self.cursor.execute("SELECT * FROM stats WHERE id=1")
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO stats (id, total) VALUES (1, 0)"
            )

        self.db.commit()

    def ensure_qr(self, qr_id):
        self.cursor.execute(
            "SELECT * FROM qr_codes WHERE qr_id=%s",
            (qr_id,)
        )
        if not self.cursor.fetchone():
            self.cursor.execute(
                "INSERT INTO qr_codes (qr_id, count) VALUES (%s, 0)",
                (qr_id,)
            )
            self.db.commit()

    def qr_exists(self, qr_id):
        """Retourne True si le QR existe dans la base, False sinon."""
        self.cursor.execute(
            "SELECT 1 FROM qr_codes WHERE qr_id=%s",
            (qr_id,)
        )
        return bool(self.cursor.fetchone())

    def increment(self, qr_id):
        self.cursor.execute(
            "UPDATE qr_codes SET count = count + 1 WHERE qr_id=%s",
            (qr_id,)
        )
        self.cursor.execute(
            "UPDATE stats SET total = total + 1 WHERE id=1"
        )
        self.db.commit()

    def get_total(self):
        """Retourne le total global depuis la table stats."""
        self.cursor.execute("SELECT total FROM stats WHERE id=1")
        row = self.cursor.fetchone()
        return row["total"] if row else 0

    def get_counts(self, qr_id):
        # retourne (total, count_for_qr). Ne crée pas de QR si absent.
        total = self.get_total()

        self.cursor.execute(
            "SELECT count FROM qr_codes WHERE qr_id=%s",
            (qr_id,)
        )
        row = self.cursor.fetchone()
        qr = row["count"] if row else 0

        return total, qr
