import streamlit as st
import os
from datetime import timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import RowMapping


DATABASE_URL = os.environ.get("DATABASE_URL") or st.secrets.get("DATABASE_URL")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

@st.cache_resource
def get_database_engine():
    url = DATABASE_URL
    if url and url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    return create_engine(
        url,
        pool_size=5,
        pool_recycle=1800,
        pool_pre_ping=True
    )

engine = get_database_engine()


# ------------------- Initialization functions -------------------

def init_teams_db() -> None:
    query = text("""
        CREATE TABLE IF NOT EXISTS teams
            (team_color TEXT PRIMARY KEY,
            team_name TEXT DEFAULT NULL,
            initial_password TEXT,
            password TEXT DEFAULT NULL,
            points INTEGER DEFAULT 0,
            total_time INTERVAL DEFAULT INTERVAL '0 seconds')
    """)
    with engine.begin() as conn:
        conn.execute(query)


def init_actions_db() -> None:
    query = text("""
        CREATE TABLE IF NOT EXISTS actions
            (id SERIAL PRIMARY KEY,
            team_color TEXT,
            puzzle_id INTEGER REFERENCES puzzles(id),
            action TEXT,  -- possible actions: begin, hint, dead, submit
            input TEXT DEFAULT NULL,
            correct BOOLEAN,
            time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)
    """)
    with engine.begin() as conn:
        conn.execute(query)


def init_logging_db() -> None:
    query = text("""
        CREATE TABLE IF NOT EXISTS login_attempts
            (id SERIAL PRIMARY KEY,
            input_username TEXT DEFAULT NULL,
            password TEXT,
            ip_address TEXT,
            user_agent TEXT,
            time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)
    """)
    with engine.begin() as conn:
        conn.execute(query)


def init_puzzles_db() -> None:
    query = text("""
        CREATE TABLE IF NOT EXISTS puzzles
            (id SERIAL PRIMARY KEY,
            name TEXT,
            begin_code TEXT DEFAULT NULL,
            solution TEXT)
    """)
    with engine.begin() as conn:
        conn.execute(query)

# ------------------------ Admin functions ------------------------

def create_team(team_color: str, initial_password: str) -> bool:
    query = text("""
        INSERT INTO teams 
            (team_color, initial_password)
        VALUES 
            (:team_color, :password)
    """)
    try:
        with engine.begin() as conn:
            conn.execute(query, {"team_color": team_color, 
                                 "password": initial_password})
            return True
    except IntegrityError:
        return False


def remove_team(team_color: str) -> bool:
    query = text("""
        DELETE FROM teams
        WHERE team_color = :team_color
    """)
    with engine.begin() as conn:
        result = conn.execute(query, {"team_color": team_color})
        return result.rowcount > 0


def edit_team(team_color: str, team_name: str, password: str, points: str, total_time: str) -> bool:
    if len(total_time) > 0 and not total_time.isdigit():
        return False

    select_query = text("""
        SELECT * FROM teams
        WHERE team_color = :team_color
    """)
    update_query = text("""
        UPDATE teams SET 
            team_name = :team_name,
            password = :password,
            points = :points,
            total_time = :total_time
        WHERE team_color = :team_color
    """)
    with engine.begin() as conn:
        result = conn.execute(select_query, {"team_color": team_color})
        if result.rowcount == 0:
            return False
        user_data = result.fetchone()
        team_name = team_name if team_name else user_data[1]
        password = password if password else user_data[3]
        points = points if points else user_data[4]
        total_time = timedelta(seconds=int(total_time)) if len(total_time) > 0 else user_data[5]
        conn.execute(update_query, {"team_color": team_color, "team_name": team_name,
                                    "password": password, "points": points,
                                    "total_time": total_time})
        return True


def create_puzzle(name: str, solution: str) -> None:
    query = text("""
        INSERT INTO puzzles
            (name, solution)
        VALUES
            (:name, :solution)
    """)
    with engine.begin() as conn:
        conn.execute(query, {"name": name, "solution": solution})


def remove_puzzle(puzzle_id: str) -> bool:
    query = text("""
        DELETE FROM puzzles
        WHERE id = :puzzle_id
    """)
    with engine.begin() as conn:
        result = conn.execute(query, {"puzzle_id": puzzle_id})
        return result.rowcount > 0


def edit_puzzle(puzzle_id: str, name: str, begin_code: str, solution: str) -> bool:
    select_query = text("""
        SELECT * FROM puzzles
        WHERE id = :puzzle_id
    """)
    update_query = text("""
        UPDATE puzzles SET 
            name = :name,
            begin_code = :begin_code,
            solution = :solution
        WHERE id = :puzzle_id
    """)
    with engine.begin() as conn:
        result = conn.execute(select_query, {"puzzle_id": puzzle_id})
        if result.rowcount == 0:
            return False
        puzzle_data = result.fetchone()
        name = name if name else puzzle_data[1]
        begin_code = begin_code if begin_code else puzzle_data[2]
        solution = solution if solution else puzzle_data[3]
        conn.execute(update_query, {"name": name, "begin_code": begin_code,
                              "solution": solution})
        return True

# ----------------------- Logging functions -----------------------

def log_login_attempt(input_username: str | None, password: str, ip_address: str, user_agent: str) -> None:
    query = text("""
        INSERT INTO login_attempts 
            (input_username, password, ip_address, user_agent)
        VALUES
            (:input_username, :password, :ip_address, :user_agent)
    """)
    with engine.begin() as conn:
        conn.execute(query, {"input_username": input_username, "password": password, "ip_address": ip_address, "user_agent": user_agent})


def log_action(team_color: str, puzzle_id: str, action: str, input_data: str) -> None:
    query = text("""
        INSERT INTO actions
            (team_color, puzzle_id, action, input)
        VALUES
            (:team_color, :puzzle_id, :action, :input_data)
    """)
    with engine.begin() as conn:
        conn.execute(query, {"team_color": team_color, "puzzle_id": puzzle_id, "action": action, "input_data": input_data})

# ----------------------- Display functions -----------------------

def get_leaderboard() -> list[RowMapping]:
    query = text("""
        SELECT
            team_color AS "Barva týmu",
            team_name AS "Jméno týmu",
            points AS "Body",
            TO_CHAR(total_time, 'FMHH24 "h" FMMI "m" FMSS "s"') AS "Čas"
        FROM teams ORDER BY points DESC, total_time ASC
    """)
    with engine.connect() as conn:
        return conn.execute(query).mappings().all()


def get_action_log() -> list[RowMapping]:
    query = text("""
        SELECT
            id,
            team_color AS "Barva týmu",
            action AS "Akce",
            input AS "Input",
            correct AS "Správně",
            TO_CHAR(time AT TIME ZONE 'Europe/Bratislava', 'YYYY-MM-DD HH24:MI:SS') AS "Datum a čas"
        FROM actions
    """)
    with engine.connect() as conn:
        return conn.execute(query).mappings().all()


def get_login_attempts() -> list[RowMapping]:
    query = text("""
        SELECT
            id,
            input_username AS "Input",
            password AS "Heslo",
            ip_address AS "IP adresa",
            user_agent AS "Agent",
            TO_CHAR(time AT TIME ZONE 'Europe/Bratislava', 'YYYY-MM-DD HH24:MI:SS') AS "Datum a čas"
        FROM login_attempts
    """)
    with engine.connect() as conn:
        return conn.execute(query).mappings().all()


def get_puzzles() -> list[RowMapping]:
    query = text("""
        SELECT
            id,
            name AS "Název",
            begin_code AS "Aktivační kód",
            solution AS "Heslo"
        FROM puzzles
    """)
    with engine.connect() as conn:
        return conn.execute(query).mappings().all()

# ------------------------ Other functions ------------------------

def check_login(input_username: str, password: str) -> bool:
    query = text("""SELECT * FROM teams WHERE :input_username IN (team_color, team_name) AND :password IN (initial_password, password)""")
    with engine.connect() as conn:
        result = conn.execute(query, {"input_username": input_username, "password": password})
        return result.fetchone() is not None


def process_action(team_color: str, puzzle_id: int, action: str, input: str) -> bool:
    pass
