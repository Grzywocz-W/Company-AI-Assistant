# Backend/neural_network/train_model.py
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
from sklearn.metrics import classification_report, confusion_matrix
import pickle

from guardrail_network_model import GuardrailNN


class GuardrailDataset(Dataset):
    def __init__(self, features, labels):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels = torch.tensor(labels, dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def train():
    # 1. Wczytanie danych z nowego datasetu
    sciezka_csv = 'Backend/neural_network/data/guardrail_dataset.csv'
    df = pd.read_csv(sciezka_csv)

    print(f"[TRAIN] Wczytano {len(df)} rekordów.")
    print(f"[TRAIN] Rozkład etykiet:\n{df['decyzja'].value_counts()}\n")

    # Features muszą być w tej samej kolejności co w guardrail_checker.py
    feature_columns = [
        'liczba_zamowien',
        'suma_wydatkow',
        'wskaznik_zwrotow',
        'liczba_anulowanych',
        'stan_zadluzenia',
        'typ_konta_num',
        'dni_jako_klient'
    ]

    X = df[feature_columns].values
    y = df['decyzja'].values

    # 2. Podział na zbiór treningowy i testowy
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. Skalowanie — KLUCZOWE dla sieci neuronowych
    # Scaler dopasowujemy TYLKO na danych treningowych
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Zapisujemy scaler — guardrail_checker.py będzie go używał przy inferencji
    os.makedirs('Backend/neural_network/saved_models', exist_ok=True)
    with open('Backend/neural_network/saved_models/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print("[TRAIN] Scaler zapisany.")

    # 4. DataLoadery
    train_dataset = GuardrailDataset(X_train, y_train)
    test_dataset = GuardrailDataset(X_test, y_test)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    # 5. Model — input_dim=7 zgodny z liczbą features
    INPUT_DIM = len(feature_columns)  # 7
    model = GuardrailNN(INPUT_DIM)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    # Scheduler zmniejsza learning rate gdy loss przestaje spadać
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', patience=5, factor=0.5
    )

    # 6. Pętla treningowa
    epochs = 50
    train_losses = []
    print(f"[TRAIN] Rozpoczęcie trenowania (input_dim={INPUT_DIM}, epochs={epochs})...")
    for epoch in range(epochs):
        model.train()
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
        scheduler.step(avg_loss)

        if (epoch + 1) % 10 == 0:
            print(f'  Epoka [{epoch + 1}/{epochs}] | Loss: {avg_loss:.4f} '
                  f'| LR: {optimizer.param_groups[0]["lr"]:.6f}')

    # 7. Zapis wag modelu
    torch.save(
        model.state_dict(),
        'Backend/neural_network/saved_models/guardrail_weights.pth'
    )
    print("\n[TRAIN] Wagi modelu zapisane.")

    # 8. Ewaluacja
    model.eval()
    all_preds = []
    all_labels = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs = model(batch_X)
            predicted = (outputs >= 0.5).float()
            all_preds.extend(predicted.squeeze().tolist())
            all_labels.extend(batch_y.squeeze().tolist())

    accuracy = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)
    print(f"\n[TRAIN] Dokładność na zbiorze testowym: {accuracy * 100:.2f}%")
    print("\n[TRAIN] Raport klasyfikacji:")
    print(classification_report(
        all_labels, all_preds,
        target_names=['ZABLOKOWANO (0)', 'ZEZWOLONO (1)']
    ))

    print("[TRAIN] Macierz pomyłek:")
    print(confusion_matrix(all_labels, all_preds))


    # 9. Wykres loss
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Strata treningowa (BCELoss)', color='royalblue')
    plt.title('Proces uczenia sieci Guardrail')
    plt.xlabel('Epoka')
    plt.ylabel('Błąd BCELoss')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('Backend/neural_network/data/training_plot.png')
    print("\n[TRAIN] Wykres zapisany jako 'training_plot.png'")


if __name__ == "__main__":
    train()