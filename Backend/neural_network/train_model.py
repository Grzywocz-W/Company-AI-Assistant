import os
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle

from guardrail_model import GuardrailNN


# Definicja Datasetu dla PyTorcha
class GuardrailDataset(Dataset):
    def __init__(self, features, labels):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def train():
    # 1. Wczytanie danych
    df = pd.read_csv('Backend/neural_network/data/guardrail_dataset.csv')
    X = df.drop('decyzja', axis=1).values
    y = df['decyzja'].values

    # 2. Podział na zbiór treningowy i testowy
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 3. Skalowanie danych (Bardzo ważne dla sieci neuronowych!)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Zapisujemy scaler, by agent mógł z niego korzystać w czasie rzeczywistym
    os.makedirs('Backend/neural_network/saved_models', exist_ok=True)
    with open('Backend/neural_network/saved_models/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)

    # 4. Przygotowanie DataLoaderów
    train_dataset = GuardrailDataset(X_train, y_train)
    test_dataset = GuardrailDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    # 5. Inicjalizacja modelu
    input_dim = X_train.shape[1]
    model = GuardrailNN(input_dim)

    # Definicja funkcji straty i optymalizatora
    criterion = nn.BCELoss()  # Binary Cross Entropy (Dla klasyfikacji binarnej)
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 6. Pętla treningowa
    epochs = 30
    train_losses = []

    print("Rozpoczęcie trenowania modelu...")
    for epoch in range(epochs):
        model.train()  # Tryb treningu (aktywuje Dropout i BatchNorm)
        epoch_loss = 0

        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_loss = epoch_loss / len(train_loader)
        train_losses.append(avg_loss)

        if (epoch + 1) % 5 == 0:
            print(f'Epoka [{epoch + 1}/{epochs}], Strata: {avg_loss:.4f}')

    # 7. Zapis wytrenowanego modelu
    torch.save(model.state_dict(), 'Backend/neural_network/saved_models/guardrail_weights.pth')
    print("Model zapisany!")

    # 8. Ewaluacja na zbiorze testowym
    model.eval()  # Tryb ewaluacji
    correct = 0
    total = 0
    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            predicted = (outputs >= 0.5).float()
            total += batch_y.size(0)
            correct += (predicted == batch_y).sum().item()

    accuracy = 100 * correct / total
    print(f'Dokładność modelu na zbiorze testowym: {accuracy:.2f}%')

    # 9. Wykres straty
    plt.plot(train_losses, label='Strata Treningowa (Loss)')
    plt.title('Proces uczenia sieci walidującej (Guardrail)')
    plt.xlabel('Epoka')
    plt.ylabel('Błąd BCELoss')
    plt.legend()
    plt.grid(True)
    plt.savefig('Backend/neural_network/data/training_plot.png')
    print("Wykres uczenia zapisany jako 'training_plot.png'. Możesz go użyć w pracy inżynierskiej!")


if __name__ == "__main__":
    train()