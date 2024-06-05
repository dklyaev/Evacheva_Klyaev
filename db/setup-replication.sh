#!/bin/bash

set -e

# Осуществляем проверку наличие переменных окружения
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$PGDATA" ] || [ -z "$PG_MAX_WAL_SENDERS" ] || [ -z "$PG_WAL_KEEP_SEGMENTS" ]; then
    echo "Осуществите установку переменных окружения POSTGRES_USER, POSTGRES_PASSWORD, PGDATA, PG_MAX_WAL_SENDERS и PG_WAL_KEEP_SEGMENTS"
    exit 1
fi

# В случае, если переменные окружения определены, используем устаревшие 
PGUSER="${PGUSER:-$POSTGRES_USER}"
PGPASSWORD="${PGPASSWORD:-$POSTGRES_PASSWORD}"

# Экспорт PGPASSWORD
export PGPASSWORD="$POSTGRES_PASSWORD"

# Конфигурация PostgreSQL
configure_postgresql() {
    if [ -z "$REPLICATE_FROM" ]; then
        cat >> "$PGDATA/postgresql.conf" <<EOF
wal_level = hot_standby
max_wal_senders = $PG_MAX_WAL_SENDERS
wal_keep_segments = $PG_WAL_KEEP_SEGMENTS
hot_standby = on
synchronous_commit = off
EOF
    else
        # Конфигурация реплики
        cat > "$PGDATA/recovery.conf" <<EOF
standby_mode = on
primary_conninfo = 'host=$REPLICATE_FROM port=5432 user=$POSTGRES_USER password=$POSTGRES_PASSWORD'
trigger_file = '/tmp/promote_me_to_master'
EOF
        chown postgres "$PGDATA/recovery.conf"
        chmod 600 "$PGDATA/recovery.conf"
    fi
}

# Конфигурация postgresql
configure_postgresql

echo "Была осуществлена успешная конфигурация PostgreSQL"

