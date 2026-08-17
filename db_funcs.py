import os
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

import streamlit as st
from sqlalchemy import create_engine, exc, text
from sqlalchemy.engine import RowMapping

DATABASE_URL = os.environ.get("DATABASE_URL") or st.secrets.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

@st.cache_resource
def get_database_engine():
    url = DATABASE_URL
    if not url:
        raise ValueError("No database URL found.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
        
    return create_engine(
        url,
        pool_size=5,
        pool_recycle=1800,
        pool_pre_ping=True
    )

engine = get_database_engine()


# ------------------- Initialization functions -------------------

def init_puzzles_db() -> None:
    query = text("""
        CREATE TABLE IF NOT EXISTS puzzles
            (puzzle_order INTEGER UNIQUE DEFAULT NULL,
            name TEXT,
            activation_code TEXT DEFAULT NULL,
            solution TEXT,
            hint TEXT,
            filename TEXT DEFAULT NULL,
            location TEXT DEFAULT '|')
    """)
    with engine.begin() as conn:
        conn.execute(query)


def init_teams_db() -> None:
    query = text("""
        CREATE TABLE IF NOT EXISTS teams
            (id SERIAL PRIMARY KEY,
            team_color TEXT UNIQUE,
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
            team_id INTEGER REFERENCES teams(id),
            puzzle_order INTEGER REFERENCES puzzles(puzzle_order),
            action TEXT,  -- possible actions: begin, hint, dead, submit
            time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP)
    """)
    with engine.begin() as conn:
        conn.execute(query)


def init_submissions_db() -> None:
    query = text("""
        CREATE TABLE IF NOT EXISTS submissions
            (id SERIAL PRIMARY KEY,
            team_id INTEGER REFERENCES teams(id),
            puzzle_order INTEGER REFERENCES puzzles(puzzle_order),
            input TEXT,
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


def init_settings_db() -> None:
    query = text("""
        CREATE TABLE IF NOT EXISTS app_settings
            (key TEXT PRIMARY KEY,
            value TEXT NOT NULL)
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
    except exc.IntegrityError:
        return False


def remove_team(team_color: str) -> bool:
    query = text("""
        DELETE FROM teams
        WHERE team_color = :team_color
    """)
    with engine.begin() as conn:
        result = conn.execute(query, {"team_color": team_color})
        return result.rowcount > 0


def edit_team(team_color: str, team_name: str, password: str, points: str, total_time: timedelta | None) -> bool:
    select_query = text("""
        SELECT team_name, password, points, total_time FROM teams
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
        if not user_data:
            return False
        team_name = team_name if team_name else user_data[0]
        password = password if password else user_data[1]
        points = points if points else user_data[2]
        total_time = total_time if total_time else user_data[3]
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


def remove_puzzle(name: str) -> bool:
    query = text("""
        DELETE FROM puzzles
        WHERE name = :name
    """)
    with engine.begin() as conn:
        result = conn.execute(query, {"name": name})
        return result.rowcount > 0


def edit_puzzle(name: str, order: int | None, activation_code: str, solution: str,
                hint: str, filename: str, location: str) -> bool:
    select_query = text("""
        SELECT * FROM puzzles
        WHERE name = :name
    """)
    update_query = text("""
        UPDATE puzzles SET
            puzzle_order = :order,
            name = :name,
            activation_code = :activation_code,
            solution = :solution,
            hint = :hint,
            filename = :filename,
            location = :location
        WHERE name = :name
    """)
    try:
        with engine.begin() as conn:
            result = conn.execute(select_query, {"name": name})
            if result.rowcount == 0:
                return False
            puzzle_data = result.fetchone()
            if not puzzle_data:
                return False
            order = order if order else puzzle_data[0]
            name = name if name else puzzle_data[1]
            activation_code = activation_code if activation_code else puzzle_data[2]
            solution = solution if solution else puzzle_data[3]
            hint = hint if hint else puzzle_data[4]
            filename = filename if filename else puzzle_data[5]
            location = location if location else puzzle_data[6]
            conn.execute(update_query, {"name": name, "order": order,
                                        "activation_code": activation_code,
                                        "solution": solution, "hint": hint,
                                        "filename": filename,
                                        "location": location})
            return True
    except exc.IntegrityError:
        return False


def execute_query(input_query: str) -> tuple[bool, list[dict[str, Any]]]:
    query = text(input_query)
    with engine.begin() as conn:
        try:
            result = conn.execute(query)
            if result.returns_rows:
                return True, [dict(row._mapping) for row in result.fetchall()]
            return True, []
        except exc.SQLAlchemyError as e:
            return False, [{"error": e}]

# ----------------------- Logging functions -----------------------

def log_login_attempt(input_username: str | None, password: str, ip_address: str | None, user_agent: str | None) -> None:
    query = text("""
        INSERT INTO login_attempts 
            (input_username, password, ip_address, user_agent)
        VALUES
            (:input_username, :password, :ip_address, :user_agent)
    """)
    with engine.begin() as conn:
        conn.execute(query, {"input_username": input_username, "password": password, "ip_address": ip_address, "user_agent": user_agent})


def log_action(team_id: int, puzzle_order: int, action: str) -> None:
    query = text("""
        INSERT INTO actions
            (team_id, puzzle_order, action)
        VALUES
            (:team_id, :puzzle_order, :action)
    """)
    with engine.begin() as conn:
        conn.execute(query, {"team_id": team_id, "puzzle_order": puzzle_order, "action": action})

# ----------------------- Display functions -----------------------

def get_leaderboard() -> Sequence[RowMapping]:
    query = text("""
        SELECT
            ROW_NUMBER() OVER (
                ORDER BY points DESC, total_time ASC
            ) AS "Pořadí",
            team_color AS "Barva týmu",
            team_name AS "Jméno týmu",
            points AS "Body",
            TO_CHAR(total_time, 'FMHH24 "h" FMMI "m" FMSS "s"') AS "Celkový čas"
        FROM teams
        ORDER BY points DESC, total_time ASC
    """)
    with engine.connect() as conn:
        return conn.execute(query).mappings().all()


def get_action_log() -> Sequence[RowMapping]:
    query = text("""
        SELECT
            a.id,
            t.team_color AS "Barva týmu",
            a.puzzle_order AS "Pořadí šifry",
            a.action AS "Akce",
            TO_CHAR(a.time AT TIME ZONE 'Europe/Bratislava', 'YYYY-MM-DD HH24:MI:SS') AS "Datum a čas"
        FROM actions a
        LEFT JOIN teams t ON a.team_id = t.id
    """)
    with engine.connect() as conn:
        return conn.execute(query).mappings().all()


def get_submissions() -> Sequence[RowMapping]:
    query = text("""
        SELECT
            s.id,
            t.team_color AS "Barva týmu",
            s.puzzle_order AS "Pořadí šifry",
            s.input AS "Input",
            s.correct AS "Správně",
            TO_CHAR(s.time AT TIME ZONE 'Europe/Bratislava', 'YYYY-MM-DD HH24:MI:SS') AS "Datum a čas"
        FROM submissions s
        LEFT JOIN teams t ON s.team_id = t.id
    """)
    with engine.connect() as conn:
        return conn.execute(query).mappings().all()


def get_login_attempts() -> Sequence[RowMapping]:
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


def get_puzzles() -> Sequence[RowMapping]:
    query = text("""
        SELECT
            puzzle_order as "Pořadí",
            name AS "Název",
            activation_code AS "Aktivační kód",
            solution AS "Heslo",
            hint AS "Nápověda",
            filename as "Název souboru",
            location as "Lokace šifry"
        FROM puzzles
        ORDER BY puzzle_order
    """)
    with engine.connect() as conn:
        return conn.execute(query).mappings().all()

# ----------------------- Puzzle functions -----------------------

@st.cache_data(ttl=600)
def get_active_puzzles() -> list[str]:
    query = text("""
        SELECT puzzle_order FROM puzzles
        WHERE puzzle_order IS NOT NULL
        ORDER BY puzzle_order
    """)
    with engine.connect() as conn:
        result = conn.execute(query).fetchall()
    return ["puzzle_" + str(row[0]) for row in result]


def get_puzzle_name(puzzle_order: int) -> str:
    query = text("""
        SELECT name FROM puzzles
        WHERE puzzle_order = :puzzle_order
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"puzzle_order": puzzle_order}).one()
        return result[0]


def get_puzzle_activation_code(puzzle_order: int) -> str:
    query = text("""
        SELECT activation_code FROM puzzles
        WHERE puzzle_order = :puzzle_order
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"puzzle_order": puzzle_order}).one()
        return result[0]


def get_puzzle_solution(puzzle_order: int) -> str:
    query = text("""
        SELECT solution FROM puzzles
        WHERE puzzle_order = :puzzle_order
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"puzzle_order": puzzle_order}).one()
        return result[0]


def get_puzzle_location(puzzle_order: int) -> str:
    query = text("""
        SELECT location FROM puzzles
        WHERE puzzle_order = :puzzle_order
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"puzzle_order": puzzle_order}).one()
        return result[0]


def get_puzzle_hint(puzzle_order: int) -> str:
    query = text("""
        SELECT hint FROM puzzles
        WHERE puzzle_order = :puzzle_order
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"puzzle_order": puzzle_order}).one()
        return result[0]


def get_current_puzzle(team_id: int) -> int:
    query = text("""
        SELECT puzzle_order FROM submissions
        WHERE team_id = :team_id AND correct = TRUE
        ORDER BY puzzle_order DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"team_id": team_id}).fetchone()
        return result[0]+1 if result else 1


def get_start_time(team_id: int, puzzle_order: int) -> datetime:
    query = text("""
        SELECT time FROM actions
        WHERE
            team_id = :team_id AND
            puzzle_order = :puzzle_order AND
            action = 'begin'
    """)
    with engine.connect() as conn:
        return conn.execute(query, {"team_id": team_id,
                                    "puzzle_order": puzzle_order}).scalar_one()


def get_incorrect_attempts(team_id: int, puzzle_order: int) -> int:
    query = text("""
        SELECT * FROM submissions
        WHERE
            team_id = :team_id AND
            puzzle_order = :puzzle_order AND
            correct = FALSE
    """)
    with engine.connect() as conn:
        return conn.execute(query, {"team_id": team_id,
                                    "puzzle_order": puzzle_order}).rowcount


def is_activated(team_id: int, puzzle_order: int) -> bool:
    query = text("""
        SELECT * FROM actions
        WHERE
            team_id = :team_id AND
            puzzle_order = :puzzle_order AND
            action = 'begin'
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"team_id": team_id, "puzzle_order": puzzle_order})
        return result.rowcount > 0


def is_hinted(team_id: int, puzzle_order: int) -> bool:
    query = text("""
        SELECT * FROM actions
        WHERE
            team_id = :team_id AND
            puzzle_order = :puzzle_order AND
            action = 'hint'
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"team_id": team_id, "puzzle_order": puzzle_order})
        return result.rowcount > 0


def is_deaded(team_id: int, puzzle_order: int) -> bool:
    query = text("""
        SELECT * FROM actions
        WHERE
            team_id = :team_id AND
            puzzle_order = :puzzle_order AND
            action = 'dead'
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"team_id": team_id, "puzzle_order": puzzle_order})
        return result.rowcount > 0


def check_hint_eligiblity(team_id: int, puzzle_order: int) -> bool:
    start_time = get_start_time(team_id, puzzle_order)
    return (datetime.now(timezone.utc) - start_time) >= timedelta(minutes=15)


def check_dead_eligiblity(team_id: int, puzzle_order: int) -> bool:
    if not is_hinted(team_id, puzzle_order):
        return False
    start_time = get_start_time(team_id, puzzle_order)
    return (datetime.now(timezone.utc) - start_time) >= timedelta(minutes=30)


def dead_puzzle(team_id: int, puzzle_order: int) -> None:
    submit_solution(team_id, puzzle_order, get_puzzle_solution(puzzle_order))


def submit_solution(team_id: int, puzzle_order: int, input_solution: str) -> bool:
    query = text("""
        INSERT INTO submissions
            (team_id, puzzle_order, input, correct)
        VALUES
            (:team_id, :puzzle_order, :input_solution, :is_correct)
    """)
    solution = get_puzzle_solution(puzzle_order)
    is_correct = solution == input_solution
    with engine.begin() as conn:
        conn.execute(query, {"team_id": team_id, "puzzle_order": puzzle_order,
                             "input_solution": input_solution, "is_correct": is_correct})
        if is_correct:
            start_time = get_start_time(team_id, puzzle_order)
            add_time(team_id, start_time)
            if not is_deaded(team_id, puzzle_order):
                if is_hinted(team_id, puzzle_order):
                    add_points(team_id, 1)
                else:
                    if get_incorrect_attempts(team_id, puzzle_order) > 1:
                        add_points(team_id, 1)
                    else:
                        add_points(team_id, 2)

        return is_correct

# ------------------------ Other functions ------------------------

def check_login(input_username: str, password: str) -> int | None:
    query = text("""
        SELECT id FROM teams
        WHERE :input_username IN (team_color, team_name) 
        AND :password IN (initial_password, password)
    """)
    with engine.connect() as conn:
        result = conn.execute(query, {"input_username": input_username, "password": password}).fetchone()
        return result[0] if result is not None else None


def set_password(team_id: int, new_password: str) -> None:
    query = text("""
        UPDATE teams SET
            password = :password
        WHERE id = :team_id
    """)
    with engine.begin() as conn:
        conn.execute(query, {"team_id": team_id, "password": new_password})


def add_points(team_id: int, amount: int) -> None:
    query = text("""
        UPDATE teams SET
            points = points + :amount
        WHERE
            id = :team_id
    """)
    with engine.begin() as conn:
        conn.execute(query, {"team_id": team_id, "amount": amount})


def add_time(team_id: int, start_time: datetime) -> None:
    query = text("""
        UPDATE teams SET
            total_time = total_time + NOW() - :start_time
        WHERE
            id = :team_id
    """)
    with engine.begin() as conn:
        conn.execute(query, {"team_id": team_id, "start_time": start_time})


def get_setting(setting: str) -> bool:
    query = text("""
        SELECT value FROM app_settings
        WHERE
            key = :setting
    """)
    with engine.connect() as conn:
        return conn.execute(query, {"setting": setting}).one()[0] == "true"
