#!/usr/bin/env bash

SOURCE="${BASH_SOURCE[0]}"
DIR="$( dirname "$SOURCE" )"
cd $DIR

crontab -l > /tmp/jobs.txt   #save existing jobs
echo "* * * * * curl http://172.105.86.177/monitor/monitor/routine" >> /tmp/jobs.txt  #add the desired job for 1st every month
# echo "* * * * * curl http://172.105.86.177/monitor/monitor/send_sms" >> /tmp/jobs.txt
crontab /tmp/jobs.txt    #import all jobs
