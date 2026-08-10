import pandas as pd
import numpy as np
import random
import os


def generate_synthetic_data(num_samples=10000):
    np.random.seed(42)

    # Generowanie cech opartych na Twoim opisie z pracy inżynierskiej:
    # 1. Historia transakcji (suma wydatków w zł)
    suma_wydatkow = np.random.exponential(scale=1500, size=num_samples)

    # 2. Liczba dotychczasowych zamówień
    liczba_zamowien = np.random.poisson(lam=5, size=num_samples) + 1

    # 3. Zdolność kredytowa (skala 0-100)
    zdolnosc_kredytowa = np.random.normal(loc=65, scale=15, size=num_samples)
    zdolnosc_kredytowa = np.clip(zdolnosc_kredytowa, 0, 100)

    # 4. Historia opóźnień w płatnościach (liczba spóźnionych faktur)
    opoznienia_w_platnosciach = np.random.poisson(lam=1, size=num_samples)

    # 5. Aktywne zadłużenie (w zł)
    aktywne_zadluzenie = np.where(np.random.rand(num_samples) > 0.7,
                                  np.random.exponential(scale=500, size=num_samples), 0)

    # Tworzenie DataFrame
    df = pd.DataFrame({
        'suma_wydatkow': suma_wydatkow,
        'liczba_zamowien': liczba_zamowien,
        'zdolnosc_kredytowa': zdolnosc_kredytowa,
        'opoznienia_w_platnosciach': opoznienia_w_platnosciach,
        'aktywne_zadluzenie': aktywne_zadluzenie
    })

    # LOGIKA DECYZYJNA (Tworzenie etykiety 0 lub 1)
    # Etykieta 1 (Zgoda) / 0 (Odmowa - Guardrail zadziała)
    labels = []
    for _, row in df.iterrows():
        # Warunki krytyczne - jeśli zadłużenie duże lub opóźnienia, sieć ma się nauczyć odmawiać
        if row['aktywne_zadluzenie'] > 1000 or row['opoznienia_w_platnosciach'] > 3 or row['zdolnosc_kredytowa'] < 30:
            labels.append(0)
        # Sytuacje graniczne
        elif row['aktywne_zadluzenie'] > 200 and row['zdolnosc_kredytowa'] < 50:
            labels.append(0)
        else:
            labels.append(1)

    # Wprowadzamy 5% szumu, by sieć faktycznie musiała się uczyć aproksymacji, a nie tylko if-ów
    noise_indices = np.random.choice(num_samples, int(0.05 * num_samples), replace=False)
    for idx in noise_indices:
        labels[idx] = 1 - labels[idx]

    df['decyzja'] = labels

    # Zapis
    os.makedirs('Backend/neural_network/data', exist_ok=True)
    df.to_csv('Backend/neural_network/data/guardrail_dataset.csv', index=False)
    print(f"Wygenerowano {num_samples} rekordów w 'data/guardrail_dataset.csv'.")
    print(df['decyzja'].value_counts())


if __name__ == "__main__":
    generate_synthetic_data()