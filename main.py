import sys
from datetime import datetime, timedelta
import sqlite3
from contextlib import contextmanager
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog, QLabel,
    QLineEdit, QSpinBox, QComboBox, QMessageBox, QTabWidget, QFrame,
    QTextEdit, QHeaderView, QDateEdit, QGroupBox, QRadioButton, QCheckBox
)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont, QColor, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.unicode_minus'] = False


# ============ MODERN STYLE SHEET ============

LIBRARY_STYLE = """
    QMainWindow {
        background-color: #0a0e27;
    }
    QTabWidget::pane {
        border: none;
        background-color: #131b3c;
        border-radius: 12px;
    }
    QTabBar::tab {
        background-color: #1a2350;
        color: #c4d0ff;
        padding: 12px 30px;
        margin-right: 5px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        font-weight: bold;
        font-size: 13px;
    }
    QTabBar::tab:selected {
        background-color: #6c63ff;
        color: white;
    }
    QTabBar::tab:hover:!selected {
        background-color: #2a3570;
    }
    QTableWidget {
        background-color: #131b3c;
        alternate-background-color: #1a2350;
        color: #c4d0ff;
        gridline-color: #2a3570;
        border: none;
        border-radius: 10px;
    }
    QTableWidget::item {
        padding: 10px;
    }
    QTableWidget::item:selected {
        background-color: #6c63ff;
        color: white;
    }
    QHeaderView::section {
        background-color: #0a0e27;
        color: #6c63ff;
        font-weight: bold;
        padding: 12px;
        border: none;
    }
    QPushButton {
        background-color: #6c63ff;
        color: white;
        border: none;
        padding: 10px 25px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #857dff;
    }
    QPushButton:pressed {
        background-color: #554ccf;
    }
    QPushButton#danger {
        background-color: #ff5e5e;
    }
    QPushButton#danger:hover {
        background-color: #ff7a7a;
    }
    QPushButton#success {
        background-color: #4caf50;
    }
    QPushButton#success:hover {
        background-color: #6cbb6f;
    }
    QLineEdit, QComboBox, QSpinBox, QDateEdit, QTextEdit {
        background-color: #1a2350;
        border: 1px solid #2a3570;
        border-radius: 8px;
        padding: 10px;
        color: #c4d0ff;
        font-size: 12px;
    }
    QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
        border: 1px solid #6c63ff;
    }
    QLabel {
        color: #c4d0ff;
    }
    QDialog {
        background-color: #131b3c;
    }
    QGroupBox {
        border: 1px solid #2a3570;
        border-radius: 10px;
        margin-top: 12px;
        font-weight: bold;
        color: #6c63ff;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 15px;
        padding: 0 8px;
    }
    QRadioButton, QCheckBox {
        color: #c4d0ff;
        spacing: 8px;
    }
    QRadioButton::indicator, QCheckBox::indicator {
        width: 16px;
        height: 16px;
    }
"""


# ============ DATABASE MANAGER ============

class DatabaseManager:
    """Veritabanı işlemlerini yöneten sınıf"""

    def __init__(self, db_name="digital_library.db"):
        self.db_name = db_name
        self.create_tables()

    @contextmanager
    def get_connection(self):
        """Veritabanı bağlantısı sağlayan context manager"""
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_tables(self):
        """Tüm tabloları oluşturur"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Kitaplar tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kitaplar (
                    kitap_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    yazar TEXT NOT NULL,
                    kategori TEXT NOT NULL,
                    yayin_yili INTEGER,
                    sayfa_sayisi INTEGER,
                    dil TEXT DEFAULT 'Türkçe',
                    durum TEXT DEFAULT 'Mevcut',
                    aciklama TEXT,
                    eklenme_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Üyeler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS uyeler (
                    uye_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uye_no TEXT UNIQUE NOT NULL,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    telefon TEXT NOT NULL,
                    adres TEXT,
                    kayit_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    durum TEXT DEFAULT 'Aktif'
                )
            ''')

            # Ödünç tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS odunc (
                    odunc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kitap_id INTEGER NOT NULL,
                    uye_id INTEGER NOT NULL,
                    odunc_tarihi TIMESTAMP NOT NULL,
                    iade_tarihi TIMESTAMP,
                    son_tarih TIMESTAMP NOT NULL,
                    durum TEXT DEFAULT 'Ödünçte',
                    gecikme_ucreti REAL DEFAULT 0,
                    FOREIGN KEY (kitap_id) REFERENCES kitaplar (kitap_id),
                    FOREIGN KEY (uye_id) REFERENCES uyeler (uye_id)
                )
            ''')

            # Sistem kullanıcıları tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sistem_kullanicilari (
                    kullanici_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kullanici_adi TEXT UNIQUE NOT NULL,
                    sifre TEXT NOT NULL,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    rol TEXT DEFAULT 'personel',
                    durum TEXT DEFAULT 'Aktif',
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Kategoriler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kategoriler (
                    kategori_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kategori_adi TEXT UNIQUE NOT NULL,
                    aciklama TEXT
                )
            ''')

            # Varsayılan kategorileri ekle
            default_categories = ['Roman', 'Hikaye', 'Şiir', 'Bilim Kurgu', 'Fantastik',
                                 'Tarih', 'Bilim', 'Sanat', 'Felsefe', 'Psikoloji',
                                 'Çocuk', 'Eğitim', 'Sözlük', 'Ansiklopedi', 'Diğer']
            for kategori in default_categories:
                cursor.execute('INSERT OR IGNORE INTO kategoriler (kategori_adi) VALUES (?)', (kategori,))

            # Varsayılan kitaplar ekle
            cursor.execute('SELECT COUNT(*) FROM kitaplar')
            if cursor.fetchone()[0] == 0:
                default_books = [
                    ("Sefiller", "Victor Hugo", "Roman", 1862, 1234, "Türkçe"),
                    ("Suç ve Ceza", "Dostoyevski", "Roman", 1866, 672, "Türkçe"),
                    ("Yüz Yıllık Yalnızlık", "Gabriel García Márquez", "Roman", 1967, 448, "Türkçe"),
                    ("Dönüşüm", "Franz Kafka", "Hikaye", 1915, 96, "Türkçe"),
                    ("Hayvan Çiftliği", "George Orwell", "Roman", 1945, 152, "Türkçe"),
                    ("İnsan Ne İle Yaşar", "Tolstoy", "Hikaye", 1885, 96, "Türkçe"),
                    ("Kürk Mantolu Madonna", "Sabahattin Ali", "Roman", 1943, 160, "Türkçe"),
                    ("Beyaz Zambaklar Ülkesinde", "Grigory Petrov", "Roman", 1923, 200, "Türkçe"),
                    ("Simyacı", "Paulo Coelho", "Roman", 1988, 208, "Türkçe"),
                    ("Uçurtma Avcısı", "Khaled Hosseini", "Roman", 2003, 384, "Türkçe"),
                ]
                for kitap in default_books:
                    cursor.execute('''
                        INSERT INTO kitaplar (ad, yazar, kategori, yayin_yili, sayfa_sayisi, dil)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', kitap)

            # Varsayılan admin kullanıcısı
            cursor.execute('SELECT COUNT(*) FROM sistem_kullanicilari WHERE kullanici_adi = "admin"')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO sistem_kullanicilari (kullanici_adi, sifre, ad, soyad, rol)
                    VALUES ('kutuphane', '12345', 'Admin', 'Kullanıcı', 'admin')
                ''')

    # ============ KİTAP İŞLEMLERİ ============

    def kitap_ekle(self, ad, yazar, kategori, yayin_yili=None, sayfa_sayisi=None, dil="Türkçe", aciklama=""):
        """Yeni kitap ekler"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO kitaplar (ad, yazar, kategori, yayin_yili, sayfa_sayisi, dil, aciklama)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (ad, yazar, kategori, yayin_yili, sayfa_sayisi, dil, aciklama))
            return cursor.lastrowid

    def kitaplari_getir(self, filtre=None, arama=None):
        """Tüm kitapları getirir, filtre ve arama desteği"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = 'SELECT * FROM kitaplar'
            params = []

            if filtre:
                query += ' WHERE kategori = ?'
                params.append(filtre)
            elif arama:
                query += ' WHERE ad LIKE ? OR yazar LIKE ?'
                arama_term = f'%{arama}%'
                params = [arama_term, arama_term]

            query += ' ORDER BY ad'
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def kitap_getir(self, kitap_id):
        """ID'ye göre kitap getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM kitaplar WHERE kitap_id = ?', (kitap_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def kitap_guncelle(self, kitap_id, ad, yazar, kategori, yayin_yili, sayfa_sayisi, dil, aciklama):
        """Kitap bilgilerini günceller"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE kitaplar
                SET ad = ?, yazar = ?, kategori = ?, yayin_yili = ?, sayfa_sayisi = ?, dil = ?, aciklama = ?
                WHERE kitap_id = ?
            ''', (ad, yazar, kategori, yayin_yili, sayfa_sayisi, dil, aciklama, kitap_id))

    def kitap_sil(self, kitap_id):
        """Kitap siler, önce ödünç durumunu kontrol eder"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Ödünçte mi kontrol et
            cursor.execute('SELECT COUNT(*) as count FROM odunc WHERE kitap_id = ? AND durum = "Ödünçte"', (kitap_id,))
            if cursor.fetchone()['count'] > 0:
                raise ValueError("Bu kitap ödünçte olduğu için silinemez!")

            cursor.execute('DELETE FROM kitaplar WHERE kitap_id = ?', (kitap_id,))

    def kitap_durumunu_degistir(self, kitap_id, durum):
        """Kitap durumunu değiştirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE kitaplar SET durum = ? WHERE kitap_id = ?', (durum, kitap_id))

    def kategori_kontrol(self, kategori):
        """Kategori varlığını kontrol eder"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM kategoriler WHERE kategori_adi = ?', (kategori,))
            return cursor.fetchone() is not None

    def kategorileri_getir(self):
        """Tüm kategorileri getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT kategori_adi FROM kategoriler ORDER BY kategori_adi')
            return [row['kategori_adi'] for row in cursor.fetchall()]

    # ============ ÜYE İŞLEMLERİ ============

    def uye_ekle(self, uye_no, ad, soyad, email, telefon, adres=""):
        """Yeni üye ekler"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO uyeler (uye_no, ad, soyad, email, telefon, adres)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (uye_no, ad, soyad, email, telefon, adres))
            return cursor.lastrowid

    def uyeleri_getir(self, arama=None):
        """Tüm üyeleri getirir, arama desteği"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if arama:
                cursor.execute('''
                    SELECT * FROM uyeler
                    WHERE ad LIKE ? OR soyad LIKE ? OR uye_no LIKE ? OR email LIKE ?
                    ORDER BY ad
                ''', (f'%{arama}%', f'%{arama}%', f'%{arama}%', f'%{arama}%'))
            else:
                cursor.execute('SELECT * FROM uyeler ORDER BY ad')
            return [dict(row) for row in cursor.fetchall()]

    def uye_getir(self, uye_id):
        """ID'ye göre üye getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM uyeler WHERE uye_id = ?', (uye_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def uye_sil(self, uye_id):
        """Üye siler, önce ödünç durumunu kontrol eder"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) as count FROM odunc WHERE uye_id = ? AND durum = "Ödünçte"', (uye_id,))
            if cursor.fetchone()['count'] > 0:
                raise ValueError("Bu üyenin ödünç kitabı var! Önce kitapları iade edilmeli.")

            cursor.execute('DELETE FROM uyeler WHERE uye_id = ?', (uye_id,))

    def uye_guncelle(self, uye_id, ad, soyad, email, telefon, adres):
        """Üye bilgilerini günceller"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE uyeler SET ad = ?, soyad = ?, email = ?, telefon = ?, adres = ?
                WHERE uye_id = ?
            ''', (ad, soyad, email, telefon, adres, uye_id))

    def son_uye_numarasini_getir(self):
        """Son üye numarasını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT uye_no FROM uyeler ORDER BY uye_id DESC LIMIT 1')
            row = cursor.fetchone()
            if row:
                num = int(row['uye_no'].replace('LIB', ''))
                return f"LIB{num + 1:06d}"
            return "LIB000001"

    # ============ ÖDÜNÇ İŞLEMLERİ ============

    def odunc_ver(self, kitap_id, uye_id, gun_sayisi=14):
        """Kitap ödünç verir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Kitap müsait mi kontrol et
            cursor.execute('SELECT durum FROM kitaplar WHERE kitap_id = ?', (kitap_id,))
            kitap = cursor.fetchone()
            if not kitap or kitap['durum'] != 'Mevcut':
                raise ValueError("Bu kitap şu anda ödünç verilemez!")

            # Üye aktif mi kontrol et
            cursor.execute('SELECT durum FROM uyeler WHERE uye_id = ?', (uye_id,))
            uye = cursor.fetchone()
            if not uye or uye['durum'] != 'Aktif':
                raise ValueError("Bu üye aktif değil!")

            odunc_tarihi = datetime.now()
            son_tarih = odunc_tarihi + timedelta(days=gun_sayisi)

            cursor.execute('''
                INSERT INTO odunc (kitap_id, uye_id, odunc_tarihi, son_tarih, durum)
                VALUES (?, ?, ?, ?, 'Ödünçte')
            ''', (kitap_id, uye_id, odunc_tarihi, son_tarih))

            cursor.execute('UPDATE kitaplar SET durum = "Ödünçte" WHERE kitap_id = ?', (kitap_id,))

            return cursor.lastrowid

    def iade_al(self, odunc_id):
        """Kitap iade alır"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('SELECT kitap_id, son_tarih FROM odunc WHERE odunc_id = ? AND durum = "Ödünçte"', (odunc_id,))
            odunc = cursor.fetchone()
            if not odunc:
                raise ValueError("Geçersiz ödünç kaydı!")

            iade_tarihi = datetime.now()
            son_tarih = datetime.fromisoformat(odunc['son_tarih'].replace(' ', 'T'))

            # Gecikme ücreti hesapla
            gecikme_ucreti = 0
            if iade_tarihi > son_tarih:
                gecikme_gunu = (iade_tarihi - son_tarih).days
                gecikme_ucreti = gecikme_gunu * 5  # Günde 5 TL
                QMessageBox.warning(None, "Uyarı", f"Kitap {gecikme_gunu} gün gecikmeli! Gecikme ücreti: {gecikme_ucreti} TL")

            cursor.execute('''
                UPDATE odunc
                SET iade_tarihi = ?, durum = 'İade Edildi', gecikme_ucreti = ?
                WHERE odunc_id = ?
            ''', (iade_tarihi, gecikme_ucreti, odunc_id))

            cursor.execute('UPDATE kitaplar SET durum = "Mevcut" WHERE kitap_id = ?', (odunc['kitap_id'],))

            return gecikme_ucreti

    def odunc_listele(self, durum=None):
        """Ödünç listesini getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            query = '''
                SELECT o.*, k.ad as kitap_adi, k.yazar, u.ad as uye_adi, u.soyad as uye_soyad, u.uye_no
                FROM odunc o
                JOIN kitaplar k ON o.kitap_id = k.kitap_id
                JOIN uyeler u ON o.uye_id = u.uye_id
            '''
            params = []

            if durum:
                query += ' WHERE o.durum = ?'
                params.append(durum)

            query += ' ORDER BY o.odunc_tarihi DESC'

            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def uyenin_odunc_kitaplari(self, uye_id):
        """Üyenin ödünç kitaplarını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.*, k.ad as kitap_adi, k.yazar
                FROM odunc o
                JOIN kitaplar k ON o.kitap_id = k.kitap_id
                WHERE o.uye_id = ? AND o.durum = 'Ödünçte'
            ''', (uye_id,))
            return [dict(row) for row in cursor.fetchall()]

    def gecikmeli_kitaplari_getir(self):
        """Gecikmiş kitapları getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT o.*, k.ad as kitap_adi, k.yazar, u.ad as uye_adi, u.soyad as uye_soyad, u.telefon
                FROM odunc o
                JOIN kitaplar k ON o.kitap_id = k.kitap_id
                JOIN uyeler u ON o.uye_id = u.uye_id
                WHERE o.durum = 'Ödünçte' AND o.son_tarih < ?
            ''', (datetime.now(),))
            return [dict(row) for row in cursor.fetchall()]

    # ============ SİSTEM KULLANICILARI ============

    def kullanici_kontrol(self, kullanici_adi, sifre):
        """Kullanıcı giriş kontrolü"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM sistem_kullanicilari
                WHERE kullanici_adi = ? AND sifre = ? AND durum = 'Aktif'
            ''', (kullanici_adi, sifre))
            result = cursor.fetchone()
            return dict(result) if result else None

    def kullanici_ekle(self, kullanici_adi, sifre, ad, soyad, rol='personel'):
        """Sistem kullanıcısı ekler"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sistem_kullanicilari (kullanici_adi, sifre, ad, soyad, rol)
                VALUES (?, ?, ?, ?, ?)
            ''', (kullanici_adi, sifre, ad, soyad, rol))
            return cursor.lastrowid

    def kullanicilari_getir(self):
        """Tüm sistem kullanıcılarını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM sistem_kullanicilari ORDER BY kullanici_id')
            return [dict(row) for row in cursor.fetchall()]

    def kullanici_sil(self, kullanici_id):
        """Sistem kullanıcısı siler"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sistem_kullanicilari WHERE kullanici_id = ?', (kullanici_id,))

    # ============ İSTATİSTİKLER ============

    def toplam_kitap_sayisi(self):
        """Toplam kitap sayısını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM kitaplar')
            return cursor.fetchone()['count']

    def oduncte_kitap_sayisi(self):
        """Ödünçteki kitap sayısını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM kitaplar WHERE durum = "Ödünçte"')
            return cursor.fetchone()['count']

    def mevcut_kitap_sayisi(self):
        """Mevcut kitap sayısını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM kitaplar WHERE durum = "Mevcut"')
            return cursor.fetchone()['count']

    def toplam_uye_sayisi(self):
        """Toplam üye sayısını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM uyeler')
            return cursor.fetchone()['count']

    def toplam_odunc_sayisi(self):
        """Toplam ödünç sayısını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM odunc')
            return cursor.fetchone()['count']

    def aktif_odunc_sayisi(self):
        """Aktif ödünç sayısını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM odunc WHERE durum = "Ödünçte"')
            return cursor.fetchone()['count']

    def toplam_gecikme_ucreti(self):
        """Toplam gecikme ücretini getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT SUM(gecikme_ucreti) as total FROM odunc')
            return cursor.fetchone()['total'] or 0

    def kategori_dagilimi(self):
        """Kategorilere göre kitap dağılımını getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT kategori, COUNT(*) as sayi
                FROM kitaplar
                GROUP BY kategori
                ORDER BY sayi DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def en_cok_okunan_kitaplar(self, limit=10):
        """En çok ödünç alınan kitapları getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT k.kitap_id, k.ad, k.yazar, COUNT(o.odunc_id) as odunc_sayisi
                FROM kitaplar k
                LEFT JOIN odunc o ON k.kitap_id = o.kitap_id
                GROUP BY k.kitap_id
                ORDER BY odunc_sayisi DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]

    def en_aktif_uyeler(self, limit=10):
        """En çok kitap okuyan üyeleri getirir"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT u.uye_id, u.ad, u.soyad, u.uye_no, COUNT(o.odunc_id) as kitap_sayisi
                FROM uyeler u
                LEFT JOIN odunc o ON u.uye_id = o.uye_id
                GROUP BY u.uye_id
                ORDER BY kitap_sayisi DESC
                LIMIT ?
            ''', (limit,))
            return [dict(row) for row in cursor.fetchall()]


# ============ LOGIN DIALOG ============

class LoginDialog(QDialog):
    """Giriş penceresi"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Dijital Kütüphane - Giriş")
        self.setGeometry(400, 300, 450, 400)
        self.setStyleSheet(LIBRARY_STYLE)
        self.setModal(True)
        self.init_ui()
        self.kullanici = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 40, 30, 30)

        baslik = QLabel("📚 DİJİTAL KÜTÜPHANE")
        baslik_font = QFont("Arial", 20, QFont.Bold)
        baslik.setFont(baslik_font)
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")

        alt_baslik = QLabel("Sisteme Giriş Yapın")
        alt_baslik.setFont(QFont("Arial", 12))
        alt_baslik.setAlignment(Qt.AlignCenter)
        alt_baslik.setStyleSheet("color: #c4d0ff; margin-bottom: 30px;")

        kadi_label = QLabel("Kullanıcı Adı")
        kadi_label.setFont(QFont("Arial", 11, QFont.Bold))
        kadi_label.setStyleSheet("color: #6c63ff;")
        self.kadi_input = QLineEdit()
        self.kadi_input.setPlaceholderText("Kullanıcı adınızı girin")
        self.kadi_input.setStyleSheet("padding: 12px; font-size: 12px;")

        sifre_label = QLabel("Şifre")
        sifre_label.setFont(QFont("Arial", 11, QFont.Bold))
        sifre_label.setStyleSheet("color: #6c63ff;")
        self.sifre_input = QLineEdit()
        self.sifre_input.setEchoMode(QLineEdit.Password)
        self.sifre_input.setPlaceholderText("Şifrenizi girin")
        self.sifre_input.setStyleSheet("padding: 12px; font-size: 12px;")
        self.sifre_input.returnPressed.connect(self.giris_yap)

        bilgi_label = QLabel("Demo Hesap: admin / admin123")
        bilgi_label.setAlignment(Qt.AlignCenter)
        bilgi_label.setStyleSheet("color: #7a7fb0; font-size: 11px; margin-top: 15px;")

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        giris_btn = QPushButton("📖 Giriş Yap")
        giris_btn.setStyleSheet("background-color: #6c63ff; padding: 12px; border-radius: 10px; font-weight: bold; font-size: 13px;")
        giris_btn.clicked.connect(self.giris_yap)

        iptal_btn = QPushButton("❌ Çıkış")
        iptal_btn.setObjectName("danger")
        iptal_btn.setStyleSheet("background-color: #ff5e5e; padding: 12px; border-radius: 10px; font-weight: bold; font-size: 13px;")
        iptal_btn.clicked.connect(self.reject)

        button_layout.addWidget(giris_btn)
        button_layout.addWidget(iptal_btn)

        layout.addWidget(baslik)
        layout.addWidget(alt_baslik)
        layout.addWidget(kadi_label)
        layout.addWidget(self.kadi_input)
        layout.addWidget(sifre_label)
        layout.addWidget(self.sifre_input)
        layout.addWidget(bilgi_label)
        layout.addSpacing(20)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def giris_yap(self):
        kadi = self.kadi_input.text().strip()
        sifre = self.sifre_input.text().strip()

        if not kadi or not sifre:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı ve şifre giriniz!")
            return

        kullanici = self.db.kullanici_kontrol(kadi, sifre)
        if kullanici:
            self.kullanici = kullanici
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı veya şifre hatalı!")


# ============ DİĞER DİALOGLAR ============

class KitapEkleDialog(QDialog):
    """Kitap ekleme penceresi"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Yeni Kitap Ekle")
        self.setGeometry(200, 200, 500, 600)
        self.setStyleSheet(LIBRARY_STYLE)
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        baslik = QLabel("📖 Yeni Kitap Ekle")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Kitap Adı:"), 0, 0)
        self.ad_input = QLineEdit()
        self.ad_input.setPlaceholderHeader(True)
        self.ad_input.setPlaceholderText("Kitabın tam adını girin")
        grid.addWidget(self.ad_input, 0, 1)

        grid.addWidget(QLabel("Yazar:"), 1, 0)
        self.yazar_input = QLineEdit()
        self.yazar_input.setPlaceholderText("Yazarın adını girin")
        grid.addWidget(self.yazar_input, 1, 1)

        grid.addWidget(QLabel("Kategori:"), 2, 0)
        self.kategori_combo = QComboBox()
        self.kategori_combo.addItems(self.db.kategorileri_getir())
        self.kategori_combo.setEditable(True)
        grid.addWidget(self.kategori_combo, 2, 1)

        grid.addWidget(QLabel("Yayın Yılı:"), 3, 0)
        self.yil_input = QSpinBox()
        self.yil_input.setMinimum(1000)
        self.yil_input.setMaximum(datetime.now().year)
        self.yil_input.setValue(2000)
        grid.addWidget(self.yil_input, 3, 1)

        grid.addWidget(QLabel("Sayfa Sayısı:"), 4, 0)
        self.sayfa_input = QSpinBox()
        self.sayfa_input.setMinimum(1)
        self.sayfa_input.setMaximum(10000)
        grid.addWidget(self.sayfa_input, 4, 1)

        grid.addWidget(QLabel("Dil:"), 5, 0)
        self.dil_combo = QComboBox()
        self.dil_combo.addItems(["Türkçe", "İngilizce", "Fransızca", "Almanca", "Rusça", "Diğer"])
        grid.addWidget(self.dil_combo, 5, 1)

        grid.addWidget(QLabel("Açıklama:"), 6, 0)
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setMaximumHeight(80)
        grid.addWidget(self.aciklama_input, 6, 1)

        layout.addWidget(baslik)
        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("📚 Kitap Ekle")
        ekle_btn.setStyleSheet("background-color: #6c63ff; padding: 12px; border-radius: 10px; font-weight: bold;")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setObjectName("danger")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def ekle(self):
        if self.ad_input.text().strip() and self.yazar_input.text().strip():
            # Yeni kategori kontrolü
            kategori = self.kategori_combo.currentText().strip()
            if not self.db.kategori_kontrol(kategori):
                self.db.kategorileri_getir()  # Kategori zaten eklenmiş olacak

            self.result = (
                self.ad_input.text().strip(),
                self.yazar_input.text().strip(),
                kategori,
                self.yil_input.value(),
                self.sayfa_input.value(),
                self.dil_combo.currentText(),
                self.aciklama_input.toPlainText()
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Kitap adı ve yazar alanları zorunludur!")


class KitapDuzenleDialog(QDialog):
    """Kitap düzenleme penceresi"""

    def __init__(self, db, kitap, parent=None):
        super().__init__(parent)
        self.db = db
        self.kitap = kitap
        self.setWindowTitle("Kitap Düzenle")
        self.setGeometry(200, 200, 500, 600)
        self.setStyleSheet(LIBRARY_STYLE)
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        baslik = QLabel("✏️ Kitap Düzenle")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Kitap Adı:"), 0, 0)
        self.ad_input = QLineEdit(self.kitap['ad'])
        grid.addWidget(self.ad_input, 0, 1)

        grid.addWidget(QLabel("Yazar:"), 1, 0)
        self.yazar_input = QLineEdit(self.kitap['yazar'])
        grid.addWidget(self.yazar_input, 1, 1)

        grid.addWidget(QLabel("Kategori:"), 2, 0)
        self.kategori_combo = QComboBox()
        self.kategori_combo.addItems(self.db.kategorileri_getir())
        self.kategori_combo.setCurrentText(self.kitap['kategori'])
        self.kategori_combo.setEditable(True)
        grid.addWidget(self.kategori_combo, 2, 1)

        grid.addWidget(QLabel("Yayın Yılı:"), 3, 0)
        self.yil_input = QSpinBox()
        self.yil_input.setMinimum(1000)
        self.yil_input.setMaximum(datetime.now().year)
        self.yil_input.setValue(self.kitap['yayin_yili'] or 2000)
        grid.addWidget(self.yil_input, 3, 1)

        grid.addWidget(QLabel("Sayfa Sayısı:"), 4, 0)
        self.sayfa_input = QSpinBox()
        self.sayfa_input.setMinimum(1)
        self.sayfa_input.setMaximum(10000)
        self.sayfa_input.setValue(self.kitap['sayfa_sayisi'] or 100)
        grid.addWidget(self.sayfa_input, 4, 1)

        grid.addWidget(QLabel("Dil:"), 5, 0)
        self.dil_combo = QComboBox()
        self.dil_combo.addItems(["Türkçe", "İngilizce", "Fransızca", "Almanca", "Rusça", "Diğer"])
        self.dil_combo.setCurrentText(self.kitap['dil'])
        grid.addWidget(self.dil_combo, 5, 1)

        grid.addWidget(QLabel("Açıklama:"), 6, 0)
        self.aciklama_input = QTextEdit(self.kitap['aciklama'] or "")
        self.aciklama_input.setMaximumHeight(80)
        grid.addWidget(self.aciklama_input, 6, 1)

        layout.addWidget(baslik)
        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        kaydet_btn = QPushButton("💾 Kaydet")
        kaydet_btn.setStyleSheet("background-color: #6c63ff; padding: 12px; border-radius: 10px; font-weight: bold;")
        kaydet_btn.clicked.connect(self.kaydet)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setObjectName("danger")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(kaydet_btn)
        button_layout.addWidget(iptal_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def kaydet(self):
        if self.ad_input.text().strip() and self.yazar_input.text().strip():
            self.result = (
                self.kitap['kitap_id'],
                self.ad_input.text().strip(),
                self.yazar_input.text().strip(),
                self.kategori_combo.currentText().strip(),
                self.yil_input.value(),
                self.sayfa_input.value(),
                self.dil_combo.currentText(),
                self.aciklama_input.toPlainText()
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Kitap adı ve yazar alanları zorunludur!")


class UyeEkleDialog(QDialog):
    """Üye ekleme penceresi"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Yeni Üye Ekle")
        self.setGeometry(200, 200, 500, 550)
        self.setStyleSheet(LIBRARY_STYLE)
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        baslik = QLabel("👤 Yeni Üye Ekle")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Üye No:"), 0, 0)
        self.uye_no_input = QLineEdit(self.db.son_uye_numarasini_getir())
        self.uye_no_input.setReadOnly(True)
        grid.addWidget(self.uye_no_input, 0, 1)

        grid.addWidget(QLabel("Ad:"), 1, 0)
        self.ad_input = QLineEdit()
        grid.addWidget(self.ad_input, 1, 1)

        grid.addWidget(QLabel("Soyad:"), 2, 0)
        self.soyad_input = QLineEdit()
        grid.addWidget(self.soyad_input, 2, 1)

        grid.addWidget(QLabel("Email:"), 3, 0)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("ornek@email.com")
        grid.addWidget(self.email_input, 3, 1)

        grid.addWidget(QLabel("Telefon:"), 4, 0)
        self.tel_input = QLineEdit()
        self.tel_input.setPlaceholderText("5XX XXX XX XX")
        grid.addWidget(self.tel_input, 4, 1)

        grid.addWidget(QLabel("Adres:"), 5, 0)
        self.adres_input = QTextEdit()
        self.adres_input.setMaximumHeight(80)
        grid.addWidget(self.adres_input, 5, 1)

        layout.addWidget(baslik)
        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("✅ Üye Ekle")
        ekle_btn.setStyleSheet("background-color: #6c63ff; padding: 12px; border-radius: 10px; font-weight: bold;")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setObjectName("danger")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def ekle(self):
        if (self.ad_input.text().strip() and self.soyad_input.text().strip() and
            self.email_input.text().strip() and self.tel_input.text().strip()):

            if "@" not in self.email_input.text() or "." not in self.email_input.text():
                QMessageBox.warning(self, "Uyarı", "Geçerli bir email adresi giriniz!")
                return

            if not self.tel_input.text().isdigit() or len(self.tel_input.text()) < 10:
                QMessageBox.warning(self, "Uyarı", "Geçerli bir telefon numarası giriniz!")
                return

            self.result = (
                self.uye_no_input.text(),
                self.ad_input.text().strip(),
                self.soyad_input.text().strip(),
                self.email_input.text().strip(),
                self.tel_input.text().strip(),
                self.adres_input.toPlainText()
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Tüm zorunlu alanları doldurun!")


class UyeDuzenleDialog(QDialog):
    """Üye düzenleme penceresi"""

    def __init__(self, db, uye, parent=None):
        super().__init__(parent)
        self.db = db
        self.uye = uye
        self.setWindowTitle("Üye Düzenle")
        self.setGeometry(200, 200, 500, 550)
        self.setStyleSheet(LIBRARY_STYLE)
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        baslik = QLabel("✏️ Üye Düzenle")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Üye No:"), 0, 0)
        self.uye_no_input = QLineEdit(self.uye['uye_no'])
        self.uye_no_input.setReadOnly(True)
        grid.addWidget(self.uye_no_input, 0, 1)

        grid.addWidget(QLabel("Ad:"), 1, 0)
        self.ad_input = QLineEdit(self.uye['ad'])
        grid.addWidget(self.ad_input, 1, 1)

        grid.addWidget(QLabel("Soyad:"), 2, 0)
        self.soyad_input = QLineEdit(self.uye['soyad'])
        grid.addWidget(self.soyad_input, 2, 1)

        grid.addWidget(QLabel("Email:"), 3, 0)
        self.email_input = QLineEdit(self.uye['email'])
        grid.addWidget(self.email_input, 3, 1)

        grid.addWidget(QLabel("Telefon:"), 4, 0)
        self.tel_input = QLineEdit(self.uye['telefon'])
        grid.addWidget(self.tel_input, 4, 1)

        grid.addWidget(QLabel("Adres:"), 5, 0)
        self.adres_input = QTextEdit(self.uye['adres'] or "")
        self.adres_input.setMaximumHeight(80)
        grid.addWidget(self.adres_input, 5, 1)

        layout.addWidget(baslik)
        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        kaydet_btn = QPushButton("💾 Kaydet")
        kaydet_btn.setStyleSheet("background-color: #6c63ff; padding: 12px; border-radius: 10px; font-weight: bold;")
        kaydet_btn.clicked.connect(self.kaydet)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setObjectName("danger")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(kaydet_btn)
        button_layout.addWidget(iptal_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def kaydet(self):
        if (self.ad_input.text().strip() and self.soyad_input.text().strip() and
            self.email_input.text().strip() and self.tel_input.text().strip()):

            if "@" not in self.email_input.text() or "." not in self.email_input.text():
                QMessageBox.warning(self, "Uyarı", "Geçerli bir email adresi giriniz!")
                return

            if not self.tel_input.text().isdigit() or len(self.tel_input.text()) < 10:
                QMessageBox.warning(self, "Uyarı", "Geçerli bir telefon numarası giriniz!")
                return

            self.result = (
                self.uye['uye_id'],
                self.ad_input.text().strip(),
                self.soyad_input.text().strip(),
                self.email_input.text().strip(),
                self.tel_input.text().strip(),
                self.adres_input.toPlainText()
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Tüm zorunlu alanları doldurun!")


class OduncVerDialog(QDialog):
    """Ödünç verme penceresi"""

    def __init__(self, db, kitaplar, uyeler, parent=None):
        super().__init__(parent)
        self.db = db
        self.kitaplar = kitaplar
        self.uyeler = uyeler
        self.setWindowTitle("Kitap Ödünç Ver")
        self.setGeometry(200, 200, 500, 450)
        self.setStyleSheet(LIBRARY_STYLE)
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        baslik = QLabel("📚 Kitap Ödünç Ver")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Kitap:"), 0, 0)
        self.kitap_combo = QComboBox()
        for kitap in self.kitaplar:
            if kitap['durum'] == 'Mevcut':
                self.kitap_combo.addItem(f"📖 {kitap['ad']} - {kitap['yazar']}", kitap['kitap_id'])
        grid.addWidget(self.kitap_combo, 0, 1)

        grid.addWidget(QLabel("Üye:"), 1, 0)
        self.uye_combo = QComboBox()
        for uye in self.uyeler:
            self.uye_combo.addItem(f"👤 {uye['ad']} {uye['soyad']} ({uye['uye_no']})", uye['uye_id'])
        grid.addWidget(self.uye_combo, 1, 1)

        grid.addWidget(QLabel("Ödünç Süresi (gün):"), 2, 0)
        self.sure_input = QSpinBox()
        self.sure_input.setMinimum(1)
        self.sure_input.setMaximum(60)
        self.sure_input.setValue(14)
        grid.addWidget(self.sure_input, 2, 1)

        layout.addWidget(baslik)
        layout.addLayout(grid)

        bilgi_label = QLabel("Not: Gecikme durumunda günlük 5 TL ücret uygulanır.")
        bilgi_label.setStyleSheet("color: #ff5e5e; font-size: 11px; margin-top: 10px;")
        layout.addWidget(bilgi_label)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ver_btn = QPushButton("🔖 Ödünç Ver")
        ver_btn.setStyleSheet("background-color: #6c63ff; padding: 12px; border-radius: 10px; font-weight: bold;")
        ver_btn.clicked.connect(self.odunc_ver)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setObjectName("danger")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(ver_btn)
        button_layout.addWidget(iptal_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def odunc_ver(self):
        kitap_id = self.kitap_combo.currentData()
        uye_id = self.uye_combo.currentData()
        sure = self.sure_input.value()

        if kitap_id and uye_id:
            self.result = (kitap_id, uye_id, sure)
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen kitap ve üye seçiniz!")


class IadeAlDialog(QDialog):
    """İade alma penceresi"""

    def __init__(self, db, odunc_list, parent=None):
        super().__init__(parent)
        self.db = db
        self.odunc_list = odunc_list
        self.setWindowTitle("Kitap İade Al")
        self.setGeometry(200, 200, 500, 400)
        self.setStyleSheet(LIBRARY_STYLE)
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        baslik = QLabel("📚 Kitap İade Al")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Ödünç Kaydı:"), 0, 0)
        self.odunc_combo = QComboBox()
        for odunc in self.odunc_list:
            son_tarih = datetime.fromisoformat(odunc['son_tarih'].replace(' ', 'T')) if odunc['son_tarih'] else None
            son_tarih_str = son_tarih.strftime("%d.%m.%Y") if son_tarih else "Belirtilmemiş"
            self.odunc_combo.addItem(
                f"{odunc['kitap_adi']} - {odunc['uye_adi']} {odunc.get('uye_soyad', '')} (Son Tarih: {son_tarih_str})",
                odunc['odunc_id']
            )
        grid.addWidget(self.odunc_combo, 0, 1)

        layout.addWidget(baslik)
        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        iade_btn = QPushButton("✅ İade Al")
        iade_btn.setStyleSheet("background-color: #6c63ff; padding: 12px; border-radius: 10px; font-weight: bold;")
        iade_btn.clicked.connect(self.iade_al)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setObjectName("danger")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(iade_btn)
        button_layout.addWidget(iptal_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def iade_al(self):
        odunc_id = self.odunc_combo.currentData()
        if odunc_id:
            self.result = odunc_id
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Lütfen bir ödünç kaydı seçiniz!")


class SistemKullaniciDialog(QDialog):
    """Sistem kullanıcısı ekleme penceresi"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Sistem Kullanıcısı Ekle")
        self.setGeometry(200, 200, 450, 500)
        self.setStyleSheet(LIBRARY_STYLE)
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(25, 25, 25, 25)

        baslik = QLabel("👤 Yeni Sistem Kullanıcısı")
        baslik.setFont(QFont("Arial", 16, QFont.Bold))
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #6c63ff; margin-bottom: 10px;")

        grid = QGridLayout()
        grid.setSpacing(12)

        grid.addWidget(QLabel("Ad:"), 0, 0)
        self.ad_input = QLineEdit()
        grid.addWidget(self.ad_input, 0, 1)

        grid.addWidget(QLabel("Soyad:"), 1, 0)
        self.soyad_input = QLineEdit()
        grid.addWidget(self.soyad_input, 1, 1)

        grid.addWidget(QLabel("Kullanıcı Adı:"), 2, 0)
        self.kadi_input = QLineEdit()
        grid.addWidget(self.kadi_input, 2, 1)

        grid.addWidget(QLabel("Şifre:"), 3, 0)
        self.sifre_input = QLineEdit()
        self.sifre_input.setEchoMode(QLineEdit.Password)
        grid.addWidget(self.sifre_input, 3, 1)

        grid.addWidget(QLabel("Rol:"), 4, 0)
        self.rol_combo = QComboBox()
        self.rol_combo.addItems(["personel", "admin"])
        grid.addWidget(self.rol_combo, 4, 1)

        layout.addWidget(baslik)
        layout.addLayout(grid)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("✅ Kullanıcı Ekle")
        ekle_btn.setStyleSheet("background-color: #6c63ff; padding: 12px; border-radius: 10px; font-weight: bold;")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setObjectName("danger")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def ekle(self):
        if (self.ad_input.text().strip() and self.soyad_input.text().strip() and
            self.kadi_input.text().strip() and self.sifre_input.text().strip()):
            self.result = (
                self.kadi_input.text().strip(),
                self.sifre_input.text().strip(),
                self.ad_input.text().strip(),
                self.soyad_input.text().strip(),
                self.rol_combo.currentText()
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Uyarı", "Tüm alanları doldurun!")


# ============ GRAFİKLER ============

class LibraryStatsWidget(QWidget):
    """Kütüphane istatistikleri widget'ı"""

    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.figure = Figure(figsize=(14, 6), dpi=100, facecolor='#131b3c')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: transparent;")
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_charts(self):
        self.figure.clear()

        # 1. Grafik - Kitap Durumu Dağılımı
        ax1 = self.figure.add_subplot(131)
        ax1.set_facecolor('#1a2350')

        mevcut = self.db.mevcut_kitap_sayisi()
        oduncte = self.db.oduncte_kitap_sayisi()

        if mevcut > 0 or oduncte > 0:
            sizes = [mevcut, oduncte]
            labels = [f'Mevcut Kitaplar\n{mevcut}', f'Ödünçteki Kitaplar\n{oduncte}']
            colors = ['#4caf50', '#ff5e5e']
            wedges, texts, autotexts = ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
                                                colors=colors, startangle=90, textprops={'fontsize': 10, 'color': '#c4d0ff'})
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            ax1.set_title('Kitap Durumu Dağılımı', fontsize=12, fontweight='bold', color='#6c63ff', pad=15)
        else:
            ax1.text(0.5, 0.5, 'Henüz Kitap Yok', ha='center', va='center', fontsize=12, color='#c4d0ff')
            ax1.set_title('Kitap Durumu Dağılımı', fontsize=12, fontweight='bold', color='#6c63ff', pad=15)

        # 2. Grafik - Kategori Dağılımı
        ax2 = self.figure.add_subplot(132)
        ax2.set_facecolor('#1a2350')

        kategoriler = self.db.kategori_dagilimi()
        if kategoriler:
            kate_adi = [k['kategori'] for k in kategoriler[:5]]
            kate_sayi = [k['sayi'] for k in kategoriler[:5]]
            bars = ax2.bar(kate_adi, kate_sayi, color='#6c63ff', edgecolor='none', width=0.6)
            ax2.set_title('En Çok Kitap Bulunan Kategoriler', fontsize=12, fontweight='bold', color='#6c63ff', pad=15)
            ax2.set_ylabel('Kitap Sayısı', fontsize=10, color='#c4d0ff')
            ax2.tick_params(axis='y', colors='#c4d0ff')
            ax2.tick_params(axis='x', colors='#c4d0ff', labelsize=9, rotation=15)

            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{int(height)}',
                        ha='center', va='bottom', fontweight='bold', fontsize=9, color='#c4d0ff')
        else:
            ax2.text(0.5, 0.5, 'Veri Yok', ha='center', va='center', fontsize=12, color='#c4d0ff')
            ax2.set_title('Kategori Dağılımı', fontsize=12, fontweight='bold', color='#6c63ff', pad=15)

        # 3. Grafik - Sistem İstatistikleri
        ax3 = self.figure.add_subplot(133)
        ax3.set_facecolor('#1a2350')

        istatistikler = [
            self.db.toplam_kitap_sayisi(),
            self.db.toplam_uye_sayisi(),
            self.db.toplam_odunc_sayisi(),
            self.db.aktif_odunc_sayisi()
        ]
        labels = ['📚 Kitaplar', '👥 Üyeler', '📖 Ödünçler', '🔁 Aktif']
        colors_bar = ['#6c63ff', '#4caf50', '#ff9800', '#ff5e5e']

        bars = ax3.bar(labels, istatistikler, color=colors_bar, edgecolor='none', width=0.6)
        ax3.set_title('Sistem İstatistikleri', fontsize=12, fontweight='bold', color='#6c63ff', pad=15)
        ax3.set_ylabel('Sayı', fontsize=10, color='#c4d0ff')
        ax3.tick_params(axis='y', colors='#c4d0ff')
        ax3.tick_params(axis='x', colors='#c4d0ff', labelsize=10)
        ax3.set_ylim(0, max(istatistikler) + 5 if max(istatistikler) > 0 else 10)

        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5, f'{int(height)}',
                    ha='center', va='bottom', fontweight='bold', fontsize=9, color='#c4d0ff')

        self.figure.tight_layout()
        self.canvas.draw()


# ============ ANA PENCERE ============

class LibraryMainWindow(QMainWindow):
    """Ana pencere"""

    def __init__(self, kullanici, db):
        super().__init__()
        self.kullanici = kullanici
        self.db = db
        self.setWindowTitle(f"📚 Dijital Kütüphane - Hoşgeldiniz, {kullanici['ad']} {kullanici['soyad']}")
        self.setGeometry(50, 50, 1400, 850)
        self.setStyleSheet(LIBRARY_STYLE)
        self.init_ui()
        self.load_data()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # Header
        header_frame = QFrame()
        header_frame.setStyleSheet("background-color: #1a2350; border-radius: 15px;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(25, 15, 25, 15)

        # Logo ve başlık
        left_header = QWidget()
        left_layout = QHBoxLayout()
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)

        logo_label = QLabel("📚")
        logo_label.setFont(QFont("Arial", 28))
        left_layout.addWidget(logo_label)

        header = QLabel("DİJİTAL KÜTÜPHANE")
        header_font = QFont("Arial", 18, QFont.Bold)
        header.setFont(header_font)
        header.setStyleSheet("color: #6c63ff;")
        left_layout.addWidget(header)
        left_header.setLayout(left_layout)

        # Sağ taraf - Arama ve kullanıcı
        right_widget = QWidget()
        right_layout = QHBoxLayout()
        right_layout.setSpacing(15)
        right_layout.setContentsMargins(0, 0, 0, 0)

        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #131b3c;
                border: 1px solid #2a3570;
                border-radius: 25px;
                padding: 2px;
            }
            QFrame:focus-within {
                border: 1px solid #6c63ff;
            }
        """)
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)
        search_layout.setContentsMargins(12, 5, 12, 5)

        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #6c63ff; font-size: 14px; background: transparent;")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Kitap, yazar, üye ara...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                color: #c4d0ff;
                font-size: 12px;
                padding: 5px 0;
                min-width: 250px;
            }
        """)
        self.search_input.textChanged.connect(self.arama_yap)

        search_layout.addWidget(search_icon)
        search_layout.addWidget(self.search_input)
        search_frame.setLayout(search_layout)

        kullanici_label = QLabel(f"👤 {self.kullanici['ad']} {self.kullanici['soyad']} [{self.kullanici['rol']}]")
        kullanici_label.setFont(QFont("Arial", 10, QFont.Bold))
        kullanici_label.setStyleSheet("color: #6c63ff; background-color: #131b3c; padding: 8px 15px; border-radius: 20px;")

        cikis_btn = QPushButton("🚪 Çıkış")
        cikis_btn.setObjectName("danger")
        cikis_btn.clicked.connect(self.cikis_yap)

        right_layout.addWidget(search_frame)
        right_layout.addWidget(kullanici_label)
        right_layout.addWidget(cikis_btn)
        right_widget.setLayout(right_layout)

        header_layout.addWidget(left_header)
        header_layout.addStretch()
        header_layout.addWidget(right_widget)
        header_frame.setLayout(header_layout)

        # Dashboard Kartları
        dashboard_layout = QHBoxLayout()
        dashboard_layout.setSpacing(20)

        kitap_card = self.create_modern_card("📚 Toplam Kitap", "0", "#6c63ff")
        uye_card = self.create_modern_card("👥 Toplam Üye", "0", "#4caf50")
        odunc_card = self.create_modern_card("📖 Aktif Ödünçler", "0", "#ff9800")
        gecikme_card = self.create_modern_card("💰 Gecikme Ücreti", "0 TL", "#ff5e5e")

        dashboard_layout.addWidget(kitap_card)
        dashboard_layout.addWidget(uye_card)
        dashboard_layout.addWidget(odunc_card)
        dashboard_layout.addWidget(gecikme_card)

        self.kitap_label = kitap_card.findChild(QLabel, "value_label")
        self.uye_label = uye_card.findChild(QLabel, "value_label")
        self.odunc_label = odunc_card.findChild(QLabel, "value_label")
        self.gecikme_label = gecikme_card.findChild(QLabel, "value_label")

        # Sekmeler
        self.tabs = QTabWidget()

        self.kitap_tab = self.create_kitap_tab()
        self.uye_tab = self.create_uye_tab()
        self.odunc_tab = self.create_odunc_tab()
        self.stats_widget = LibraryStatsWidget(self.db)
        self.rapor_tab = self.create_rapor_tab()

        self.tabs.addTab(self.kitap_tab, "📚 Kitaplar")
        self.tabs.addTab(self.uye_tab, "👥 Üyeler")
        self.tabs.addTab(self.odunc_tab, "📖 Ödünç İşlemleri")
        self.tabs.addTab(self.stats_widget, "📊 İstatistikler")
        self.tabs.addTab(self.rapor_tab, "📄 Raporlar")

        if self.kullanici['rol'] == 'admin':
            self.kullanici_tab = self.create_sistem_kullanici_tab()
            self.tabs.addTab(self.kullanici_tab, "👤 Kullanıcılar")

        main_layout.addWidget(header_frame)
        main_layout.addLayout(dashboard_layout)
        main_layout.addWidget(self.tabs)
        central_widget.setLayout(main_layout)

        # Timer ile otomatik yenileme
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(3000)  # 3 saniyede bir yenile

    def create_modern_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: #1a2350;
                border-radius: 15px;
                padding: 20px;
                min-width: 180px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(8)

        title_label = QLabel(title)
        title_font = QFont("Arial", 11, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"color: {color};")

        value_label = QLabel(value)
        value_font = QFont("Arial", 24, QFont.Bold)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")
        value_label.setObjectName("value_label")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def create_kitap_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Filtre paneli
        filter_panel = QFrame()
        filter_panel.setStyleSheet("background-color: #1a2350; border-radius: 10px; padding: 10px;")
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)

        filter_label = QLabel("Kategori Filtresi:")
        filter_label.setStyleSheet("color: #6c63ff; font-weight: bold;")
        filter_layout.addWidget(filter_label)

        self.kategori_filter = QComboBox()
        self.kategori_filter.addItem("Tüm Kategoriler")
        self.kategori_filter.addItems(self.db.kategorileri_getir())
        self.kategori_filter.currentTextChanged.connect(self.kitaplari_filtrele)
        filter_layout.addWidget(self.kategori_filter)

        filter_layout.addStretch()

        filter_panel.setLayout(filter_layout)
        layout.addWidget(filter_panel)

        # Buton paneli
        button_panel = QFrame()
        button_panel.setStyleSheet("background-color: #1a2350; border-radius: 10px; padding: 10px;")
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        ekle_btn = QPushButton("➕ Yeni Kitap Ekle")
        ekle_btn.clicked.connect(self.kitap_ekle)

        duzenle_btn = QPushButton("✏️ Kitap Düzenle")
        duzenle_btn.clicked.connect(self.kitap_duzenle)

        sil_btn = QPushButton("🗑️ Kitap Sil")
        sil_btn.setObjectName("danger")
        sil_btn.clicked.connect(self.kitap_sil)

        yenile_btn = QPushButton("🔄 Yenile")
        yenile_btn.clicked.connect(self.kitaplari_listele)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(duzenle_btn)
        button_layout.addWidget(sil_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()
        button_panel.setLayout(button_layout)

        self.kitap_table = QTableWidget()
        self.kitap_table.setColumnCount(8)
        self.kitap_table.setHorizontalHeaderLabels(["ID", "Kitap Adı", "Yazar", "Kategori", "Yıl", "Sayfa", "Dil", "Durum"])
        self.kitap_table.setAlternatingRowColors(True)
        self.kitap_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.kitap_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.kitap_table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(button_panel)
        layout.addWidget(self.kitap_table)
        widget.setLayout(layout)
        return widget

    def create_uye_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        button_panel = QFrame()
        button_panel.setStyleSheet("background-color: #1a2350; border-radius: 10px; padding: 10px;")
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        ekle_btn = QPushButton("➕ Yeni Üye Ekle")
        ekle_btn.clicked.connect(self.uye_ekle)

        duzenle_btn = QPushButton("✏️ Üye Düzenle")
        duzenle_btn.clicked.connect(self.uye_duzenle)

        sil_btn = QPushButton("🗑️ Üye Sil")
        sil_btn.setObjectName("danger")
        sil_btn.clicked.connect(self.uye_sil)

        yenile_btn = QPushButton("🔄 Yenile")
        yenile_btn.clicked.connect(self.uyeleri_listele)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(duzenle_btn)
        button_layout.addWidget(sil_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()
        button_panel.setLayout(button_layout)

        self.uye_table = QTableWidget()
        self.uye_table.setColumnCount(7)
        self.uye_table.setHorizontalHeaderLabels(["ID", "Üye No", "Ad", "Soyad", "Email", "Telefon", "Durum"])
        self.uye_table.setAlternatingRowColors(True)
        self.uye_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.uye_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.uye_table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(button_panel)
        layout.addWidget(self.uye_table)
        widget.setLayout(layout)
        return widget

    def create_odunc_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        # Durum filtresi
        filter_panel = QFrame()
        filter_panel.setStyleSheet("background-color: #1a2350; border-radius: 10px; padding: 10px;")
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)

        filter_label = QLabel("Durum:")
        filter_label.setStyleSheet("color: #6c63ff; font-weight: bold;")
        filter_layout.addWidget(filter_label)

        self.durum_filter = QComboBox()
        self.durum_filter.addItems(["Tümü", "Ödünçte", "İade Edildi"])
        self.durum_filter.currentTextChanged.connect(self.odunc_listele)
        filter_layout.addWidget(self.durum_filter)

        filter_layout.addStretch()

        filter_panel.setLayout(filter_layout)
        layout.addWidget(filter_panel)

        button_panel = QFrame()
        button_panel.setStyleSheet("background-color: #1a2350; border-radius: 10px; padding: 10px;")
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        odunc_ver_btn = QPushButton("🔖 Kitap Ödünç Ver")
        odunc_ver_btn.clicked.connect(self.odunc_ver)

        iade_al_btn = QPushButton("✅ Kitap İade Al")
        iade_al_btn.setObjectName("success")
        iade_al_btn.clicked.connect(self.iade_al)

        gecikme_btn = QPushButton("⚠️ Gecikmiş Kitaplar")
        gecikme_btn.clicked.connect(self.gecikmis_kitaplari_goster)

        yenile_btn = QPushButton("🔄 Yenile")
        yenile_btn.clicked.connect(self.odunc_listele)

        button_layout.addWidget(odunc_ver_btn)
        button_layout.addWidget(iade_al_btn)
        button_layout.addWidget(gecikme_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()
        button_panel.setLayout(button_layout)

        self.odunc_table = QTableWidget()
        self.odunc_table.setColumnCount(9)
        self.odunc_table.setHorizontalHeaderLabels(["ID", "Kitap", "Üye", "Ödünç Tarihi", "Son Tarih", "İade Tarihi", "Durum", "Gecikme Ücreti", "Üye No"])
        self.odunc_table.setAlternatingRowColors(True)
        self.odunc_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.odunc_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.odunc_table.setEditTriggers(QTableWidget.NoEditTriggers)

        layout.addWidget(button_panel)
        layout.addWidget(self.odunc_table)
        widget.setLayout(layout)
        return widget

    def create_rapor_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        button_panel = QFrame()
        button_panel.setStyleSheet("background-color: #1a2350; border-radius: 10px; padding: 10px;")
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        populer_kitap_btn = QPushButton("📊 En Çok Okunan Kitaplar")
        populer_kitap_btn.clicked.connect(self.populer_kitaplari_goster)

        aktif_uye_btn = QPushButton("🏆 En Aktif Üyeler")
        aktif_uye_btn.clicked.connect(self.aktif_uyeleri_goster)

        kapsamli_rapor_btn = QPushButton("📋 Kapsamlı Rapor Oluştur")
        kapsamli_rapor_btn.setStyleSheet("background-color: #6c63ff;")
        kapsamli_rapor_btn.clicked.connect(self.kapsamli_rapor)

        button_layout.addWidget(populer_kitap_btn)
        button_layout.addWidget(aktif_uye_btn)
        button_layout.addWidget(kapsamli_rapor_btn)
        button_layout.addStretch()
        button_panel.setLayout(button_layout)

        self.rapor_text = QTextEdit()
        self.rapor_text.setReadOnly(True)
        self.rapor_text.setStyleSheet("""
            QTextEdit {
                background-color: #1a2350;
                border: 1px solid #6c63ff;
                border-radius: 10px;
                padding: 15px;
                font-family: 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
            }
        """)

        layout.addWidget(button_panel)
        layout.addWidget(self.rapor_text)
        widget.setLayout(layout)
        return widget

    def create_sistem_kullanici_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)

        button_panel = QFrame()
        button_panel.setStyleSheet("background-color: #1a2350; border-radius: 10px; padding: 10px;")
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)

        ekle_btn = QPushButton("➕ Yeni Kullanıcı Ekle")
        ekle_btn.clicked.connect(self.sistem_kullanici_ekle)

        sil_btn = QPushButton("🗑️ Kullanıcı Sil")
        sil_btn.setObjectName("danger")
        sil_btn.clicked.connect(self.sistem_kullanici_sil)

        yenile_btn = QPushButton("🔄 Yenile")
        yenile_btn.clicked.connect(self.sistem_kullanici_listele)

        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(sil_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()
        button_panel.setLayout(button_layout)

        self.kullanici_table = QTableWidget()
        self.kullanici_table.setColumnCount(6)
        self.kullanici_table.setHorizontalHeaderLabels(["ID", "Kullanıcı Adı", "Ad", "Soyad", "Rol", "Durum"])
        self.kullanici_table.setAlternatingRowColors(True)
        self.kullanici_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(button_panel)
        layout.addWidget(self.kullanici_table)
        widget.setLayout(layout)
        return widget

    def load_data(self):
        self.kitaplari_listele()
        self.uyeleri_listele()
        self.odunc_listele()
        if self.kullanici['rol'] == 'admin':
            self.sistem_kullanici_listele()

    def refresh_all(self):
        self.kitaplari_listele()
        self.uyeleri_listele()
        self.odunc_listele()
        if self.kullanici['rol'] == 'admin':
            self.sistem_kullanici_listele()

        self.kitap_label.setText(str(self.db.toplam_kitap_sayisi()))
        self.uye_label.setText(str(self.db.toplam_uye_sayisi()))
        self.odunc_label.setText(str(self.db.aktif_odunc_sayisi()))
        self.gecikme_label.setText(f"{self.db.toplam_gecikme_ucreti():.2f} TL")

        self.stats_widget.update_charts()

    def arama_yap(self):
        arama_metni = self.search_input.text().strip().lower()

        if not arama_metni:
            self.kitaplari_listele()
            self.uyeleri_listele()
            self.odunc_listele()
            return

        # Kitaplarda ara
        self.kitap_table.setRowCount(0)
        for kitap in self.db.kitaplari_getir():
            if (arama_metni in kitap['ad'].lower() or
                arama_metni in kitap['yazar'].lower() or
                arama_metni in kitap['kategori'].lower()):
                row = self.kitap_table.rowCount()
                self.kitap_table.insertRow(row)
                self.kitap_table.setItem(row, 0, QTableWidgetItem(str(kitap['kitap_id'])))
                self.kitap_table.setItem(row, 1, QTableWidgetItem(kitap['ad']))
                self.kitap_table.setItem(row, 2, QTableWidgetItem(kitap['yazar']))
                self.kitap_table.setItem(row, 3, QTableWidgetItem(kitap['kategori']))
                self.kitap_table.setItem(row, 4, QTableWidgetItem(str(kitap['yayin_yili'] or "-")))
                self.kitap_table.setItem(row, 5, QTableWidgetItem(str(kitap['sayfa_sayisi'] or "-")))
                self.kitap_table.setItem(row, 6, QTableWidgetItem(kitap['dil']))
                durum_item = QTableWidgetItem(kitap['durum'])
                if kitap['durum'] == 'Mevcut':
                    durum_item.setForeground(QColor("#4caf50"))
                else:
                    durum_item.setForeground(QColor("#ff5e5e"))
                self.kitap_table.setItem(row, 7, durum_item)

        # Üyelerde ara
        self.uye_table.setRowCount(0)
        for uye in self.db.uyeleri_getir(arama_metni):
            row = self.uye_table.rowCount()
            self.uye_table.insertRow(row)
            self.uye_table.setItem(row, 0, QTableWidgetItem(str(uye['uye_id'])))
            self.uye_table.setItem(row, 1, QTableWidgetItem(uye['uye_no']))
            self.uye_table.setItem(row, 2, QTableWidgetItem(uye['ad']))
            self.uye_table.setItem(row, 3, QTableWidgetItem(uye['soyad']))
            self.uye_table.setItem(row, 4, QTableWidgetItem(uye['email']))
            self.uye_table.setItem(row, 5, QTableWidgetItem(uye['telefon']))
            durum_item = QTableWidgetItem(uye['durum'])
            if uye['durum'] == 'Aktif':
                durum_item.setForeground(QColor("#4caf50"))
            else:
                durum_item.setForeground(QColor("#ff5e5e"))
            self.uye_table.setItem(row, 6, durum_item)

    def kitaplari_filtrele(self):
        kategori = self.kategori_filter.currentText()
        if kategori == "Tüm Kategoriler":
            kitaplar = self.db.kitaplari_getir()
        else:
            kitaplar = self.db.kitaplari_getir(filtre=kategori)

        self.kitap_table.setRowCount(0)
        for kitap in kitaplar:
            row = self.kitap_table.rowCount()
            self.kitap_table.insertRow(row)
            self.kitap_table.setItem(row, 0, QTableWidgetItem(str(kitap['kitap_id'])))
            self.kitap_table.setItem(row, 1, QTableWidgetItem(kitap['ad']))
            self.kitap_table.setItem(row, 2, QTableWidgetItem(kitap['yazar']))
            self.kitap_table.setItem(row, 3, QTableWidgetItem(kitap['kategori']))
            self.kitap_table.setItem(row, 4, QTableWidgetItem(str(kitap['yayin_yili'] or "-")))
            self.kitap_table.setItem(row, 5, QTableWidgetItem(str(kitap['sayfa_sayisi'] or "-")))
            self.kitap_table.setItem(row, 6, QTableWidgetItem(kitap['dil']))
            durum_item = QTableWidgetItem(kitap['durum'])
            if kitap['durum'] == 'Mevcut':
                durum_item.setForeground(QColor("#4caf50"))
            else:
                durum_item.setForeground(QColor("#ff5e5e"))
            self.kitap_table.setItem(row, 7, durum_item)

    def kitaplari_listele(self):
        kitaplar = self.db.kitaplari_getir()

        self.kitap_table.setRowCount(0)
        for kitap in kitaplar:
            row = self.kitap_table.rowCount()
            self.kitap_table.insertRow(row)
            self.kitap_table.setItem(row, 0, QTableWidgetItem(str(kitap['kitap_id'])))
            self.kitap_table.setItem(row, 1, QTableWidgetItem(kitap['ad']))
            self.kitap_table.setItem(row, 2, QTableWidgetItem(kitap['yazar']))
            self.kitap_table.setItem(row, 3, QTableWidgetItem(kitap['kategori']))
            self.kitap_table.setItem(row, 4, QTableWidgetItem(str(kitap['yayin_yili'] or "-")))
            self.kitap_table.setItem(row, 5, QTableWidgetItem(str(kitap['sayfa_sayisi'] or "-")))
            self.kitap_table.setItem(row, 6, QTableWidgetItem(kitap['dil']))
            durum_item = QTableWidgetItem(kitap['durum'])
            if kitap['durum'] == 'Mevcut':
                durum_item.setForeground(QColor("#4caf50"))
            else:
                durum_item.setForeground(QColor("#ff5e5e"))
            self.kitap_table.setItem(row, 7, durum_item)

    def uyeleri_listele(self):
        uyeler = self.db.uyeleri_getir()

        self.uye_table.setRowCount(0)
        for uye in uyeler:
            row = self.uye_table.rowCount()
            self.uye_table.insertRow(row)
            self.uye_table.setItem(row, 0, QTableWidgetItem(str(uye['uye_id'])))
            self.uye_table.setItem(row, 1, QTableWidgetItem(uye['uye_no']))
            self.uye_table.setItem(row, 2, QTableWidgetItem(uye['ad']))
            self.uye_table.setItem(row, 3, QTableWidgetItem(uye['soyad']))
            self.uye_table.setItem(row, 4, QTableWidgetItem(uye['email']))
            self.uye_table.setItem(row, 5, QTableWidgetItem(uye['telefon']))
            durum_item = QTableWidgetItem(uye['durum'])
            if uye['durum'] == 'Aktif':
                durum_item.setForeground(QColor("#4caf50"))
            else:
                durum_item.setForeground(QColor("#ff5e5e"))
            self.uye_table.setItem(row, 6, durum_item)

    def odunc_listele(self):
        durum = self.durum_filter.currentText()
        if durum == "Tümü":
            odunc_list = self.db.odunc_listele()
        else:
            odunc_list = self.db.odunc_listele(durum=durum)

        self.odunc_table.setRowCount(0)
        for odunc in odunc_list:
            row = self.odunc_table.rowCount()
            self.odunc_table.insertRow(row)

            self.odunc_table.setItem(row, 0, QTableWidgetItem(str(odunc['odunc_id'])))
            self.odunc_table.setItem(row, 1, QTableWidgetItem(odunc['kitap_adi']))
            self.odunc_table.setItem(row, 2, QTableWidgetItem(f"{odunc['uye_adi']} {odunc.get('uye_soyad', '')}"))

            odunc_tarihi = datetime.fromisoformat(odunc['odunc_tarihi'].replace(' ', 'T')) if odunc['odunc_tarihi'] else None
            self.odunc_table.setItem(row, 3, QTableWidgetItem(odunc_tarihi.strftime("%d.%m.%Y") if odunc_tarihi else "-"))

            son_tarih = datetime.fromisoformat(odunc['son_tarih'].replace(' ', 'T')) if odunc['son_tarih'] else None
            son_tarih_item = QTableWidgetItem(son_tarih.strftime("%d.%m.%Y") if son_tarih else "-")
            if son_tarih and son_tarih < datetime.now() and odunc['durum'] == 'Ödünçte':
                son_tarih_item.setForeground(QColor("#ff5e5e"))
            self.odunc_table.setItem(row, 4, son_tarih_item)

            iade_tarihi = datetime.fromisoformat(odunc['iade_tarihi'].replace(' ', 'T')) if odunc['iade_tarihi'] else None
            self.odunc_table.setItem(row, 5, QTableWidgetItem(iade_tarihi.strftime("%d.%m.%Y") if iade_tarihi else "-"))

            durum_item = QTableWidgetItem(odunc['durum'])
            if odunc['durum'] == 'Ödünçte':
                durum_item.setForeground(QColor("#ff9800"))
            else:
                durum_item.setForeground(QColor("#4caf50"))
            self.odunc_table.setItem(row, 6, durum_item)

            self.odunc_table.setItem(row, 7, QTableWidgetItem(f"{odunc['gecikme_ucreti']:.2f} TL" if odunc['gecikme_ucreti'] else "0.00 TL"))
            self.odunc_table.setItem(row, 8, QTableWidgetItem(odunc.get('uye_no', '-')))

    def kitap_ekle(self):
        dialog = KitapEkleDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            try:
                self.db.kitap_ekle(*dialog.result)
                QMessageBox.information(self, "Başarılı", "📚 Kitap başarıyla eklendi!")
                self.kitaplari_listele()
                self.kategori_filter.clear()
                self.kategori_filter.addItem("Tüm Kategoriler")
                self.kategori_filter.addItems(self.db.kategorileri_getir())
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Kitap eklenirken hata oluştu: {str(e)}")

    def kitap_duzenle(self):
        row = self.kitap_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek kitabı seçin!")
            return

        kitap_id = int(self.kitap_table.item(row, 0).text())
        kitap = self.db.kitap_getir(kitap_id)

        if not kitap:
            QMessageBox.warning(self, "Hata", "Kitap bulunamadı!")
            return

        dialog = KitapDuzenleDialog(self.db, kitap, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            try:
                self.db.kitap_guncelle(*dialog.result)
                QMessageBox.information(self, "Başarılı", "✏️ Kitap başarıyla güncellendi!")
                self.kitaplari_listele()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Kitap güncellenirken hata oluştu: {str(e)}")

    def kitap_sil(self):
        row = self.kitap_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek kitabı seçin!")
            return

        kitap_id = int(self.kitap_table.item(row, 0).text())
        kitap_adi = self.kitap_table.item(row, 1).text()

        reply = QMessageBox.question(self, "Onay", f"'{kitap_adi}' kitabını silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                self.db.kitap_sil(kitap_id)
                QMessageBox.information(self, "Başarılı", "Kitap silindi!")
                self.kitaplari_listele()
            except ValueError as e:
                QMessageBox.warning(self, "Hata", str(e))

    def uye_ekle(self):
        dialog = UyeEkleDialog(self.db, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            try:
                self.db.uye_ekle(*dialog.result)
                QMessageBox.information(self, "Başarılı", "👤 Üye başarıyla eklendi!")
                self.uyeleri_listele()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Hata", "Bu üye numarası veya email adresi zaten kayıtlı!")

    def uye_duzenle(self):
        row = self.uye_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen düzenlenecek üyeyi seçin!")
            return

        uye_id = int(self.uye_table.item(row, 0).text())
        uye = self.db.uye_getir(uye_id)

        if not uye:
            QMessageBox.warning(self, "Hata", "Üye bulunamadı!")
            return

        dialog = UyeDuzenleDialog(self.db, uye, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            try:
                self.db.uye_guncelle(*dialog.result)
                QMessageBox.information(self, "Başarılı", "✏️ Üye başarıyla güncellendi!")
                self.uyeleri_listele()
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Üye güncellenirken hata oluştu: {str(e)}")

    def uye_sil(self):
        row = self.uye_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek üyeyi seçin!")
            return

        uye_id = int(self.uye_table.item(row, 0).text())
        uye_adi = f"{self.uye_table.item(row, 2).text()} {self.uye_table.item(row, 3).text()}"

        reply = QMessageBox.question(self, "Onay", f"'{uye_adi}' üyesini silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            try:
                self.db.uye_sil(uye_id)
                QMessageBox.information(self, "Başarılı", "Üye silindi!")
                self.uyeleri_listele()
            except ValueError as e:
                QMessageBox.warning(self, "Hata", str(e))

    def odunc_ver(self):
        kitaplar = self.db.kitaplari_getir()
        mevcut_kitaplar = [k for k in kitaplar if k['durum'] == 'Mevcut']

        if not mevcut_kitaplar:
            QMessageBox.warning(self, "Uyarı", "Ödünç verilebilecek kitap bulunamadı!")
            return

        uyeler = self.db.uyeleri_getir()
        if not uyeler:
            QMessageBox.warning(self, "Uyarı", "Kayıtlı üye bulunamadı!")
            return

        dialog = OduncVerDialog(self.db, mevcut_kitaplar, uyeler, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            kitap_id, uye_id, sure = dialog.result
            try:
                self.db.odunc_ver(kitap_id, uye_id, sure)
                QMessageBox.information(self, "Başarılı", "🔖 Kitap ödünç verildi!")
                self.kitaplari_listele()
                self.odunc_listele()
                self.refresh_all()
            except ValueError as e:
                QMessageBox.warning(self, "Hata", str(e))

    def iade_al(self):
        odunc_list = self.db.odunc_listele(durum="Ödünçte")
        if not odunc_list:
            QMessageBox.warning(self, "Uyarı", "İade edilecek kitap bulunamadı!")
            return

        dialog = IadeAlDialog(self.db, odunc_list, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            odunc_id = dialog.result
            try:
                gecikme_ucreti = self.db.iade_al(odunc_id)
                if gecikme_ucreti > 0:
                    QMessageBox.information(self, "İade Tamamlandı", f"✅ Kitap iade alındı!\nGecikme ücreti: {gecikme_ucreti:.2f} TL")
                else:
                    QMessageBox.information(self, "Başarılı", "✅ Kitap iade alındı!")
                self.kitaplari_listele()
                self.odunc_listele()
                self.refresh_all()
            except ValueError as e:
                QMessageBox.warning(self, "Hata", str(e))

    def gecikmis_kitaplari_goster(self):
        gecikmeler = self.db.gecikmeli_kitaplari_getir()

        if not gecikmeler:
            QMessageBox.information(self, "Bilgi", "Gecikmiş kitap bulunamadı!")
            return

        mesaj = "⚠️ GECİKMİŞ KİTAPLAR ⚠️\n\n"
        for g in gecikmeler:
            son_tarih = datetime.fromisoformat(g['son_tarih'].replace(' ', 'T')) if g['son_tarih'] else None
            if son_tarih:
                gecikme_gunu = (datetime.now() - son_tarih).days
                ucret = gecikme_gunu * 5
                mesaj += f"📖 {g['kitap_adi']}\n"
                mesaj += f"👤 {g['uye_adi']} {g['uye_soyad']}\n"
                mesaj += f"📞 {g['telefon']}\n"
                mesaj += f"⏰ {gecikme_gunu} gün gecikmeli (Ücret: {ucret} TL)\n"
                mesaj += "-" * 40 + "\n"

        QMessageBox.warning(self, "Gecikmiş Kitaplar", mesaj)

    def populer_kitaplari_goster(self):
        populer = self.db.en_cok_okunan_kitaplar(10)

        if not populer:
            QMessageBox.information(self, "Bilgi", "Henüz ödünç verilmiş kitap yok!")
            return

        mesaj = "📊 EN ÇOK OKUNAN KİTAPLAR 📊\n\n"
        for i, kitap in enumerate(populer, 1):
            mesaj += f"{i}. {kitap['ad']} - {kitap['yazar']}\n"
            mesaj += f"   📖 {kitap['odunc_sayisi']} kez ödünç alındı\n\n"

        self.rapor_text.setText(mesaj)
        self.tabs.setCurrentIndex(4)

    def aktif_uyeleri_goster(self):
        aktif = self.db.en_aktif_uyeler(10)

        if not aktif:
            QMessageBox.information(self, "Bilgi", "Henüz ödünç işlemi yapılmamış!")
            return

        mesaj = "🏆 EN AKTİF ÜYELER 🏆\n\n"
        for i, uye in enumerate(aktif, 1):
            mesaj += f"{i}. {uye['ad']} {uye['soyad']} ({uye['uye_no']})\n"
            mesaj += f"   📚 {uye['kitap_sayisi']} kitap okudu\n\n"

        self.rapor_text.setText(mesaj)
        self.tabs.setCurrentIndex(4)

    def kapsamli_rapor(self):
        rapor = "╔" + "═" * 70 + "╗\n"
        rapor += "║" + " " * 15 + "📚 DİJİTAL KÜTÜPHANE SİSTEMİ RAPORU" + " " * 15 + "║\n"
        rapor += "╚" + "═" * 70 + "╝\n\n"

        rapor += "┌" + "─" * 45 + "┐\n"
        rapor += "│ " + " " * 12 + "📊 GENEL İSTATİSTİKLER" + " " * 18 + "│\n"
        rapor += "├" + "─" * 45 + "┤\n"
        rapor += f"│ Toplam Kitap Sayısı           : {self.db.toplam_kitap_sayisi():>15} │\n"
        rapor += f"│ Mevcut Kitap Sayısı           : {self.db.mevcut_kitap_sayisi():>15} │\n"
        rapor += f"│ Ödünçteki Kitap Sayısı        : {self.db.oduncte_kitap_sayisi():>15} │\n"
        rapor += f"│ Toplam Üye Sayısı             : {self.db.toplam_uye_sayisi():>15} │\n"
        rapor += f"│ Toplam Ödünç Sayısı           : {self.db.toplam_odunc_sayisi():>15} │\n"
        rapor += f"│ Aktif Ödünç Sayısı            : {self.db.aktif_odunc_sayisi():>15} │\n"
        rapor += f"│ Toplam Gecikme Ücreti         : {self.db.toplam_gecikme_ucreti():>15,.2f} TL │\n"
        rapor += "└" + "─" * 45 + "┘\n\n"

        rapor += "┌" + "─" * 45 + "┐\n"
        rapor += "│ " + " " * 13 + "📚 KATEGORİ DAĞILIMI" + " " * 18 + "│\n"
        rapor += "├" + "─" * 45 + "┤\n"
        for kat in self.db.kategori_dagilimi()[:8]:
            rapor += f"│ {kat['kategori']:<20} : {kat['sayi']:>3} kitap{' ' * (45 - 24 - len(str(kat['sayi'])))}│\n"
        rapor += "└" + "─" * 45 + "┘\n\n"

        rapor += "┌" + "─" * 45 + "┐\n"
        rapor += "│ " + " " * 12 + "📖 EN POPÜLER 5 KİTAP" + " " * 20 + "│\n"
        rapor += "├" + "─" * 45 + "┤\n"
        for i, kitap in enumerate(self.db.en_cok_okunan_kitaplar(5), 1):
            rapor += f"│ {i}. {kitap['ad'][:28]:<28} : {kitap['odunc_sayisi']:>2} kez │\n"
        rapor += "└" + "─" * 45 + "┘\n\n"

        rapor += "┌" + "─" * 45 + "┐\n"
        rapor += "│ " + " " * 12 + "🏆 EN AKTİF 5 ÜYE" + " " * 22 + "│\n"
        rapor += "├" + "─" * 45 + "┤\n"
        for i, uye in enumerate(self.db.en_aktif_uyeler(5), 1):
            rapor += f"│ {i}. {uye['ad']} {uye['soyad'][:18]:<18} : {uye['kitap_sayisi']:>2} kitap │\n"
        rapor += "└" + "─" * 45 + "┘\n"

        self.rapor_text.setText(rapor)
        self.tabs.setCurrentIndex(4)

    def sistem_kullanici_ekle(self):
        dialog = SistemKullaniciDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            try:
                self.db.kullanici_ekle(*dialog.result)
                QMessageBox.information(self, "Başarılı", "👤 Sistem kullanıcısı eklendi!")
                self.sistem_kullanici_listele()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Hata", "Bu kullanıcı adı zaten var!")

    def sistem_kullanici_sil(self):
        row = self.kullanici_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen silinecek kullanıcıyı seçin!")
            return

        kullanici_id = int(self.kullanici_table.item(row, 0).text())
        kullanici_adi = self.kullanici_table.item(row, 1).text()

        if kullanici_adi == "admin":
            QMessageBox.warning(self, "Hata", "Admin kullanıcısı silinemez!")
            return
        if kullanici_adi == self.kullanici['kullanici_adi']:
            QMessageBox.warning(self, "Hata", "Kendi hesabınızı silemezsiniz!")
            return

        reply = QMessageBox.question(self, "Onay", f"'{kullanici_adi}' kullanıcısını silmek istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.db.kullanici_sil(kullanici_id)
            QMessageBox.information(self, "Başarılı", "Kullanıcı silindi!")
            self.sistem_kullanici_listele()

    def sistem_kullanici_listele(self):
        self.kullanici_table.setRowCount(0)
        for k in self.db.kullanicilari_getir():
            row = self.kullanici_table.rowCount()
            self.kullanici_table.insertRow(row)
            self.kullanici_table.setItem(row, 0, QTableWidgetItem(str(k['kullanici_id'])))
            self.kullanici_table.setItem(row, 1, QTableWidgetItem(k['kullanici_adi']))
            self.kullanici_table.setItem(row, 2, QTableWidgetItem(k['ad']))
            self.kullanici_table.setItem(row, 3, QTableWidgetItem(k['soyad']))
            self.kullanici_table.setItem(row, 4, QTableWidgetItem(k['rol']))
            durum_item = QTableWidgetItem(k['durum'])
            if k['durum'] == 'Aktif':
                durum_item.setForeground(QColor("#4caf50"))
            else:
                durum_item.setForeground(QColor("#ff5e5e"))
            self.kullanici_table.setItem(row, 5, durum_item)

    def cikis_yap(self):
        reply = QMessageBox.question(self, "Çıkış", "Oturumu kapatmak istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()
            self.yeni_giris()

    def yeni_giris(self):
        login = LoginDialog(self.db)
        if login.exec_() == QDialog.Accepted and login.kullanici:
            self.kullanici = login.kullanici
            self.setWindowTitle(f"📚 Dijital Kütüphane - Hoşgeldiniz, {self.kullanici['ad']} {self.kullanici['soyad']}")

            # Kullanıcı bilgisini güncelle
            for widget in self.centralWidget().findChildren(QLabel):
                if "👤" in widget.text() and "[" in widget.text():
                    widget.setText(f"👤 {self.kullanici['ad']} {self.kullanici['soyad']} [{self.kullanici['rol']}]")

            admin_sekme_var = any("Kullanıcılar" in self.tabs.tabText(i) for i in range(self.tabs.count()))

            if self.kullanici['rol'] == 'admin' and not admin_sekme_var:
                self.kullanici_tab = self.create_sistem_kullanici_tab()
                self.tabs.addTab(self.kullanici_tab, "👤 Kullanıcılar")
            elif self.kullanici['rol'] != 'admin' and admin_sekme_var:
                for i in range(self.tabs.count()):
                    if "Kullanıcılar" in self.tabs.tabText(i):
                        self.tabs.removeTab(i)
                        break

            self.load_data()
            self.show()
        else:
            sys.exit()


# ============ MAIN ============

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    db = DatabaseManager()

    login = LoginDialog(db)
    if login.exec_() == QDialog.Accepted:
        kullanici = login.kullanici
        window = LibraryMainWindow(kullanici, db)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()


if __name__ == "__main__":
    main()
