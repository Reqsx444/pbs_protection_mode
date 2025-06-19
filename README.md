# PBS Custom Protection Mode
## Intruduction
pbs_protection_mode is a Python automation script designed to manage snapshot protection on a Proxmox Backup Server (PBS). \
It performs two main functions:
- Automatically protects the first working day snapshot of each virtual machine
- Removes protection from snapshots older than 5 years
