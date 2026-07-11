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

cursor.execute("""
CREATE TABLE IF NOT EXISTS calendar_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    start_datetime TEXT NOT NULL,
    end_datetime TEXT,
    module TEXT,
    responsible_user INTEGER NOT NULL,
    priority TEXT DEFAULT 'normal',
    reminder_minutes INTEGER DEFAULT 0,
    repeat_rule TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()

ROLE_NAMES = (
    "OWNER",
    "ADMIN",
    "OTC_MANAGER",
    "AGRO_MANAGER",
    "LAWYER",
    "ENGINEER",
    "BEAUTY_MANAGER",
    "VIEWER",
    # legacy roles (CRM compatibility)
    "MANAGER",
    "DRONE_ENGINEER",
    "CLIENT",
)

ROLE_DESCRIPTIONS = {
    "OWNER": "Владелец системы",
    "ADMIN": "Администратор",
    "OTC_MANAGER": "Менеджер Crypto OTC",
    "AGRO_MANAGER": "Менеджер Agro Trading",
    "LAWYER": "Юрист",
    "ENGINEER": "Инженер Drone Engineering",
    "BEAUTY_MANAGER": "Менеджер Cafe & Beauty",
    "VIEWER": "Наблюдатель (только просмотр)",
    "MANAGER": "Менеджер CRM",
    "DRONE_ENGINEER": "Инженер дронов",
    "CLIENT": "Клиент",
}

SYSTEM_PERMISSIONS = (
    "crypto_access",
    "agro_access",
    "legal_access",
    "drone_access",
    "beauty_access",
    "calendar_access",
    "reports_access",
    "ai_access",
    "users_access",
)

MODULE_PERMISSIONS = {
    "crypto_otc": "crypto_access",
    "agro_trading": "agro_access",
    "law": "legal_access",
    "drone": "drone_access",
    "cafe_beauty": "beauty_access",
    "calendar": "calendar_access",
    "reports": "reports_access",
    "ai_assistant": "ai_access",
    "users": "users_access",
}

_ALL = set(SYSTEM_PERMISSIONS)

ROLE_PERMISSIONS = {
    "OWNER": _ALL,
    "ADMIN": _ALL,
    "OTC_MANAGER": {
        "crypto_access", "calendar_access", "reports_access", "ai_access",
    },
    "AGRO_MANAGER": {
        "agro_access", "calendar_access", "reports_access", "ai_access",
    },
    "LAWYER": {"legal_access", "calendar_access", "ai_access"},
    "ENGINEER": {"drone_access", "calendar_access", "ai_access"},
    "BEAUTY_MANAGER": {"beauty_access", "calendar_access", "ai_access"},
    "VIEWER": {"calendar_access", "reports_access", "ai_access"},
    "MANAGER": {
        "crypto_access", "agro_access", "calendar_access", "reports_access", "ai_access",
    },
    "DRONE_ENGINEER": {"drone_access", "calendar_access", "ai_access"},
    "CLIENT": {"calendar_access", "ai_access"},
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
    # TODO: future implementation — cache roles per session
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
    return "VIEWER"


def assign_role(telegram_id: int, role_name: str, assigned_by: int = None) -> bool:
    # TODO: future implementation — Telegram UI for role assignment
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
    return cursor.rowcount > 0


def revoke_role(telegram_id: int, role_name: str) -> bool:
    # TODO: future implementation — Telegram UI for role revocation
    cursor.execute(
        "SELECT id FROM roles WHERE role_name = ?",
        (role_name,),
    )
    role_row = cursor.fetchone()
    if not role_row:
        return False

    cursor.execute(
        "DELETE FROM user_roles WHERE user_id = ? AND role_id = ?",
        (telegram_id, role_row[0]),
    )
    conn.commit()
    return cursor.rowcount > 0


def has_permission(telegram_id: int, permission: str) -> bool:
    # TODO: future implementation — per-user permission overrides from DB
    if permission not in SYSTEM_PERMISSIONS:
        return False

    roles = get_user_roles(telegram_id)
    if not roles:
        return False

    for role in roles:
        if permission in ROLE_PERMISSIONS.get(role, set()):
            return True
    return False


def has_module_access(telegram_id: int, module: str) -> bool:
    # TODO: future implementation — combine module status and user activity
    permission = MODULE_PERMISSIONS.get(module)
    if not permission:
        return False
    return has_permission(telegram_id, permission)


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


# ==========================================================
# SYSTEM MODULES (infrastructure)
# ==========================================================

SYSTEM_MODULES = {
    "crypto_otc": "Crypto OTC",
    "agro_trading": "Agro Trading",
    "law": "Юриспруденция",
    "drone": "Drone Engineering",
    "cafe_beauty": "Cafe & Beauty",
    "users": "Пользователи",
    "reports": "Отчеты",
    "calendar": "Календарь",
    "ai_assistant": "AI помощник",
}

# Modules that will register events in the central calendar
CALENDAR_SOURCE_MODULES = (
    "crypto_otc",
    "agro_trading",
    "law",
    "drone",
    "cafe_beauty",
)

# TODO: future implementation — module-specific AI agents
MODULE_AI_AGENTS = {
    "crypto_otc": None,
    "agro_trading": None,
    "law": None,
    "drone": None,
    "cafe_beauty": None,
    "users": None,
    "reports": None,
    "calendar": None,
}


def register_calendar_event(
    user_id: int,
    module: str,
    title: str,
    start_datetime: str = None,
    end_datetime: str = None,
    description: str = "",
    priority: str = "normal",
    reminder_minutes: int = 0,
    repeat_rule: str = None,
):
    # TODO: future implementation — validation and module-specific event mapping
    if module not in CALENDAR_SOURCE_MODULES and module != "calendar":
        return None

    if not start_datetime:
        start_datetime = "1970-01-01 00:00:00"

    event_id = create_calendar_event(
        responsible_user=user_id,
        title=title,
        description=description,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        module=module,
        priority=priority,
        reminder_minutes=reminder_minutes,
        repeat_rule=repeat_rule,
    )

    log_audit(
        user_id,
        "register_event",
        "calendar",
        f"{module}|{title}|{start_datetime}",
    )
    return event_id


def create_calendar_event(
    responsible_user: int,
    title: str,
    start_datetime: str,
    description: str = "",
    end_datetime: str = None,
    module: str = "calendar",
    priority: str = "normal",
    reminder_minutes: int = 0,
    repeat_rule: str = None,
    status: str = "active",
) -> int:
    # TODO: future implementation — datetime validation and conflict checks
    cursor.execute(
        """
        INSERT INTO calendar_events (
            title, description, start_datetime, end_datetime,
            module, responsible_user, priority, reminder_minutes,
            repeat_rule, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title.strip(),
            description.strip() if description else None,
            start_datetime,
            end_datetime,
            module,
            responsible_user,
            priority,
            reminder_minutes,
            repeat_rule,
            status,
        ),
    )
    conn.commit()
    return cursor.lastrowid


def get_calendar_event(event_id: int, user_id: int):
    # TODO: future implementation — shared events and role-based visibility
    cursor.execute(
        """
        SELECT id, title, description, start_datetime, end_datetime,
               module, responsible_user, priority, reminder_minutes,
               repeat_rule, status, created_at, updated_at
        FROM calendar_events
        WHERE id = ? AND responsible_user = ?
        """,
        (event_id, user_id),
    )
    return cursor.fetchone()


def get_calendar_events(
    user_id: int,
    module: str = None,
    status: str = None,
    limit: int = 20,
):
    # TODO: future implementation — date range filters (today, week, reminders)
    query = """
        SELECT id, title, description, start_datetime, end_datetime,
               module, responsible_user, priority, reminder_minutes,
               repeat_rule, status, created_at, updated_at
        FROM calendar_events
        WHERE responsible_user = ?
    """
    params = [user_id]

    if module:
        query += " AND module = ?"
        params.append(module)

    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY start_datetime ASC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    return cursor.fetchall()


def update_calendar_event(event_id: int, user_id: int, **fields) -> bool:
    # TODO: future implementation — partial update validation
    allowed = {
        "title", "description", "start_datetime", "end_datetime",
        "module", "priority", "reminder_minutes", "repeat_rule", "status",
    }
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return False

    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [event_id, user_id]

    cursor.execute(
        f"""
        UPDATE calendar_events
        SET {set_clause}, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND responsible_user = ?
        """,
        values,
    )
    conn.commit()
    return cursor.rowcount > 0


def delete_calendar_event(event_id: int, user_id: int) -> bool:
    # TODO: future implementation — soft delete and audit trail
    cursor.execute(
        "DELETE FROM calendar_events WHERE id = ? AND responsible_user = ?",
        (event_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def complete_calendar_event(event_id: int, user_id: int) -> bool:
    # TODO: future implementation — completion workflow and notifications
    return update_calendar_event(event_id, user_id, status="done")


def reschedule_calendar_event(
    event_id: int,
    user_id: int,
    start_datetime: str,
    end_datetime: str = None,
) -> bool:
    # TODO: future implementation — reschedule notifications and conflict checks
    return update_calendar_event(
        event_id,
        user_id,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )


def format_calendar_events_text(user_id: int, module: str = None, limit: int = 10) -> str:
    # TODO: future implementation — rich formatting and timezone support
    events = get_calendar_events(user_id, module=module, limit=limit)
    if not events:
        return "Событий пока нет."

    lines = ["📅 События:\n"]
    for event in events:
        event_id = event[0]
        title = event[1]
        description = event[2]
        start_dt = event[3]
        end_dt = event[4]
        mod = event[5]
        status = event[10]
        lines.append(
            f"#{event_id} · {title}\n"
            f"   🕒 {start_dt} — {end_dt or '—'}\n"
            f"   📦 {mod or '—'} · {status}"
        )
        if description:
            lines.append(f"   📝 {description}")
    return "\n".join(lines)


def check_module_access(telegram_id: int, module: str) -> bool:
    # TODO: future implementation — deprecated alias, use has_module_access
    return has_module_access(telegram_id, module)


def list_users(limit: int = 50):
    # TODO: future implementation — pagination, search, filters
    cursor.execute(
        """
        SELECT telegram_id, username, full_name, is_active, created_at
        FROM users
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    )
    return cursor.fetchall()


def format_users_list_text(limit: int = 20) -> str:
    # TODO: future implementation — rich user cards with roles
    rows = list_users(limit)
    if not rows:
        return "Пользователи не найдены."

    lines = ["📋 Список пользователей:\n"]
    for telegram_id, username, full_name, is_active, created_at in rows:
        roles = get_user_roles(telegram_id)
        roles_text = ", ".join(roles) if roles else "без ролей"
        status = "активен" if is_active else "неактивен"
        lines.append(
            f"• {full_name or '—'} (@{username or '—'})\n"
            f"  ID: {telegram_id} · {status}\n"
            f"  🛡 {roles_text}\n"
            f"  🕒 {created_at}"
        )
    return "\n\n".join(lines)


def format_roles_catalog_text() -> str:
    # TODO: future implementation — role editor with permissions preview
    lines = ["🛡 Роли системы:\n"]
    for role_name in ROLE_NAMES:
        desc = ROLE_DESCRIPTIONS.get(role_name, "")
        perms = ROLE_PERMISSIONS.get(role_name, set())
        perm_list = ", ".join(sorted(perms)) if perms else "—"
        lines.append(f"• {role_name}\n  {desc}\n  🔐 {perm_list}")
    return "\n\n".join(lines)


def format_permissions_text(telegram_id: int) -> str:
    # TODO: future implementation — per-user permission matrix
    roles = get_user_roles(telegram_id)
    granted = set()
    for role in roles:
        granted.update(ROLE_PERMISSIONS.get(role, set()))

    lines = [
        "🔐 Права доступа:\n",
        f"Ваши роли: {', '.join(roles) if roles else 'не назначены'}\n",
        "Модули:",
    ]
    for module, permission in MODULE_PERMISSIONS.items():
        allowed = permission in granted
        icon = "✅" if allowed else "❌"
        lines.append(f"{icon} {SYSTEM_MODULES.get(module, module)} ({permission})")
    return "\n".join(lines)


def format_audit_log_text(limit: int = 10) -> str:
    # TODO: future implementation — filters by module, user, date
    rows = get_user_audit_log(limit=limit)
    if not rows:
        return "📝 Журнал действий пуст."

    lines = ["📝 Журнал действий:\n"]
    for user_id, action, module, details, created_at in rows:
        lines.append(
            f"• [{created_at}] user {user_id}\n"
            f"  {module} / {action} — {details or '—'}"
        )
    return "\n".join(lines)


def get_user_audit_log(user_id: int = None, limit: int = 20):
    # TODO: future implementation — extended audit filters and pagination
    if user_id is not None:
        cursor.execute(
            """
            SELECT user_id, action, module, details, created_at
            FROM audit_log
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
    else:
        cursor.execute(
            """
            SELECT user_id, action, module, details, created_at
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
    return cursor.fetchall()


def get_user_activity_summary(user_id: int, limit: int = 10) -> str:
    # TODO: future implementation — activity dashboard for users module
    rows = get_user_audit_log(user_id, limit)
    if not rows:
        return "Активность пользователя не зафиксирована."

    lines = [f"📈 Активность пользователя {user_id}:\n"]
    for row in rows:
        lines.append(f"• [{row[4]}] {row[2]} / {row[1]} — {row[3] or '—'}")
    return "\n".join(lines)


def get_module_ai_agent(module: str):
    # TODO: future implementation — return configured AI agent for module
    return MODULE_AI_AGENTS.get(module)


# ==========================================================
# REPORTS (central hub)
# ==========================================================

REPORT_TYPES = {
    "finance": "💰 Финансы",
    "profit": "📈 Прибыль",
    "users": "👥 Пользователи",
    "calendar": "📅 Календарь",
    "agro_trading": "🌾 Agro Trading",
    "crypto_otc": "💵 Crypto OTC",
    "drone": "🚁 Drone Engineering",
    "law": "⚖️ Юриспруденция",
    "cafe_beauty": "☕ Cafe & Beauty",
    "ai_analytics": "🤖 AI аналитика",
}

REPORT_BUTTON_TO_TYPE = {label: key for key, label in REPORT_TYPES.items()}

REPORT_DEPARTMENTS = {
    "finance": "Финансы",
    "agro_trading": "Agro Trading",
    "crypto_otc": "Crypto OTC",
    "drone": "Drone Engineering",
    "law": "Юриспруденция",
    "cafe_beauty": "Cafe & Beauty",
    "users": "Пользователи",
    "calendar": "Календарь",
    "ai_assistant": "AI помощник",
}


def build_report_filters(
    date_from: str = None,
    date_to: str = None,
    user_id: int = None,
    department: str = None,
) -> dict:
    # TODO: future implementation — validate and normalize filter values
    return {
        "date_from": date_from,
        "date_to": date_to,
        "user_id": user_id,
        "department": department,
    }


def get_report_data(
    report_type: str,
    requested_by: int,
    filters: dict = None,
):
    # TODO: future implementation — aggregate data from modules and CRM
    _ = requested_by
    _ = filters or {}
    if report_type not in REPORT_TYPES:
        return None
    return {
        "type": report_type,
        "title": REPORT_TYPES[report_type],
        "rows": [],
        "filters": filters or {},
    }


def format_report_stub_text(
    report_type: str,
    user_id: int,
    filters: dict = None,
) -> str:
    # TODO: future implementation — render real report tables and charts
    title = REPORT_TYPES.get(report_type, report_type)
    filters = filters or {}
    filter_lines = []
    if filters.get("date_from") or filters.get("date_to"):
        filter_lines.append(
            f"📅 Период: {filters.get('date_from') or '—'} — {filters.get('date_to') or '—'}"
        )
    if filters.get("user_id"):
        filter_lines.append(f"👤 Пользователь: {filters['user_id']}")
    if filters.get("department"):
        dept = REPORT_DEPARTMENTS.get(filters["department"], filters["department"])
        filter_lines.append(f"🏢 Отдел: {dept}")

    filters_text = "\n".join(filter_lines) if filter_lines else "Фильтры не заданы."
    return (
        f"{title}\n\n"
        f"{filters_text}\n\n"
        "Отчёт находится в разработке.\n"
        "Доступны будущие фильтры и экспорт в Excel / PDF."
    )


def export_report_excel(
    report_type: str,
    user_id: int,
    filters: dict = None,
) -> str:
    # TODO: future implementation — generate .xlsx file and return path
    _ = get_report_data(report_type, user_id, filters)
    return ""


def export_report_pdf(
    report_type: str,
    user_id: int,
    filters: dict = None,
) -> str:
    # TODO: future implementation — generate .pdf file and return path
    _ = get_report_data(report_type, user_id, filters)
    return ""


def can_access_report(user_id: int, report_type: str) -> bool:
    # TODO: future implementation — fine-grained report permissions
    module_map = {
        "crypto_otc": "crypto_otc",
        "agro_trading": "agro_trading",
        "law": "law",
        "drone": "drone",
        "cafe_beauty": "cafe_beauty",
        "calendar": "calendar",
        "users": "users",
        "ai_analytics": "ai_assistant",
    }
    if report_type in {"finance", "profit"}:
        return has_permission(user_id, "reports_access")
    module = module_map.get(report_type)
    if module:
        return has_module_access(user_id, module) or has_permission(user_id, "reports_access")
    return has_permission(user_id, "reports_access")


# ==========================================================
# DRONE ENGINEERING
# ==========================================================

DRONE_SECTIONS = {
    "projects": "📁 Проекты",
    "bom": "📋 Спецификации BOM",
    "batteries": "🔋 Аккумуляторы",
    "electronics": "⚡ Электроника",
    "vtx": "📡 Связь и VTX",
    "gps": "🛰 Навигация и GPS",
    "autopilot": "🧠 Автопилоты",
    "cad": "📐 CAD и чертежи",
    "cost": "💰 Себестоимость",
    "procurement": "📦 Закупки",
    "ai_engineer": "🤖 AI инженер",
}

DRONE_BUTTON_TO_SECTION = {label: key for key, label in DRONE_SECTIONS.items()}

# Areas the drone AI engineer will access in future implementation
DRONE_AI_CONTEXT_AREAS = (
    "projects",
    "bom",
    "batteries",
    "specifications",
    "drawings",
    "procurement",
    "project_history",
)


def can_access_drone_section(user_id: int, section_key: str) -> bool:
    # TODO: future implementation — section-level permissions
    if not has_module_access(user_id, "drone"):
        return False
    return section_key in DRONE_SECTIONS


def format_drone_section_stub(section_key: str, user_id: int) -> str:
    # TODO: future implementation — load real section data from DB
    title = DRONE_SECTIONS.get(section_key, section_key)
    return (
        f"{title}\n\n"
        f"Раздел Drone Engineering.\n"
        f"Пользователь: {user_id}\n\n"
        "Раздел находится в разработке."
    )


def get_drone_ai_context(user_id: int) -> dict:
    # TODO: future implementation — aggregate context for drone AI engineer
    return {
        "user_id": user_id,
        "projects": [],
        "bom": [],
        "batteries": [],
        "specifications": [],
        "drawings": [],
        "procurement": [],
        "project_history": [],
    }


def format_drone_ai_engineer_stub(user_id: int) -> str:
    # TODO: future implementation — connect dedicated drone AI agent
    context = get_drone_ai_context(user_id)
    areas = ", ".join(DRONE_AI_CONTEXT_AREAS)
    loaded = sum(1 for k in DRONE_AI_CONTEXT_AREAS if context.get(k))
    return (
        "🤖 AI инженер\n\n"
        f"Будущий доступ к: {areas}.\n"
        f"Загружено контекстных блоков: {loaded}/{len(DRONE_AI_CONTEXT_AREAS)}.\n\n"
        "AI инженер находится в разработке."
    )


def format_drone_ai_context_stub(area: str, user_id: int) -> str:
    # TODO: future implementation — preview AI context for specific area
    context = get_drone_ai_context(user_id)
    items = context.get(area, [])
    return (
        f"🤖 AI контекст: {area}\n\n"
        f"Записей: {len(items)}.\n\n"
        "Раздел находится в разработке."
    )