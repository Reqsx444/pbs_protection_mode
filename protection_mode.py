import os
import glob
from datetime import datetime, timedelta
import subprocess
import re
from workalendar.europe import Poland

# Pobranie dzisiejszej daty
current_month = datetime.now().month
current_year = datetime.now().year

# Inicjalizacja kalendarza polskiego
cal = Poland()

# Funkcja do znalezienia pierwszego dnia roboczego w Polsce dla danego miesiąca i roku
def first_workday(year, month):
    # Zaczynamy od pierwszego dnia miesiąca
    first_day = datetime(year, month, 1)

    # Szukamy pierwszego dnia roboczego, iterując od pierwszego dnia miesiąca
    while not cal.is_working_day(first_day):
        first_day += timedelta(days=1)

    return first_day

# Katalog z backupami
backups_dir = '/storage2/proxmox-backup/vm/'
# Lista maszyn obsługiwanych przez PBS
machines = os.listdir(backups_dir)
# Wyczyszczenie listy z maszyn Crowd i innych niedziałających
machines_to_remove = ['101', '102', '103', '104', '106', '5003', '5004', '5002', '5006', '911', '5005', '5001', '5021']
for machine in machines_to_remove:
    machines.remove(machine)

# Funkcja do wyszukiwania pierwszego backupu i ustawiania protection mode
def set_protection(machine):
    # Pobieramy pierwszy dzień roboczy miesiąca
    first_workday_date = first_workday(current_year, current_month)
    formatted_date = first_workday_date.strftime("%Y-%m-%dT%H")

    # Wzorzec do wyszukiwania backupów z pierwszego dnia roboczego
    pattern = f"{backups_dir}/{machine}/{formatted_date}*"
    matching_files = glob.glob(pattern)

    if matching_files:
        for file in matching_files:
            snapshot_id = os.path.basename(file)
            command = f'proxmox-backup-client snapshot protected update vm/{machine}/{snapshot_id} true --repository NAVIGATOR2'
            print(f"Running command: {command}")
            subprocess.run(command, shell=True)
            os.system(f'echo vm/{machine}/{snapshot_id} >> /root/protected_backups_list')
    else:
        print(f"No matching files for machine {machine} on the first workday {formatted_date}")

# Funkcja do wyszukiwania backupów starszych niż 5 lat i zdejmowania protection mode
def check_and_remove_protection(machine):
    # Definiujemy datę sprzed dokładnie 5 lat od dziś
    five_years_ago = datetime.now() - timedelta(days=5*365)  # 5 lat = 5 * 365 dni (przybliżenie)

    # Wzorzec do wyszukiwania wszystkich backupów dla maszyny
    pattern = f"{backups_dir}/{machine}/*"
    matching_files = glob.glob(pattern)

    # Wyrażenie regularne do wyciągnięcia daty w formacie YYYY-MM-DD z nazwy snapshotu
    date_regex = re.compile(r'(\d{4})-(\d{2})-(\d{2})')

    for file in matching_files:
        # Wydobycie snapshot_id
        snapshot_id = os.path.basename(file)
        # Próba dopasowania daty w formacie YYYY-MM-DD
        match = date_regex.search(snapshot_id)

        if match:
            try:
                # Konwersja daty ze stringa na obiekt datetime
                snapshot_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))

                # Sprawdzenie, czy backup jest starszy niż 5 lat
                if snapshot_date < five_years_ago:  # Usuwamy ochronę tylko dla kopii starszych niż 5 lat
                    # Sprawdzenie, czy snapshot ma włączoną ochronę
                    command_check = f'proxmox-backup-client snapshot protected show vm/{machine}/{snapshot_id} --repository NAVIGATOR2'
                    result = subprocess.run(command_check, shell=True, capture_output=True, text=True)

                    if 'protected: true' in result.stdout:
                        # Jeśli ma ochronę, zdejmujemy ją
                        command_remove = f'proxmox-backup-client snapshot protected update vm/{machine}/{snapshot_id} false --repository NAVIGATOR2'
                        print(f"Running command to remove protection: {command_remove}")
                        subprocess.run(command_remove, shell=True)
                        os.system(f'echo vm/{machine}/{snapshot_id} >> /root/unprotected_backups_list')
                    else:
                        print(f"Snapshot {snapshot_id} nie jest chroniony.")
                else:
                    print(f"Snapshot {snapshot_id} nie jest starszy niż 5 lat. Ochrona pozostaje.")
            except Exception as e:
                print(f"Błąd przy przetwarzaniu snapshotu {snapshot_id}: {str(e)}")
        else:
            print(f"Nie można dopasować daty do snapshotu {snapshot_id}, pomijam ten plik.")

# Uruchomienie funkcji ustawiania protection mode dla wszystkich maszyn
for machine in machines:
    set_protection(machine)

# Uruchomienie funkcji sprawdzania i usuwania protection mode dla starszych niż 5 lat
for machine in machines:
    check_and_remove_protection(machine)
