#Backend/neural_network/guardrail_network_model.py
import torch
import torch.nn as nn


class GuardrailNN(nn.Module):
    def __init__(self, input_dim: int):
        super(GuardrailNN, self).__init__()

        #Warstwa nr 1: kompresja + normalizacja + regularyzacja
        self.layer1 = nn.Linear(input_dim, 64)
        self.norm1 = nn.LayerNorm(64)
        
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.3)

        #Warstwa nr 2: ekstrakcja cech
        self.layer2 = nn.Linear(64, 32)
        self.norm2 = nn.LayerNorm(32)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.2)

        #Warstwa nr 3: kondensacja
        self.layer3 = nn.Linear(32, 16)
        self.relu3 = nn.ReLU()

        #Warstwa wyjściowa: klasyfikacja
        self.output_layer = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()     #  (0, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        #Warstwa 1
        output = self.layer1(x)
        output = self.norm1(output)
        output = self.relu1(output)
        output = self.dropout1(output)

        #Warstwa 2
        output = self.layer2(output)
        output = self.norm2(output)
        output = self.relu2(output)
        output = self.dropout2(output)

        #Warstwa 3
        output = self.layer3(output)
        output = self.relu3(output)

        #Wyjście
        output = self.output_layer(output)
        output = self.sigmoid(output)

        return output


if __name__ == "__main__":
    """
    10 features = 7 bazowych + 3 time-window (okno 30 dni)

    CECHY BAZOWE (profil klienta):
    0. typ_konta_num        - 0=Standard, 1=Premium, 2=Firma
    1. dni_jako_klient      - jak długo jest klientem
    2. stan_zadluzenia      - obecne zadłużenie w złotych
    3. liczba_zamowien      - łączna liczba zamówień
    4. suma_wydatkow        - łączna kwota wydana
    5. wskaznik_zwrotow     - procent zwróconych zamówień (0.0 - 1.0)
    6. liczba_anulowanych   - łączna liczba anulowanych zamówień

    CECHY TIME-WINDOW (ostatnie 30 dni - Feature Engineering):
    7. zamowienia_30dni     - liczba zamówień w ostatnich 30 dniach
    8. wydatki_30dni        - suma wydatków w ostatnich 30 dniach
    9. anulowane_30dni      - liczba anulowanych w ostatnich 30 dniach
    """

    #2 testy architektury
    INPUT_DIM = 10
    model = GuardrailNN(input_dim=INPUT_DIM)
    model.eval()

    print("=" * 50)
    print("TEST 1: Klient niskiego ryzyka")
    print("=" * 50)
    klient_bezpieczny = torch.tensor([[
        1.0,     #Premium
        365.0,   #Rok jako klient
        0.0,     #Brak zadłużenia
        12.0,    #12 zamówień łącznie
        2400.0,  #2400 zł wydane
        0.08,    #8% zwrotów
        1.0,     #1 anulowanie łącznie
        2.0,     #2 zamówienia w ostatnich 30 dniach
        350.0,   #350 zł wydane w ostatnich 30 dniach
        0.0,     #0 anulowań w ostatnich 30 dniach
    ]], dtype=torch.float32)

    with torch.no_grad():
        prediction = model(klient_bezpieczny)
    probability = prediction.item()
    if probability >= 0.5:
        is_allowed = 1
    else:
        is_allowed = 0


    print(f"Features wejściowe: {klient_bezpieczny.tolist()}")
    print(f"Prawdopodobieństwo zezwolenia: {probability:.4f}")
    print(f"Decyzja Guardrail: {'ZEZWOLONO' if is_allowed else 'ZABLOKOWANO'}")

    print()
    print("=" * 50)
    print("TEST 2: Klient wysokiego ryzyka (rosnący dług)")
    print("=" * 50)
    klient_ryzykowny = torch.tensor([[
        0.0,     #Standard
        45.0,    #Nowy klient (45 dni)
        1800.0,  #Duże zadłużenie
        8.0,     #8 zamówień łącznie
        950.0,   #950 zł wydane łącznie
        0.37,    #37% zwrotów - czerwona flaga
        3.0,     #3 anulowania łącznie
        5.0,     #5 zamówień w ostatnich 30 dniach
        800.0,   #800 zł wydane w ostatnich 30 dniach
        2.0,     #2 anulowania w ostatnich 30 dniach
    ]], dtype=torch.float32)

    with torch.no_grad():
        prediction = model(klient_ryzykowny)
    probability = prediction.item()
    if probability >= 0.5:
        is_allowed = 1
    else:
        is_allowed = 0

    print(f"Features wejściowe: {klient_ryzykowny.tolist()}")
    print(f"Prawdopodobieństwo zezwolenia: {probability:.4f}")
    print(f"Decyzja Guardrail: {'ZEZWOLONO' if is_allowed else 'ZABLOKOWANO'}")
