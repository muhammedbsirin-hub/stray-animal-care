"""
(Re)creates the database from the SQL files:  01 -> 02 -> 03 -> 05
Run from the project root:   python tools/setup_database.py
Needs: 00_setup_user.sql executed once as root, and the .env file.
WARNING: drops and recreates stray_db (all data is reset to the sample data).
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app.config import DB_CONFIG

FILES = ["01_schema.sql", "02_functions_views.sql", "03_procedures_triggers.sql", "05_seed_data.sql"]


def find_mysql():
    found = shutil.which("mysql")
    if found:
        return found
    base = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "MySQL"
    for exe in sorted(base.glob("MySQL Server */bin/mysql.exe"), reverse=True):
        return str(exe)
    sys.exit("mysql client not found. Run the SQL files in MySQL Workbench instead (01, 02, 03, 05).")


def main():
    mysql = find_mysql()
    env = dict(os.environ, MYSQL_PWD=DB_CONFIG["password"])
    for name in FILES:
        path = ROOT / "database" / name
        print(f"running {name} ...", flush=True)
        with open(path, "rb") as fh:
            result = subprocess.run([mysql, "-h", DB_CONFIG["host"], "-P", str(DB_CONFIG["port"]),
                                     "-u", DB_CONFIG["user"], "--default-character-set=utf8mb4"],
                                    stdin=fh, env=env, capture_output=True)
        if result.returncode != 0:
            print(result.stderr.decode("utf-8", "replace"))
            sys.exit(f"FAILED in {name}")
    print("Database is ready.")


if __name__ == "__main__":
    main()
