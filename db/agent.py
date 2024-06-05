import os
import time
import psycopg2
from psycopg2 import OperationalError
import requests
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

@dataclass
class DatabaseConfig:
    host: str
    port: str
    dbname: str
    user: str
    password: str
    role: str
    table: str

@dataclass
class DatabaseStatus:
    is_alive: bool
    is_master_alive: Optional[bool]

class PostgresAgent:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.table_name = "health_check"
        self.arbiter_url = "http://pg_arbiter:8000/health"
        self.check_interval = 10  # initial check interval

    def _create_table(self):
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name} (id SERIAL PRIMARY KEY)")
                    conn.commit()
        except OperationalError as e:
            logger.error(f"Error creating table '{self.table_name}': {e}")

    def _get_connection(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(
            dbname=self.config.dbname,
            user=self.config.user,
            password=self.config.password,
            port=self.config.port,
            host=self.config.host
        )

    def _get_arbiter_status(self) -> Optional[bool]:
        try:
            response = requests.get(self.arbiter_url)
            return response.json()["Master"] == "Alive"
        except (requests.exceptions.RequestException, KeyError) as e:
            logger.error(f"Error getting arbiter status: {e}")
            return None

    def check_status(self) -> DatabaseStatus:
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(f"SELECT 1 FROM {self.table_name} LIMIT 1")
                    conn.commit()
            is_alive = True
        except OperationalError as e:
            is_alive = False
            logger.error(f"Error checking database status: {e}")

        if self.config.role == "Slave":
            is_master_alive = self._get_arbiter_status()
        else:
            is_master_alive = None

        return DatabaseStatus(is_alive=is_alive, is_master_alive=is_master_alive)

    def promote_to_master(self):
        try:
            subprocess.run(["touch", "/tmp/promote_me_to_master"])
            logger.info("Promoted to master")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error promoting to master: {e}")

    def run(self):
        self._create_table()

        while True:
            status = self.check_status()
            if self.config.role == "Slave" and not status.is_alive and (status.is_master_alive is False):
                self.promote_to_master()
                self.check_interval = 10  # reset check interval
            else:
                self.check_interval = min(self.check_interval * 2, 600)  # increase interval up to 10 minutes
            time.sleep(self.check_interval)

if __name__ == "__main__":
    config = DatabaseConfig(
        host=os.environ['MASTER_HOST'],
        port='5432',
        dbname=os.environ['POSTGRES_DB'],
        user=os.environ['POSTGRES_USER'],
        password=os.environ['POSTGRES_PASSWORD'],
        role=os.environ['ROLE'],
        table='test_table'
    )
    agent = PostgresAgent(config)
    agent.run()
