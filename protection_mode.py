import os
import glob
from datetime import datetime, timedelta
import subprocess
import re
from workalendar.europe import Poland

current_month = datetime.now().month
current_year = datetime.now().year

cal = Poland()

def first_workday(year, month):
    first_day = datetime(year, month, 1)

    while not cal.is_working_day(first_day):
        first_day += timedelta(days=1)

    return first_day

backups_dir = '/data/proxmox-backup/vm/'
machines = os.listdir(backups_dir)
machines_to_remove = ['101', '102', '103', '104', '106', '5003', '5004', '5002', '5006', '911', '5005', '5001', '5021']
for machine in machines_to_remove:
    machines.remove(machine)

def set_protection(machine):
    first_workday_date = first_workday(current_year, current_month)
    formatted_date = first_workday_date.strftime("%Y-%m-%dT%H")

    pattern = f"{backups_dir}/{machine}/{formatted_date}*"
    matching_files = glob.glob(pattern)

    if matching_files:
        for file in matching_files:
            snapshot_id = os.path.basename(file)
            command = f'proxmox-backup-client snapshot protected update vm/{machine}/{snapshot_id} true --repository XYZ'
            print(f"Running command: {command}")
            subprocess.run(command, shell=True)
            os.system(f'echo vm/{machine}/{snapshot_id} >> /root/protected_backups_list')
    else:
        print(f"No matching files for machine {machine} on the first workday {formatted_date}")

def check_and_remove_protection(machine):
    five_years_ago = datetime.now() - timedelta(days=5*365)

    pattern = f"{backups_dir}/{machine}/*"
    matching_files = glob.glob(pattern)

    date_regex = re.compile(r'(\d{4})-(\d{2})-(\d{2})')

    for file in matching_files:
        snapshot_id = os.path.basename(file)
        match = date_regex.search(snapshot_id)

        if match:
            try:
                snapshot_date = datetime(int(match.group(1)), int(match.group(2)), int(match.group(3)))

                if snapshot_date < five_years_ago:
                    command_check = f'proxmox-backup-client snapshot protected show vm/{machine}/{snapshot_id} --repository XYZ'
                    result = subprocess.run(command_check, shell=True, capture_output=True, text=True)

                    if 'protected: true' in result.stdout:
                        command_remove = f'proxmox-backup-client snapshot protected update vm/{machine}/{snapshot_id} false --repository XYZ'
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

for machine in machines:
    set_protection(machine)

for machine in machines:
    check_and_remove_protection(machine)
