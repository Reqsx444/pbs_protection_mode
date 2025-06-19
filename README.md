# PBS Custom Protection Mode
## Intruduction
pbs_protection_mode is a Python automation script designed to manage snapshot protection on a Proxmox Backup Server (PBS). \
It performs two main functions:
- Automatically protects the first working day snapshot of each virtual machine
- Removes protection from snapshots older than 5 years

##  Requirements:
- Python 3.8+
- workalendar
- Access to proxmox-backup-client

## Usage
You can automate execution using a cron job. For example, to run the script daily at 9:00 AM: </br>
```
0 9 * * * root python3 pbs_protection_mode.py
```
If your PBS repository requires authentication (e.g. username and password), it is recommended to store credentials in environment variables rather than hardcoding them into the script.
```
export PBS_PASSWORD='your_secure_password'
export PBS_USER='your_username'
```
