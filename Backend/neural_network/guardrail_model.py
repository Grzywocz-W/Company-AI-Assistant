# Backend/neural_network/guardrail_model.py
import torch
import torch.nn as nn


class GuardrailNN(nn.Module):
    def __init__(self, input_dim):
        super(GuardrailNN, self).__init__()

        # Pierwsza warstwa ukryta
        self.layer1 = nn.Linear(input_dim, 64)
        self.bn1 = nn.BatchNorm1d(64)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.3)

        # Druga warstwa ukryta
        self.layer2 = nn.Linear(64, 32)
        self.bn2 = nn.BatchNorm1d(32)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.2)

        # Trzecia warstwa ukryta (16 neuronów - kondensacja cech)
        self.layer3 = nn.Linear(32, 16)
        self.relu3 = nn.ReLU()

        # Warstwa wyjściowa (1 neuron klasyfikujący binarnie)
        self.output_layer = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()  # Kompresuje wynik do przedziału (0, 1)

    def forward(self, x):
        # Przepływ danych przez sieć (typ Forward pass)
        out = self.layer1(x)

        # BatchNorm1d wymaga batch_size >= 2 podczas treningu.
        # Podczas inferencji (eval mode) działa poprawnie z batch_size=1.
        # Zabezpieczenie: jeśli batch ma 1 próbkę i jesteśmy w trybie treningu
        # pomijamy BatchNorm żeby uniknąć błędu.
        if self.training and out.size(0) == 1:
            pass
        else:
            out = self.bn1(out)

        out = self.relu1(out)
        out = self.dropout1(out)

        out = self.layer2(out)

        if self.training and out.size(0) == 1:
            pass
        else:
            out = self.bn2(out)

        out = self.relu2(out)
        out = self.dropout2(out)

        out = self.layer3(out)
        out = self.relu3(out)

        out = self.output_layer(out)
        out = self.sigmoid(out)

        return out


if __name__ == "__main__":
    # 7 features zgodnych z generate_training_dataset.py:
    # liczba_zamowien, suma_wydatkow, wskaznik_zwrotow,
    # liczba_anulowanych, stan_zadluzenia, typ_konta_num, dni_jako_klient
    INPUT_DIM = 7
    model = GuardrailNN(input_dim=INPUT_DIM)
    model.eval()

    # Symulacja danych jednego klienta podczas inferencji
    sample_data = torch.tensor([[
        5.0,      # liczba_zamowien
        1200.50,  # suma_wydatkow
        0.10,     # wskaznik_zwrotow (10% zwrotów)
        1.0,      # liczba_anulowanych
        0.00,     # stan_zadluzenia (brak zadłużenia)
        1.0,      # typ_konta_num (Premium)
        365.0     # dni_jako_klient (rok)
    ]], dtype=torch.float32)

    prediction = model(sample_data)
    probability = prediction.item()
    is_allowed = 1 if probability >= 0.5 else 0

    print(f"Features wejściowe: {sample_data.tolist()}")
    print(f"Prawdopodobieństwo zezwolenia: {probability:.4f}")
    print(f"Decyzja Guardrail: {'ZEZWOLONO' if is_allowed else 'ZABLOKOWANO'}")