# Backend/neural_network/generate_training_dataset.py
import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configLoader import loadConfig


# Mapowanie typu konta na wartość numeryczną dla sieci
TYP_KONTA_MAP = {
    'Standard': 0,
    'Premium': 1,
    'Firma': 2
}

def pobierz_dane_z_bazy() -> pd.DataFrame:
    """
    Pobiera z bazy danych wszystkie potrzebne dane o klientach
    i ich zamówieniach, a następnie agreguje je do jednego wiersza
    na klienta — gotowego jako wejście do sieci neuronowej.
    """
    import mysql.connector

    backend_config = loadConfig('config.txt')

    conn = mysql.connector.connect(
        host=backend_config.get("DB_HOST_ADMIN", "127.0.0.1"),
        user=backend_config.get("DB_USER_ADMIN", "agent_admin"),
        password=backend_config.get("DB_PASSWORD_ADMIN", "haslo_admina"),
        database=backend_config.get("DB_NAME", "e_commerce_db")
    )
    cursor = conn.cursor(dictionary=True)

    # Główne zapytanie agregujące dane klienta i jego zamówień
    # Każdy wiersz wyniku = jeden klient z wyliczonymi statystykami
    query = """
        SELECT
            k.id_klienta,
            k.stan_zadluzenia,
            k.typ_konta,
            DATEDIFF(NOW(), k.data_rejestracji)            AS dni_jako_klient,
            COUNT(z.id_zamowienia)                          AS liczba_zamowien,
            COALESCE(
                SUM(z.cena_jednostkowa * z.ilosc + z.koszt_dostawy),
                0.00
            )                                               AS suma_wydatkow,
            COALESCE(
                SUM(CASE WHEN z.status_zamowienia = 'Zwrot'     THEN 1 ELSE 0 END),
                0
            )                                               AS liczba_zwrotow,
            COALESCE(
                SUM(CASE WHEN z.status_zamowienia = 'Anulowane' THEN 1 ELSE 0 END),
                0
            )                                               AS liczba_anulowanych
        FROM klienci k
        LEFT JOIN zamowienia z ON k.id_klienta = z.id_klienta
        GROUP BY
            k.id_klienta,
            k.stan_zadluzenia,
            k.typ_konta,
            k.data_rejestracji
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"[DATASET] Pobrano dane dla {len(rows)} klientów z bazy.")
    return pd.DataFrame(rows)


def oblicz_wskaznik_zwrotow(row: pd.Series) -> float:
    """
    Wylicza procentowy wskaźnik zwrotów dla klienta.
    Jeśli klient nie ma żadnych zamówień — zwraca 0.
    """
    if row['liczba_zamowien'] == 0:
        return 0.0
    return round(row['liczba_zwrotow'] / row['liczba_zamowien'], 4)


def generuj_etykiete(row: pd.Series) -> int:
    """
    Deterministyczna logika decyzyjna guardrail.
    Zwraca 1 (akcja dozwolona) lub 0 (akcja zablokowana).

    Guardrail blokuje gdy:
    - Zadłużenie przekracza 1500 zł                  -> wysokie ryzyko finansowe
    - Zadłużenie > 500 zł I wskaźnik zwrotów > 30%   -> zadłużony i nadużywa zwrotów
    - Wskaźnik zwrotów przekracza 50%                -> ewidentne nadużycie zwrotów
    - Ponad 3 anulowane zamówienia                   -> nierzetelny klient
    - Konto zarejestrowane krócej niż 7 dni          -> nowe/niezaufane konto
      I zamówienie przekracza 2000 zł sumarycznie
    """
    # Warunek 1: Bardzo wysokie zadłużenie
    if row['stan_zadluzenia'] > 1500:
        return 0

    # Warunek 2: Umiarkowane zadłużenie + tendencja do zwrotów
    if row['stan_zadluzenia'] > 500 and row['wskaznik_zwrotow'] > 0.30:
        return 0

    # Warunek 3: Masowe zwroty (ponad połowa zamówień zwrócona)
    if row['wskaznik_zwrotow'] > 0.50:
        return 0

    # Warunek 4: Zbyt wiele anulowań
    if row['liczba_anulowanych'] > 3:
        return 0

    # Warunek 5: Nowe konto + duże wydatki (ryzyko fraudu)
    if row['dni_jako_klient'] < 7 and row['suma_wydatkow'] > 2000:
        return 0

    return 1


def generuj_dataset():
    """
    Główna funkcja:
    1. Pobiera realne dane z bazy MySQL
    2. Wylicza dodatkowe features
    3. Generuje etykiety decyzyjne
    4. Augmentuje dane syntetycznie (by zwiększyć zbiór treningowy)
    5. Zapisuje gotowy CSV
    """

    # --- KROK 1: Dane realne z bazy ---
    df = pobierz_dane_z_bazy()

    # --- KROK 2: Dodatkowe features ---
    df['typ_konta_num'] = df['typ_konta'].map(TYP_KONTA_MAP).fillna(0).astype(int)
    df['wskaznik_zwrotow'] = df.apply(oblicz_wskaznik_zwrotow, axis=1)

    # --- KROK 3: Etykiety decyzyjne ---
    df['decyzja'] = df.apply(generuj_etykiete, axis=1)

    # Wybieramy tylko kolumny które trafi do sieci neuronowej
    kolumny_modelu = [
        'liczba_zamowien',
        'suma_wydatkow',
        'wskaznik_zwrotow',
        'liczba_anulowanych',
        'stan_zadluzenia',
        'typ_konta_num',
        'dni_jako_klient',
        'decyzja'
    ]
    df_model = df[kolumny_modelu].copy()

    print(f"\n[DATASET] Rozkład etykiet z danych realnych:")
    print(df_model['decyzja'].value_counts())
    print(f"Łącznie rekordów realnych: {len(df_model)}")

    # --- KROK 4: Augmentacja syntetyczna ---
    # 100 klientów to za mało żeby wytrenować solidną sieć.
    # Generujemy dodatkowe syntetyczne próbki zachowując
    # tę samą logikę decyzyjną co wyżej.
    print("\n[DATASET] Generowanie danych syntetycznych...")
    np.random.seed(42)
    syntetyczne = []
    liczba_syntetycznych = 9000  # łącznie ~9100 próbek

    for _ in range(liczba_syntetycznych):
        liczba_zamowien = int(np.random.poisson(lam=5)) + 1
        suma_wydatkow = round(float(np.random.exponential(scale=800)), 2)
        liczba_zwrotow = int(np.random.binomial(n=liczba_zamowien, p=0.12))
        liczba_anulowanych = int(np.random.poisson(lam=0.8))
        stan_zadluzenia = round(
            float(np.random.exponential(scale=300))
            if np.random.random() > 0.65 else 0.0,
            2
        )
        typ_konta_num = int(np.random.choice([0, 1, 2], p=[0.65, 0.25, 0.10]))
        dni_jako_klient = int(np.random.randint(1, 730))

        wskaznik_zwrotow = round(liczba_zwrotow / liczba_zamowien, 4)

        # Tworzymy tymczasowy wiersz żeby użyć tej samej funkcji etykietowania
        row = pd.Series({
            'stan_zadluzenia': stan_zadluzenia,
            'wskaznik_zwrotow': wskaznik_zwrotow,
            'liczba_anulowanych': liczba_anulowanych,
            'dni_jako_klient': dni_jako_klient,
            'suma_wydatkow': suma_wydatkow
        })
        decyzja = generuj_etykiete(row)

        syntetyczne.append({
            'liczba_zamowien': liczba_zamowien,
            'suma_wydatkow': suma_wydatkow,
            'wskaznik_zwrotow': wskaznik_zwrotow,
            'liczba_anulowanych': liczba_anulowanych,
            'stan_zadluzenia': stan_zadluzenia,
            'typ_konta_num': typ_konta_num,
            'dni_jako_klient': dni_jako_klient,
            'decyzja': decyzja
        })

    df_syntetyczne = pd.DataFrame(syntetyczne)

    # --- KROK 5: Połączenie i zapis ---
    df_final = pd.concat([df_model, df_syntetyczne], ignore_index=True)

    # Małe losowe zaburzenie etykiet (5% szumu) — sieć nie uczy się
    # prostych if-ów, tylko aproksymuje granicę decyzyjną
    idx_szum = np.random.choice(len(df_final), int(0.05 * len(df_final)), replace=False)
    df_final.loc[idx_szum, 'decyzja'] = 1 - df_final.loc[idx_szum, 'decyzja']

    os.makedirs('Backend/neural_network/data', exist_ok=True)
    sciezka = 'Backend/neural_network/data/guardrail_dataset.csv'
    df_final.to_csv(sciezka, index=False)

    print(f"\n[DATASET] Rozkład etykiet w finalnym datasecie:")
    print(df_final['decyzja'].value_counts())
    print(f"\n[DATASET] Zapisano {len(df_final)} rekordów do '{sciezka}'")
    print(f"[DATASET] Features: {[k for k in kolumny_modelu if k != 'decyzja']}")


if __name__ == "__main__":
    generuj_dataset()