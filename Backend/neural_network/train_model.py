# Backend/neural_network/train_model.py
import os
import sys
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import pickle

from guardrail_network_model import GuardrailNN


class GuardrailDataset(Dataset):
    def __init__(self, features, labels):
        self.features = torch.tensor(features, dtype=torch.float32)
        self.labels   = torch.tensor(labels,   dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def train():
    #1. Wczytanie datasetu
    # Skrypt odpalamy z Backend/neural_network/ więc ścieżka względna
    sciezka_csv = 'data/guardrail_dataset.csv'
    if not os.path.exists(sciezka_csv):
        print(f"[TRAIN] BŁĄD: Nie znaleziono pliku '{sciezka_csv}'")
        print("[TRAIN] Najpierw uruchom: python generate_training_dataset.py")
        sys.exit(1)

    df = pd.read_csv(sciezka_csv)
    print(f"[TRAIN] Wczytano {len(df)} rekordów.")
    print(f"[TRAIN] Rozkład etykiet:\n{df['decyzja'].value_counts()}\n")

    # 2. Definicja features
    # Kolejność MUSI być identyczna jak w generate_training_dataset.py
    # i jak w guardrail_checker.py (inferencja agenta)
    feature_columns = [
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
    ]

    INPUT_DIM = len(feature_columns)  # 10
    print(f"[TRAIN] INPUT_DIM = {INPUT_DIM}")
    print(f"[TRAIN] Features: {feature_columns}\n")

    X = df[feature_columns].values
    y = df['decyzja'].values

    # 3. Podział train/test
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y          # zachowuje proporcje klas 0/1
    )
    print(f"[TRAIN] Zbiór treningowy: {len(X_train)} próbek")
    print(f"[TRAIN] Zbiór testowy:    {len(X_test)} próbek\n")

    # 4. Skalowanie
    # StandardScaler: mean=0, std=1 dla każdej cechy
    # WAŻNE: fit() dla scalera TYLKO na danych treningowych, żeby nie było wycieku danych
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    # Zapisujemy scaler — guardrail_checker.py użyje go przy inferencji
    os.makedirs('saved_models', exist_ok=True)
    with open('saved_models/scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    print("[TRAIN] Scaler zapisany w: saved_models/scaler.pkl")


    # 5. DataLoadery
    train_dataset = GuardrailDataset(X_train, y_train)
    test_dataset  = GuardrailDataset(X_test,  y_test)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True, drop_last=False)
    test_loader  = DataLoader(test_dataset,  batch_size=64, shuffle=False)

    # 6. Model, loss, optimizer
    model     = GuardrailNN(input_dim=INPUT_DIM)
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001, weight_decay=1e-4)

    # ReduceLROnPlateau: zmniejsza LR gdy loss przestaje spadać przez 5 epok
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', patience=5, factor=0.5
    )

    # 7. Pętla treningowa
    EPOCHS = 60
    train_losses = []
    val_losses = []

    print(f"[TRAIN] Rozpoczęcie trenowania (epochs={EPOCHS})...")
    print("-" * 55)

    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0.0

        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss    = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_train_loss = epoch_loss / len(train_loader)
        train_losses.append(avg_train_loss)

        # Walidacja
        model.eval()
        epoch_val_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                outputs = model(batch_X)
                loss = criterion(outputs, batch_y)
                epoch_val_loss += loss.item()

        avg_val_loss = epoch_val_loss / len(test_loader)
        val_losses.append(avg_val_loss)

        # Scheduler reaguje na stratę walidacyjną
        scheduler.step(avg_val_loss)

        # Wypisujemy co 10 epok + ostatnia
        if (epoch + 1) % 10 == 0 or epoch == EPOCHS - 1:
            current_lr = optimizer.param_groups[0]['lr']
            print(f"  Epoka [{epoch + 1:>3}/{EPOCHS}] "
                  f"| Train Loss: {avg_train_loss:.4f} "
                  f"| Val Loss: {avg_val_loss:.4f} "
                  f"| LR: {current_lr:.6f}")

    print("-" * 55)

    # 8. Zapis wag modelu
    torch.save(
        model.state_dict(),
        'saved_models/guardrail_network_weights.pth'
    )
    print("[TRAIN] Wagi modelu zapisane w: saved_models/guardrail_network_weights.pth\n")



    # 9. Ewaluacja na zbiorze testowym
    model.eval()
    all_preds  = []
    all_labels = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs   = model(batch_X)
            predicted = (outputs >= 0.5).float()
            all_preds.extend(predicted.view(-1).tolist())
            all_labels.extend(batch_y.view(-1).tolist())

    accuracy = sum(p == l for p, l in zip(all_preds, all_labels)) / len(all_labels)
    print(f"[TRAIN] Dokładność na zbiorze testowym: {accuracy * 100:.2f}%\n")

    print("[TRAIN] Raport klasyfikacji:")
    print(classification_report(
        all_labels, all_preds,
        target_names=['ZABLOKOWANO (0)', 'ZEZWOLONO (1)']
    ))

    print("[TRAIN] Macierz pomyłek:")
    cm = confusion_matrix(all_labels, all_preds)
    print(cm)
    print("======================================================================")
    print(f"  TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"  FN={cm[1,0]}  TP={cm[1,1]}")
    print("======================================================================")
    print(f"\n  FP = klient ryzykowny przepuszczony jako bezpieczny")
    print(f"  FN = klient bezpieczny zablokowany przez pomyłkę")

    # Macierz pomyłek (wykres)
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt='d', cmap='Blues',
        xticklabels=['ZABLOKOWANO (0)', 'ZEZWOLONO (1)'],
        yticklabels=['ZABLOKOWANO (0)', 'ZEZWOLONO (1)']
    )
    plt.title('Macierz pomyłek modelu Guardrail')
    plt.ylabel('Rzeczywista etykieta')
    plt.xlabel('Przewidziana etykieta')
    plt.tight_layout()
    plt.savefig('data/confusion_matrix.png')
    plt.close()
    print("[TRAIN] Macierz pomyłek (wykres) zapisana w: data/confusion_matrix.png")

    # 10. Wykres loss
    os.makedirs('data', exist_ok=True)
    plt.figure(figsize=(10, 5))
    plt.plot(train_losses, label='Strata treningowa (Train Loss)', color='royalblue', linewidth=2)
    plt.plot(val_losses, label='Strata walidacyjna (Val Loss)', color='darkorange', linewidth=2, linestyle='--')
    plt.title('Krzywa uczenia sieci Guardrail (Loss Curve)')
    plt.xlabel('Epoka')
    plt.ylabel('BCELoss')
    plt.legend()
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.tight_layout()
    plt.savefig('data/training_plot.png')
    plt.close()
    print("[TRAIN] Wykres uczenia zapisany w: data/training_plot.png")


if __name__ == "__main__":
    train()