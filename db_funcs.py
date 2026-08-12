import streamlit as st
import os
from datetime import timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


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
        action TEXT,  -- possible actions: begin, hint, dead, submit
        input TEXT DEFAULT NULL,
        correct BOOLEAN DEFAULT NULL,
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


def check_login(input_username: str, password: str) -> bool:
    query = text("""SELECT * FROM teams WHERE :input_username IN (team_color, team_name) AND :password IN (initial_password, password)""")
    with engine.connect() as conn:
        result = conn.execute(query, {"input_username": input_username, "password": password})
        return result.fetchone() is not None


def create_team(team_color: str, initial_password: str) -> bool:
    query = text("""INSERT INTO teams (team_color, initial_password) VALUES (:team_color, :password)""")
    try:
        with engine.begin() as conn:
            conn.execute(query, {"team_color": team_color, "password": initial_password})
            return True
    except IntegrityError:
        return False


def remove_team(team_color: str) -> bool:
    query = text("""DELETE FROM teams WHERE team_color= :team_color""")
    with engine.begin() as conn:
        result = conn.execute(query, {"team_color": team_color})
        return result.rowcount > 0


def edit_team(team_color: str, team_name: str, password: str, points: str, total_time: str) -> bool:
    if len(total_time) > 0 and not total_time.isdigit():
        return False
    query1 = text("""SELECT * FROM teams WHERE team_color= :team_color""")
    query2 = text("""
        UPDATE teams SET 
            team_name= :team_name,
            password= :password,
            points= :points,
            total_time= :total_time
        WHERE team_color= :team_color""")
    with engine.begin() as conn:
        result = conn.execute(query1, {"team_color": team_color})
        if result.rowcount == 0:
            return False
        user_data = result.fetchone()
        team_name = team_name if team_name else user_data[1]
        password = password if password else user_data[3]
        points = points if points else user_data[4]
        total_time = timedelta(seconds=int(total_time)) if len(total_time) > 0 else user_data[5]
        conn.execute(query2, {"team_color": team_color, "team_name": team_name, "password": password, "points": points, "total_time": total_time})
        return True
