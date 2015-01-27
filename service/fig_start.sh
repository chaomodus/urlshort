#!/bin/sh
#
# this script starts the system after being orchestrated by fig.
#
echo "Starting urlshort."
cd /deploy
# sleep to let db startup
sleep 10s
python urlshort_app.py fig.ini
