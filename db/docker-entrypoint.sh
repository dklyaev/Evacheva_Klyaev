#!/bin/bash

set -e

# Осуществляем проверку наличия переменных окружения
if [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] || [ -z "$POSTGRES_DB" ]; then
    echo "Осуществите обозначение переменные окружения POSTGRES_USER, POSTGRES_PASSWORD и POSTGRES_DB"
    exit 1
fi

# В случае определения переменных окружения используем устаревшие 
PGUSER="${PGUSER:-$POSTGRES_USER}"
PGPASSWORD="${PGPASSWORD:-$POSTGRES_PASSWORD}"

# Экспорт переменной окружения PGPASSWORD
export PGPASSWORD="$POSTGRES_PASSWORD"

# Инициализируем базу данных
initialize_database() {
    # Далее создадим директорию для данных PostgreSQL
    mkdir -p "$PGDATA"
    chmod 700 "$PGDATA"

    # В случае если база данных еще не инициализирована, инициализируем   if [ ! -f "$PGDATA/PG_VERSION" ]; then
        if [ -z "$REPLICATE_FROM" ]; then
            # Инициализация
            echo "Инициализация новой БД PostgreSQL"
            initdb -D "$PGDATA"
        else
            # Репликация из мастера
            echo "Репликация базы данных PostgreSQL из $REPLICATE_FROM"
            pg_basebackup -h "$REPLICATE_FROM" -P -D "$PGDATA"
        fi
    fi

    # Конфигурируем pg_hba.conf
    echo "host all all 0.0.0.0/0 trust" >> "$PGDATA/pg_hba.conf"

    postgres -D "$PGDATA" &
    POSTGRES_PID=$!

    # Осуществляем создание необходимого пользователя и базы данных
    createuser -s "$PGUSER"
    createdb -O "$PGUSER" "$POSTGRES_DB"
}

# Функция для инициализации
run_initialization_scripts() {
        for f in /docker-entrypoint-initdb.d/*; do
        case "$f" in
            *.sh)
                echo "$0: выполнение $f"
                . "$f"
                ;;
            *.sql)
                echo "$0: выполнение $f"
                psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" < "$f"
                ;;
            *.sql.gz)
                echo "$0: выполнение $f"
                gunzip -c "$f" | psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"
                ;;
            *)
                echo "$0: пропуск $f"
                ;;
        esac
    done
}

# Инициализация БД
initialize_database
run_initialization_scripts

# Если БД инициализирована (а не реплицирована), останавливаем PostgreSQL
if [ -z "$REPLICATE_FROM" ]; then
    echo "Осуществляем остановку внутреннего PostgreSQL"
    pg_ctl -D "$PGDATA" stop
fi

echo "Инициализация PostgreSQL осуществлена"

