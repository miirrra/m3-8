import sqlite3
# conn=sqlite3.connect("debate.db")
# cursor=conn.cursor()
DB_NAME="debate.db"

def init_db():
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS debates(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT,
        side TEXT,
        argument TEXT
        ) """)
    conn.commit()
    conn.close()
    
def get_argument(topic,side):
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("SELECT argument FROM debates WHERE topic=? AND side=?",(topic,side))
    result=cursor.fetchone()
    conn.close()
    return result[0] if result else None

def save_argument(topic,side,argument):
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("INSERT INTO debates (topic,side, argument) VALUES (?, ?, ?)",(topic,side, argument))
    conn.commit()
    conn.close()