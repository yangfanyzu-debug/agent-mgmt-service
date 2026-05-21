import os


class Settings:
    def __init__(self):
        self.db_host = os.getenv("AGENT_MGMT_DB_HOST", "43.135.134.42")
        self.db_port = int(os.getenv("AGENT_MGMT_DB_PORT", "3306"))
        self.db_name = os.getenv("AGENT_MGMT_DB_NAME", "ry-cloud")
        self.db_user = os.getenv("AGENT_MGMT_DB_USER", "root")
        self.db_password = os.getenv("AGENT_MGMT_DB_PASSWORD", os.getenv("MYSQL_PASSWORD", ""))
        self.db_charset = os.getenv("AGENT_MGMT_DB_CHARSET", "utf8mb4")


settings = Settings()
