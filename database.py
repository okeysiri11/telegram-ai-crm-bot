import sqlite3

conn = sqlite3.connect("memory.db")
cursor = conn.cursor()

# ----------------------------
# Память пользователя
# ----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_memory (
    user_id INTEGER,
    key TEXT,
    value TEXT,
    PRIMARY KEY (user_id, key)
)
""")

# ----------------------------
# Пользователи
# ----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    name TEXT,
    role TEXT
)
""")

# ----------------------------
# Роли
# ----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_name TEXT UNIQUE,
    description TEXT
)
""")

# ----------------------------
# Назначение ролей
# ----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER,
    role_id INTEGER,
    assigned_by INTEGER,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
)
""")

# ----------------------------
# Журнал действий
# ----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT,
    module TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

# ----------------------------
# Заявки CRM
# ----------------------------

cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number INTEGER UNIQUE,
    client_id INTEGER,
    client_name TEXT,
    product TEXT,
    request_text TEXT,
    status TEXT DEFAULT 'NEW',
    manager_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

# ==========================================================
# USER MEMORY
# ==========================================================

MEMORY_FIELDS = {
    "name": "Имя",
    "company": "Компания",
    "city": "Город",
    "country": "Страна",
    "activity": "Сфера деятельности",
    "interests": "Интересы",
}


def save_memory(user_id: int, key: str, value: str):
    cursor.execute(
        "REPLACE INTO user_memory (user_id, key, value) VALUES (?, ?, ?)",
        (user_id, key, value)
    )
    conn.commit()


def load_memory(user_id: int):
    cursor.execute(
        "SELECT key, value FROM user_memory WHERE user_id=?",
        (user_id,)
    )

    rows = cursor.fetchall()

    return {
        key: value
        for key, value in rows
    }


def get_memory(user_id: int, key: str):
    cursor.execute(
        "SELECT value FROM user_memory WHERE user_id=? AND key=?",
        (user_id, key)
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    return None


def get_user_profile(user_id: int) -> dict:
    profile = load_memory(user_id)
    return {
        key: profile[key]
        for key in MEMORY_FIELDS
        if key in profile and profile[key]
    }


def save_profile_fields(user_id: int, fields: dict):
    for key, value in fields.items():
        if key not in MEMORY_FIELDS:
            continue
        if value and str(value).strip():
            save_memory(user_id, key, str(value).strip())


def format_memory_context(user_id: int) -> str:
    profile = get_user_profile(user_id)
    if not profile:
        return ""

    lines = [
        f"- {MEMORY_FIELDS[key]}: {value}"
        for key, value in profile.items()
    ]
    return "Известная информация о пользователе:\n" + "\n".join(lines)


# ==========================================================
# CRM REQUESTS
# ==========================================================

def create_request(
    client_id: int,
    client_name: str,
    product: str,
    request_text: str,
    manager_id: int
):
    cursor.execute(
        """
        INSERT INTO requests (
            request_number,
            client_id,
            client_name,
            product,
            request_text,
            status,
            manager_id
        )
        VALUES (
            (SELECT COALESCE(MAX(request_number),1000) + 1 FROM requests),
            ?, ?, ?, ?, ?, ?
        )
        """,
        (
            client_id,
            client_name,
            product,
            request_text,
            "NEW",
            manager_id
        )
    )

    conn.commit()

    cursor.execute(
        "SELECT request_number FROM requests WHERE id=?",
        (cursor.lastrowid,)
    )

    row = cursor.fetchone()

    return row[0]


def update_request_status(
    request_number: int,
    status: str,
    manager_id: int = None
):
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE requests
        SET status = ?,
            manager_id = ?
        WHERE request_number = ?
        """,
        (
            status,
            manager_id,
            request_number
        )
    )

    conn.commit()
    conn.close()
def get_request_status(
    request_number: int
):
    cursor.execute(
        """
        SELECT status
        FROM requests
        WHERE request_number=?
        """,
        (
            request_number,
        )
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    return None


def get_request_client(
    request_number: int
):
    cursor.execute(
        """
        SELECT client_id
        FROM requests
        WHERE request_number=?
        """,
        (
            request_number,
        )
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    return None
def get_requests_by_status(status):
    cursor.execute(
        """
        SELECT request_number,
               status,
               product,
               client_name
        FROM requests
        WHERE status=?
        ORDER BY created_at DESC
        """,
        (status,)
    )

    return cursor.fetchall()


def get_all_active_requests():
    cursor.execute(
        """
        SELECT
            request_number,
            client_name,
            product,
            manager_id,
            status
        FROM requests
        WHERE status IN ('NEW', 'IN_PROGRESS')
        ORDER BY request_number DESC
        """
    )

    return cursor.fetchall()    

def get_request(
    request_number: int
):
    cursor.execute(
        """
        SELECT *
        FROM requests
        WHERE request_number=?
        """,
        (
            request_number,
        )
    )

    return cursor.fetchone()
def get_request_by_number(request_number: int):
    cursor.execute(
        """
        SELECT client_id
        FROM requests
        WHERE request_number=?
        """,
        (request_number,)
    )

    row = cursor.fetchone()

    if row:
        return row[0]

    return None
def get_request_by_number(number):
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM requests
        WHERE request_number = ?
    """, (number,))

    request = cursor.fetchone()

    conn.close()

    return request 
def assign_manager(request_number, manager_id):
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE requests
        SET manager_id = ?
        WHERE request_number = ?
        """,
        (manager_id, request_number)
    )

    conn.commit()
    conn.close()
def get_requests_by_manager(manager_id):
    conn = sqlite3.connect("memory.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM requests
        WHERE manager_id = ?
        ORDER BY id DESC
    """, (manager_id,))

    requests = cursor.fetchall()

    conn.close()

    return requests   