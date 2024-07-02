#!/usr/bin/env bash

make install && psql $DATABASE_URL -a -f database.sql