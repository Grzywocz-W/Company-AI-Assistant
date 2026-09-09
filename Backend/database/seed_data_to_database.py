# Backend/database/seed_data_to_database.py
import os
import sys
import random
from datetime import datetime, timedelta
import mysql.connector
from faker import Faker

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configLoader import loadConfig

fake = Faker('pl_PL')

# Słownik produktów: kategoria -> lista (nazwa, cena)
PRODUKTY_MOCK = {
    "Elektronika": [
        ("Smartfon 5G 128GB", 1499.99),
        ("Słuchawki bezprzewodowe ANC", 299.00),
        ("Ładowarka indukcyjna 15W", 79.90),
        ("Telewizor 55 cali 4K SmartTV", 2499.00),
        ("Konsola do gier NextGen", 2199.00),
        ("Powerbank 20000mAh", 119.00),
        ("Myszka bezprzewodowa ergonomiczna", 149.00),
        ("Klawiatura mechaniczna RGB", 249.00)
    ],
    "Moda": [
        ("Koszulka bawełniana męska", 59.99),
        ("Sukienka letnia w kwiaty", 129.90),
        ("Buty sportowe do biegania", 349.00),
        ("Kurtka zimowa puchowa", 450.00),
        ("Skórzany pasek do spodni", 89.00),
        ("Ciepła bluza z kapturem", 159.00),
        ("Skarpetki bambusowe 5-pak", 39.99),
        ("Okulary przeciwsłoneczne UV400", 79.00)
    ],
    "Dom i Ogród": [
        ("Kosiarka spalinowa z napędem", 1250.00),
        ("Zestaw garnków stalowych (10 el.)", 399.00),
        ("Wiertarka udarowa 800W", 189.00),
        ("Nowoczesna lampa stojąca", 149.90),
        ("Ergonomiczny fotel biurowy", 549.00),
        ("Zestaw narzędzi ogrodowych", 99.00),
        ("Patelnia nieprzywierająca 28cm", 85.00),
        ("Koc puszysty mikrofibra", 69.90)
    ],
    "Motoryzacja": [
        ("Wycieraczki samochodowe komplet", 65.00),
        ("Olej silnikowy 5W30 5L", 179.00),
        ("Opony zimowe komplet 16 cali", 1150.00),
        ("Wideorejestrator jazdy FullHD", 249.00),
        ("Pokrowce na fotele samochodowe", 139.00),
        ("Zestaw kluczy nasadowych", 320.00),
        ("Szampon samochodowy z woskiem", 29.90),
        ("Alkomat elektrochemiczny", 199.00)
    ],
    "Ksiazki i Rozrywka": [
        ("Powieść kryminalna (Bestseller)", 39.90),
        ("Podręcznik: Python od podstaw", 69.00),
        ("Biografia znanego sportowca", 45.00),
        ("Gra planszowa strategiczna", 149.00),
        ("Komiks Uniwersum polskie wydanie", 59.90),
        ("Puzzle 1000 elementów Krajobraz", 34.90)
    ]
}

WOJEWODZTWA = [
    "Mazowieckie", "Małopolskie", "Wielkopolskie", "Śląskie", "Dolnośląskie",
    "Pomorskie", "Łódzkie", "Zachodniopomorskie", "Kujawsko-Pomorskie",
    "Lubelskie", "Podkarpackie", "Opolskie", "Lubuskie", "Podlaskie",
    "Świętokrzyskie", "Warmińsko-Mazurskie"
]

STATUSY_ZAMOWIENIA = [
    'Nowe', 'Oplacone', 'W realizacji',
    'Wyslane', 'Dostarczone', 'Anulowane', 'Zwrot'
]
METODY_PLATNOSCI = ['BLIK', 'Karta', 'Przelew', 'Za pobraniem']
TYPY_KONTA = ['Standard', 'Premium', 'Firma']


def generuj_baze_danych(liczba_klientow=60, liczba_zamowien=300):
    backend_config = loadConfig('config.txt')
    try:
        conn = mysql.connector.connect(
            host=backend_config.get("DB_HOST_ADMIN", "127.0.0.1"),
            user=backend_config.get("DB_USER_ADMIN", "agent_admin"),
            password=backend_config.get("DB_PASSWORD_ADMIN", "haslo_admina"),
            database=backend_config.get("DB_NAME", "e_commerce_db")
        )
        cursor = conn.cursor()
        print("[SEEDER] Połączono pomyślnie z bazą MySQL.")

        # ETAP 1: GENEROWANIE KLIENTÓW
        print(f"[SEEDER] Generowanie {liczba_klientow} fikcyjnych klientów...")
        klienci_ids = []

        for _ in range(liczba_klientow):
            imie = fake.first_name()
            nazwisko = fake.last_name()
            email = fake.unique.email()
            telefon = fake.phone_number()
            miasto = fake.city()
            wojewodztwo = random.choice(WOJEWODZTWA)
            data_rejestracji = datetime.now() - timedelta(days=random.randint(1, 730))
            typ_konta = random.choice(TYPY_KONTA)
            status_konta = random.choices(
                ['Aktywne', 'Zablokowane', 'Niezweryfikowane'],
                weights=[90, 5, 5],
                k=1
            )[0]

            # Zadłużenie: 70% klientów ma 0 zł, 30% ma losowe zadłużenie do 3000 zł
            # Ta kolumna będzie używana przez sieć neuronową jako feature
            if random.random() > 0.70:
                stan_zadluzenia = round(random.uniform(50.00, 3000.00), 2)
            else:
                stan_zadluzenia = 0.00

            sql = """
                INSERT INTO klienci (
                    imie, nazwisko, email, telefon, miasto, wojewodztwo,
                    data_rejestracji, typ_konta, status_konta, stan_zadluzenia
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (
                imie, nazwisko, email, telefon, miasto, wojewodztwo,
                data_rejestracji, typ_konta, status_konta, stan_zadluzenia
            )
            cursor.execute(sql, val)
            klienci_ids.append(cursor.lastrowid)

        conn.commit()
        print("[SEEDER] Klienci zostali pomyślnie dodani.")


        # ETAP 2: GENEROWANIE PRODUKTÓW
        print("[SEEDER] Generowanie produktów do tabeli 'produkty'...")

        # Słownik: (nazwa_produktu, kategoria) -> id_produktu (do użycia przy zamówieniach)
        produkty_ids = {}

        for kategoria, lista_produktow in PRODUKTY_MOCK.items():
            for nazwa_produktu, _ in lista_produktow:
                sql = """
                    INSERT INTO produkty (nazwa_produktu, kategoria_produktu)
                    VALUES (%s, %s)
                """
                cursor.execute(sql, (nazwa_produktu, kategoria))
                # Zapisujemy id wstawionego produktu pod kluczem (nazwa, kategoria)
                produkty_ids[(nazwa_produktu, kategoria)] = cursor.lastrowid

        conn.commit()
        print(f"[SEEDER] Dodano {len(produkty_ids)} produktów do bazy.")


        # ETAP 3: GENEROWANIE ZAMÓWIEŃ
        print(f"[SEEDER] Generowanie {liczba_zamowien} fikcyjnych zamówień...")

        for i in range(liczba_zamowien):
            id_klienta = random.choice(klienci_ids)
            numer_zamowienia = f"ZA-{datetime.now().year}-{1000 + i}"
            data_zamowienia = datetime.now() - timedelta(
                days=random.randint(1, 180),
                hours=random.randint(0, 23)
            )
            status_zamowienia = random.choices(
                STATUSY_ZAMOWIENIA,
                weights=[10, 20, 15, 20, 25, 5, 5],
                k=1
            )[0]

            # Losujemy kategorię, a potem produkt z tej kategorii
            kategoria = random.choice(list(PRODUKTY_MOCK.keys()))
            produkt_nazwa, cena_jednostkowa = random.choice(PRODUKTY_MOCK[kategoria])

            # Pobieramy id_produktu z wcześniej wygenerowanego słownika
            id_produktu = produkty_ids[(produkt_nazwa, kategoria)]

            ilosc = random.choices([1, 2, 3], weights=[85, 12, 3], k=1)[0]
            koszt_dostawy = 0.00 if random.random() > 0.5 else 14.99
            metoda_platnosci = random.choice(METODY_PLATNOSCI)

            sql = """
                INSERT INTO zamowienia (
                    id_klienta, id_produktu, numer_zamowienia,
                    data_zamowienia, status_zamowienia,
                    cena_jednostkowa, ilosc, koszt_dostawy, metoda_platnosci
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (
                id_klienta, id_produktu, numer_zamowienia,
                data_zamowienia, status_zamowienia,
                cena_jednostkowa, ilosc, koszt_dostawy, metoda_platnosci
            )
            cursor.execute(sql, val)

        conn.commit()
        print(f"[SEEDER] Pomyślnie zasilono bazę {liczba_zamowien} zamówieniami!")

        cursor.close()
        conn.close()
        print("[SEEDER] Zamknięto połączenie z bazą danych. Seedowanie zakończone sukcesem.")

    except mysql.connector.Error as err:
        print(f"[SEEDER] BŁĄD PODCZAS SEEDOWANIA: {err}")
        if conn.is_connected():
            conn.rollback()
            cursor.close()
            conn.close()


if __name__ == "__main__":
    generuj_baze_danych(liczba_klientow=100, liczba_zamowien=300)