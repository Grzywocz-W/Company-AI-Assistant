import torch
import torch.nn as nn


class GuardrailNN(nn.Module):
    def __init__(self, input_dim):
        super(GuardrailNN, self).__init__()

        # Pierwsza warstwa ukryta
        self.layer1 = nn.Linear(input_dim, 64)
        self.bn1 = nn.BatchNorm1d(64)
        self.relu1 = nn.ReLU()
        self.dropout1 = nn.Dropout(0.3)  # Wyłącza 30% neuronów podczas treningu (zapobiega przeuczeniu)

        # Druga warstwa ukryta
        self.layer2 = nn.Linear(64, 32)
        self.bn2 = nn.BatchNorm1d(32)
        self.relu2 = nn.ReLU()
        self.dropout2 = nn.Dropout(0.2)

        # Trzecia warstwa ukryta (16 neuronów - kondensacja cech)
        self.layer3 = nn.Linear(32, 16)
        self.relu3 = nn.ReLU()

        # Warstwa wyjściowa (1 neuron klasyfikujący)
        self.output_layer = nn.Linear(16, 1)
        self.sigmoid = nn.Sigmoid()  # Kompresuje wynik do przedziału (0, 1)

    def forward(self, x):
        # Przepływ danych przez sieć (typ Forward pass)
        out = self.layer1(x)
        out = self.bn1(out)
        out = self.relu1(out)
        out = self.dropout1(out)

        out = self.layer2(out)
        out = self.bn2(out)
        out = self.relu2(out)
        out = self.dropout2(out)

        out = self.layer3(out)
        out = self.relu3(out)

        out = self.output_layer(out)
        out = self.sigmoid(out)

        return out


# Szybki test działania architektury
if __name__ == "__main__":
    # Załóżmy na razie, że będziemy mieli 5 cech z bazy danych
    # np. [l_zamowien, suma_wydatkow, l_zwrotow, l_dni_opoznienia, zaufanie_kredytowe]
    test_input_dim = 5
    model = GuardrailNN(input_dim=test_input_dim)
    model.eval()  # ustawia BatchNorm i Dropout w tryb testowy

    # Przykładowy tensor symulujący dane jednego klienta
    sample_data = torch.randn(1, test_input_dim)

    prediction = model(sample_data)
    print(f"Struktura wejścia: {sample_data}")
    print(f"Wynik sieci (prawdopodobieństwo): {prediction.item():.4f}")

    # Decyzja deterministyczna (zgodnie z założeniami RAG/Agenta)
    is_allowed = 1 if prediction.item() >= 0.5 else 0
    print(f"Ostateczna decyzja Guardraila: {is_allowed}")