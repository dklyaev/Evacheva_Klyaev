import random
import time
import logging
import psycopg2
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s: %(message)s')

@contextmanager
def get_connection(dbname, user, password, host, port):
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    try:
        yield conn
    finally:
        conn.close()

def check_server_availability(cursor):
    try:
        cursor.execute("SELECT 1")
        return True
    except psycopg2.OperationalError:
        return False

def insert_data():
    with get_connection('benchmark', 'postgres', 'postgres', 'localhost', '5432') as conn_master, \
         get_connection('benchmark', 'postgres', 'postgres', 'localhost', '5433') as conn_slave:
        with conn_master.cursor() as cur_master, conn_slave.cursor() as cur_slave:
            def task(i):
                time.sleep(random.choice([1, 2, 3]))
                if check_server_availability(cur_master):
                    logging.warning(f'Основной сервер на данный момент не доступен')
                elif check_server_availability(cur_slave):
                    logging.warning(f'Сервер-репликации доступен')
                else:
                    logging.error(f'Не получиось осуществить успешное  подключение ни к одному из серверов')

            with ThreadPoolExecutor(max_workers=8) as executor:
                [executor.submit(task, i) for i in range(500000)]

def select_value():
    with get_connection('benchmark', 'postgres', 'postgres', 'localhost', '5432') as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM test")
            print(cur.fetchall())
            conn.commit()

if __name__ == '__main__':
    try:
        with get_connection('benchmark', 'postgres', 'postgres', 'localhost', '5432') as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS test(id int)")
                conn.commit()
    except psycopg2.Error:
        pass

    insert_data()
    select_value()
