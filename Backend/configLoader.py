import os
def loadConfig(filePath = "config.txt"):#zakładamy, że plik konfiguracyjny jest w tym samym miejscu co jego loader
    settingsData = {}
    if not (os.path.exists(filePath)):
        print("PLIK USTAWIEŃ USZKODZONY")
        return settingsData

    try:
        configTxtFile = open(filePath,"r",encoding="utf-8")
        lines = configTxtFile.readlines()
        configTxtFile.close()
        
        for line in lines:
            if line and not (line.startswith('#')):#umożliwiamy komentarz
                if "=" in line:
                    key, content = line.split("=",1)#bo URL też mają =
                    settingsData[key.strip()]=content.strip()
    except IOError as e:
        print(f"BŁĄD ODCZYTU USTAWIEŃ: {e}")
    except Exception as e:
        print(f"NIEOCZEKIWANY BŁĄD KONFIGURACJI: {e}")
    return settingsData
                
    
