#!/bin/sh
echo "Starting urlshort."
cd /deploy
# sleep to let db startup
sleep 10s
python urlshort_app.py fig.ini
