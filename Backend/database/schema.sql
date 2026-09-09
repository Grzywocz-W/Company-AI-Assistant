-- Tworzenie bazy danych (jeśli nie istnieje)
CREATE DATABASE IF NOT EXISTS e_commerce_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE e_commerce_db;

-- 1. Tabela Klienci
CREATE TABLE IF NOT EXISTS KLIENCI (
    id_klienta INT AUTO_INCREMENT PRIMARY KEY,
    imie VARCHAR(50) NOT NULL,
    nazwisko VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    telefon VARCHAR(20),
    miasto VARCHAR(50),
    wojewodztwo VARCHAR(50),
    data_rejestracji DATETIME DEFAULT CURRENT_TIMESTAMP,
    typ_konta ENUM('Standard', 'Premium', 'Firma') DEFAULT 'Standard',
    status_konta ENUM('Aktywne', 'Zablokowane', 'Niezweryfikowane') DEFAULT 'Aktywne',
    stan_zadluzenia DECIMAL(10, 2) DEFAULT 0.00
) ENGINE=InnoDB;

-- 2. Tabela Produkty
CREATE TABLE IF NOT EXISTS PRODUKTY (
    id_produktu INT AUTO_INCREMENT PRIMARY KEY,
    nazwa_produktu VARCHAR(150) NOT NULL,
    kategoria_produktu VARCHAR(50) NOT NULL
) ENGINE=InnoDB;

-- 3. Tabela Zamówienia (z kluczami obcymi do klienci i produkty)
CREATE TABLE IF NOT EXISTS zamowienia (
    id_zamowienia INT AUTO_INCREMENT PRIMARY KEY,
    id_klienta INT NOT NULL,
    id_produktu INT NOT NULL,
    numer_zamowienia VARCHAR(30) NOT NULL UNIQUE,
    data_zamowienia DATETIME DEFAULT CURRENT_TIMESTAMP,
    status_zamowienia ENUM(
        'Nowe',
        'Oplacone',
        'W realizacji',
        'Wyslane',
        'Dostarczone',
        'Anulowane',
        'Zwrot'
    ) DEFAULT 'Nowe',
    cena_jednostkowa DECIMAL(10, 2) NOT NULL,
    ilosc INT NOT NULL DEFAULT 1,
    koszt_dostawy DECIMAL(6, 2) DEFAULT 0.00,
    metoda_platnosci ENUM(
        'BLIK',
        'Karta',
        'Przelew',
        'Za pobraniem'
    ) DEFAULT 'BLIK',

    -- Klucz obcy do tabeli klienci
    FOREIGN KEY (id_klienta)
        REFERENCES klienci(id_klienta)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- Klucz obcy do tabeli produkty
    FOREIGN KEY (id_produktu)
        REFERENCES produkty(id_produktu)
        ON DELETE RESTRICT
        ON UPDATE CASCADE

) ENGINE=InnoDB;

-- 4. Utworzenie użytkowników bazy danych

-- Użytkownik dla zwykłego klienta (tylko odczyt)
CREATE USER IF NOT EXISTS 'db_user'@'localhost' IDENTIFIED BY 'db_password';

GRANT SELECT ON e_commerce_db.* TO 'db_user'@'localhost';

-- Użytkownik dla administratora (pełen dostęp do danych, bez zmian struktury)
CREATE USER IF NOT EXISTS 'agent_admin'@'localhost' IDENTIFIED BY 'haslo_admina';

GRANT SELECT, INSERT, UPDATE, DELETE ON e_commerce_db.klienci TO 'agent_admin'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE ON e_commerce_db.produkty TO 'agent_admin'@'localhost';

GRANT SELECT, INSERT, UPDATE, DELETE ON e_commerce_db.zamowienia TO 'agent_admin'@'localhost';

-- Odświeżenie uprawnień
FLUSH PRIVILEGES;