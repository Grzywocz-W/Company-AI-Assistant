# Backend/neural_network/generate_training_dataset.py
import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from configLoader import loadConfig

TYP_KONTA_MAP = {
    'Standard': 0,
    'Premium':  1,
    'Firma':    2
}

def pobierz_dane_z_bazy() -> pd.DataFrame:
    """
    Pobiera z bazy danych wszystkie potrzebne dane o klientach
    i ich zamówieniach, a następnie agreguje je do jednego wiersza
    na klienta - gotowego jako wejście do sieci neuronowej.
    """
    import mysql.connector

    backend_config = loadConfig('config.txt')
    conn = mysql.connector.connect(
        host=backend_config.get("DB_HOST_ADMIN", "127.0.0.1"),
        user=backend_config.get("DB_USER_ADMIN", "agent_admin"),
        password=backend_config.get("DB_PASSWORD_ADMIN", "admin_password"),
        database=backend_config.get("DB_NAME", "e_commerce_db")
    )
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT
            k.id_klienta,
            k.typ_konta,
            DATEDIFF(NOW(), k.data_rejestracji)                               AS dni_jako_klient,
            k.stan_zadluzenia,
            -- === CECHY BAZOWE ===
            COUNT(z.id_zamowienia)                                            AS liczba_zamowien,
            COALESCE(SUM(z.cena_jednostkowa * z.ilosc + z.koszt_dostawy), 0)  AS suma_wydatkow,
            COALESCE(SUM(CASE WHEN z.status_zamowienia = 'Zwrot'
                              THEN 1 ELSE 0 END), 0)                          AS liczba_zwrotow,
            COALESCE(SUM(CASE WHEN z.status_zamowienia = 'Anulowane'
                              THEN 1 ELSE 0 END), 0)                          AS liczba_anulowanych,
            -- === CECHY TIME-WINDOW (ostatnie 30 dni) ===
            COALESCE(SUM(CASE
                WHEN z.data_zamowienia >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                THEN 1 ELSE 0 END), 0)                                   AS zamowienia_30dni,
            COALESCE(SUM(CASE
                WHEN z.data_zamowienia >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                THEN z.cena_jednostkowa * z.ilosc + z.koszt_dostawy
                ELSE 0 END), 0)                                          AS wydatki_30dni,
            COALESCE(SUM(CASE
                WHEN z.data_zamowienia >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                AND z.status_zamowienia = 'Anulowane'
                THEN 1 ELSE 0 END), 0)                                   AS anulowane_30dni
        FROM klienci k
        LEFT JOIN zamowienia z ON k.id_klienta = z.id_klienta
        GROUP BY
            k.id_klienta,
            k.typ_konta,
            k.stan_zadluzenia,
            k.data_rejestracji
    """

    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"[DATASET] Pobrano dane dla {len(rows)} klientów z bazy.")
    return pd.DataFrame(rows)


'''def oblicz_wskaznik_zwrotow(row: pd.Series) -> float:
    if float(row['liczba_zamowien']) == 0.0:
        return 0.0
    return round(float(row['liczba_zwrotow']) / float(row['liczba_zamowien']), 4)'''


def generuj_etykiete(row: pd.Series) -> int:
    """
    Deterministyczna logika guardrail — zwraca 1 (dozwolone) lub 0 (blokada).

    Blokuje gdy:
    - Zadłużenie > 1500 zł
    - Zadłużenie > 500 zł I wskaźnik zwrotów > 30%
    - Wskaźnik zwrotów > 50%
    - Więcej niż 3 anulowane zamówienia
    - Konto < 7 dni I suma wydatków > 2500 zł (ryzyko fraudu)
    - Nagły wzrost aktywności: >4 zamówienia w 30 dniach I zadłużenie > 500 zł
    - Dużo anulowań w ostatnich 30 dniach (>= 2) I zadłużenie > 500 zł
    """
    if row['stan_zadluzenia'] > 1500:
        return 0

    if row['stan_zadluzenia'] > 500 and row['wskaznik_zwrotow'] > 0.30:
        return 0

    if row['wskaznik_zwrotow'] > 0.50:
        return 0

    if row['liczba_anulowanych'] > 3:
        return 0

    if row['dni_jako_klient'] < 7 and row['suma_wydatkow'] > 2500:
        return 0

    # Reguły time-window
    if row['zamowienia_30dni'] > 4 and row['stan_zadluzenia'] > 500:
        return 0

    if row['anulowane_30dni'] >= 2 and row['stan_zadluzenia'] > 500:
        return 0

    return 1



def generuj_dataset():
    """
    1. Pobiera realne dane z bazy (10 features)
    2. Generuje etykiety
    3. Augmentuje dane syntetycznie (by zwiększyć zbiór treningowy)
    4. Dodaje 5% szumu
    5. Zapisuje CSV
    """

    # --- KROK 1: Dane realne ---
    df = pobierz_dane_z_bazy()

    # --- KROK 2: Wylicz pochodne cechy ---
    df['typ_konta_num']    = df['typ_konta'].map(TYP_KONTA_MAP).fillna(0).astype(int)
    df['wskaznik_zwrotow'] = df['liczba_zwrotow'].astype(float).div(
        df['liczba_zamowien'].astype(float).replace(0, np.nan)).fillna(0.0).round(4)
    df['decyzja']          = df.apply(generuj_etykiete, axis=1)

    # Kolejność musi być identyczna jak INPUT_DIM=10 w modelu!
    kolumny_modelu = [
        'typ_konta_num',       # 0
        'dni_jako_klient',     # 1
        'stan_zadluzenia',     # 2
        'liczba_zamowien',     # 3
        'suma_wydatkow',       # 4
        'wskaznik_zwrotow',    # 5
        'liczba_anulowanych',  # 6
        'zamowienia_30dni',    # 7
        'wydatki_30dni',       # 8
        'anulowane_30dni',     # 9
        'decyzja'              # etykieta
    ]
    df_model = df[kolumny_modelu].copy()

    print(f"\n[DATASET] Rozkład etykiet z danych realnych:")
    print(df_model['decyzja'].value_counts())
    print(f"Łącznie rekordów realnych: {len(df_model)}")

    # --- KROK 3: Augmentacja syntetyczna ---
    print("\n[DATASET] Generowanie danych syntetycznych...")
    np.random.seed(42)
    syntetyczne = []

    for _ in range(9000):
        typ_konta_num = int(np.random.choice([0, 1, 2], p=[0.65, 0.25, 0.10]))
        dni_jako_klient  = int(np.random.randint(1, 730))
        stan_zadluzenia = round(
            float(np.random.exponential(scale=300))
            if np.random.random() > 0.65 else 0.0, 2
        )
        liczba_zamowien  = int(np.random.poisson(lam=5)) + 1
        suma_wydatkow    = round(float(np.random.exponential(scale=800)), 2)
        liczba_zwrotow   = int(np.random.binomial(n=liczba_zamowien, p=0.12))
        wskaznik_zwrotow = round(liczba_zwrotow / liczba_zamowien, 4)
        liczba_anulowanych = int(np.random.poisson(lam=0.8))

        # Time-window — proporcjonalnie do całości
        # Zakładamy że ostatnie 30 dni to ~1/6 wszystkich zamówień
        zamowienia_30dni   = int(np.random.binomial(n=liczba_zamowien, p=0.17))
        wydatki_30dni      = round(suma_wydatkow * np.random.uniform(0.0, 0.35), 2)
        anulowane_30dni    = int(np.random.binomial(n=liczba_anulowanych + 1, p=0.25))


        row = pd.Series({
            'stan_zadluzenia':   stan_zadluzenia,
            'wskaznik_zwrotow':  wskaznik_zwrotow,
            'liczba_anulowanych': liczba_anulowanych,
            'dni_jako_klient':   dni_jako_klient,
            'suma_wydatkow':     suma_wydatkow,
            'zamowienia_30dni':  zamowienia_30dni,
            'anulowane_30dni':   anulowane_30dni,
        })
        decyzja = generuj_etykiete(row)

        syntetyczne.append({
            'typ_konta_num':      typ_konta_num,
            'dni_jako_klient':    dni_jako_klient,
            'stan_zadluzenia':    stan_zadluzenia,
            'liczba_zamowien':    liczba_zamowien,
            'suma_wydatkow':      suma_wydatkow,
            'wskaznik_zwrotow':   wskaznik_zwrotow,
            'liczba_anulowanych': liczba_anulowanych,
            'zamowienia_30dni':   zamowienia_30dni,
            'wydatki_30dni':      wydatki_30dni,
            'anulowane_30dni':    anulowane_30dni,
            'decyzja':            decyzja,
        })

    df_syntetyczne = pd.DataFrame(syntetyczne)

    # --- KROK 4: Połącz i dodaj szum ---
    df_final = pd.concat([df_model, df_syntetyczne], ignore_index=True)

    # 5% szumu — sieć uczy się granicy decyzyjnej, nie if-ów
    idx_szum = np.random.choice(len(df_final),
                                int(0.05 * len(df_final)),
                                replace=False)
    df_final.loc[idx_szum, 'decyzja'] = 1 - df_final.loc[idx_szum, 'decyzja']

    # --- KROK 5: Zapis ---
    #os.makedirs('Backend/neural_network/data', exist_ok=True)
    #sciezka = 'Backend/neural_network/data/guardrail_dataset.csv'
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    sciezka = os.path.join(data_dir, 'guardrail_dataset.csv')
    df_final.to_csv(sciezka, index=False)

    print(f"\n[DATASET] Rozkład etykiet w finalnym datasecie:")
    print(df_final['decyzja'].value_counts())
    print(f"\n[DATASET] Zapisano {len(df_final)} rekordów w --> '{sciezka}'")
    print(f"[DATASET] Features (10): {kolumny_modelu[:-1]}")


if __name__ == "__main__":
    generuj_dataset()