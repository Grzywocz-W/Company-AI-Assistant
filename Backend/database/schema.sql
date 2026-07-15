-- Tworzenie bazy danych (jeśli nie istnieje)
CREATE DATABASE IF NOT EXISTS e_commerce_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE e_commerce_db;

-- 1. Tabela Klienci
CREATE TABLE IF NOT EXISTS klienci (
    id_klienta INT AUTO_INCREMENT PRIMARY KEY,
    imie VARCHAR(50) NOT NULL,
    nazwisko VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    telefon VARCHAR(20),
    miasto VARCHAR(50),
    wojewodztwo VARCHAR(50),
    data_rejestracji DATETIME DEFAULT CURRENT_TIMESTAMP,
    typ_konta ENUM('Standard', 'Premium', 'Firma') DEFAULT 'Standard',
    status_konta ENUM('Aktywne', 'Zablokowane', 'Niezweryfikowane') DEFAULT 'Aktywne'
) ENGINE=InnoDB;

-- 2. Tabela Zamówienia (z kluczem obcym)
CREATE TABLE IF NOT EXISTS zamowienia (
    id_zamowienia INT AUTO_INCREMENT PRIMARY KEY,
    id_klienta INT NOT NULL,
    numer_zamowienia VARCHAR(30) NOT NULL UNIQUE, -- np. ZA-2026-0001
    data_zamowienia DATETIME DEFAULT CURRENT_TIMESTAMP,
    status_zamowienia ENUM('Nowe', 'Oplacone', 'W realizacji', 'Wyslane', 'Dostarczone', 'Anulowane', 'Zwrot') DEFAULT 'Nowe',

    -- Dane produktu (wersja uproszczona pod agenta, imitująca Allegro)
    produkt_nazwa VARCHAR(150) NOT NULL,
    kategoria VARCHAR(50) NOT NULL, -- Elektronika, Moda, Dom i Ogród, Motoryzacja, Książki itp.
    cena_jednostkowa DECIMAL(10, 2) NOT NULL,
    ilosc INT NOT NULL DEFAULT 1,
    koszt_dostawy DECIMAL(6, 2) DEFAULT 0.00,
    metoda_platnosci ENUM('BLIK', 'Karta', 'Przelew', 'Za pobraniem') DEFAULT 'BLIK',

    -- Relacja klucza obcego
    FOREIGN KEY (id_klienta) REFERENCES klienci(id_klienta)
        ON DELETE CASCADE
        ON UPDATE CASCADE
) ENGINE=InnoDB;