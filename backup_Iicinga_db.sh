#!/bin/bash

set -ex
DATE=`date +%d-%m-%y`

# Create directory to copy files for back up
TEMP_DIR="/var/backup_db/backup_icinga_db_${DATE}/"
mkdir -p ${TEMP_DIR}
cd /home/postgres
sudo -u postgres pg_dumpall > /home/postgres/backup_icinga_db_${DATE}.bak

# Copy files to backup directory
cp /home/postgres/backup_icinga_db_${DATE}.bak ${TEMP_DIR}
rsync -aRv /var/lib/icinga2 ${TEMP_DIR}
rsync -aRv /etc/icinga2 ${TEMP_DIR}
rsync -aRv /etc/icingaweb2 ${TEMP_DIR}

# Create a tarball with the backup
cd /var/backup_db/
tar -czvf backup_icinga_db_${DATE}.tar.gz ./backup_icinga_db_${DATE}

# Remove temp dir
rm -rf ${TEMP_DIR}
rm /home/postgres/backup_icinga_db_${DATE}.bak

# Copy files to Archive server (Read script bellow for more information)
/root/utils/rSyncBackups.sh -u root -r snf-11813.ok-kno.grnetcloud.net -k ~/.ssh/id_rsa -f /var/backup_db/backup_icinga_db_${DATE}.tar.gz -t /home/backups/icinga
