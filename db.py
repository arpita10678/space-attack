import sqlite3

DB_NAME = "game_stats.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            score INTEGER,
            kills INTEGER
        )
    """)
    conn.commit()
    conn.close()


def update_stats(score, kills):
    """Insert final game stats into database"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO stats (score, kills) VALUES (?, ?)", (score, kills))
    conn.commit()
    conn.close()


def get_high_scores():
    """Return top 10 highest scores for the stats page"""
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT score, kills
        FROM stats
        ORDER BY score DESC
        LIMIT 10
    """)

    rows = cur.fetchall()
    conn.close()
    return rows
