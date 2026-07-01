# Backend/database/seed_data.py
import os
import sys
import random
from datetime import datetime, timedelta
import mysql.connector
from faker import Faker

# Dodajemy wyższy katalog do ścieżki, aby móc zaimportować configLoader
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configLoader import loadConfig

# Inicjalizacja Fakera z polską lokalizacją
fake = Faker('pl_PL')

# Słownik z kategoriami i przykładowymi produktami (Imitacja Allegro)
PRODUKTY_MOCK = {
    "Elektronika": [
        ("Smartfon 5G 128GB", 1499.99), ("Słuchawki bezprzewodowe ANC", 299.00),
        ("Ładowarka indukcyjna 15W", 79.90), ("Telewizor 55 cali 4K SmartTV", 2499.00),
        ("Konsola do gier NextGen", 2199.00), ("Powerbank 20000mAh", 119.00),
        ("Myszka bezprzewodowa ergonomiczna", 149.00), ("Klawiatura mechaniczna RGB", 249.00)
    ],
    "Moda": [
        ("Koszulka bawełniana męska", 59.99), ("Sukienka letnia w kwiaty", 129.90),
        ("Buty sportowe do biegania", 349.00), ("Kurtka zimowa puchowa", 450.00),
        ("Skórzany pasek do spodni", 89.00), ("Ciepła bluza z kapturem", 159.00),
        ("Skarpetki bambusowe 5-pak", 39.99), ("Okulary przeciwsłoneczne UV400", 79.00)
    ],
    "Dom i Ogród": [
        ("Kosiarka spalinowa z napędem", 1250.00), ("Zestaw garnków stalowych (10 el.)", 399.00),
        ("Wiertarka udarowa 800W", 189.00), ("Nowoczesna lampa stojąca", 149.90),
        ("Ergonomiczny fotel biurowy", 549.00), ("Zestaw narzędzi ogrodowych", 99.00),
        ("Patelnia nieprzywierająca 28cm", 85.00), ("Koc puszysty mikrofibra", 69.90)
    ],
    "Motoryzacja": [
        ("Wycieraczki samochodowe komplet", 65.00), ("Olej silnikowy 5W30 5L", 179.00),
        ("Opony zimowe komplet 16 cali", 1150.00), ("Wideorejestrator jazdy FullDH", 249.00),
        ("Pokrowce na fotele samochodowe", 139.00), ("Zestaw kluczy nasadowych", 320.00),
        ("Szampon samochodowy z woskiem", 29.90), ("Alkomat elektrochemiczny", 199.00)
    ],
    "Książki i Rozrywka": [
        ("Powieść kryminalna (Bestseller)", 39.90), ("Podręcznik: Python od podstaw", 69.00),
        ("Biografia znanego sportowca", 45.00), ("Gra planszowa strategiczna", 149.00),
        ("Komiks Uniwersum polskie wydanie", 59.90), ("Puzzle 1000 elementów Krajobraz", 34.90)
    ]
}

WOJEWODZTWA = [
    "Mazowieckie", "Małopolskie", "Wielkopolskie", "Śląskie", "Dolnośląskie",
    "Pomorskie", "Łódzkie", "Zachodniopomorskie", "Kujawsko-Pomorskie",
    "Lubelskie", "Podkarpackie", "Opolskie", "Lubuskie", "Podlaskie",
    "Świętokrzyskie", "Warmińsko-Mazurskie"
]

STATUSY_ZAMOWIENA = ['Nowe', 'Oplacone', 'W realizacji', 'Wyslane', 'Dostarczone', 'Anulowane', 'Zwrot']
METODY_PLATNOSCI = ['BLIK', 'Karta', 'Przelew', 'Za pobraniem']
TYPY_KONTA = ['Standard', 'Premium', 'Firma']


def generuj_baze_danych(liczba_klientow=50, liczba_zamowien=250):
    # Wczytanie konfiguracji z pliku config.txt (używamy ROOT, by mieć pełne prawa zapisu)
    backend_config = loadConfig('config.txt')

    try:
        conn = mysql.connector.connect(
            host=backend_config.get("DB_HOST_ROOT", "127.0.0.1"),
            user=backend_config.get("DB_USER_ROOT", "root"),
            password=backend_config.get("DB_PASSWORD_ROOT", "root_password"),
            database=backend_config.get("DB_NAME", "e_commerce_db")
        )
        cursor = conn.cursor()
        print("[SEEDER] Połączono pomyślnie z bazą MySQL.")

        # 1. GENEROWANIE KLIENTÓW
        print(f"[SEEDER] Generowanie {liczba_klientow} fikcyjnych klientów...")
        klienci_ids = []

        for _ in range(liczba_klientow):
            imie = fake.first_name()
            nazwisko = fake.last_name()
            email = fake.unique.email()
            telefon = fake.phone_number()
            miasto = fake.city()
            wojewodztwo = random.choice(WOJEWODZTWA)
            # Rejestracja w ciągu ostatnich 2 lat
            data_rejestracji = datetime.now() - timedelta(days=random.randint(1, 730))
            typ_konta = random.choice(TYPY_KONTA)
            status_konta = random.choices(['Aktywne', 'Zablokowane', 'Niezweryfikowane'], weights=[90, 5, 5], k=1)[0]

            sql = """INSERT INTO klienci (imie, nazwisko, email, telefon, miasto, wojewodztwo, data_rejestracji, \
                                          typ_konta, status_konta)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            val = (imie, nazwisko, email, telefon, miasto, wojewodztwo, data_rejestracji, typ_konta, status_konta)

            cursor.execute(sql, val)
            klienci_ids.append(cursor.lastrowid)

        conn.commit()
        print("[SEEDER] Klienci zostali pomyślnie dodani.")

        # 2. GENEROWANIE ZAMÓWIEŃ
        print(f"[SEEDER] Generowanie {liczba_zamowien} fikcyjnych zamówień...")

        for i in range(liczba_zamowien):
            id_klienta = random.choice(klienci_ids)
            numer_zamowienia = f"ZA-{datetime.now().year}-{1000 + i}"

            # Data zamówienia musi być późniejsza niż data rejestracji (losowo w ciągu ostatnich 6 miesięcy)
            data_zamowienia = datetime.now() - timedelta(days=random.randint(1, 180), hours=random.randint(0, 23))
            status_zamowienia = random.choices(STATUSY_ZAMOWIENA, weights=[10, 20, 15, 20, 25, 5, 5], k=1)[0]

            # Wybór losowej kategorii i produktu z tej kategorii
            kategoria = random.choice(list(PRODUKTY_MOCK.keys()))
            produkt = random.choice(PRODUKTY_MOCK[kategoria])
            produkt_nazwa = produkt[0]
            cena_jednostkowa = produkt[1]

            ilosc = random.choices([1, 2, 3], weights=[85, 12, 3], k=1)[0]
            koszt_dostawy = 0.00 if random.random() > 0.5 else 14.99  # Co drugie zamówienie ma darmową dostawę (np. Smart)
            metoda_platnosci = random.choice(METODY_PLATNOSCI)

            sql = """INSERT INTO zamowienia (id_klienta, numer_zamowienia, data_zamowienia, status_zamowienia, \
                                             produkt_nazwa, kategoria, cena_jednostkowa, ilosc, koszt_dostawy, \
                                             metoda_platnosci)
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            val = (id_klienta, numer_zamowienia, data_zamowienia, status_zamowienia, produkt_nazwa, kategoria,
                   cena_jednostkowa, ilosc, koszt_dostawy, metoda_platnosci)

            cursor.execute(sql, val)

        conn.commit()
        print(f"[SEEDER] Pomyślnie zasilono bazę {liczba_zamowien} zamówieniami!")

        cursor.close()
        conn.close()
        print("[SEEDER] Zamknięto połączenie z bazą danych.")

    except mysql.connector.Error as err:
        print(f"[SEEDER] BŁĄD PODCZAS SEEDOWANIA: {err}")


if __name__ == "__main__":
    # Domyślnie generujemy 60 klientów i 300 zamówień
    generuj_baze_danych(liczba_klientow=60, liczba_zamowien=300)