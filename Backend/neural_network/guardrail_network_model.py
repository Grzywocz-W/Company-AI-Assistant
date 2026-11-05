# Backend/neural_network/guardrail_network_model.py
import torch
import torch.nn as nn


class GuardrailNN(nn.Module):
    """
        Wielowarstwowy perceptron (MLP - Multi Layer Perceptron) do binarnej klasyfikacji ryzyka klienta.
        Jest to sieć typy Feedforward Neural Network (FNN), należąca do kategorii głęgokich sieci neuronowych (DNN) i zawiera ona 3 warstwy ukryte (hidden layers).
        Architektura: ((Linear -> LayerNorm -> ReLU -> Dropout) x2) -> Linear -> ReLu -> Linear -> Sigmoid
        LayerNorm normalizuje po wymiarze cech - działa poprawnie dla każdego rozmiaru batcha nawet =1.
    """

    def __init__(self, input_dim: int):
        super(GuardrailNN, self).__init__()

        # Warstwa 1: kompresja + normalizacja
        self.layer1 = nn.Linear(input_dim, 64)
        self.norm1 = nn.LayerNorm(64)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.3)

        # Warstwa 2: ekstrakcja cech
        self.layer2 = nn.Linear(64, 32)
        self.norm2 = nn.LayerNorm(32)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.2)

        # Warstwa 3: kondensacja (16 neuronow - kondensacja cech)
        self.layer3 = nn.Linear(32, 16)
        self.relu3 = nn.ReLU()

        # Warstwa wyjściowa (1 neuron klasyfikujący binarnie)
        self.output_layer = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()  # Wynik z przedziału (0, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Przepływ danych przez sieć (typ Forward pass - Feedforward Neural Network (FNN))
        # Warstwa 1
        out = self.layer1(x)
        out = self.norm1(out)
        out = self.relu1(out)
        out = self.dropout1(out)

        # Warstwa 2
        out = self.layer2(out)
        out = self.norm2(out)
        out = self.relu2(out)
        out = self.dropout2(out)

        # Warstwa 3
        out = self.layer3(out)
        out = self.relu3(out)

        # Wyjście
        out = self.output_layer(out)
        out = self.sigmoid(out)

        return out


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

    INPUT_DIM = 10
    model = GuardrailNN(input_dim=INPUT_DIM)
    model.eval()

    print("=" * 50)
    print("TEST 1: Klient niskiego ryzyka")
    print("=" * 50)
    klient_bezpieczny = torch.tensor([[
        1.0,     # Premium
        365.0,   # Rok jako klient
        0.0,     # Brak zadłużenia
        12.0,    # 12 zamówień łącznie
        2400.0,  # 2400 zł wydane łącznie
        0.08,    # 8% zwrotów
        1.0,     # 1 anulowanie łącznie
        2.0,     # 2 zamówienia w ostatnich 30 dniach
        350.0,   # 350 zł wydane w ostatnich 30 dniach
        0.0,     # 0 anulowań w ostatnich 30 dniach
    ]], dtype=torch.float32)

    with torch.no_grad():
        prediction = model(klient_bezpieczny)
    probability = prediction.item()
    is_allowed = 1 if probability >= 0.5 else 0

    print(f"Features wejściowe: {klient_bezpieczny.tolist()}")
    print(f"Prawdopodobieństwo zezwolenia: {probability:.4f}")
    print(f"Decyzja Guardrail: {'ZEZWOLONO' if is_allowed else 'ZABLOKOWANO'}")

    print()
    print("=" * 50)
    print("TEST 2: Klient wysokiego ryzyka (rosnący dług)")
    print("=" * 50)
    klient_ryzykowny = torch.tensor([[
        0.0,     # Standard
        45.0,    # Nowy klient (45 dni)
        1800.0,  # Duże zadłużenie
        8.0,     # 8 zamówień łącznie
        950.0,   # 950 zł wydane łącznie
        0.37,    # 37% zwrotów - czerwona flaga
        3.0,     # 3 anulowania łącznie
        5.0,     # 5 zamówień w ostatnich 30 dniach
        800.0,   # 800 zł wydane w ostatnich 30 dniach
        2.0,     # 2 anulowania w ostatnich 30 dniach
    ]], dtype=torch.float32)

    with torch.no_grad():
        prediction = model(klient_ryzykowny)
    probability = prediction.item()
    is_allowed = 1 if probability >= 0.5 else 0

    print(f"Features wejściowe: {klient_ryzykowny.tolist()}")
    print(f"Prawdopodobieństwo zezwolenia: {probability:.4f}")
    print(f"Decyzja Guardrail: {'ZEZWOLONO' if is_allowed else 'ZABLOKOWANO'}")