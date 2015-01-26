#!/bin/bash
echo "URLshort DB setups."
# gosu postgres postgres --single < /deploy/createdb.sql
echo "CREATE DATABASE urlshort;" | gosu postgres postgres --single
gosu postgres postgres --single urlshort < /deploy/urlshort.sql
echo "ALTER USER postgres WITH PASSWORD 'postgres';" | gosu postgres postgres --single
# echo "host all all 0.0.0.0/0 md5" >> /etc/postgresql/9.4/main/pg_hba.conf
