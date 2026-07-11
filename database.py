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

cursor.execute("""
CREATE TABLE IF NOT EXISTS ai_dialog_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ai_settings (
    user_id INTEGER PRIMARY KEY,
    model TEXT DEFAULT 'openai/gpt-5-mini',
    tone TEXT DEFAULT 'neutral',
    language TEXT DEFAULT 'ru',
    context_depth INTEGER DEFAULT 20,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ai_projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ai_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_id INTEGER,
    title TEXT NOT NULL,
    status TEXT DEFAULT 'todo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES ai_projects(id)
)
""")

conn.commit()

# ==========================================================
# ROLES (подготовка к разделению доступа)
# ==========================================================

ROLE_NAMES = (
    "OWNER",
    "MANAGER",
    "LAWYER",
    "DRONE_ENGINEER",
    "BEAUTY_MANAGER",
    "CLIENT",
)

ROLE_DESCRIPTIONS = {
    "OWNER": "Владелец системы",
    "MANAGER": "Менеджер CRM",
    "LAWYER": "Юрист",
    "DRONE_ENGINEER": "Инженер дронов",
    "BEAUTY_MANAGER": "Менеджер Cafe & Beauty",
    "CLIENT": "Клиент",
}


def _seed_roles():
    for role_name in ROLE_NAMES:
        cursor.execute(
            """
            INSERT OR IGNORE INTO roles (role_name, description)
            VALUES (?, ?)
            """,
            (role_name, ROLE_DESCRIPTIONS.get(role_name, "")),
        )
    conn.commit()


_seed_roles()


def ensure_user(telegram_id: int, full_name: str = "", username: str = ""):
    cursor.execute(
        "SELECT id FROM users WHERE telegram_id = ?",
        (telegram_id,),
    )
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute(
        """
        INSERT INTO users (telegram_id, username, full_name)
        VALUES (?, ?, ?)
        """,
        (telegram_id, username or None, full_name or None),
    )
    conn.commit()
    return cursor.lastrowid


def get_user_roles(telegram_id: int) -> list[str]:
    cursor.execute(
        """
        SELECT r.role_name
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE ur.user_id = ?
        ORDER BY r.role_name
        """,
        (telegram_id,),
    )
    return [row[0] for row in cursor.fetchall()]


def get_primary_role(telegram_id: int) -> str:
    roles = get_user_roles(telegram_id)
    if roles:
        return roles[0]
    return "CLIENT"


def assign_role(telegram_id: int, role_name: str, assigned_by: int = None):
    cursor.execute(
        "SELECT id FROM roles WHERE role_name = ?",
        (role_name,),
    )
    role_row = cursor.fetchone()
    if not role_row:
        return False

    ensure_user(telegram_id)
    cursor.execute(
        """
        INSERT OR IGNORE INTO user_roles (user_id, role_id, assigned_by)
        VALUES (?, ?, ?)
        """,
        (telegram_id, role_row[0], assigned_by),
    )
    conn.commit()
    return True


def log_audit(user_id: int, action: str, module: str, details: str = ""):
    cursor.execute(
        """
        INSERT INTO audit_log (user_id, action, module, details)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, action, module, details),
    )
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


def format_memory_text(user_id: int) -> str:
    memory = load_memory(user_id)
    if not memory:
        return "🧠 Память пуста. AI запомнит данные из будущих диалогов."

    lines = ["🧠 Моя память:\n"]
    for key, value in memory.items():
        label = MEMORY_FIELDS.get(key, key)
        lines.append(f"• {label}: {value}")
    return "\n".join(lines)


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


# ==========================================================
# AI ASSISTANT
# ==========================================================

DEFAULT_AI_SETTINGS = {
    "model": "openai/gpt-5-mini",
    "tone": "neutral",
    "language": "ru",
    "context_depth": 20,
}

TONE_LABELS = {
    "neutral": "Нейтральный",
    "formal": "Формальный",
    "friendly": "Дружелюбный",
}


def get_ai_settings(user_id: int) -> dict:
    cursor.execute(
        """
        SELECT model, tone, language, context_depth
        FROM ai_settings
        WHERE user_id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    if not row:
        return dict(DEFAULT_AI_SETTINGS)

    return {
        "model": row[0],
        "tone": row[1],
        "language": row[2],
        "context_depth": row[3],
    }


def save_ai_settings(user_id: int, **fields):
    current = get_ai_settings(user_id)
    current.update({k: v for k, v in fields.items() if v is not None})

    cursor.execute(
        """
        INSERT INTO ai_settings (user_id, model, tone, language, context_depth)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            model = excluded.model,
            tone = excluded.tone,
            language = excluded.language,
            context_depth = excluded.context_depth,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            current["model"],
            current["tone"],
            current["language"],
            current["context_depth"],
        ),
    )
    conn.commit()


def add_dialog_message(user_id: int, role: str, content: str):
    cursor.execute(
        """
        INSERT INTO ai_dialog_messages (user_id, role, content)
        VALUES (?, ?, ?)
        """,
        (user_id, role, content),
    )
    conn.commit()


def get_dialog_history(user_id: int, limit: int = 20) -> list[dict]:
    cursor.execute(
        """
        SELECT role, content, created_at
        FROM ai_dialog_messages
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (user_id, limit),
    )
    rows = cursor.fetchall()
    rows.reverse()
    return [
        {"role": role, "content": content, "created_at": created_at}
        for role, content, created_at in rows
    ]


def get_dialog_history_for_llm(user_id: int, limit: int = 20) -> list[dict]:
    history = get_dialog_history(user_id, limit)
    return [{"role": item["role"], "content": item["content"]} for item in history]


def clear_dialog_history(user_id: int):
    cursor.execute(
        "DELETE FROM ai_dialog_messages WHERE user_id = ?",
        (user_id,),
    )
    conn.commit()


def format_dialog_history_text(user_id: int, limit: int = 10) -> str:
    history = get_dialog_history(user_id, limit)
    if not history:
        return "История диалогов пуста."

    lines = []
    for item in history:
        prefix = "👤 Вы" if item["role"] == "user" else "🤖 AI"
        lines.append(f"{prefix} ({item['created_at']}):\n{item['content']}")
    return "\n\n".join(lines)


def format_profile_text(user_id: int) -> str:
    profile = get_user_profile(user_id)
    if not profile:
        return "Профиль пока пуст. AI запомнит данные из диалога."

    lines = [f"• {MEMORY_FIELDS[key]}: {value}" for key, value in profile.items()]
    return "👤 Ваш профиль:\n\n" + "\n".join(lines)


def create_ai_project(user_id: int, title: str, description: str = "") -> int:
    cursor.execute(
        """
        INSERT INTO ai_projects (user_id, title, description)
        VALUES (?, ?, ?)
        """,
        (user_id, title.strip(), description.strip()),
    )
    conn.commit()
    return cursor.lastrowid


def get_ai_projects(user_id: int):
    cursor.execute(
        """
        SELECT id, title, description, status, created_at
        FROM ai_projects
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )
    return cursor.fetchall()


def get_ai_project(user_id: int, project_id: int):
    cursor.execute(
        """
        SELECT id, title, description, status, created_at
        FROM ai_projects
        WHERE user_id = ? AND id = ?
        """,
        (user_id, project_id),
    )
    return cursor.fetchone()


def create_ai_task(
    user_id: int,
    title: str,
    project_id: int = None,
) -> int:
    if project_id is not None:
        project = get_ai_project(user_id, project_id)
        if not project:
            return 0

    cursor.execute(
        """
        INSERT INTO ai_tasks (user_id, project_id, title)
        VALUES (?, ?, ?)
        """,
        (user_id, project_id, title.strip()),
    )
    conn.commit()
    return cursor.lastrowid


def get_ai_tasks(user_id: int, project_id: int = None):
    if project_id is not None:
        cursor.execute(
            """
            SELECT id, project_id, title, status, created_at
            FROM ai_tasks
            WHERE user_id = ? AND project_id = ?
            ORDER BY id DESC
            """,
            (user_id, project_id),
        )
    else:
        cursor.execute(
            """
            SELECT id, project_id, title, status, created_at
            FROM ai_tasks
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        )
    return cursor.fetchall()


def update_ai_task_status(user_id: int, task_id: int, status: str) -> bool:
    cursor.execute(
        """
        UPDATE ai_tasks
        SET status = ?
        WHERE user_id = ? AND id = ?
        """,
        (status, user_id, task_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def format_projects_text(user_id: int) -> str:
    projects = get_ai_projects(user_id)
    if not projects:
        return "У вас пока нет проектов."

    lines = ["📁 Ваши проекты:\n"]
    for project_id, title, description, status, created_at in projects:
        lines.append(
            f"#{project_id} · {title} ({status})\n"
            f"   {description or '—'}\n"
            f"   🕒 {created_at}"
        )
    return "\n\n".join(lines)


def format_tasks_text(user_id: int, project_id: int = None) -> str:
    tasks = get_ai_tasks(user_id, project_id)
    if not tasks:
        return "Задач пока нет."

    status_icons = {
        "todo": "⬜",
        "in_progress": "🔄",
        "done": "✅",
    }
    lines = ["✅ Ваши задачи:\n"]
    for task_id, proj_id, title, status, created_at in tasks:
        icon = status_icons.get(status, "⬜")
        project_part = f" · проект #{proj_id}" if proj_id else ""
        lines.append(f"{icon} #{task_id} {title}{project_part} ({created_at})")
    return "\n".join(lines)


def format_ai_settings_text(user_id: int) -> str:
    settings = get_ai_settings(user_id)
    tone_label = TONE_LABELS.get(settings["tone"], settings["tone"])
    return (
        "⚙️ Настройки AI:\n\n"
        f"• Модель: {settings['model']}\n"
        f"• Тон: {tone_label}\n"
        f"• Язык: {settings['language']}\n"
        f"• Глубина контекста: {settings['context_depth']} сообщений"
    )