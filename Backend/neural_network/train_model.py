#Backend/neural_network/train_model.py
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
        self.labels= torch.tensor(
            labels,
            dtype=torch.float32
            ).unsqueeze(1)
        
        self.features = torch.tensor(
            features,
            dtype=torch.float32
            )

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def train():
    #1Odczyt datasetu
    #Skrypt włącza się z poziomu Backend/neural_network/ wykorzysta ścieżka względna względna
    sciezka_csv = 'data/guardrail_dataset.csv'
    if not os.path.exists(sciezka_csv):
        print(f"[TRAINING] Err4r: Brak pliku '{sciezka_csv}'")
        print("[TRAINING] Zacznij od uruchomienia: python generate_training_dataset.py")
        sys.exit(1)#kończymy

    df = pd.read_csv(sciezka_csv)
    print(f"[TRAINING] Wczytano {len(df)} rekordów.  \n [TRAINING] Rozkład etykiet:  \n  {df['decyzja'].value_counts()}   \n")

    #2 określenie cech
    #Kolejność JEST identyczna jak  ustalono wcześniej w generate_training_dataset.py
    # analogicznie guardrail_checker.py
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

    INPUT_DIM = len(feature_columns)  #10
    print(f"[TRAINING] INPUT_DIM = {INPUT_DIM} \n    [TRAINING] Features: {feature_columns}\n")

    X = df[feature_columns].values
    y = df['decyzja'].values

    #3. train/test z sclearn
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.25,
        random_state=42,
        stratify=y  #zachowane są proporcje klasy
    )
    print(f"[TRAINING] Zbiór treningowy: {len(X_train)} próbek, \n[TRAINING] Zbiór testowy:    {len(X_test)} próbek\n")

    #4Skalowanie
    #StandardScaler: rozkład normalny
    #fit() dla scalera używać tylko na danych treningowych, inaczej wyciek danych
    stdScaler = StandardScaler()
    X_train = stdScaler.fit_transform(X_train)
    X_test  = stdScaler.transform(X_test)

    #zapisanie scalera - guardrail_checker.py użyje go ponownie przy inferencji
    os.makedirs('saved_models', exist_ok=True)
    with open('saved_models/scaler.pkl', 'wb') as f:
        pickle.dump(stdScaler, f)
    print("[TRAINING] zapisano scaller w lokalizacji w: saved_models/scaler.pkl")


    #5.DataLoader
    train_dataset = GuardrailDataset(X_train, y_train)
    test_dataset  = GuardrailDataset(X_test,  y_test)

    train_loader = DataLoader(train_dataset,
                              batch_size=64,
                              shuffle=True,
                              drop_last=False)
    test_loader  = DataLoader(test_dataset,
                              batch_size=64,
                              shuffle=False
                              )

    #6. Model, loss oraz optimizer
    model= GuardrailNN(input_dim=INPUT_DIM)
    criterion =nn.BCELoss()
    optimizer =optim.Adam(model.parameters(),
                          lr=0.001,
                          weight_decay=1e-4
                          )

    #ReduceLROnPlateau: zmniejsza LR pod warunkiem, iż loss przestał spadać przez 5 kolejnych epok
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode='min',
        patience=5,
        factor=0.5
    )

    #7. trening
    EPOCHS = 60
    training_losses =[]
    valid_losses= []

    print(f"[TRAINING] Trenign rozpoczetydla epochs={EPOCHS}...")
    print("-" * 42)

    for epoch in range(EPOCHS):
        model.train()
        epoch_loss = 0.0

        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            outputs = model(batch_X)
            loss= criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()

        avg_training_loss = epoch_loss / len(train_loader)
        training_losses.append(avg_training_loss)

        #Walidacja
        model.eval()
        epoch_valid_loss = 0.0
        with torch.no_grad():
            for batch_X, batch_y in test_loader:
                outputs = model(batch_X)
                loss = criterion(outputs,batch_y)
                epoch_valid_loss += loss.item()

        avg_valid_loss = epoch_valid_loss / len(test_loader)
        valid_losses.append(avg_valid_loss)

        # Scheduler reaguje na stratę walidacyjną
        scheduler.step(avg_valid_loss)

        # Wypisujemy co 10 epok + ostatnia
        if (epoch + 1) % 10 == 0 or epoch == EPOCHS - 1:
            current_lr = optimizer.param_groups[0]['lr']
            print(f"  Epoka [{epoch + 1:>3}/{EPOCHS}] "
                  f"| Train Loss: {avg_training_loss:.4f} "
                  f"| Val Loss: {avg_valid_loss:.4f} "
                  f"| LR: {current_lr:.6f}")

    print("-" * 42)

    #8 zapis modelu
    torch.save(
        model.state_dict(),
        'saved_models/guardrail_network_weights.pth'
    )
    print("[TRAINING] Wagi modelu zostały zapisane w lokalizacji: \nsaved_models/guardrail_network_weights.pth")



    #9. Ewaluacja zbioru testowego
    model.eval()
    all_predictions  = []
    all_labels = []

    with torch.no_grad():
        for batch_X, batch_y in test_loader:
            outputs =model(batch_X)
            predicted= (outputs >= 0.5).float()
            all_predictions.extend(predicted.view(-1).tolist())
            all_labels.extend(batch_y.view(-1).tolist())

    accuracy = sum(p == l for p, l in zip(all_predictions, all_labels)) / len(all_labels)
    print(f"[TRAINING] Dokładność zbioru testowego: {accuracy * 100:.2f}%")

    print("[TRAINING] Raport klasyfikacji:")
    print(classification_report(
        all_labels, all_predictions,
        target_names=['ZABLOKOWANO (0)', 'ZEZWOLONO (1)']
    ))

    print("[TRAINING] Macierz pomyłek:")
    cm = confusion_matrix(all_labels, all_predictions)
    print(cm)
    print("======================================================================")
    print(f"  TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"  FN={cm[1,0]}  TP={cm[1,1]}")
    print("======================================================================")
    print(f"\n  FP = klient ryzykowny przepuszczony jako bezpieczny")
    print(f"  FN = klient bezpieczny zablokowany przez pomyłkę")

    #macierz pomyłek jako heatmapa
    plt.figure(
        figsize=(6, 5)
        )
    sns.heatmap(
        cm,
        cmap='Blues',
        fmt='d',
        annot=True,
        xticklabels= ['ZABLOKOWANO (0)', 'ZEZWOLONO (1)'],
        yticklabels=['ZABLOKOWANO (0)', 'ZEZWOLONO (1)']
    )
    plt.title('Macierz pomyłek modelu dla Guardrail')
    plt.ylabel('Rzeczywista etykieta')
    plt.xlabel('Przewidziana etykieta')
    plt.tight_layout()
    plt.savefig('data/confusion_matrix.png')
    plt.close()
    print("[TRAINING] Macierz pomyłek zastała zapisana na dysku w lokalizacji: data/confusion_matrix.png")

    #10 Wykres straty
    os.makedirs('data', exist_ok=True)

    
    plt.figure(
        figsize=(10, 5)
        )
    plt.plot(training_losses,
             label='Strata treningowa (Train Loss)',
             color='royalblue',
             linewidth=2)
    plt.plot(valid_losses,
             label='Strata walidacyjna (Val Loss)',
             color='darkorange',
             linestyle='--',
             linewidth=2,)
    plt.title('Krzywa uczenia sieci (Loss Curve)')
    plt.xlabel('Epoka')
    plt.ylabel('BCELoss')
    plt.legend()
    plt.grid(True,
             linestyle=':',
             alpha=0.64)
    plt.tight_layout()
    plt.savefig('data/training_plot.png')
    plt.close()
    print("[TRAINING] Wykres uczenia został zapisany w: data/training_plot.png")


if __name__ == "__main__":
    train()
