# Backend/neural_network/guardrail_checker.py
"""
Guardrail Checker — most między siecią neuronową a agentem bazy danych.

Odpowiada za:
1. Wczytanie wytrenowanego modelu PyTorch i scalera z dysku
2. Pobranie i agregację danych klienta z MySQL (w tym cech z 30-dniowego okna)
3. Uruchomienie inferencji sieci neuronowej
4. Zwrócenie decyzji (True/False) wraz z komunikatem do agenta
"""
import os
import sys
import pickle
import numpy as np
import torch
import mysql.connector

# Dodajemy Backend/ do sys.path — plik jest w Backend/neural_network/
# więc idziemy dwa poziomy wyżej, aby configLoader był widoczny
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from configLoader import loadConfig
# Obsługa importu GuardrailNN
try:
    from guardrail_network_model import GuardrailNN
except ImportError:
    from neural_network.guardrail_network_model import GuardrailNN


# Mapowanie typ konta -> liczba
TYP_KONTA_MAP = {
    'Standard': 0,
    'Premium':  1,
    'Firma':    2
}

# Ścieżki do zapisanych plików modelu (względem lokalizacji tego pliku)
_NN_DIR     = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH  = os.path.join(_NN_DIR, 'saved_models', 'guardrail_network_weights.pth')
SCALER_PATH = os.path.join(_NN_DIR, 'saved_models', 'scaler.pkl')
INPUT_DIM   = 10


class GuardrailChecker:
    """
    Klasa odpowiedzialna za ocenę ryzyka operacji klienta.
    Ładuje model i scaler dokładnie RAZ podczas inicjalizacji,
    następnie odpowiada na kolejne zapytania bez ponownego ładowania -
    co jest kluczowe dla wydajności przy każdym zapytaniu do agenta.
    """

    def __init__(self):
        self._model    = None
        self._scaler   = None
        self._is_loaded = False
        self._load_model()


    # Inicjalizacja modelu

    def _load_model(self):
        """
                Wczytuje wagi sieci neuronowej i scaler z dysku.
                Jeśli pliki nie istnieją (model jeszcze nie wytrenowany),
                przechodzi w tryb awaryjny - wszystkie operacje modyfikacji
                będą blokowane.
        """
        if not os.path.exists(MODEL_PATH):
            print(f"[GUARDRAIL] UWAGA: Brak pliku modelu: {MODEL_PATH}")
            print("[GUARDRAIL] Uruchom najpierw: python train_model.py")
            print("[GUARDRAIL] Tryb awaryjny: operacje modyfikacji ZABLOKOWANE.")
            return

        if not os.path.exists(SCALER_PATH):
            print(f"[GUARDRAIL] UWAGA: Brak pliku scalera: {SCALER_PATH}")
            print("[GUARDRAIL] Uruchom najpierw: python train_model.py")
            print("[GUARDRAIL] Tryb awaryjny: operacje modyfikacji ZABLOKOWANE.")
            return

        try:
            # Wczytanie wag sieci - map_location='cpu' zapewnia
            # działanie nawet bez karty graficznej
            self._model = GuardrailNN(input_dim=INPUT_DIM)
            self._model.load_state_dict(
                torch.load(MODEL_PATH, map_location=torch.device('cpu'), weights_only=True)
            )
            self._model.eval()

            with open(SCALER_PATH, 'rb') as f:
                self._scaler = pickle.load(f)

            self._is_loaded = True
            print("[GUARDRAIL] Model i scaler wczytane pomyślnie.")

        except Exception as e:
            print(f"[GUARDRAIL] Błąd wczytywania modelu: {e}")
            print("[GUARDRAIL] Tryb awaryjny: operacje modyfikacji ZABLOKOWANE.")
            self._is_loaded = False


    # Pobranie danych klienta z bazy

    def _pobierz_features_klienta(self, id_klienta: int) -> dict:
        backend_config = loadConfig('.env')
        try:
            conn = mysql.connector.connect(
                host=backend_config.get("DB_HOST_CUSTOMER", "127.0.0.1"),
                user=backend_config.get("DB_USER_CUSTOMER", "db_user"),
                password=backend_config.get("DB_PASSWORD_CUSTOMER", "db_password"),
                database=backend_config.get("DB_NAME", "e_commerce_db")
            )
            cursor = conn.cursor(dictionary=True)

            query = """
                SELECT
                    k.stan_zadluzenia,
                    k.typ_konta,
                    DATEDIFF(NOW(), k.data_rejestracji)              AS dni_jako_klient,
                    COUNT(z.id_zamowienia)                           AS liczba_zamowien,
                    COALESCE(
                        SUM(z.cena_jednostkowa * z.ilosc + z.koszt_dostawy), 0.00
                    )                                                AS suma_wydatkow,
                    COALESCE(
                        SUM(CASE WHEN z.status_zamowienia = 'Zwrot'
                            THEN 1 ELSE 0 END), 0
                    )                                                AS liczba_zwrotow,
                    COALESCE(
                        SUM(CASE WHEN z.status_zamowienia = 'Anulowane'
                            THEN 1 ELSE 0 END), 0
                    )                                                AS liczba_anulowanych,
                    COALESCE(
                        SUM(CASE WHEN z.data_zamowienia >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
                            THEN 1 ELSE 0 END), 0
                    )                                                AS zamowienia_30dni,
                    COALESCE(
                        SUM(CASE WHEN z.data_zamowienia >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
                            THEN (z.cena_jednostkowa * z.ilosc + z.koszt_dostawy) ELSE 0.00 END), 0.00
                    )                                                AS wydatki_30dni,
                    COALESCE(
                        SUM(CASE WHEN z.status_zamowienia = 'Anulowane' 
                                 AND z.data_zamowienia >= DATE_SUB(NOW(), INTERVAL 30 DAY) 
                            THEN 1 ELSE 0 END), 0
                    )                                                AS anulowane_30dni
                FROM klienci k
                LEFT JOIN zamowienia z ON k.id_klienta = z.id_klienta
                WHERE k.id_klienta = %s
                GROUP BY
                    k.id_klienta,
                    k.stan_zadluzenia,
                    k.typ_konta,
                    k.data_rejestracji
            """

            cursor.execute(query, (id_klienta,))
            row = cursor.fetchone()
            cursor.close()
            conn.close()

            if row is None:
                print(f"[GUARDRAIL] Nie znaleziono klienta o id={id_klienta}.")

            return row

        except mysql.connector.Error as e:
            print(f"[GUARDRAIL] Błąd połączenia z bazą: {e}")
            return None


    # Przygotowanie wektora cech

    def _przygotuj_features(self, row: dict) -> np.ndarray:
        liczba_zamowien = int(row['liczba_zamowien'])
        liczba_zwrotow  = int(row['liczba_zwrotow'])

        wskaznik_zwrotow = (
            round(liczba_zwrotow / liczba_zamowien, 4)
            if liczba_zamowien > 0 else 0.0
        )

        features = np.array([[
            float(TYP_KONTA_MAP.get(row['typ_konta'], 0)), # 0. typ_konta_num
            float(row['dni_jako_klient'] or 0.0),          # 1. dni_jako_klient
            float(row['stan_zadluzenia'] or 0.0),          # 2. stan_zadluzenia
            float(liczba_zamowien),                        # 3. liczba_zamowien
            float(row['suma_wydatkow'] or 0.0),            # 4. suma_wydatkow
            float(wskaznik_zwrotow),                       # 5. wskaznik_zwrotow
            float(row['liczba_anulowanych'] or 0.0),       # 6. liczba_anulowanych
            float(row['zamowienia_30dni'] or 0.0),         # 7. zamowienia_30dni
            float(row['wydatki_30dni'] or 0.0),            # 8. wydatki_30dni
            float(row['anulowane_30dni'] or 0.0)           # 9. anulowane_30dni
        ]], dtype=np.float32)

        return features


    # Główna metoda publiczna

    def sprawdz(self, id_klienta: int) -> tuple[bool, float, str]:
        """
                Główna metoda guardrail - ocenia ryzyko operacji dla danego klienta.
                Args:
                    id_klienta: ID klienta z tabeli klienci
                Returns:
                    Tuple: (is_allowed: bool, probability: float, message: str):
                      - is_allowed:  True = operacja dozwolona, False = zablokowana (operacje dozwolone gdy probability >= 0.6 - zastosowano dodatkowe techniczne zabezpieczenie przed FP)
                      - probability: pewność sieci (0.0 - 1.0)
                      - message:     czytelny komunikat dla agenta / logów
        """
        if not self._is_loaded:
            return (
                False,
                0.0,
                "Guardrail: model nie jest wytrenowany - operacja zablokowana."
            )

        row = self._pobierz_features_klienta(id_klienta)
        if row is None:
            return (
                False,
                0.0,
                f"Guardrail: nie znaleziono klienta id={id_klienta} - operacja zablokowana."
            )

        features        = self._przygotuj_features(row)
        features_scaled = self._scaler.transform(features)

        tensor = torch.tensor(features_scaled, dtype=torch.float32)
        with torch.no_grad():
            probability = self._model(tensor).item()

        is_allowed = probability >= 0.6     # Zastosowano dodatkowe zabezpieczenie inżynieryjne, podnosząc próg z 0.5 do 0.6, aby zaimplementować dodatkowe techniczne zabezpieczenie przed False Positive, ponieważ FP są w naszym systemie potencjalnie dużo bardziej niebezpieczne niż FN

        if is_allowed:
            message = (
                f"Guardrail: operacja dozwolona dla klienta id={id_klienta} "
                f"(wiarygodność klienta: {probability:.2%})."
            )
        else:
            message = (
                f"Guardrail: operacja ZABLOKOWANA dla klienta id={id_klienta}"
                f"(ocena ryzyka: {(1.0 - probability):.2%}). "
                f"Klient nie spełnia kryteriów bezpieczeństwa."
            )
        print(
            f"[GUARDRAIL] id_klienta={id_klienta} | "
            f"prob={probability:.4f} | "
            f"{'ZEZWOLONO' if is_allowed else 'ZABLOKOWANO'}"
        )

        return is_allowed, probability, message


if __name__ == "__main__":
    print("=== Test GuardrailChecker ===\n")
    checker = GuardrailChecker()

    for client_id in [1, 2, 3, 4, 5]:
        is_allowed, prob, msg = checker.sprawdz(client_id)
        print(f"Klient {client_id:>3} | prob={prob:.4f} | {msg}")
