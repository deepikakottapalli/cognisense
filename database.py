import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "cognisense.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP,
            bri_score    INTEGER NOT NULL,
            risk_level   TEXT NOT NULL,
            tone_label   TEXT NOT NULL,
            neg_score    REAL,
            keyword_hits INTEGER,
            session_tag  TEXT DEFAULT 'anonymous'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sharing_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER,
            timestamp   DATETIME DEFAULT CURRENT_TIMESTAMP,
            bri_score   INTEGER,
            risk_level  TEXT,
            center_name TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_session(bri_score: int, risk_level: str, tone_label: str,
                 neg_score: float, keyword_hits: int, input_text: str = None) -> int:
    """
    Save session result. input_text is accepted for API compatibility
    but intentionally discarded — never stored.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO sessions (bri_score, risk_level, tone_label, neg_score, keyword_hits)
        VALUES (?, ?, ?, ?, ?)
    """, (bri_score, risk_level, tone_label, neg_score, keyword_hits))
    session_id = c.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_recent_sessions(n: int = 5) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM sessions ORDER BY timestamp DESC LIMIT ?
    """, (n,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_sessions_last_n_days(n: int = 7) -> list:
    conn = get_connection()
    c = conn.cursor()
    since = (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        SELECT * FROM sessions WHERE timestamp >= ? ORDER BY timestamp DESC
    """, (since,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_all_sessions() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sessions ORDER BY timestamp DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_risk_counts(days: int = 7) -> dict:
    conn = get_connection()
    c = conn.cursor()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        SELECT risk_level, COUNT(*) as cnt
        FROM sessions
        WHERE timestamp >= ?
        GROUP BY risk_level
    """, (since,))
    result = {"low": 0, "medium": 0, "high": 0, "total": 0}
    for row in c.fetchall():
        key = row["risk_level"].lower()
        if key in result:
            result[key] = row["cnt"]
    result["total"] = result["low"] + result["medium"] + result["high"]
    conn.close()
    return result


def get_daily_breakdown(days: int = 7) -> list:
    conn = get_connection()
    c = conn.cursor()
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
        SELECT
            DATE(timestamp) as day,
            SUM(CASE WHEN risk_level = 'Low'    THEN 1 ELSE 0 END) as low,
            SUM(CASE WHEN risk_level = 'Medium' THEN 1 ELSE 0 END) as medium,
            SUM(CASE WHEN risk_level = 'High'   THEN 1 ELSE 0 END) as high,
            ROUND(AVG(bri_score), 1) as avg_bri,
            COUNT(*) as total
        FROM sessions
        WHERE timestamp >= ?
        GROUP BY DATE(timestamp)
        ORDER BY day DESC
    """, (since,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_7day_heatmap() -> list:
    """
    Returns one entry per day for the last 7 days.
    Days with no sessions get a placeholder entry.
    """
    conn = get_connection()
    c = conn.cursor()

    result = []
    today = datetime.now().date()

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")

        c.execute("""
            SELECT bri_score, risk_level, tone_label
            FROM sessions
            WHERE DATE(timestamp) = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (day_str,))
        row = c.fetchone()

        entry = {
            "date": day_str,
            "day_name": day.strftime("%a"),
            "short_date": day.strftime("%b %d"),
        }
        if row:
            entry.update({
                "bri_score": row["bri_score"],
                "risk_level": row["risk_level"],
                "tone_label": row["tone_label"],
                "has_data": True
            })
        else:
            entry.update({
                "bri_score": None,
                "risk_level": None,
                "tone_label": None,
                "has_data": False
            })
        result.append(entry)

    conn.close()
    return result


def delete_session_by_id(session_id: int) -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    affected = c.rowcount
    conn.commit()
    conn.close()
    return affected > 0


def delete_all_sessions() -> bool:
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM sessions")
    c.execute("DELETE FROM sharing_log")
    conn.commit()
    conn.close()
    return True


def save_sharing_log_entry(session_id: int, bri_score: int,
                           risk_level: str, center_name: str) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO sharing_log (session_id, bri_score, risk_level, center_name)
        VALUES (?, ?, ?, ?)
    """, (session_id, bri_score, risk_level, center_name))
    log_id = c.lastrowid
    conn.commit()
    conn.close()
    return log_id


def get_sharing_log() -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM sharing_log ORDER BY timestamp DESC")
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


def get_session_count() -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM sessions")
    count = c.fetchone()["cnt"]
    conn.close()
    return count


def get_sharing_count() -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as cnt FROM sharing_log")
    count = c.fetchone()["cnt"]
    conn.close()
    return count


def get_streak() -> int:
    """Calculate consecutive days with at least one check-in."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT DISTINCT DATE(timestamp) as day
        FROM sessions
        ORDER BY day DESC
    """)
    days = [row["day"] for row in c.fetchall()]
    conn.close()

    if not days:
        return 0

    streak = 0
    today = datetime.now().date()

    for i, day_str in enumerate(days):
        expected = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        if day_str == expected:
            streak += 1
        else:
            break

    return streak


def get_7day_trend_direction() -> str:
    """Returns Rising, Improving, or Stable based on BRI trend."""
    sessions = get_sessions_last_n_days(7)
    if len(sessions) < 2:
        return "Stable"

    # Compare first half avg vs second half avg
    mid = len(sessions) // 2
    recent = sessions[:mid]
    older = sessions[mid:]

    avg_recent = sum(s["bri_score"] for s in recent) / len(recent)
    avg_older = sum(s["bri_score"] for s in older) / len(older)

    diff = avg_recent - avg_older
    if diff > 5:
        return "Rising"
    elif diff < -5:
        return "Improving"
    else:
        return "Stable"


def get_consecutive_rising_count() -> int:
    """Count consecutive sessions with rising BRI scores (for pattern warning)."""
    sessions = get_recent_sessions(10)
    if len(sessions) < 3:
        return 0

    count = 0
    for i in range(len(sessions) - 1):
        if sessions[i]["bri_score"] > sessions[i + 1]["bri_score"]:
            count += 1
        else:
            break
    return count