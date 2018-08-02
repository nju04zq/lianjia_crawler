#!/bin/bash

REMOTE_PATH="~/lianjia_crawler"
TMP_FILE="/tmp/$(date +%s).log"

ssh ${VULTR} "${REMOTE_PATH}/lianjia_data.py export | tee ${TMP_FILE}"
fname=$(ssh ${VULTR} "grep -o -e 'data-[0-9]\+.tgz' ${TMP_FILE}")
scp ${VULTR}:${fname} .
ssh ${VULTR} rm ${TMP_FILE} ${fname}
./lianjia_data.py import ${fname}
echo "Import from ${fname}, this file not removed".
