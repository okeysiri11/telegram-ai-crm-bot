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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    username TEXT,
    full_name TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    category TEXT DEFAULT 'general',
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS ai_project_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES ai_projects(id) ON DELETE CASCADE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    module TEXT DEFAULT 'system',
    project_id INTEGER,
    creator_id INTEGER NOT NULL,
    assignee_id INTEGER,
    priority TEXT DEFAULT 'NORMAL',
    status TEXT DEFAULT 'NEW',
    deadline TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    calendar_event_id INTEGER
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
    module TEXT DEFAULT 'system',
    event_type TEXT DEFAULT 'general',
    creator_id INTEGER NOT NULL,
    owner_id INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT,
    remind_before INTEGER DEFAULT 0,
    status TEXT DEFAULT 'PLANNED',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    start_datetime TEXT,
    end_datetime TEXT,
    responsible_user INTEGER,
    priority TEXT DEFAULT 'normal',
    reminder_minutes INTEGER DEFAULT 0,
    repeat_rule TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT,
    priority TEXT DEFAULT 'INFO',
    status TEXT DEFAULT 'NEW',
    is_important INTEGER DEFAULT 0,
    is_reminder INTEGER DEFAULT 0,
    source_module TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    archived_at TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS system_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    creator_id INTEGER NOT NULL,
    assigned_user_id INTEGER,
    module TEXT,
    priority TEXT DEFAULT 'NORMAL',
    status TEXT DEFAULT 'NEW',
    due_date TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    uploaded_by INTEGER NOT NULL,
    module TEXT,
    project_id INTEGER,
    task_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size INTEGER,
    mime_type TEXT,
    tags TEXT,
    description TEXT,
    version INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agro_counterparties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    counterparty_type TEXT NOT NULL,
    country TEXT,
    contact_info TEXT,
    notes TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agro_contracts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_number TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    execution_status TEXT DEFAULT 'DRAFT',
    request_number INTEGER,
    counterparty_id INTEGER,
    notes TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agro_logistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number INTEGER,
    transport TEXT,
    route TEXT,
    loading_date TEXT,
    eta TEXT,
    delivery_status TEXT DEFAULT 'PLANNED',
    notes TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agro_documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number INTEGER,
    doc_type TEXT NOT NULL,
    title TEXT NOT NULL,
    file_id INTEGER,
    notes TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agro_finance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number INTEGER,
    deal_amount REAL,
    currency TEXT DEFAULT 'USD',
    paid_amount REAL DEFAULT 0,
    debt_amount REAL DEFAULT 0,
    payment_schedule TEXT,
    notes TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS workflow_processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    module TEXT,
    trigger TEXT,
    status TEXT DEFAULT 'ACTIVE',
    created_by INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS workflow_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    module TEXT,
    trigger TEXT,
    actions_json TEXT,
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS agro_deals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_number INTEGER UNIQUE NOT NULL,
    client_id INTEGER NOT NULL,
    product TEXT,
    status TEXT DEFAULT 'NEW',
    manager_id INTEGER,
    workflow_process_id INTEGER,
    manager_task_id INTEGER,
    document_folder_id INTEGER,
    calendar_event_id INTEGER,
    contract_id INTEGER,
    logistics_id INTEGER,
    finance_id INTEGER,
    report_file_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
)
""")

conn.commit()


def _column_exists(table: str, column: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table})")
    return column in {row[1] for row in cursor.fetchall()}


def _migrate_schema():
    if not _column_exists("system_tasks", "task_source"):
        cursor.execute(
            "ALTER TABLE system_tasks ADD COLUMN task_source TEXT DEFAULT 'SYSTEM'"
        )
        conn.commit()

    legacy_map = {
        "COMPLETED": "DONE",
        "CANCELED": "CANCELLED",
        "CANCEL": "CANCELLED",
    }
    for old, new in legacy_map.items():
        cursor.execute(
            "UPDATE requests SET status = ? WHERE status = ?",
            (new, old),
        )
    conn.commit()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS agro_deals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_number INTEGER UNIQUE NOT NULL,
            client_id INTEGER NOT NULL,
            product TEXT,
            status TEXT DEFAULT 'NEW',
            manager_id INTEGER,
            workflow_process_id INTEGER,
            manager_task_id INTEGER,
            document_folder_id INTEGER,
            calendar_event_id INTEGER,
            contract_id INTEGER,
            logistics_id INTEGER,
            finance_id INTEGER,
            report_file_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TIMESTAMP
        )
        """
    )
    conn.commit()

    if not _column_exists("ai_projects", "category"):
        cursor.execute(
            "ALTER TABLE ai_projects ADD COLUMN category TEXT DEFAULT 'general'"
        )
        conn.commit()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_project_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES ai_projects(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            module TEXT DEFAULT 'system',
            project_id INTEGER,
            creator_id INTEGER NOT NULL,
            assignee_id INTEGER,
            priority TEXT DEFAULT 'NORMAL',
            status TEXT DEFAULT 'NEW',
            deadline TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            calendar_event_id INTEGER
        )
        """
    )
    conn.commit()
    _migrate_legacy_tasks()
    _migrate_calendar_schema()
    _migrate_multi_agent_platform()


def _migrate_calendar_schema():
    new_columns = {
        "event_type": "TEXT DEFAULT 'general'",
        "creator_id": "INTEGER",
        "owner_id": "INTEGER",
        "start_time": "TEXT",
        "end_time": "TEXT",
        "remind_before": "INTEGER DEFAULT 0",
    }
    for column, definition in new_columns.items():
        if not _column_exists("calendar_events", column):
            cursor.execute(
                f"ALTER TABLE calendar_events ADD COLUMN {column} {definition}"
            )
    if not _column_exists("calendar_events", "start_datetime"):
        cursor.execute(
            "ALTER TABLE calendar_events ADD COLUMN start_datetime TEXT"
        )
    if not _column_exists("calendar_events", "responsible_user"):
        cursor.execute(
            "ALTER TABLE calendar_events ADD COLUMN responsible_user INTEGER"
        )
    conn.commit()

    cursor.execute(
        """
        UPDATE calendar_events SET
            start_time = COALESCE(start_time, start_datetime),
            end_time = COALESCE(end_time, end_datetime),
            owner_id = COALESCE(owner_id, responsible_user),
            creator_id = COALESCE(creator_id, responsible_user),
            remind_before = COALESCE(remind_before, reminder_minutes, 0),
            start_datetime = COALESCE(start_datetime, start_time),
            end_datetime = COALESCE(end_datetime, end_time),
            responsible_user = COALESCE(responsible_user, owner_id),
            reminder_minutes = COALESCE(reminder_minutes, remind_before, 0),
            module = COALESCE(module, 'system')
        WHERE start_time IS NULL OR owner_id IS NULL OR creator_id IS NULL
        """
    )
    status_map = {
        "active": "ACTIVE",
        "done": "DONE",
        "cancelled": "CANCELLED",
        "canceled": "CANCELLED",
        "planned": "PLANNED",
        "missed": "MISSED",
    }
    for old, new in status_map.items():
        cursor.execute(
            "UPDATE calendar_events SET status = ? WHERE lower(status) = ?",
            (new, old),
        )
    conn.commit()


def _migrate_legacy_tasks():
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] > 0:
        return

    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='system_tasks'
        """
    )
    if cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO tasks (
                id, title, description, module, project_id, creator_id,
                assignee_id, priority, status, deadline, created_at, completed_at
            )
            SELECT
                id, title, description,
                COALESCE(module, 'system'), NULL, creator_id,
                assigned_user_id, priority, status, due_date, created_at, completed_at
            FROM system_tasks
            """
        )
        conn.commit()

    cursor.execute(
        """
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='ai_tasks'
        """
    )
    if cursor.fetchone():
        cursor.execute(
            """
            INSERT INTO tasks (
                title, description, module, project_id, creator_id,
                assignee_id, priority, status, created_at
            )
            SELECT
                title, '', 'ai_assistant', project_id, user_id,
                user_id, 'NORMAL',
                CASE status WHEN 'done' THEN 'DONE' WHEN 'in_progress' THEN 'IN_PROGRESS' ELSE 'NEW' END,
                created_at
            FROM ai_tasks
            """
        )
        conn.commit()


def _migrate_multi_agent_platform():
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            model TEXT DEFAULT 'openai/gpt-5-mini',
            prompt TEXT,
            active INTEGER DEFAULT 1
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_dialogs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            agent_code TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_code TEXT NOT NULL,
            module TEXT,
            action_type TEXT NOT NULL,
            action_payload TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS workflow_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trigger_code TEXT NOT NULL,
            module TEXT,
            user_id INTEGER,
            entity_type TEXT,
            entity_id INTEGER,
            action_type TEXT,
            status TEXT DEFAULT 'OK',
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()

    notif_cols = {
        "module": "TEXT",
        "event_type": "TEXT DEFAULT 'general'",
        "is_read": "INTEGER DEFAULT 0",
        "sent_at": "TEXT",
        "channel": "TEXT DEFAULT 'SYSTEM'",
    }
    for col, defn in notif_cols.items():
        if not _column_exists("notifications", col):
            cursor.execute(f"ALTER TABLE notifications ADD COLUMN {col} {defn}")
    conn.commit()
    cursor.execute(
        """
        UPDATE notifications SET
            module = COALESCE(module, source_module, category),
            is_read = CASE WHEN status IN ('READ', 'ARCHIVED') THEN 1 ELSE 0 END,
            channel = COALESCE(channel, 'SYSTEM')
        WHERE module IS NULL OR is_read IS NULL
        """
    )
    conn.commit()

    file_cols = {
        "calendar_event_id": "INTEGER",
        "request_number": "INTEGER",
    }
    for col, defn in file_cols.items():
        if not _column_exists("files", col):
            cursor.execute(f"ALTER TABLE files ADD COLUMN {col} {defn}")
    conn.commit()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_agent_settings (
            user_id INTEGER NOT NULL,
            agent_code TEXT NOT NULL,
            model TEXT DEFAULT 'openai/gpt-5-mini',
            tone TEXT DEFAULT 'neutral',
            language TEXT DEFAULT 'ru',
            context_depth INTEGER DEFAULT 20,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, agent_code)
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ai_agent_memory (
            user_id INTEGER NOT NULL,
            agent_code TEXT NOT NULL,
            memory_key TEXT NOT NULL,
            memory_value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, agent_code, memory_key)
        )
        """
    )
    conn.commit()

    _seed_ai_agents()
    _seed_workflow_rules()


def _seed_ai_agents():
    agents = [
        ("AI_GENERAL", "Общий AI", "Универсальный помощник платформы", None,
         "Ты AI_GENERAL — универсальный ассистент ERP/CRM платформы Фомы."),
        ("AI_DRONE", "Drone AI", "Инженерия и проекты дронов", "drone",
         "Ты AI_DRONE — инженерный ассистент по дронам, BOM, проектам и производству."),
        ("AI_LEGAL", "Legal AI", "Юриспруденция и документы", "law",
         "Ты AI_LEGAL — юридический ассистент. Законодательство Украины, договоры, compliance."),
        ("AI_AGRO", "Agro AI", "Agro Trading и сделки", "agro_trading",
         "Ты AI_AGRO — ассистент Agro Trading: зерно, контракты, логистика, финансы."),
        ("AI_CRYPTO", "Crypto AI", "Crypto OTC операции", "crypto_otc",
         "Ты AI_CRYPTO — ассистент Crypto OTC: USDT, платежи, compliance."),
        ("AI_BEAUTY", "Beauty AI", "Cafe & Beauty", "cafe_beauty",
         "Ты AI_BEAUTY — ассистент Cafe & Beauty: операции, маркeting, клиенты."),
        ("AI_FINANCE", "Finance AI", "Финансы и аналитика", "reports",
         "Ты AI_FINANCE — финансовый ассистент: PnL, бюджеты, отчёты, cashflow, KPI."),
    ]
    for code, name, desc, module, prompt in agents:
        cursor.execute("SELECT id FROM ai_agents WHERE code = ?", (code,))
        if cursor.fetchone():
            continue
        cursor.execute(
            """
            INSERT INTO ai_agents (code, name, description, prompt, active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (code, name, desc, prompt),
        )
    conn.commit()


def _seed_workflow_rules():
    rules = [
        ("AGRO_REQUEST_CREATED", "agro_trading", "send_notification",
         '{"title":"Новая Agro заявка","priority":"HIGH"}'),
        ("TASK_CREATED", "system", "send_notification",
         '{"title":"Создана задача","priority":"NORMAL"}'),
        ("TASK_COMPLETED", "system", "send_notification",
         '{"title":"Задача завершена","priority":"INFO"}'),
        ("EVENT_CREATED", "calendar", "send_notification",
         '{"title":"Создано событие","priority":"INFO"}'),
        ("PROJECT_CREATED", "ai_assistant", "send_notification",
         '{"title":"Создан AI проект","priority":"INFO"}'),
        ("FILE_UPLOADED", "system", "send_notification",
         '{"title":"Загружен файл","priority":"INFO"}'),
        ("USER_CREATED", "users", "send_notification",
         '{"title":"Новый пользователь","priority":"INFO"}'),
    ]
    for trigger, module, action, payload in rules:
        cursor.execute(
            "SELECT id FROM workflow_rules WHERE trigger_code = ? AND action_type = ?",
            (trigger, action),
        )
        if cursor.fetchone():
            continue
        cursor.execute(
            """
            INSERT INTO workflow_rules (trigger_code, module, action_type, action_payload, active)
            VALUES (?, ?, ?, ?, 1)
            """,
            (trigger, module, action, payload),
        )
    conn.commit()


_migrate_schema()

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
    from services.workflow_engine import WorkflowEngine
    WorkflowEngine.execute_workflow(
        "USER_CREATED",
        telegram_id,
        "users",
        entity_type="user",
        entity_id=telegram_id,
        payload={"full_name": full_name},
    )
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
    from services.permissions import PermissionService
    return PermissionService.has_permission(telegram_id, permission)


def has_module_access(telegram_id: int, module: str) -> bool:
    from services.permissions import PermissionService
    return PermissionService.can_access_module(telegram_id, module)


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
    from services.statuses import normalize_status
    from services.workflow_triggers import WorkflowTriggers

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
            normalize_status("NEW"),
            manager_id
        )
    )

    conn.commit()

    cursor.execute(
        "SELECT request_number FROM requests WHERE id=?",
        (cursor.lastrowid,)
    )

    row = cursor.fetchone()
    request_number = row[0]

    WorkflowTriggers.on_request_created(
        client_id,
        request_number,
        module="agro_trading",
        product=product,
    )
    from services.workflow_engine import WorkflowEngine
    WorkflowEngine.execute_workflow(
        "AGRO_REQUEST_CREATED",
        client_id,
        "agro_trading",
        entity_type="request",
        entity_id=request_number,
        payload={"title": f"Новая заявка #{request_number}", "product": product},
    )
    notify_agro_managers_new_request(
        request_number,
        product=product,
        client_name=client_name,
    )
    log_audit(client_id, "create_request", "agro_trading", f"#{request_number}|{product}")
    return request_number


def notify_agro_managers_new_request(
    request_number: int,
    product: str = "",
    client_name: str = "",
    exclude_id: int = None,
) -> list[int]:
    from config import MANAGER_ID, OWNER_ID

    manager_ids = {MANAGER_ID, OWNER_ID}
    cursor.execute(
        """
        SELECT DISTINCT ur.user_id
        FROM user_roles ur
        JOIN roles r ON r.id = ur.role_id
        WHERE r.role_name IN ('AGRO_MANAGER', 'MANAGER', 'ADMIN', 'OWNER')
        """
    )
    for row in cursor.fetchall():
        if row[0]:
            manager_ids.add(row[0])

    notified = []
    for mid in manager_ids:
        if not mid or mid == exclude_id:
            continue
        register_module_notification(
            mid,
            "agro_trading",
            title=f"Новая Agro заявка #{request_number}",
            message=f"{client_name} · {product}".strip(" ·"),
            priority="HIGH",
        )
        notified.append(mid)
    return notified


def update_request_status(
    request_number: int,
    status: str,
    manager_id: int = None
):
    from services.statuses import normalize_status
    from services.workflow_triggers import WorkflowTriggers

    status = normalize_status(status)
    old_status = get_request_status(request_number)

    cursor.execute(
        """
        UPDATE requests
        SET status = ?,
            manager_id = COALESCE(?, manager_id)
        WHERE request_number = ?
        """,
        (
            status,
            manager_id,
            request_number
        )
    )

    conn.commit()

    if old_status and old_status != status:
        req = get_request_by_number(request_number)
        actor = manager_id or (req[2] if req else 0)
        WorkflowTriggers.on_request_status_changed(
            actor,
            request_number,
            old_status,
            status,
            module="agro_trading",
        )
        log_audit(
            actor,
            "update_request_status",
            "agro_trading",
            f"#{request_number}:{old_status}->{status}",
        )
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
        from services.statuses import normalize_status
        return normalize_status(row[0])

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
    from services.statuses import normalize_status
    status = normalize_status(status)
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


def get_request_by_number(number):
    cursor.execute(
        """
        SELECT *
        FROM requests
        WHERE request_number = ?
        """,
        (number,),
    )
    return cursor.fetchone()


def assign_manager(request_number, manager_id):
    from services.workflow_triggers import WorkflowTriggers

    cursor.execute(
        """
        UPDATE requests
        SET manager_id = ?
        WHERE request_number = ?
        """,
        (manager_id, request_number),
    )

    conn.commit()
    WorkflowTriggers.on_manager_assigned(
        manager_id,
        request_number,
        manager_id,
        module="agro_trading",
    )
    log_audit(
        manager_id,
        "assign_manager",
        "agro_trading",
        f"#{request_number}:manager={manager_id}",
    )
def get_requests_by_manager(manager_id):
    cursor.execute(
        """
        SELECT *
        FROM requests
        WHERE manager_id = ?
        ORDER BY id DESC
        """,
        (manager_id,),
    )
    return cursor.fetchall()


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


def create_ai_project(
    user_id: int,
    title: str,
    description: str = "",
    category: str = "general",
) -> int:
    category = (category or "general").strip().lower()[:64]
    cursor.execute(
        """
        INSERT INTO ai_projects (user_id, title, description, category)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, title.strip(), description.strip(), category),
    )
    conn.commit()
    project_id = cursor.lastrowid
    from services.workflow_engine import WorkflowEngine
    WorkflowEngine.execute_workflow(
        "PROJECT_CREATED",
        user_id,
        "ai_assistant",
        entity_type="project",
        entity_id=project_id,
        payload={"title": title},
    )
    return project_id


def get_ai_projects(user_id: int, include_deleted: bool = False):
    if include_deleted:
        cursor.execute(
            """
            SELECT id, title, description, category, status, created_at, user_id
            FROM ai_projects
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user_id,),
        )
    else:
        cursor.execute(
            """
            SELECT id, title, description, category, status, created_at, user_id
            FROM ai_projects
            WHERE user_id = ? AND status != 'deleted'
            ORDER BY id DESC
            """,
            (user_id,),
        )
    return cursor.fetchall()


def get_ai_project(user_id: int, project_id: int):
    cursor.execute(
        """
        SELECT id, title, description, category, status, created_at, user_id
        FROM ai_projects
        WHERE user_id = ? AND id = ? AND status != 'deleted'
        """,
        (user_id, project_id),
    )
    return cursor.fetchone()


def delete_ai_project(user_id: int, project_id: int) -> bool:
    project = get_ai_project(user_id, project_id)
    if not project:
        return False
    cursor.execute(
        "DELETE FROM ai_project_messages WHERE project_id = ?",
        (project_id,),
    )
    cursor.execute(
        "DELETE FROM ai_projects WHERE id = ? AND user_id = ?",
        (project_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def add_ai_project_message(project_id: int, role: str, message: str) -> int:
    cursor.execute(
        """
        INSERT INTO ai_project_messages (project_id, role, message)
        VALUES (?, ?, ?)
        """,
        (project_id, role, message),
    )
    conn.commit()
    return cursor.lastrowid


def get_ai_project_messages(project_id: int, limit: int = 50) -> list[dict]:
    cursor.execute(
        """
        SELECT role, message, created_at
        FROM ai_project_messages
        WHERE project_id = ?
        ORDER BY id DESC
        LIMIT ?
        """,
        (project_id, limit),
    )
    rows = cursor.fetchall()
    rows.reverse()
    return [
        {"role": role, "message": message, "created_at": created_at}
        for role, message, created_at in rows
    ]


def get_ai_project_history_for_llm(project_id: int, limit: int = 20) -> list[dict]:
    messages = get_ai_project_messages(project_id, limit)
    return [{"role": item["role"], "content": item["message"]} for item in messages]


AI_PROJECT_CATEGORIES = {
    "general": "Общее",
    "business": "Бизнес",
    "health": "Здоровье / БАД",
    "tech": "Технологии",
    "construction": "Строительство",
    "crypto": "Криптовалюта",
    "legal": "Юриспруденция",
    "agro": "Agro",
}


def _extract_labeled_field(text: str, labels: tuple[str, ...]) -> str:
    import re
    for label in labels:
        pattern = rf"(?mi){re.escape(label)}\s*[:：]\s*(.+?)(?:\n|$)"
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def parse_project_create_text(text: str) -> dict | None:
    import re
    lower = text.lower().strip()
    create_keywords = (
        "создай проект",
        "создать проект",
        "новый проект",
        "create project",
    )
    if not any(keyword in lower for keyword in create_keywords):
        return None

    title = _extract_labeled_field(text, ("название", "title", "name"))
    description = _extract_labeled_field(text, ("описание", "description"))
    category_raw = _extract_labeled_field(text, ("категория", "category"))
    category = category_raw.strip().lower() if category_raw else "general"

    if not title:
        inline = re.sub(
            r"(?i)(создай проект|создать проект|новый проект|create project)\s*[:：]?\s*",
            "",
            text.strip(),
        )
        if inline and "\n" not in inline:
            title = inline.strip()

    if not title:
        return {"title": "", "description": description, "category": category}

    return {
        "title": title,
        "description": description,
        "category": category,
    }


def format_ai_project_context(project_row) -> str:
    if not project_row:
        return ""
    project_id, title, description, category, status, created_at, owner_id = project_row
    category_label = AI_PROJECT_CATEGORIES.get(category, category)
    return (
        f"\n\nАктивный проект #{project_id}: «{title}»\n"
        f"Категория: {category_label}\n"
        f"Описание: {description or '—'}\n"
        f"Статус: {status}\n"
        f"Создан: {created_at}\n"
        f"Владелец ID: {owner_id}\n"
        "Все сообщения пользователя в этом диалоге относятся к этому проекту."
    )


def format_ai_project_detail(user_id: int, project_id: int) -> str:
    project = get_ai_project(user_id, project_id)
    if not project:
        return "Проект не найден."
    pid, title, description, category, status, created_at, owner_id = project
    category_label = AI_PROJECT_CATEGORIES.get(category, category)
    msg_count = len(get_ai_project_messages(project_id, limit=1000))
    return (
        f"📁 Проект #{pid}\n\n"
        f"📌 Название: {title}\n"
        f"📝 Описание: {description or '—'}\n"
        f"🏷 Категория: {category_label}\n"
        f"📊 Статус: {status}\n"
        f"👤 Владелец ID: {owner_id}\n"
        f"🕒 Создан: {created_at}\n"
        f"💬 Сообщений: {msg_count}"
    )


def format_projects_text(user_id: int, active_project_id: int = None) -> str:
    projects = get_ai_projects(user_id)
    if not projects:
        return (
            "У вас пока нет проектов.\n\n"
            "Создайте проект сообщением, например:\n"
            "Создай проект:\n"
            "Название: Производство БАД\n"
            "Описание: Запуск капсульного производства"
        )

    lines = ["📁 Ваши проекты:\n"]
    for project_id, title, description, category, status, created_at, owner_id in projects:
        category_label = AI_PROJECT_CATEGORIES.get(category, category)
        active_mark = " 🔵 активный" if active_project_id == project_id else ""
        lines.append(
            f"#{project_id} · {title}{active_mark}\n"
            f"   🏷 {category_label} · {status}\n"
            f"   {description or '—'}\n"
            f"   👤 владелец: {owner_id} · 🕒 {created_at}"
        )
    return "\n\n".join(lines)


def create_ai_task(
    user_id: int,
    title: str,
    project_id: int = None,
) -> int:
    if project_id is not None:
        project = get_ai_project(user_id, project_id)
        if not project:
            return 0
    return create_task(
        creator_id=user_id,
        title=title,
        module="ai_assistant",
        project_id=project_id,
        assignee_id=user_id,
    )


def get_ai_tasks(user_id: int, project_id: int = None):
    rows = get_tasks_by_user(user_id, scope="my", limit=100)
    rows = [r for r in rows if r[3] == "ai_assistant"]
    if project_id is not None:
        rows = [r for r in rows if r[4] == project_id]
    return [(r[0], r[4], r[1], r[8], r[10]) for r in rows]


def update_ai_task_status(user_id: int, task_id: int, status: str) -> bool:
    return update_task_status(task_id, user_id, status)


def format_tasks_text(user_id: int, project_id: int = None) -> str:
    rows = get_tasks_by_user(user_id, scope="my", limit=50)
    rows = [r for r in rows if r[3] == "ai_assistant"]
    if project_id is not None:
        rows = [r for r in rows if r[4] == project_id]
    if not rows:
        return "Задач пока нет."

    lines = ["✅ Ваши задачи:\n"]
    for tid, _title, _desc, _mod, proj_id, *_rest in rows:
        title = _title
        status = _rest[3]
        created_at = _rest[5]
        icon = TASK_STATUS_ICONS.get(status, "🆕")
        project_part = f" · проект #{proj_id}" if proj_id else ""
        lines.append(f"{icon} #{tid} {title}{project_part} ({created_at})")
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
    "notifications": "Уведомления",
    "tasks": "Задачи",
}

# ==========================================================
# UNIFIED CALENDAR
# ==========================================================

CALENDAR_MODULES = {
    "agro_trading": "AGRO",
    "crypto_otc": "CRYPTO",
    "drone": "DRONE",
    "cafe_beauty": "CAFE",
    "law": "LEGAL",
    "ai_assistant": "AI",
    "system": "SYSTEM",
    "calendar": "CALENDAR",
}

CALENDAR_MODULE_ALIASES = {
    "agro": "agro_trading",
    "crypto": "crypto_otc",
    "drone": "drone",
    "cafe": "cafe_beauty",
    "beauty": "cafe_beauty",
    "legal": "law",
    "law": "law",
    "ai": "ai_assistant",
    "system": "system",
}

CALENDAR_STATUSES = ("PLANNED", "ACTIVE", "DONE", "CANCELLED", "MISSED")

CALENDAR_EVENT_TYPES = (
    "general", "task", "meeting", "deadline", "reminder", "agro", "agro_task",
    "payment", "delivery",
)

CALENDAR_STATUS_ICONS = {
    "PLANNED": "📋",
    "ACTIVE": "▶️",
    "DONE": "✅",
    "CANCELLED": "❌",
    "MISSED": "⚠️",
}

CALENDAR_SOURCE_MODULES = tuple(CALENDAR_MODULES.keys())

_EVENT_SELECT = """
    SELECT id, title, description, module, event_type, creator_id, owner_id,
           start_time, end_time, remind_before, status, created_at,
           start_datetime, end_datetime, responsible_user, priority,
           reminder_minutes, repeat_rule, updated_at
    FROM calendar_events
"""


def _normalize_calendar_module(module: str) -> str:
    if not module:
        return "system"
    key = module.strip().lower()
    if key in CALENDAR_MODULES:
        return key
    return CALENDAR_MODULE_ALIASES.get(key, "system")


def _normalize_calendar_status(status: str) -> str:
    if not status:
        return "PLANNED"
    value = str(status).strip().upper()
    legacy = {
        "ACTIVE": "ACTIVE", "DONE": "DONE", "CANCELLED": "CANCELLED",
        "CANCELED": "CANCELLED", "PLANNED": "PLANNED", "MISSED": "MISSED",
    }
    return legacy.get(value, "PLANNED")


def create_event(
    creator_id: int,
    title: str,
    start_time: str,
    description: str = "",
    module: str = "system",
    event_type: str = "general",
    owner_id: int = None,
    end_time: str = None,
    remind_before: int = 0,
    status: str = "PLANNED",
) -> int:
    module = _normalize_calendar_module(module)
    owner_id = owner_id or creator_id
    status = _normalize_calendar_status(status)
    event_type = event_type if event_type in CALENDAR_EVENT_TYPES else "general"

    cursor.execute(
        """
        INSERT INTO calendar_events (
            title, description, module, event_type, creator_id, owner_id,
            start_time, end_time, remind_before, status,
            start_datetime, end_datetime, responsible_user,
            reminder_minutes, priority
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title.strip(),
            description.strip() if description else None,
            module,
            event_type,
            creator_id,
            owner_id,
            start_time,
            end_time,
            remind_before,
            status,
            start_time,
            end_time,
            owner_id,
            remind_before,
            "normal",
        ),
    )
    conn.commit()
    event_id = cursor.lastrowid
    log_audit(creator_id, "create_event", "calendar", f"{module}|{title}|{start_time}")
    from services.workflow_triggers import WorkflowTriggers
    WorkflowTriggers.on_calendar_event_created(
        creator_id, event_id, title, module=module,
    )
    from services.workflow_engine import WorkflowEngine
    WorkflowEngine.execute_workflow(
        "EVENT_CREATED",
        creator_id,
        module,
        entity_type="event",
        entity_id=event_id,
        payload={"title": title},
    )
    return event_id


def get_event(event_id: int, user_id: int = None):
    cursor.execute(f"{_EVENT_SELECT} WHERE id = ?", (event_id,))
    row = cursor.fetchone()
    if not row or user_id is None:
        return row
    from config import OWNER_ID, MANAGER_ID
    if user_id in (OWNER_ID, MANAGER_ID):
        return row
    if user_id in (row[5], row[6]):
        return row
    from services.permissions import PermissionService
    if PermissionService.is_crm_operator(user_id):
        return row
    return None


def get_events_by_user(
    user_id: int,
    scope: str = "my",
    status: str = None,
    limit: int = 20,
):
    query = f"{_EVENT_SELECT} WHERE 1=1"
    params = []

    if scope == "my":
        query += " AND (creator_id = ? OR owner_id = ?)"
        params.extend([user_id, user_id])
    elif scope == "owned":
        query += " AND owner_id = ?"
        params.append(user_id)
    elif scope == "all":
        pass
    else:
        query += " AND (creator_id = ? OR owner_id = ?)"
        params.extend([user_id, user_id])

    if status:
        query += " AND status = ?"
        params.append(_normalize_calendar_status(status))

    query += " ORDER BY start_time ASC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def get_events_by_module(
    module: str,
    user_id: int = None,
    limit: int = 20,
):
    module = _normalize_calendar_module(module)
    query = f"{_EVENT_SELECT} WHERE module = ?"
    params = [module]
    if user_id is not None:
        query += " AND (creator_id = ? OR owner_id = ?)"
        params.extend([user_id, user_id])
    query += " ORDER BY start_time ASC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def get_today_events(user_id: int, scope: str = "my", limit: int = 20):
    query = f"""
        {_EVENT_SELECT}
        WHERE date(COALESCE(start_time, start_datetime)) = date('now')
    """
    params = []
    if scope != "all":
        query += " AND (creator_id = ? OR owner_id = ?)"
        params.extend([user_id, user_id])
    query += " ORDER BY start_time ASC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def get_week_events(user_id: int, scope: str = "my", limit: int = 50):
    query = f"""
        {_EVENT_SELECT}
        WHERE datetime(COALESCE(start_time, start_datetime)) >= datetime('now', 'start of day')
          AND datetime(COALESCE(start_time, start_datetime)) < datetime('now', '+7 days', 'start of day')
    """
    params = []
    if scope != "all":
        query += " AND (creator_id = ? OR owner_id = ?)"
        params.extend([user_id, user_id])
    query += " ORDER BY start_time ASC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def get_month_events(user_id: int, scope: str = "my", limit: int = 100):
    query = f"""
        {_EVENT_SELECT}
        WHERE strftime('%Y-%m', COALESCE(start_time, start_datetime)) = strftime('%Y-%m', 'now')
    """
    params = []
    if scope != "all":
        query += " AND (creator_id = ? OR owner_id = ?)"
        params.extend([user_id, user_id])
    query += " ORDER BY start_time ASC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def get_reminder_events(user_id: int, limit: int = 20):
    query = f"""
        {_EVENT_SELECT}
        WHERE (creator_id = ? OR owner_id = ?)
          AND remind_before > 0
          AND status IN ('PLANNED', 'ACTIVE')
          AND datetime(COALESCE(start_time, start_datetime), '-' || remind_before || ' minutes')
              <= datetime('now', '+1 day')
        ORDER BY start_time ASC LIMIT ?
    """
    cursor.execute(query, (user_id, user_id, limit))
    return cursor.fetchall()


def get_events_needing_reminder(limit: int = 50):
    """API for future NotificationService — events due for reminder dispatch."""
    query = f"""
        {_EVENT_SELECT}
        WHERE remind_before > 0
          AND status IN ('PLANNED', 'ACTIVE')
          AND datetime(COALESCE(start_time, start_datetime), '-' || remind_before || ' minutes')
              <= datetime('now')
          AND datetime(COALESCE(start_time, start_datetime)) >= datetime('now', '-1 hour')
        ORDER BY start_time ASC LIMIT ?
    """
    cursor.execute(query, (limit,))
    return cursor.fetchall()


def build_calendar_notification_payload(event_row: tuple) -> dict:
    """API for future NotificationService."""
    (
        eid, title, description, module, event_type, creator_id, owner_id,
        start_time, end_time, remind_before, status, created_at, *_rest,
    ) = event_row
    mod_label = CALENDAR_MODULES.get(module, module)
    return {
        "user_id": owner_id,
        "category": "calendar",
        "title": f"🔔 {title}",
        "message": (
            f"{mod_label} · {start_time}\n"
            f"{description or ''}"
        ).strip(),
        "priority": "INFO",
        "is_reminder": True,
        "source_module": module,
        "metadata": {
            "event_id": eid,
            "event_type": event_type,
            "start_time": start_time,
            "end_time": end_time,
            "remind_before": remind_before,
            "status": status,
        },
    }


def update_event(event_id: int, user_id: int, **fields) -> bool:
    event = get_event(event_id, user_id)
    if not event:
        return False
    allowed = {
        "title", "description", "module", "event_type", "owner_id",
        "start_time", "end_time", "remind_before", "status",
    }
    parts = []
    params = []
    for key, value in fields.items():
        if key not in allowed or value is None:
            continue
        if key == "module":
            value = _normalize_calendar_module(value)
        if key == "status":
            value = _normalize_calendar_status(value)
        parts.append(f"{key} = ?")
        params.append(value)
    if not parts:
        return False
    if "start_time" in fields:
        parts.append("start_datetime = ?")
        params.append(fields["start_time"])
    if "end_time" in fields:
        parts.append("end_datetime = ?")
        params.append(fields["end_time"])
    if "owner_id" in fields:
        parts.append("responsible_user = ?")
        params.append(fields["owner_id"])
    if "remind_before" in fields:
        parts.append("reminder_minutes = ?")
        params.append(fields["remind_before"])
    parts.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([event_id])
    cursor.execute(
        f"UPDATE calendar_events SET {', '.join(parts)} WHERE id = ?",
        params,
    )
    conn.commit()
    return cursor.rowcount > 0


def delete_event(event_id: int, user_id: int) -> bool:
    event = get_event(event_id, user_id)
    if not event:
        return False
    from services.permissions import PermissionService
    if not PermissionService.can_delete_entity(
        user_id, "calendar_event", event_id, owner_id=event[6],
    ):
        return False
    cursor.execute("DELETE FROM calendar_events WHERE id = ?", (event_id,))
    conn.commit()
    log_audit(user_id, "delete_event", "calendar", str(event_id))
    return cursor.rowcount > 0


def format_event_card(event_row) -> str:
    if not event_row:
        return "Событие не найдено."
    (
        eid, title, description, module, event_type, creator_id, owner_id,
        start_time, end_time, remind_before, status, created_at, *_rest,
    ) = event_row
    mod_label = CALENDAR_MODULES.get(module, module)
    icon = CALENDAR_STATUS_ICONS.get(status, "📋")
    return (
        f"{icon} Событие #{eid}\n\n"
        f"📌 {title}\n"
        f"📝 {description or '—'}\n"
        f"🏷 Модуль: {mod_label} · тип: {event_type}\n"
        f"📊 Статус: {status}\n"
        f"👤 Создатель: {creator_id} · владелец: {owner_id}\n"
        f"🕒 Начало: {start_time}\n"
        f"🕒 Конец: {end_time or '—'}\n"
        f"🔔 Напомнить за: {remind_before or 0} мин.\n"
        f"📅 Создано: {created_at}"
    )


def format_calendar_events_text(
    user_id: int,
    module: str = None,
    limit: int = 10,
    events: list = None,
) -> str:
    if events is None:
        events = get_events_by_user(user_id, scope="my", limit=limit)
        if module:
            module = _normalize_calendar_module(module)
            events = [e for e in events if e[3] == module]
    if not events:
        return "Событий пока нет."

    lines = ["📅 События:\n"]
    for event in events:
        eid, title = event[0], event[1]
        mod, start_time, status = event[3], event[7], event[10]
        mod_label = CALENDAR_MODULES.get(mod, mod)
        icon = CALENDAR_STATUS_ICONS.get(status, "📋")
        lines.append(
            f"{icon} #{eid} · {title}\n"
            f"   🕒 {start_time} · {mod_label} · {status}"
        )
    return "\n".join(lines)


def parse_event_create_text(text: str) -> dict | None:
    import re
    lower = text.lower().strip()
    if not any(k in lower for k in ("создать событие", "новое событие", "create event")):
        return None
    title = _extract_labeled_field(text, ("название", "title"))
    description = _extract_labeled_field(text, ("описание", "description"))
    module = _extract_labeled_field(text, ("модуль", "module")) or "system"
    event_type = _extract_labeled_field(text, ("тип", "type", "event_type")) or "general"
    start_time = _extract_labeled_field(text, ("начало", "start", "start_time", "время"))
    end_time = _extract_labeled_field(text, ("конец", "end", "end_time"))
    remind_raw = _extract_labeled_field(text, ("напомнить", "remind", "remind_before"))
    remind_before = int(remind_raw) if remind_raw and remind_raw.isdigit() else 0
    if not title:
        inline = re.sub(
            r"(?i)(создать событие|новое событие|create event)\s*[:：]?\s*",
            "",
            text.strip(),
        )
        if inline and "\n" not in inline:
            title = inline.strip()
    return {
        "title": title,
        "description": description,
        "module": module,
        "event_type": event_type,
        "start_time": start_time,
        "end_time": end_time or None,
        "remind_before": remind_before,
    }


# --- Legacy calendar wrappers ---

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
    _ = priority, repeat_rule
    if module not in CALENDAR_SOURCE_MODULES and module != "calendar":
        module = "calendar"
    if not start_datetime:
        start_datetime = "1970-01-01 00:00:00"
    return create_event(
        creator_id=user_id,
        title=title,
        start_time=start_datetime,
        description=description,
        module=module,
        owner_id=user_id,
        end_time=end_datetime,
        remind_before=reminder_minutes or 0,
        status="ACTIVE",
    )


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
    _ = priority, repeat_rule
    return create_event(
        creator_id=responsible_user,
        title=title,
        start_time=start_datetime,
        description=description,
        module=module,
        owner_id=responsible_user,
        end_time=end_datetime,
        remind_before=reminder_minutes or 0,
        status=_normalize_calendar_status(status),
    )


def get_calendar_event(event_id: int, user_id: int):
    return get_event(event_id, user_id)


def get_calendar_events(
    user_id: int,
    module: str = None,
    status: str = None,
    limit: int = 20,
):
    events = get_events_by_user(user_id, scope="my", status=status, limit=limit)
    if module:
        module = _normalize_calendar_module(module)
        events = [e for e in events if e[3] == module]
    return events


def update_calendar_event(event_id: int, user_id: int, **fields) -> bool:
    mapped = {}
    key_map = {
        "start_datetime": "start_time",
        "end_datetime": "end_time",
        "reminder_minutes": "remind_before",
    }
    for key, value in fields.items():
        mapped[key_map.get(key, key)] = value
    return update_event(event_id, user_id, **mapped)


def delete_calendar_event(event_id: int, user_id: int) -> bool:
    return delete_event(event_id, user_id)


def complete_calendar_event(event_id: int, user_id: int) -> bool:
    return update_event(event_id, user_id, status="DONE")


def reschedule_calendar_event(
    event_id: int,
    user_id: int,
    start_datetime: str,
    end_datetime: str = None,
) -> bool:
    return update_event(
        event_id, user_id,
        start_time=start_datetime,
        end_time=end_datetime,
    )


MODULE_AI_AGENTS = {
    "crypto_otc": "AI_CRYPTO",
    "agro_trading": "AI_AGRO",
    "law": "AI_LEGAL",
    "drone": "AI_DRONE",
    "cafe_beauty": "AI_BEAUTY",
    "users": "AI_GENERAL",
    "reports": "AI_GENERAL",
    "calendar": "AI_GENERAL",
    "ai_assistant": "AI_GENERAL",
}


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
    code = MODULE_AI_AGENTS.get(module)
    if not code:
        return None
    return get_ai_agent(code)


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


# ==========================================================
# AGRO TRADING CRM (extension)
# ==========================================================

AGRO_COUNTERPARTY_TYPES = {
    "supplier": "Поставщик",
    "buyer": "Покупатель",
    "carrier": "Перевозчик",
    "broker": "Брокер",
    "forwarder": "Экспедитор",
}

AGRO_CONTRACT_TYPES = ("FOB", "CIF", "EXW", "FCA")

AGRO_CONTRACT_STATUSES = (
    "DRAFT", "SIGNED", "IN_PROGRESS", "FULFILLED", "CANCELLED",
)

AGRO_DELIVERY_STATUSES = (
    "PLANNED", "LOADING", "IN_TRANSIT", "ARRIVED", "DELIVERED", "DELAYED",
)

AGRO_DOCUMENT_TYPES = {
    "invoice": "Инвойс",
    "contract": "Контракт",
    "certificate": "Сертификат",
    "bill_of_lading": "Коносамент",
    "customs": "Таможенный документ",
}

AGRO_CALENDAR_EVENT_TYPES = {
    "agro_task": "Agro Task",
    "loading": "Погрузка",
    "payment": "Оплата",
    "contract_signing": "Подписание контракта",
    "cargo_arrival": "Прибытие груза",
}

AGRO_CRM_SECTIONS = {
    "counterparties": "👥 Контрагенты",
    "contracts": "📑 Контракты",
    "logistics": "🚢 Логистика",
    "documents": "📄 Документы",
    "finance": "💵 Финансы",
    "calendar": "📅 Календарь",
    "reports": "📊 Отчеты Agro",
    "ai_assistant": "🤖 AI Agro",
}

AGRO_COUNTERPARTY_BUTTON_TO_TYPE = {
    "👤 Поставщики": "supplier",
    "🛒 Покупатели": "buyer",
    "🚛 Перевозчики": "carrier",
    "🤝 Брокеры": "broker",
    "📦 Экспедиторы": "forwarder",
}

AGRO_AI_CONTEXT_AREAS = (
    "requests",
    "counterparties",
    "contracts",
    "logistics",
    "documents",
    "finance",
)


def can_access_agro_section(user_id: int, section_key: str) -> bool:
    if section_key not in AGRO_CRM_SECTIONS:
        return False
    from services.request_auth import RequestAuthService
    return RequestAuthService.can_access_agro_requests(user_id)


def create_agro_counterparty(
    created_by: int,
    name: str,
    counterparty_type: str,
    country: str = None,
    contact_info: str = None,
    notes: str = None,
) -> int:
    # TODO: future implementation — validation and duplicate checks
    if counterparty_type not in AGRO_COUNTERPARTY_TYPES:
        counterparty_type = "supplier"
    cursor.execute(
        """
        INSERT INTO agro_counterparties (
            name, counterparty_type, country, contact_info, notes, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name.strip(), counterparty_type, country, contact_info, notes, created_by),
    )
    conn.commit()
    cp_id = cursor.lastrowid
    register_module_notification(
        created_by,
        "agro_trading",
        title=f"Контрагент #{cp_id} создан",
        message=name,
        priority="INFO",
    )
    return cp_id


def get_agro_counterparties(
    user_id: int,
    counterparty_type: str = None,
    limit: int = 20,
):
    # TODO: future implementation — team-wide counterparty registry
    query = """
        SELECT id, name, counterparty_type, country, contact_info, notes, created_at
        FROM agro_counterparties
        WHERE created_by = ?
    """
    params = [user_id]
    if counterparty_type:
        query += " AND counterparty_type = ?"
        params.append(counterparty_type)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def format_agro_counterparties_text(
    user_id: int,
    counterparty_type: str = None,
    limit: int = 10,
) -> str:
    # TODO: future implementation — rich counterparty cards
    rows = get_agro_counterparties(user_id, counterparty_type, limit)
    type_label = AGRO_COUNTERPARTY_TYPES.get(counterparty_type, "Все")
    if not rows:
        return f"👥 Контрагенты ({type_label}): записей нет."
    lines = [f"👥 Контрагенты ({type_label}):\n"]
    for row in rows:
        cid, name, ctype, country, contact, notes, created_at = row
        label = AGRO_COUNTERPARTY_TYPES.get(ctype, ctype)
        lines.append(
            f"#{cid} · {name} · {label}\n"
            f"   🌍 {country or '—'} · 📞 {contact or '—'}\n"
            f"   🕒 {created_at}"
        )
        if notes:
            lines.append(f"   📝 {notes}")
    return "\n".join(lines)


def create_agro_contract(
    created_by: int,
    contract_number: str,
    contract_type: str,
    request_number: int = None,
    counterparty_id: int = None,
    execution_status: str = "DRAFT",
    notes: str = None,
) -> int:
    # TODO: future implementation — contract workflow and signing
    if contract_type not in AGRO_CONTRACT_TYPES:
        contract_type = "FOB"
    if execution_status not in AGRO_CONTRACT_STATUSES:
        execution_status = "DRAFT"
    cursor.execute(
        """
        INSERT INTO agro_contracts (
            contract_number, contract_type, execution_status,
            request_number, counterparty_id, notes, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            contract_number.strip(),
            contract_type,
            execution_status,
            request_number,
            counterparty_id,
            notes,
            created_by,
        ),
    )
    conn.commit()
    contract_id = cursor.lastrowid
    _integrate_agro_contract_created(contract_id, created_by, contract_number, request_number)
    return contract_id


def _integrate_agro_contract_created(
    contract_id: int,
    user_id: int,
    contract_number: str,
    request_number: int = None,
):
    # TODO: future implementation — calendar signing event and file attachment
    register_module_notification(
        user_id,
        "agro_trading",
        title=f"Контракт #{contract_id}",
        message=contract_number,
        priority="INFO",
    )
    register_agro_calendar_event(
        user_id,
        "contract_signing",
        title=f"Подписание: {contract_number}",
        description=f"agro_contract:{contract_id}|request:{request_number or '—'}",
    )


def get_agro_contracts(
    user_id: int,
    request_number: int = None,
    limit: int = 20,
):
    # TODO: future implementation — filters by status and type
    query = """
        SELECT id, contract_number, contract_type, execution_status,
               request_number, counterparty_id, notes, created_at
        FROM agro_contracts
        WHERE created_by = ?
    """
    params = [user_id]
    if request_number is not None:
        query += " AND request_number = ?"
        params.append(request_number)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def format_agro_contracts_text(user_id: int, request_number: int = None) -> str:
    # TODO: future implementation — contract detail view
    rows = get_agro_contracts(user_id, request_number=request_number)
    if not rows:
        return "📑 Контракты: записей нет."
    lines = ["📑 Контракты:\n"]
    for row in rows:
        cid, number, ctype, status, req_num, cp_id, notes, created_at = row
        lines.append(
            f"#{cid} · {number} · {ctype} · {status}\n"
            f"   📋 заявка #{req_num or '—'} · 👥 контрагент #{cp_id or '—'}\n"
            f"   🕒 {created_at}"
        )
        if notes:
            lines.append(f"   📝 {notes}")
    return "\n".join(lines)


def create_agro_logistics(
    created_by: int,
    request_number: int = None,
    transport: str = None,
    route: str = None,
    loading_date: str = None,
    eta: str = None,
    delivery_status: str = "PLANNED",
    notes: str = None,
) -> int:
    # TODO: future implementation — route tracking and carrier assignment
    if delivery_status not in AGRO_DELIVERY_STATUSES:
        delivery_status = "PLANNED"
    cursor.execute(
        """
        INSERT INTO agro_logistics (
            request_number, transport, route, loading_date, eta,
            delivery_status, notes, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_number, transport, route, loading_date, eta,
            delivery_status, notes, created_by,
        ),
    )
    conn.commit()
    log_id = cursor.lastrowid
    _integrate_agro_logistics_created(log_id, created_by, request_number, loading_date, eta)
    return log_id


def _integrate_agro_logistics_created(
    log_id: int,
    user_id: int,
    request_number: int = None,
    loading_date: str = None,
    eta: str = None,
):
    # TODO: future implementation — calendar loading/arrival events
    if loading_date:
        register_agro_calendar_event(
            user_id,
            "loading",
            title=f"Погрузка · заявка #{request_number or '—'}",
            start_datetime=loading_date,
            description=f"agro_logistics:{log_id}",
        )
    if eta:
        register_agro_calendar_event(
            user_id,
            "cargo_arrival",
            title=f"ETA · заявка #{request_number or '—'}",
            start_datetime=eta,
            description=f"agro_logistics:{log_id}",
        )


def get_agro_logistics(
    user_id: int,
    request_number: int = None,
    limit: int = 20,
):
    # TODO: future implementation — delivery status filters
    query = """
        SELECT id, request_number, transport, route, loading_date, eta,
               delivery_status, notes, created_at
        FROM agro_logistics
        WHERE created_by = ?
    """
    params = [user_id]
    if request_number is not None:
        query += " AND request_number = ?"
        params.append(request_number)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def format_agro_logistics_text(user_id: int, request_number: int = None) -> str:
    # TODO: future implementation — logistics timeline view
    rows = get_agro_logistics(user_id, request_number=request_number)
    if not rows:
        return "🚢 Логистика: записей нет."
    lines = ["🚢 Логистика:\n"]
    for row in rows:
        lid, req_num, transport, route, loading, eta, status, notes, created_at = row
        lines.append(
            f"#{lid} · заявка #{req_num or '—'} · {status}\n"
            f"   🚛 {transport or '—'} · 🗺 {route or '—'}\n"
            f"   📅 погрузка {loading or '—'} · ETA {eta or '—'}\n"
            f"   🕒 {created_at}"
        )
        if notes:
            lines.append(f"   📝 {notes}")
    return "\n".join(lines)


def create_agro_document(
    created_by: int,
    doc_type: str,
    title: str,
    request_number: int = None,
    file_id: int = None,
    notes: str = None,
) -> int:
    # TODO: future implementation — link to central files storage
    if doc_type not in AGRO_DOCUMENT_TYPES:
        doc_type = "invoice"
    cursor.execute(
        """
        INSERT INTO agro_documents (
            request_number, doc_type, title, file_id, notes, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (request_number, doc_type, title.strip(), file_id, notes, created_by),
    )
    conn.commit()
    doc_id = cursor.lastrowid
    if file_id:
        register_module_notification(
            created_by,
            "agro_trading",
            title=f"Документ #{doc_id} привязан",
            message=title,
            priority="INFO",
        )
    return doc_id


def get_agro_documents(
    user_id: int,
    request_number: int = None,
    doc_type: str = None,
    limit: int = 20,
):
    # TODO: future implementation — document versioning
    query = """
        SELECT id, request_number, doc_type, title, file_id, notes, created_at
        FROM agro_documents
        WHERE created_by = ?
    """
    params = [user_id]
    if request_number is not None:
        query += " AND request_number = ?"
        params.append(request_number)
    if doc_type:
        query += " AND doc_type = ?"
        params.append(doc_type)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def format_agro_documents_text(user_id: int, request_number: int = None) -> str:
    # TODO: future implementation — document list with file links
    rows = get_agro_documents(user_id, request_number=request_number)
    if not rows:
        return "📄 Документы: записей нет."
    lines = ["📄 Документы:\n"]
    doc_labels = ", ".join(AGRO_DOCUMENT_TYPES.values())
    lines.append(f"Типы: {doc_labels}\n")
    for row in rows:
        did, req_num, dtype, title, file_id, notes, created_at = row
        dtype_label = AGRO_DOCUMENT_TYPES.get(dtype, dtype)
        lines.append(
            f"#{did} · {title} · {dtype_label}\n"
            f"   📋 заявка #{req_num or '—'} · 📁 file #{file_id or '—'}\n"
            f"   🕒 {created_at}"
        )
        if notes:
            lines.append(f"   📝 {notes}")
    return "\n".join(lines)


def create_agro_finance(
    created_by: int,
    request_number: int = None,
    deal_amount: float = None,
    currency: str = "USD",
    paid_amount: float = 0,
    debt_amount: float = None,
    payment_schedule: str = None,
    notes: str = None,
) -> int:
    # TODO: future implementation — auto debt calculation and payment tracking
    if debt_amount is None and deal_amount is not None:
        debt_amount = max(deal_amount - (paid_amount or 0), 0)
    cursor.execute(
        """
        INSERT INTO agro_finance (
            request_number, deal_amount, currency, paid_amount,
            debt_amount, payment_schedule, notes, created_by
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            request_number, deal_amount, currency, paid_amount,
            debt_amount, payment_schedule, notes, created_by,
        ),
    )
    conn.commit()
    fin_id = cursor.lastrowid
    _integrate_agro_finance_created(fin_id, created_by, request_number, deal_amount, currency)
    return fin_id


def _integrate_agro_finance_created(
    fin_id: int,
    user_id: int,
    request_number: int = None,
    deal_amount: float = None,
    currency: str = "USD",
):
    # TODO: future implementation — payment calendar events from schedule
    register_module_notification(
        user_id,
        "agro_trading",
        title=f"Финансы · заявка #{request_number or '—'}",
        message=f"{deal_amount or 0} {currency}",
        priority="INFO",
    )


def get_agro_finance(
    user_id: int,
    request_number: int = None,
    limit: int = 20,
):
    # TODO: future implementation — aggregate debt reports
    query = """
        SELECT id, request_number, deal_amount, currency, paid_amount,
               debt_amount, payment_schedule, notes, created_at
        FROM agro_finance
        WHERE created_by = ?
    """
    params = [user_id]
    if request_number is not None:
        query += " AND request_number = ?"
        params.append(request_number)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def format_agro_finance_text(user_id: int, request_number: int = None) -> str:
    # TODO: future implementation — payment schedule UI
    rows = get_agro_finance(user_id, request_number=request_number)
    if not rows:
        return "💵 Финансы: записей нет."
    lines = ["💵 Финансы:\n"]
    for row in rows:
        fid, req_num, amount, currency, paid, debt, schedule, notes, created_at = row
        lines.append(
            f"#{fid} · заявка #{req_num or '—'}\n"
            f"   💰 {amount or 0} {currency} · оплачено {paid or 0}\n"
            f"   📉 задолженность {debt or 0}\n"
            f"   📅 график: {schedule or '—'}\n"
            f"   🕒 {created_at}"
        )
        if notes:
            lines.append(f"   📝 {notes}")
    return "\n".join(lines)


def register_agro_calendar_event(
    user_id: int,
    event_type: str,
    title: str,
    start_datetime: str = None,
    description: str = "",
):
    # TODO: future implementation — dedicated agro calendar sync rules
    type_label = AGRO_CALENDAR_EVENT_TYPES.get(event_type, event_type)
    full_title = f"[Agro] {type_label}: {title}"
    return register_calendar_event(
        user_id,
        "agro_trading",
        title=full_title,
        start_datetime=start_datetime,
        description=description or f"agro_event:{event_type}",
    )


def format_agro_calendar_text(user_id: int) -> str:
    # TODO: future implementation — agro-specific calendar filters
    events = get_calendar_events(user_id, module="agro_trading", limit=10)
    types = ", ".join(AGRO_CALENDAR_EVENT_TYPES.values())
    if not events:
        return (
            f"📅 Agro календарь\n\n"
            f"Типы событий: {types}\n\n"
            "Событий нет."
        )
    text = format_calendar_events_text(user_id, module="agro_trading", limit=10)
    return f"📅 Agro календарь\n\nТипы: {types}\n\n{text}"


def get_agro_report_summary(user_id: int) -> dict:
    # TODO: future implementation — real analytics from CRM data
    finance_rows = get_agro_finance(user_id, limit=100)
    contracts = get_agro_contracts(user_id, limit=100)
    total_deals = len(contracts)
    total_volume = sum(r[2] or 0 for r in finance_rows)
    total_paid = sum(r[4] or 0 for r in finance_rows)
    total_debt = sum(r[5] or 0 for r in finance_rows)
    total_profit = total_paid - total_debt if finance_rows else 0
    return {
        "deals_count": total_deals,
        "volume": total_volume,
        "profit": total_profit,
        "debt": total_debt,
    }


def format_agro_reports_text(user_id: int) -> str:
    # TODO: future implementation — export via reports module
    summary = get_agro_report_summary(user_id)
    return (
        "📊 Отчеты Agro Trading\n\n"
        f"Сделок: {summary['deals_count']}\n"
        f"Объемы: {summary['volume']}\n"
        f"Прибыль: {summary['profit']}\n"
        f"Задолженности: {summary['debt']}\n\n"
        "Детальная аналитика находится в разработке."
    )


def get_agro_ai_context(user_id: int) -> dict:
    # TODO: future implementation — aggregate context for AI Agro Assistant
    return {
        "user_id": user_id,
        "requests": [],
        "counterparties": get_agro_counterparties(user_id, limit=5),
        "contracts": get_agro_contracts(user_id, limit=5),
        "logistics": get_agro_logistics(user_id, limit=5),
        "documents": get_agro_documents(user_id, limit=5),
        "finance": get_agro_finance(user_id, limit=5),
    }


def format_agro_section_stub(section_key: str, user_id: int) -> str:
    # TODO: future implementation — load real section data from DB
    title = AGRO_CRM_SECTIONS.get(section_key, section_key)
    return (
        f"{title}\n\n"
        f"Модуль Agro Trading CRM.\n"
        f"Пользователь: {user_id}\n\n"
        "Раздел находится в разработке."
    )


def format_agro_ai_assistant_stub(user_id: int) -> str:
    # TODO: future implementation — connect dedicated AI Agro agent
    context = get_agro_ai_context(user_id)
    areas = ", ".join(AGRO_AI_CONTEXT_AREAS)
    loaded = sum(1 for area in AGRO_AI_CONTEXT_AREAS if context.get(area))
    return (
        "🤖 AI Agro Assistant\n\n"
        f"Будущий доступ к: {areas}.\n"
        f"Загружено контекстных блоков: {loaded}/{len(AGRO_AI_CONTEXT_AREAS)}.\n\n"
        "AI Agro Assistant находится в разработке."
    )


def format_agro_ai_context_stub(area: str, user_id: int) -> str:
    # TODO: future implementation — preview AI context for specific area
    context = get_agro_ai_context(user_id)
    items = context.get(area, [])
    count = len(items) if isinstance(items, list) else 0
    return (
        f"🤖 AI Agro контекст: {area}\n\n"
        f"Записей: {count}.\n\n"
        "Раздел находится в разработке."
    )


# ==========================================================
# AGRO DEAL LIFECYCLE
# ==========================================================

def create_agro_deal(
    request_number: int,
    client_id: int,
    product: str = None,
    manager_id: int = None,
    status: str = "NEW",
) -> int:
    from services.statuses import normalize_status
    cursor.execute(
        """
        INSERT OR IGNORE INTO agro_deals (
            request_number, client_id, product, manager_id, status
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (request_number, client_id, product, manager_id, normalize_status(status)),
    )
    conn.commit()
    if cursor.rowcount == 0:
        deal = get_agro_deal_by_request(request_number)
        return deal[0] if deal else 0
    return cursor.lastrowid


def get_agro_deal_by_request(request_number: int):
    cursor.execute(
        """
        SELECT id, request_number, client_id, product, status, manager_id,
               workflow_process_id, manager_task_id, document_folder_id,
               calendar_event_id, contract_id, logistics_id, finance_id,
               report_file_id, created_at, closed_at
        FROM agro_deals
        WHERE request_number = ?
        """,
        (request_number,),
    )
    return cursor.fetchone()


def update_agro_deal(request_number: int, **fields) -> bool:
    if not fields:
        return False
    from services.statuses import normalize_status
    allowed = {
        "product", "status", "manager_id", "workflow_process_id",
        "manager_task_id", "document_folder_id", "calendar_event_id",
        "contract_id", "logistics_id", "finance_id", "report_file_id", "closed_at",
    }
    parts = []
    params = []
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key == "status":
            value = normalize_status(value)
        parts.append(f"{key} = ?")
        params.append(value)
    if not parts:
        return False
    params.append(request_number)
    cursor.execute(
        f"UPDATE agro_deals SET {', '.join(parts)} WHERE request_number = ?",
        params,
    )
    conn.commit()
    return cursor.rowcount > 0


def bind_agro_deal_contract(request_number: int, contract_id: int) -> bool:
    return update_agro_deal(request_number, contract_id=contract_id)


def bind_agro_deal_logistics(request_number: int, logistics_id: int) -> bool:
    return update_agro_deal(request_number, logistics_id=logistics_id)


def bind_agro_deal_finance(request_number: int, finance_id: int) -> bool:
    return update_agro_deal(request_number, finance_id=finance_id)


def close_agro_deal(request_number: int, user_id: int) -> bool:
    from datetime import datetime
    from services.statuses import normalize_status
    _ = user_id
    return update_agro_deal(
        request_number,
        status=normalize_status("DONE"),
        closed_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )


def format_agro_deal_text(request_number: int) -> str:
    deal = get_agro_deal_by_request(request_number)
    if not deal:
        return f"Сделка по заявке #{request_number} не зарегистрирована."
    (
        did, req_num, client_id, product, status, manager_id,
        workflow_id, task_id, folder_id, cal_id, contract_id,
        logistics_id, finance_id, report_id, created_at, closed_at,
    ) = deal
    return (
        f"🌾 Agro-сделка #{did}\n\n"
        f"📋 Заявка: #{req_num}\n"
        f"📦 Товар: {product or '—'}\n"
        f"📊 Статус: {status}\n"
        f"👤 Клиент ID: {client_id}\n"
        f"👨‍💼 Менеджер ID: {manager_id or '—'}\n\n"
        f"⚙ Workflow: #{workflow_id or '—'}\n"
        f"✅ Задача: #{task_id or '—'}\n"
        f"📅 Календарь: #{cal_id or '—'}\n"
        f"📁 Папка: #{folder_id or '—'}\n"
        f"📑 Контракт: #{contract_id or '—'}\n"
        f"🚢 Логистика: #{logistics_id or '—'}\n"
        f"💵 Финансы: #{finance_id or '—'}\n"
        f"📊 Отчёт: #{report_id or '—'}\n\n"
        f"🕒 Создана: {created_at}\n"
        f"🏁 Закрыта: {closed_at or '—'}"
    )


def generate_agro_deal_report(request_number: int, user_id: int) -> int:
    from datetime import datetime

    deal = get_agro_deal_by_request(request_number)
    request = get_request_by_number(request_number)
    if not deal or not request:
        return 0

    report_body = format_agro_deal_text(request_number)
    contracts = get_agro_contracts(user_id, request_number=request_number, limit=5)
    logistics = get_agro_logistics(user_id, request_number=request_number, limit=5)
    finance = get_agro_finance(user_id, request_number=request_number, limit=5)

    lines = [report_body, "\n--- Детали ---"]
    if contracts:
        lines.append(f"\nКонтрактов: {len(contracts)}")
    if logistics:
        lines.append(f"Логистика: {len(logistics)} зап.")
    if finance:
        lines.append(f"Финансы: {len(finance)} зап.")
    summary = get_agro_report_summary(user_id)
    lines.append(
        f"\nСводка Agro: сделок {summary['deals_count']}, "
        f"объём {summary['volume']}, задолженность {summary['debt']}"
    )
    content = "\n".join(lines)

    file_id = register_module_file(
        uploaded_by=user_id,
        module="agro_trading",
        filename=f"agro/reports/deal_{request_number}.txt",
        original_filename=f"Отчёт сделка #{request_number}.txt",
        description=content[:500],
        tags=f"report,deal,{request_number}",
    )
    create_agro_document(
        created_by=user_id,
        doc_type="contract",
        title=f"Отчёт сделки #{request_number}",
        request_number=request_number,
        file_id=file_id,
        notes=f"generated_at:{datetime.utcnow().isoformat()}",
    )
    update_agro_deal(request_number, report_file_id=file_id)
    log_audit(user_id, "agro_deal_report", "agro_trading", f"deal:{request_number}")
    return file_id


# ==========================================================
# NOTIFICATIONS (central hub)
# ==========================================================

NOTIFICATION_CATEGORIES = {
    "crypto_otc": "Crypto OTC",
    "agro_trading": "Agro Trading",
    "law": "Юриспруденция",
    "drone": "Drone Engineering",
    "cafe_beauty": "Cafe & Beauty",
    "calendar": "Календарь",
    "ai_assistant": "AI Assistant",
}

NOTIFICATION_PRIORITIES = ("INFO", "WARNING", "CRITICAL")

NOTIFICATION_STATUSES = ("NEW", "READ", "ARCHIVED")

PRIORITY_ICONS = {
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "CRITICAL": "🚨",
}


def create_notification(
    user_id: int,
    category: str,
    title: str,
    message: str = "",
    priority: str = "INFO",
    is_important: bool = False,
    is_reminder: bool = False,
    source_module: str = None,
) -> int:
    # TODO: future implementation — trigger push/Telegram delivery from modules
    if category not in NOTIFICATION_CATEGORIES:
        return 0
    if priority not in NOTIFICATION_PRIORITIES:
        priority = "INFO"

    cursor.execute(
        """
        INSERT INTO notifications (
            user_id, category, title, message, priority,
            status, is_important, is_reminder, source_module,
            module, event_type, channel, is_read
        )
        VALUES (?, ?, ?, ?, ?, 'NEW', ?, ?, ?, ?, ?, ?, 0)
        """,
        (
            user_id,
            category,
            title.strip(),
            message.strip() if message else None,
            priority,
            int(is_important),
            int(is_reminder),
            source_module or category,
            source_module or category,
            "general",
            "SYSTEM",
        ),
    )
    conn.commit()
    return cursor.lastrowid


def register_module_notification(
    user_id: int,
    module: str,
    title: str,
    message: str = "",
    priority: str = "INFO",
    is_important: bool = False,
    is_reminder: bool = False,
) -> int:
    # TODO: future implementation — unified entry point for all system modules
    category = module if module in NOTIFICATION_CATEGORIES else "ai_assistant"
    notification_id = create_notification(
        user_id=user_id,
        category=category,
        title=title,
        message=message,
        priority=priority,
        is_important=is_important,
        is_reminder=is_reminder,
        source_module=module,
    )
    if notification_id:
        log_audit(user_id, "create_notification", "notifications", f"{module}|{title}")
    return notification_id


def get_notifications(
    user_id: int,
    status: str = None,
    category: str = None,
    important_only: bool = False,
    reminders_only: bool = False,
    limit: int = 20,
):
    # TODO: future implementation — pagination and full-text search
    query = """
        SELECT id, category, title, message, priority, status,
               is_important, is_reminder, source_module, created_at
        FROM notifications
        WHERE user_id = ?
    """
    params = [user_id]

    if status:
        query += " AND status = ?"
        params.append(status)
    if category:
        query += " AND category = ?"
        params.append(category)
    if important_only:
        query += " AND is_important = 1"
    if reminders_only:
        query += " AND is_reminder = 1"

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    return cursor.fetchall()


def get_notification(notification_id: int, user_id: int):
    # TODO: future implementation — shared/system notifications
    cursor.execute(
        """
        SELECT id, category, title, message, priority, status,
               is_important, is_reminder, source_module, created_at
        FROM notifications
        WHERE id = ? AND user_id = ?
        """,
        (notification_id, user_id),
    )
    return cursor.fetchone()


def mark_notification_read(notification_id: int, user_id: int) -> bool:
    # TODO: future implementation — batch read and read receipts
    cursor.execute(
        """
        UPDATE notifications
        SET status = 'READ', read_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ? AND status = 'NEW'
        """,
        (notification_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def archive_notification(notification_id: int, user_id: int) -> bool:
    # TODO: future implementation — soft archive with restore
    cursor.execute(
        """
        UPDATE notifications
        SET status = 'ARCHIVED', archived_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ? AND status != 'ARCHIVED'
        """,
        (notification_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def format_notifications_text(
    user_id: int,
    status: str = None,
    important_only: bool = False,
    reminders_only: bool = False,
    limit: int = 10,
) -> str:
    # TODO: future implementation — rich cards and grouping by category
    rows = get_notifications(
        user_id,
        status=status,
        important_only=important_only,
        reminders_only=reminders_only,
        limit=limit,
    )
    if not rows:
        return "Уведомлений нет."

    lines = ["🔔 Уведомления:\n"]
    for row in rows:
        nid = row[0]
        category = row[1]
        title = row[2]
        message = row[3]
        priority = row[4]
        nstatus = row[5]
        created_at = row[9]
        icon = PRIORITY_ICONS.get(priority, "ℹ️")
        cat_label = NOTIFICATION_CATEGORIES.get(category, category)
        lines.append(
            f"{icon} #{nid} · {title}\n"
            f"   📦 {cat_label} · {nstatus} · {priority}\n"
            f"   🕒 {created_at}"
        )
        if message:
            lines.append(f"   📝 {message}")
    return "\n".join(lines)


def get_notification_settings(user_id: int) -> dict:
    # TODO: future implementation — dedicated notification_settings table
    memory = load_memory(user_id)
    return {
        cat: memory.get(f"notify_{cat}", "1") == "1"
        for cat in NOTIFICATION_CATEGORIES
    }


def save_notification_settings(user_id: int, **settings) -> None:
    # TODO: future implementation — per-category and per-priority rules
    for key, enabled in settings.items():
        if key.startswith("notify_"):
            save_memory(user_id, key, "1" if enabled else "0")


def format_notification_settings_text(user_id: int) -> str:
    # TODO: future implementation — interactive settings UI
    settings = get_notification_settings(user_id)
    lines = ["⚙ Настройки уведомлений:\n"]
    for cat, label in NOTIFICATION_CATEGORIES.items():
        enabled = settings.get(cat, True)
        icon = "✅" if enabled else "❌"
        lines.append(f"{icon} {label}")
    lines.append(
        f"\nПриоритеты: {', '.join(NOTIFICATION_PRIORITIES)}\n"
        f"Статусы: {', '.join(NOTIFICATION_STATUSES)}"
    )
    return "\n".join(lines)


# ==========================================================
# UNIFIED TASKS (central hub)
# ==========================================================

TASK_MODULES = {
    "agro_trading": "AGRO",
    "crypto_otc": "CRYPTO",
    "drone": "DRONE",
    "cafe_beauty": "CAFE",
    "law": "LEGAL",
    "ai_assistant": "AI",
    "system": "SYSTEM",
}

TASK_MODULE_ALIASES = {
    "agro": "agro_trading",
    "crypto": "crypto_otc",
    "drone": "drone",
    "cafe": "cafe_beauty",
    "beauty": "cafe_beauty",
    "legal": "law",
    "law": "law",
    "ai": "ai_assistant",
    "system": "system",
}

TASK_STATUSES = ("NEW", "IN_PROGRESS", "WAITING", "DONE", "CANCELLED")

TASK_PRIORITIES = ("LOW", "NORMAL", "HIGH", "CRITICAL")

TASK_PRIORITY_ICONS = {
    "LOW": "🔽",
    "NORMAL": "➖",
    "HIGH": "🔼",
    "CRITICAL": "🚨",
}

TASK_STATUS_ICONS = {
    "NEW": "🆕",
    "IN_PROGRESS": "⚙️",
    "WAITING": "⏸",
    "DONE": "✅",
    "CANCELLED": "❌",
}

_TASK_SELECT = """
    SELECT id, title, description, module, project_id, creator_id, assignee_id,
           priority, status, deadline, created_at, updated_at, completed_at,
           calendar_event_id
    FROM tasks
"""


def _normalize_task_module(module: str) -> str:
    if not module:
        return "system"
    key = module.strip().lower()
    if key in TASK_MODULES:
        return key
    return TASK_MODULE_ALIASES.get(key, "system")


def _normalize_task_priority(priority: str) -> str:
    value = (priority or "NORMAL").strip().upper()
    return value if value in TASK_PRIORITIES else "NORMAL"


def _normalize_task_status(status: str) -> str:
    from services.statuses import normalize_status
    value = normalize_status(status)
    if value in TASK_STATUSES:
        return value
    if value == "BLOCKED":
        return "WAITING"
    return "NEW"


def create_task(
    creator_id: int,
    title: str,
    description: str = "",
    module: str = "system",
    project_id: int = None,
    assignee_id: int = None,
    priority: str = "NORMAL",
    deadline: str = None,
    status: str = "NEW",
) -> int:
    module = _normalize_task_module(module)
    priority = _normalize_task_priority(priority)
    status = _normalize_task_status(status)

    cursor.execute(
        """
        INSERT INTO tasks (
            title, description, module, project_id, creator_id, assignee_id,
            priority, status, deadline
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            title.strip(),
            description.strip() if description else None,
            module,
            project_id,
            creator_id,
            assignee_id,
            priority,
            status,
            deadline,
        ),
    )
    conn.commit()
    task_id = cursor.lastrowid

    calendar_event_id = None
    if deadline:
        from services.calendar_service import CalendarService
        calendar_event_id = CalendarService.sync_task_deadline(
            task_id=task_id,
            user_id=creator_id,
            title=title,
            deadline=deadline,
            module=module,
            assignee_id=assignee_id,
        )
        if calendar_event_id:
            cursor.execute(
                "UPDATE tasks SET calendar_event_id = ? WHERE id = ?",
                (calendar_event_id, task_id),
            )
            conn.commit()

    register_module_notification(
        assignee_id or creator_id,
        module if module in TASK_MODULES else "system",
        title=f"Создана задача #{task_id}",
        message=title,
        priority="INFO",
    )
    log_audit(creator_id, "create_task", "tasks", f"{module}|{title}")

    from services.workflow_engine import WorkflowEngine
    WorkflowEngine.execute_workflow(
        "TASK_CREATED",
        creator_id,
        module if module in TASK_MODULES else "system",
        entity_type="task",
        entity_id=task_id,
        payload={"title": title},
    )
    return task_id


def get_task(task_id: int, user_id: int = None):
    cursor.execute(f"{_TASK_SELECT} WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    if not row or user_id is None:
        return row
    from config import OWNER_ID, MANAGER_ID
    creator_id, assignee_id = row[5], row[6]
    if user_id in (OWNER_ID, MANAGER_ID):
        return row
    if user_id in (creator_id, assignee_id):
        return row
    from services.permissions import PermissionService
    if PermissionService.is_crm_operator(user_id):
        return row
    return None


def get_tasks_by_user(
    user_id: int,
    scope: str = "my",
    status: str = None,
    active_only: bool = False,
    overdue_only: bool = False,
    limit: int = 20,
):
    query = f"{_TASK_SELECT} WHERE 1=1"
    params = []

    if scope == "my":
        query += " AND (creator_id = ? OR assignee_id = ?)"
        params.extend([user_id, user_id])
    elif scope == "assigned":
        query += " AND assignee_id = ?"
        params.append(user_id)
    elif scope == "created":
        query += " AND creator_id = ?"
        params.append(user_id)
    elif scope == "all":
        pass
    else:
        query += " AND (creator_id = ? OR assignee_id = ?)"
        params.extend([user_id, user_id])

    if status:
        query += " AND status = ?"
        params.append(_normalize_task_status(status))
    if active_only:
        query += " AND status IN ('NEW', 'IN_PROGRESS', 'WAITING')"
    if overdue_only:
        query += (
            " AND deadline IS NOT NULL AND deadline < datetime('now')"
            " AND status NOT IN ('DONE', 'CANCELLED')"
        )

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def get_tasks_by_module(
    module: str,
    user_id: int = None,
    limit: int = 20,
):
    module = _normalize_task_module(module)
    query = f"{_TASK_SELECT} WHERE module = ?"
    params = [module]
    if user_id is not None:
        query += " AND (creator_id = ? OR assignee_id = ?)"
        params.extend([user_id, user_id])
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def update_task_status(task_id: int, user_id: int, status: str) -> bool:
    status = _normalize_task_status(status)
    if status not in TASK_STATUSES:
        return False

    completed_at = "CURRENT_TIMESTAMP" if status == "DONE" else "NULL"
    cursor.execute(
        f"""
        UPDATE tasks
        SET status = ?, updated_at = CURRENT_TIMESTAMP,
            completed_at = {completed_at}
        WHERE id = ? AND (creator_id = ? OR assignee_id = ?)
        """,
        (status, task_id, user_id, user_id),
    )
    conn.commit()
    if cursor.rowcount > 0:
        register_module_notification(
            user_id,
            "system",
            title=f"Задача #{task_id}: {status}",
            priority="INFO",
        )
        if status == "DONE":
            from services.workflow_engine import WorkflowEngine
            WorkflowEngine.execute_workflow(
                "TASK_COMPLETED",
                user_id,
                "system",
                entity_type="task",
                entity_id=task_id,
            )
        return True
    return False


def assign_task(task_id: int, user_id: int, assignee_id: int) -> bool:
    cursor.execute(
        """
        UPDATE tasks
        SET assignee_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND (creator_id = ? OR assignee_id = ?)
        """,
        (assignee_id, task_id, user_id, user_id),
    )
    conn.commit()
    if cursor.rowcount > 0:
        register_module_notification(
            assignee_id,
            "system",
            title=f"Вам назначена задача #{task_id}",
            priority="INFO",
        )
        return True
    return False


def update_task_deadline(task_id: int, user_id: int, deadline: str) -> bool:
    task = get_task(task_id, user_id)
    if not task:
        return False

    from services.calendar_service import CalendarService
    event_id = CalendarService.sync_task_deadline(
        task_id=task_id,
        user_id=user_id,
        title=task[1],
        deadline=deadline,
        module=task[3],
        assignee_id=task[6],
        existing_event_id=task[13],
    )
    cursor.execute(
        """
        UPDATE tasks
        SET deadline = ?, calendar_event_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ? AND (creator_id = ? OR assignee_id = ?)
        """,
        (deadline, event_id, task_id, user_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def update_task_fields(task_id: int, user_id: int, **fields) -> bool:
    task = get_task(task_id, user_id)
    if not task:
        return False
    allowed = {"title", "description", "priority", "module"}
    parts = []
    params = []
    for key, value in fields.items():
        if key not in allowed:
            continue
        if key == "module":
            value = _normalize_task_module(value)
        if key == "priority":
            value = _normalize_task_priority(value)
        parts.append(f"{key} = ?")
        params.append(value)
    if not parts:
        return False
    parts.append("updated_at = CURRENT_TIMESTAMP")
    params.extend([task_id, user_id, user_id])
    cursor.execute(
        f"UPDATE tasks SET {', '.join(parts)} WHERE id = ? AND (creator_id = ? OR assignee_id = ?)",
        params,
    )
    conn.commit()
    return cursor.rowcount > 0


def delete_task(task_id: int, user_id: int) -> bool:
    task = get_task(task_id, user_id)
    if not task:
        return False
    from services.permissions import PermissionService
    if not PermissionService.can_delete_entity(
        user_id, "task", task_id, owner_id=task[5],
    ):
        return False
    if task[13]:
        from services.calendar_service import CalendarService
        CalendarService.remove_task_event(task[13])
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    log_audit(user_id, "delete_task", "tasks", str(task_id))
    return cursor.rowcount > 0


def format_task_card(task_row) -> str:
    if not task_row:
        return "Задача не найдена."
    (
        tid, title, description, module, project_id, creator_id, assignee_id,
        priority, status, deadline, created_at, updated_at, completed_at,
        calendar_event_id,
    ) = task_row
    mod_label = TASK_MODULES.get(module, module)
    p_icon = TASK_PRIORITY_ICONS.get(priority, "➖")
    s_icon = TASK_STATUS_ICONS.get(status, "🆕")
    return (
        f"{s_icon} Задача #{tid}\n\n"
        f"📌 {title}\n"
        f"📝 {description or '—'}\n"
        f"🏷 Модуль: {mod_label}\n"
        f"📁 Проект: #{project_id or '—'}\n"
        f"{p_icon} Приоритет: {priority}\n"
        f"📊 Статус: {status}\n"
        f"👤 Создатель: {creator_id}\n"
        f"👥 Исполнитель: {assignee_id or '—'}\n"
        f"📅 Срок: {deadline or '—'}\n"
        f"📅 Календарь: #{calendar_event_id or '—'}\n"
        f"🕒 Создана: {created_at}\n"
        f"🔄 Обновлена: {updated_at}\n"
        f"✅ Завершена: {completed_at or '—'}"
    )


def format_tasks_list_text(
    user_id: int,
    scope: str = "my",
    status: str = None,
    active_only: bool = False,
    overdue_only: bool = False,
    limit: int = 10,
) -> str:
    rows = get_tasks_by_user(
        user_id,
        scope=scope,
        status=status,
        active_only=active_only,
        overdue_only=overdue_only,
        limit=limit,
    )
    if not rows:
        return "Задач нет."

    lines = ["📋 Задачи:\n"]
    for row in rows:
        tid, title = row[0], row[1]
        module, priority, nstatus, deadline = row[3], row[7], row[8], row[9]
        p_icon = TASK_PRIORITY_ICONS.get(priority, "➖")
        s_icon = TASK_STATUS_ICONS.get(nstatus, "🆕")
        mod_label = TASK_MODULES.get(module, module)
        lines.append(
            f"{s_icon} #{tid} · {title}\n"
            f"   {p_icon} {priority} · {mod_label} · {nstatus} · 📅 {deadline or '—'}"
        )
    return "\n".join(lines)


def parse_task_create_text(text: str) -> dict | None:
    import re
    lower = text.lower().strip()
    if not any(k in lower for k in ("новая задача", "создай задачу", "create task")):
        return None
    title = _extract_labeled_field(text, ("название", "title"))
    description = _extract_labeled_field(text, ("описание", "description"))
    module = _extract_labeled_field(text, ("модуль", "module")) or "system"
    priority = _extract_labeled_field(text, ("приоритет", "priority")) or "NORMAL"
    deadline = _extract_labeled_field(text, ("срок", "deadline", "дедлайн"))
    if not title:
        inline = re.sub(
            r"(?i)(новая задача|создай задачу|create task)\s*[:：]?\s*",
            "",
            text.strip(),
        )
        if inline and "\n" not in inline:
            title = inline.strip()
    if not title:
        return {"title": "", "description": description, "module": module,
                "priority": priority, "deadline": deadline}
    return {
        "title": title,
        "description": description,
        "module": module,
        "priority": priority,
        "deadline": deadline or None,
    }


# --- Legacy wrappers (system_tasks / ai_tasks compatibility) ---

def create_system_task(
    creator_id: int,
    title: str,
    description: str = "",
    module: str = "ai_assistant",
    priority: str = "NORMAL",
    assigned_user_id: int = None,
    due_date: str = None,
    task_source: str = "SYSTEM",
) -> int:
    _ = task_source
    return create_task(
        creator_id=creator_id,
        title=title,
        description=description,
        module=module,
        assignee_id=assigned_user_id,
        priority=priority,
        deadline=due_date,
    )


def register_module_task(
    creator_id: int,
    module: str,
    title: str,
    description: str = "",
    priority: str = "NORMAL",
    assigned_user_id: int = None,
    due_date: str = None,
) -> int:
    return create_task(
        creator_id=creator_id,
        title=title,
        description=description,
        module=module,
        assignee_id=assigned_user_id,
        priority=priority,
        deadline=due_date,
    )


def get_system_task(task_id: int, user_id: int):
    return get_task(task_id, user_id)


def get_system_tasks(
    user_id: int,
    scope: str = "my",
    status: str = None,
    module: str = None,
    overdue_only: bool = False,
    limit: int = 20,
    task_source: str = None,
):
    _ = task_source
    rows = get_tasks_by_user(
        user_id,
        scope=scope,
        status=status,
        overdue_only=overdue_only,
        limit=limit,
    )
    if module:
        module = _normalize_task_module(module)
        rows = [r for r in rows if r[3] == module]
    return rows


def assign_system_task(task_id: int, user_id: int, assigned_user_id: int) -> bool:
    return assign_task(task_id, user_id, assigned_user_id)


def update_system_task_status(task_id: int, user_id: int, status: str) -> bool:
    return update_task_status(task_id, user_id, status)


def complete_system_task(task_id: int, user_id: int) -> bool:
    return update_task_status(task_id, user_id, "DONE")


def reschedule_system_task(task_id: int, user_id: int, due_date: str) -> bool:
    return update_task_deadline(task_id, user_id, due_date)


def format_system_tasks_text(
    user_id: int,
    scope: str = "my",
    status: str = None,
    overdue_only: bool = False,
    limit: int = 10,
) -> str:
    return format_tasks_list_text(
        user_id,
        scope=scope,
        status=status,
        overdue_only=overdue_only,
        limit=limit,
    )


def format_task_filters_text(user_id: int) -> str:
    # TODO: future implementation — interactive filter UI
    return (
        "⚙ Фильтры задач\n\n"
        f"Модули: {', '.join(TASK_MODULES.values())}\n"
        f"Статусы: {', '.join(TASK_STATUSES)}\n"
        f"Приоритеты: {', '.join(TASK_PRIORITIES)}\n\n"
        "Фильтрация находится в разработке."
    )


def get_tasks_for_report(user_id: int, module: str = None, limit: int = 50):
    # TODO: future implementation — reports module integration
    return get_system_tasks(user_id, scope="all", module=module, limit=limit)


# ==========================================================
# SYSTEM FILES (central hub)
# ==========================================================

FILE_MODULES = {
    "crypto_otc": "Crypto OTC",
    "agro_trading": "Agro Trading",
    "law": "Юриспруденция",
    "drone": "Drone Engineering",
    "cafe_beauty": "Cafe & Beauty",
    "calendar": "Календарь",
    "tasks": "Задачи",
}


def create_system_file(
    uploaded_by: int,
    filename: str,
    original_filename: str,
    module: str = "tasks",
    project_id: int = None,
    task_id: int = None,
    calendar_event_id: int = None,
    request_number: int = None,
    file_size: int = None,
    mime_type: str = None,
    tags: str = None,
    description: str = None,
    version: int = 1,
) -> int:
    # TODO: future implementation — file storage on disk and validation
    if module not in FILE_MODULES:
        module = "tasks"

    cursor.execute(
        """
        INSERT INTO files (
            filename, original_filename, uploaded_by, module,
            project_id, task_id, calendar_event_id, request_number,
            file_size, mime_type, tags, description, version
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            filename.strip(),
            original_filename.strip(),
            uploaded_by,
            module,
            project_id,
            task_id,
            calendar_event_id,
            request_number,
            file_size,
            mime_type,
            tags,
            description,
            version,
        ),
    )
    conn.commit()
    file_id = cursor.lastrowid
    _integrate_file_created(file_id, uploaded_by, original_filename, module, task_id)
    return file_id


def register_module_file(
    uploaded_by: int,
    module: str,
    filename: str,
    original_filename: str,
    project_id: int = None,
    task_id: int = None,
    file_size: int = None,
    mime_type: str = None,
    tags: str = None,
    description: str = None,
    version: int = 1,
) -> int:
    # TODO: future implementation — unified entry point for all system modules
    file_id = create_system_file(
        uploaded_by=uploaded_by,
        filename=filename,
        original_filename=original_filename,
        module=module,
        project_id=project_id,
        task_id=task_id,
        file_size=file_size,
        mime_type=mime_type,
        tags=tags,
        description=description,
        version=version,
    )
    if file_id:
        log_audit(uploaded_by, "create_file", "files", f"{module}|{original_filename}")
    return file_id


def _integrate_file_created(
    file_id: int,
    user_id: int,
    original_filename: str,
    module: str,
    task_id: int = None,
):
    # TODO: future implementation — deep calendar/tasks/notifications integration
    register_module_notification(
        user_id,
        module,
        title=f"Загружен файл #{file_id}",
        message=original_filename,
        priority="INFO",
    )
    if task_id:
        register_module_notification(
            user_id,
            "tasks",
            title=f"Вложение к задаче #{task_id}",
            message=original_filename,
            priority="INFO",
        )
    from services.workflow_engine import WorkflowEngine
    WorkflowEngine.execute_workflow(
        "FILE_UPLOADED",
        user_id,
        module,
        entity_type="file",
        entity_id=file_id,
        payload={"filename": original_filename},
    )


def get_system_file(file_id: int, user_id: int):
    # TODO: future implementation — team visibility and role-based access
    cursor.execute(
        """
        SELECT id, filename, original_filename, uploaded_by, module,
               project_id, task_id, created_at, file_size, mime_type,
               tags, description, version
        FROM files
        WHERE id = ? AND uploaded_by = ?
        """,
        (file_id, user_id),
    )
    return cursor.fetchone()


def get_system_files(
    user_id: int,
    scope: str = "recent",
    module: str = None,
    task_id: int = None,
    search_query: str = None,
    tag: str = None,
    limit: int = 20,
):
    # TODO: future implementation — advanced filters, sharing and favorites
    query = """
        SELECT id, filename, original_filename, uploaded_by, module,
               project_id, task_id, created_at, file_size, mime_type,
               tags, description, version
        FROM files
        WHERE 1=1
    """
    params = []

    if scope == "incoming":
        query += " AND uploaded_by != ?"
        params.append(user_id)
    elif scope == "outgoing":
        query += " AND uploaded_by = ?"
        params.append(user_id)
    elif scope == "favorite":
        query += " AND (tags LIKE '%favorite%' OR tags LIKE '%⭐%')"
    elif scope == "task":
        query += " AND task_id IS NOT NULL"
    elif scope == "recent":
        query += " AND uploaded_by = ?"
        params.append(user_id)
    else:
        query += " AND uploaded_by = ?"
        params.append(user_id)

    if module:
        query += " AND module = ?"
        params.append(module)
    if task_id is not None:
        query += " AND task_id = ?"
        params.append(task_id)
    if search_query:
        query += (
            " AND (original_filename LIKE ? OR description LIKE ? OR tags LIKE ?)"
        )
        pattern = f"%{search_query}%"
        params.extend([pattern, pattern, pattern])
    if tag:
        query += " AND tags LIKE ?"
        params.append(f"%{tag}%")

    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)

    cursor.execute(query, params)
    return cursor.fetchall()


def format_system_files_text(
    user_id: int,
    scope: str = "recent",
    module: str = None,
    task_id: int = None,
    search_query: str = None,
    tag: str = None,
    limit: int = 10,
) -> str:
    # TODO: future implementation — rich file cards and preview
    rows = get_system_files(
        user_id,
        scope=scope,
        module=module,
        task_id=task_id,
        search_query=search_query,
        tag=tag,
        limit=limit,
    )
    if not rows:
        return "Файлов нет."

    lines = ["📁 Файлы:\n"]
    for row in rows:
        (
            fid, filename, original_filename, uploaded_by, mod,
            project_id, tid, created_at, file_size, mime_type,
            tags, description, version,
        ) = row
        mod_label = FILE_MODULES.get(mod, mod or "—")
        size_label = f"{file_size} B" if file_size else "—"
        lines.append(
            f"📄 #{fid} · {original_filename}\n"
            f"   🗂 {mod_label} · v{version} · {mime_type or '—'}\n"
            f"   👤 {uploaded_by} · 📦 {size_label}\n"
            f"   🏷 {tags or '—'} · 🕒 {created_at}"
        )
        if tid:
            lines.append(f"   📎 задача #{tid} · проект #{project_id or '—'}")
        if description:
            lines.append(f"   📝 {description}")
    return "\n".join(lines)


def format_file_modules_text(user_id: int) -> str:
    # TODO: future implementation — interactive module browser
    lines = ["🗂 Файлы по модулям:\n"]
    for key, label in FILE_MODULES.items():
        count = len(get_system_files(user_id, scope="all", module=key, limit=100))
        lines.append(f"• {label} ({key}): {count} файл(ов)")
    lines.append("\nПросмотр по модулю находится в разработке.")
    return "\n".join(lines)


def format_file_search_text(user_id: int, query: str = None) -> str:
    # TODO: future implementation — full-text search UI
    if not query:
        return (
            "🔍 Поиск файлов\n\n"
            "Поиск по имени, описанию и тегам.\n"
            "Интерактивный поиск находится в разработке."
        )
    return format_system_files_text(user_id, scope="all", search_query=query)


def format_file_tags_text(user_id: int) -> str:
    # TODO: future implementation — tag management UI
    rows = get_system_files(user_id, scope="all", limit=100)
    tags_set = set()
    for row in rows:
        tags = row[10]
        if tags:
            for t in tags.split(","):
                t = t.strip()
                if t:
                    tags_set.add(t)
    if not tags_set:
        return "🏷 Теги\n\nТегов пока нет."
    tag_list = ", ".join(sorted(tags_set))
    return f"🏷 Теги\n\n{tag_list}\n\nФильтрация по тегам находится в разработке."


def get_files_for_report(user_id: int, module: str = None, limit: int = 50):
    # TODO: future implementation — reports module integration
    return get_system_files(user_id, scope="all", module=module, limit=limit)


# ==========================================================
# GLOBAL SEARCH (central hub)
# ==========================================================

SEARCH_DOMAINS = {
    "users": "Пользователи",
    "calendar": "Календарь",
    "tasks": "Задачи",
    "files": "Файлы",
    "deals": "Сделки",
    "projects": "Проекты",
    "contracts": "Договоры",
    "reports": "Отчеты",
}

SEARCH_SCOPES = {
    "all": "Поиск по всему",
    "users": "Пользователи",
    "calendar": "Календарь",
    "tasks": "Задачи",
    "files": "Файлы",
    "crypto_otc": "Crypto OTC",
    "agro_trading": "Agro Trading",
    "law": "Юриспруденция",
    "drone": "Drone Engineering",
    "cafe_beauty": "Cafe & Beauty",
}


def global_search(
    user_id: int,
    query: str = None,
    domain: str = "all",
    module: str = None,
    limit: int = 20,
) -> dict:
    # TODO: future implementation — unified full-text search across all modules
    results = {}
    if domain in ("all", "users"):
        results["users"] = search_users(user_id, query, limit)
    if domain in ("all", "calendar"):
        results["calendar"] = search_calendar_events(user_id, query, limit)
    if domain in ("all", "tasks"):
        results["tasks"] = search_tasks(user_id, query, limit)
    if domain in ("all", "files"):
        results["files"] = search_files(user_id, query, limit)
    if domain in ("all", "deals"):
        results["deals"] = search_deals(user_id, query, module, limit)
    if domain in ("all", "projects"):
        results["projects"] = search_projects(user_id, query, module, limit)
    if domain in ("all", "contracts"):
        results["contracts"] = search_contracts(user_id, query, module, limit)
    if domain in ("all", "reports"):
        results["reports"] = search_reports(user_id, query, limit)
    return results


def search_users(user_id: int, query: str = None, limit: int = 20):
    if not query:
        return []
    cursor.execute(
        """
        SELECT u.telegram_id, u.full_name, u.username,
               GROUP_CONCAT(r.role_name, ', ')
        FROM users u
        LEFT JOIN user_roles ur ON ur.user_id = u.telegram_id
        LEFT JOIN roles r ON r.id = ur.role_id
        WHERE u.full_name LIKE ? OR u.username LIKE ?
           OR CAST(u.telegram_id AS TEXT) LIKE ?
        GROUP BY u.telegram_id
        ORDER BY u.id DESC
        LIMIT ?
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%", limit),
    )
    return cursor.fetchall()


def search_calendar_events(user_id: int, query: str = None, limit: int = 20):
    if not query:
        return []
    cursor.execute(
        """
        SELECT id, title, start_time, module, status
        FROM calendar_events
        WHERE (creator_id = ? OR owner_id = ? OR responsible_user = ?)
          AND (title LIKE ? OR description LIKE ? OR module LIKE ?)
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, user_id, user_id, f"%{query}%", f"%{query}%", f"%{query}%", limit),
    )
    return cursor.fetchall()


def search_tasks(user_id: int, query: str = None, limit: int = 20):
    if not query:
        return []
    cursor.execute(
        f"""
        {_TASK_SELECT}
        WHERE (title LIKE ? OR description LIKE ? OR CAST(id AS TEXT) LIKE ?)
        ORDER BY id DESC LIMIT ?
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%", limit),
    )
    return cursor.fetchall()


def search_files(user_id: int, query: str = None, limit: int = 20):
    # TODO: future implementation — full files search integration
    if not query:
        return []
    return get_system_files(user_id, scope="all", search_query=query, limit=limit)


def search_deals(
    user_id: int,
    query: str = None,
    module: str = None,
    limit: int = 20,
):
    # TODO: future implementation — CRM deals search (Crypto OTC, Agro Trading)
    return []


def search_projects(
    user_id: int,
    query: str = None,
    module: str = None,
    limit: int = 20,
):
    if not query:
        return []
    cursor.execute(
        """
        SELECT id, title, category, status, created_at
        FROM ai_projects
        WHERE user_id = ? AND status != 'deleted'
          AND (title LIKE ? OR description LIKE ? OR category LIKE ?)
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, f"%{query}%", f"%{query}%", f"%{query}%", limit),
    )
    return cursor.fetchall()


def search_contracts(
    user_id: int,
    query: str = None,
    module: str = None,
    limit: int = 20,
):
    # TODO: future implementation — contracts search (Юриспруденция and others)
    return []


def search_reports(user_id: int, query: str = None, limit: int = 20):
    # TODO: future implementation — reports metadata search
    return []


def format_search_hub_text(user_id: int) -> str:
    # TODO: future implementation — search dashboard with recent queries
    domains = ", ".join(SEARCH_DOMAINS.values())
    return (
        "🔎 Глобальный поиск\n\n"
        f"Области поиска: {domains}\n\n"
        "Единый интерфейс поиска по всей системе.\n"
        "Раздел находится в разработке."
    )


def format_global_search_text(
    user_id: int,
    scope: str = "all",
    query: str = None,
) -> str:
    # TODO: future implementation — formatted unified search results
    scope_label = SEARCH_SCOPES.get(scope, scope)
    domains_line = ", ".join(SEARCH_DOMAINS.values())

    if scope == "all":
        header = "🔍 Поиск по всему"
        body = (
            f"Области: {domains_line}\n\n"
            "Поиск по пользователям, календарю, задачам, файлам, "
            "сделкам, проектам, договорам и отчетам.\n"
            "Интерактивный поиск находится в разработке."
        )
    elif scope in {"users", "calendar", "tasks", "files"}:
        header = scope_label
        domain_key = scope
        body = (
            f"Поиск: {SEARCH_DOMAINS.get(domain_key, scope_label)}\n\n"
            "Введите запрос для поиска.\n"
            "Функция находится в разработке."
        )
    else:
        header = scope_label
        body = (
            f"Модуль: {scope_label}\n\n"
            "Поиск по сделкам, проектам и договорам модуля.\n"
            "Функция находится в разработке."
        )

    if query:
        results = global_search(
            user_id,
            query=query,
            domain=scope if scope in SEARCH_DOMAINS else "all",
            module=scope if scope not in SEARCH_DOMAINS and scope != "all" else None,
        )
        total = sum(len(v) for v in results.values())
        body += f"\n\nЗапрос: «{query}»\nНайдено: {total} результат(ов)."

    return f"{header}\n\n{body}"


def get_search_scope_for_button(button: str) -> str:
    # TODO: future implementation — dynamic scope mapping from UI
    mapping = {
        "🔍 Поиск по всему": "all",
        "👥 Пользователи": "users",
        "📅 Календарь": "calendar",
        "✅ Задачи": "tasks",
        "📁 Файлы": "files",
        "💰 Crypto OTC": "crypto_otc",
        "🌾 Agro Trading": "agro_trading",
        "⚖️ Юриспруденция": "law",
        "🚁 Drone Engineering": "drone",
        "☕ Cafe & Beauty": "cafe_beauty",
    }
    return mapping.get(button, "all")


# ==========================================================
# WORKFLOW ENGINE (central hub)
# ==========================================================

WORKFLOW_MODULES = {
    "agro_trading": "Agro Trading",
    "crypto_otc": "Crypto OTC",
    "drone": "Drone Engineering",
    "law": "Юриспруденция",
    "cafe_beauty": "Cafe & Beauty",
}

WORKFLOW_STATUSES = ("ACTIVE", "PAUSED", "COMPLETED", "CANCELLED")

WORKFLOW_STATUS_ICONS = {
    "ACTIVE": "▶️",
    "PAUSED": "⏸",
    "COMPLETED": "✅",
    "CANCELLED": "❌",
}

WORKFLOW_ACTION_TYPES = {
    "create_task": "Создать задачу",
    "create_calendar_event": "Создать событие календаря",
    "send_notification": "Отправить уведомление",
    "create_document": "Создать документ",
    "assign_user": "Назначить пользователя",
    "update_status": "Обновить статус",
}


def create_workflow_process(
    created_by: int,
    name: str,
    module: str = "agro_trading",
    trigger: str = None,
    status: str = "ACTIVE",
) -> int:
    # TODO: future implementation — validation and module-specific triggers
    if module not in WORKFLOW_MODULES:
        module = "agro_trading"
    if status not in WORKFLOW_STATUSES:
        status = "ACTIVE"

    cursor.execute(
        """
        INSERT INTO workflow_processes (
            name, module, trigger, status, created_by
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (name.strip(), module, trigger, status, created_by),
    )
    conn.commit()
    process_id = cursor.lastrowid
    register_module_notification(
        created_by,
        module,
        title=f"Процесс #{process_id} создан",
        message=name,
        priority="INFO",
    )
    return process_id


def register_module_workflow(
    created_by: int,
    module: str,
    name: str,
    trigger: str = None,
) -> int:
    # TODO: future implementation — unified entry point for all modules
    process_id = create_workflow_process(
        created_by=created_by,
        name=name,
        module=module,
        trigger=trigger,
    )
    if process_id:
        log_audit(created_by, "create_workflow", "workflow", f"{module}|{name}")
    return process_id


def get_workflow_process(process_id: int, user_id: int):
    # TODO: future implementation — role-based process visibility
    cursor.execute(
        """
        SELECT id, name, module, trigger, status, created_at, completed_at
        FROM workflow_processes
        WHERE id = ? AND (created_by = ? OR created_by IS NULL)
        """,
        (process_id, user_id),
    )
    return cursor.fetchone()


def get_workflow_processes(
    user_id: int,
    status: str = None,
    module: str = None,
    limit: int = 20,
):
    # TODO: future implementation — advanced filters and team processes
    query = """
        SELECT id, name, module, trigger, status, created_at, completed_at
        FROM workflow_processes
        WHERE created_by = ?
    """
    params = [user_id]
    if status:
        query += " AND status = ?"
        params.append(status)
    if module:
        query += " AND module = ?"
        params.append(module)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def update_workflow_status(
    process_id: int,
    user_id: int,
    status: str,
) -> bool:
    # TODO: future implementation — status workflow validation
    if status not in WORKFLOW_STATUSES:
        return False

    if status == "COMPLETED":
        cursor.execute(
            """
            UPDATE workflow_processes
            SET status = ?, completed_at = CURRENT_TIMESTAMP
            WHERE id = ? AND created_by = ?
            """,
            (status, process_id, user_id),
        )
    else:
        cursor.execute(
            """
            UPDATE workflow_processes
            SET status = ?, completed_at = NULL
            WHERE id = ? AND created_by = ?
            """,
            (status, process_id, user_id),
        )
    conn.commit()
    return cursor.rowcount > 0


def pause_workflow_process(process_id: int, user_id: int) -> bool:
    # TODO: future implementation — pause hooks and notifications
    return update_workflow_status(process_id, user_id, "PAUSED")


def complete_workflow_process(process_id: int, user_id: int) -> bool:
    # TODO: future implementation — completion hooks and audit
    ok = update_workflow_status(process_id, user_id, "COMPLETED")
    if ok:
        register_module_notification(
            user_id,
            "ai_assistant",
            title=f"Процесс #{process_id} завершен",
            priority="INFO",
        )
    return ok


def create_workflow_template(
    created_by: int,
    name: str,
    module: str = "agro_trading",
    trigger: str = None,
    actions_json: str = None,
) -> int:
    # TODO: future implementation — template editor and action builder
    if module not in WORKFLOW_MODULES:
        module = "agro_trading"
    cursor.execute(
        """
        INSERT INTO workflow_templates (
            name, module, trigger, actions_json, created_by
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (name.strip(), module, trigger, actions_json, created_by),
    )
    conn.commit()
    return cursor.lastrowid


def get_workflow_templates(
    user_id: int,
    module: str = None,
    limit: int = 20,
):
    # TODO: future implementation — shared templates across modules
    query = """
        SELECT id, name, module, trigger, actions_json, created_at
        FROM workflow_templates
        WHERE created_by = ?
    """
    params = [user_id]
    if module:
        query += " AND module = ?"
        params.append(module)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    return cursor.fetchall()


def execute_workflow_action(
    user_id: int,
    action_type: str,
    module: str,
    payload: dict = None,
) -> bool:
    # TODO: future implementation — action pipeline and rollback
    if action_type not in WORKFLOW_ACTION_TYPES:
        return False
    payload = payload or {}
    return _integrate_workflow_action(user_id, action_type, module, payload)


def _integrate_workflow_action(
    user_id: int,
    action_type: str,
    module: str,
    payload: dict,
) -> bool:
    # TODO: future implementation — deep integration with system modules
    if action_type == "create_task":
        create_system_task(
            creator_id=user_id,
            title=payload.get("title", "Workflow task"),
            description=payload.get("description", ""),
            module=module if module in TASK_MODULES else "ai_assistant",
        )
        return True
    if action_type == "create_calendar_event":
        register_calendar_event(
            user_id,
            module if module in CALENDAR_SOURCE_MODULES else "calendar",
            title=payload.get("title", "Workflow event"),
            start_datetime=payload.get("start_datetime"),
            description=payload.get("description", "workflow_action"),
        )
        return True
    if action_type == "send_notification":
        register_module_notification(
            user_id,
            module,
            title=payload.get("title", "Workflow notification"),
            message=payload.get("message", ""),
            priority=payload.get("priority", "INFO"),
        )
        return True
    if action_type == "create_document":
        register_module_file(
            uploaded_by=user_id,
            module=module if module in FILE_MODULES else "tasks",
            filename=payload.get("filename", "workflow/doc"),
            original_filename=payload.get("original_filename", "document"),
            description=payload.get("description", "workflow document"),
        )
        return True
    if action_type == "assign_user":
        task_id = payload.get("task_id")
        assigned_user_id = payload.get("assigned_user_id")
        if task_id and assigned_user_id:
            return assign_system_task(task_id, user_id, assigned_user_id)
        return False
    if action_type == "update_status":
        process_id = payload.get("process_id")
        status = payload.get("status")
        if process_id and status:
            return update_workflow_status(process_id, user_id, status)
        return False
    return False


def format_workflow_processes_text(
    user_id: int,
    status: str = None,
    module: str = None,
    limit: int = 10,
) -> str:
    # TODO: future implementation — rich process cards
    rows = get_workflow_processes(user_id, status=status, module=module, limit=limit)
    if not rows:
        return "Процессов нет."

    lines = ["⚙️ Бизнес-процессы:\n"]
    for row in rows:
        pid, name, mod, trigger, nstatus, created_at, completed_at = row
        icon = WORKFLOW_STATUS_ICONS.get(nstatus, "▶️")
        mod_label = WORKFLOW_MODULES.get(mod, mod or "—")
        lines.append(
            f"{icon} #{pid} · {name}\n"
            f"   🗂 {mod_label} · {nstatus}\n"
            f"   ⚡ trigger: {trigger or '—'}\n"
            f"   🕒 {created_at} · ✅ {completed_at or '—'}"
        )
    return "\n".join(lines)


def format_workflow_templates_text(user_id: int, limit: int = 10) -> str:
    # TODO: future implementation — template preview with actions
    rows = get_workflow_templates(user_id, limit=limit)
    actions = ", ".join(WORKFLOW_ACTION_TYPES.values())
    if not rows:
        return (
            f"📋 Шаблоны процессов\n\n"
            f"Доступные действия: {actions}\n\n"
            "Шаблонов нет."
        )
    lines = [f"📋 Шаблоны процессов\n\nДействия: {actions}\n"]
    for row in rows:
        tid, name, mod, trigger, actions_json, created_at = row
        mod_label = WORKFLOW_MODULES.get(mod, mod or "—")
        lines.append(
            f"#{tid} · {name}\n"
            f"   🗂 {mod_label} · ⚡ {trigger or '—'}\n"
            f"   🕒 {created_at}"
        )
        if actions_json:
            lines.append(f"   ⚙ {actions_json}")
    return "\n".join(lines)


def format_workflow_stats_text(user_id: int) -> str:
    # TODO: future implementation — charts and module breakdown
    active = len(get_workflow_processes(user_id, status="ACTIVE", limit=100))
    paused = len(get_workflow_processes(user_id, status="PAUSED", limit=100))
    completed = len(get_workflow_processes(user_id, status="COMPLETED", limit=100))
    templates = len(get_workflow_templates(user_id, limit=100))
    modules = ", ".join(WORKFLOW_MODULES.values())
    return (
        "📊 Статистика бизнес-процессов\n\n"
        f"▶️ Активные: {active}\n"
        f"⏸ Приостановленные: {paused}\n"
        f"✅ Завершенные: {completed}\n"
        f"📋 Шаблоны: {templates}\n\n"
        f"Модули: {modules}\n"
        f"Действия: {', '.join(WORKFLOW_ACTION_TYPES.values())}\n\n"
        "Детальная аналитика находится в разработке."
    )


# ==========================================================
# AI AGENTS (multi-agent layer)
# ==========================================================

AGENT_MODULE_ACCESS = {
    "AI_GENERAL": None,
    "AI_DRONE": "drone",
    "AI_LEGAL": "law",
    "AI_AGRO": "agro_trading",
    "AI_CRYPTO": "crypto_otc",
    "AI_BEAUTY": "cafe_beauty",
    "AI_FINANCE": "reports",
}


def get_ai_agent_settings(user_id: int, agent_code: str) -> dict:
    cursor.execute(
        """
        SELECT model, tone, language, context_depth
        FROM ai_agent_settings
        WHERE user_id = ? AND agent_code = ?
        """,
        (user_id, agent_code),
    )
    row = cursor.fetchone()
    if row:
        return {
            "model": row[0],
            "tone": row[1],
            "language": row[2],
            "context_depth": row[3],
        }
    return get_ai_settings(user_id)


def save_ai_agent_settings(user_id: int, agent_code: str, **fields) -> None:
    current = get_ai_agent_settings(user_id, agent_code)
    current.update({k: v for k, v in fields.items() if v is not None})
    cursor.execute(
        """
        INSERT INTO ai_agent_settings (user_id, agent_code, model, tone, language, context_depth)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, agent_code) DO UPDATE SET
            model = excluded.model,
            tone = excluded.tone,
            language = excluded.language,
            context_depth = excluded.context_depth,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            user_id,
            agent_code,
            current["model"],
            current["tone"],
            current["language"],
            current["context_depth"],
        ),
    )
    conn.commit()


def get_ai_agent_memory(user_id: int, agent_code: str) -> dict:
    cursor.execute(
        """
        SELECT memory_key, memory_value
        FROM ai_agent_memory
        WHERE user_id = ? AND agent_code = ?
        """,
        (user_id, agent_code),
    )
    return {row[0]: row[1] for row in cursor.fetchall() if row[1]}


def save_ai_agent_memory_fields(user_id: int, agent_code: str, fields: dict) -> None:
    from openrouter import MEMORY_KEYS
    for key, value in fields.items():
        if key not in MEMORY_KEYS or not value:
            continue
        cursor.execute(
            """
            INSERT INTO ai_agent_memory (user_id, agent_code, memory_key, memory_value)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, agent_code, memory_key) DO UPDATE SET
                memory_value = excluded.memory_value,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, agent_code, key, str(value).strip()),
        )
    conn.commit()


def format_ai_agent_memory_context(user_id: int, agent_code: str) -> str:
    profile = get_ai_agent_memory(user_id, agent_code)
    if not profile:
        return ""
    lines = [f"Память агента {agent_code}:"]
    for key, value in profile.items():
        label = MEMORY_FIELDS.get(key, key)
        lines.append(f"• {label}: {value}")
    return "\n".join(lines)


def get_ai_agent(code: str):
    cursor.execute(
        "SELECT id, code, name, description, model, prompt, active FROM ai_agents WHERE code = ?",
        (code,),
    )
    return cursor.fetchone()


def get_ai_agents(active_only: bool = True):
    if active_only:
        cursor.execute(
            "SELECT id, code, name, description, model, prompt, active FROM ai_agents WHERE active = 1 ORDER BY id"
        )
    else:
        cursor.execute(
            "SELECT id, code, name, description, model, prompt, active FROM ai_agents ORDER BY id"
        )
    return cursor.fetchall()


def add_ai_dialog_message(user_id: int, agent_code: str, role: str, content: str) -> int:
    cursor.execute(
        """
        INSERT INTO ai_dialogs (user_id, agent_code, role, content)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, agent_code, role, content),
    )
    conn.commit()
    return cursor.lastrowid


def get_ai_dialog_history(user_id: int, agent_code: str, limit: int = 20) -> list[dict]:
    cursor.execute(
        """
        SELECT role, content, created_at FROM ai_dialogs
        WHERE user_id = ? AND agent_code = ?
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, agent_code, limit),
    )
    rows = cursor.fetchall()
    rows.reverse()
    return [{"role": r, "content": c, "created_at": t} for r, c, t in rows]


def get_ai_dialog_history_for_llm(user_id: int, agent_code: str, limit: int = 20) -> list[dict]:
    history = get_ai_dialog_history(user_id, agent_code, limit)
    return [{"role": item["role"], "content": item["content"]} for item in history]


def format_ai_agents_text(user_id: int) -> str:
    from services.permissions import PermissionService
    agents = get_ai_agents()
    lines = ["🤖 AI Агенты:\n"]
    visible = 0
    for _id, code, name, desc, model, _prompt, active in agents:
        module = AGENT_MODULE_ACCESS.get(code)
        if module and not PermissionService.can_access_module(user_id, module):
            continue
        if code == "AI_GENERAL" and not PermissionService.has_permission(user_id, "ai_access"):
            from config import OWNER_ID, MANAGER_ID
            if user_id not in (OWNER_ID, MANAGER_ID):
                continue
        visible += 1
        lines.append(f"• {name} ({code})\n  {desc or '—'}\n  model: {model or 'default'}")
    if visible == 0:
        lines.append("Нет доступных агентов для вашей роли.")
    return "\n\n".join(lines)


def mark_all_notifications_read(user_id: int) -> int:
    cursor.execute(
        """
        UPDATE notifications
        SET status = 'READ', is_read = 1, read_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND status = 'NEW'
        """,
        (user_id,),
    )
    conn.commit()
    return cursor.rowcount


def archive_read_notifications(user_id: int) -> int:
    cursor.execute(
        """
        UPDATE notifications
        SET status = 'ARCHIVED', is_read = 1, archived_at = CURRENT_TIMESTAMP
        WHERE user_id = ? AND status = 'READ'
        """,
        (user_id,),
    )
    conn.commit()
    return cursor.rowcount


# ==========================================================
# WORKFLOW RULES ENGINE (DB)
# ==========================================================

WORKFLOW_TRIGGER_CODES = (
    "AGRO_REQUEST_CREATED",
    "TASK_CREATED",
    "TASK_COMPLETED",
    "EVENT_CREATED",
    "USER_CREATED",
    "FILE_UPLOADED",
    "PROJECT_CREATED",
)


def register_workflow_rule(
    trigger_code: str,
    action_type: str,
    module: str = "system",
    action_payload: str = None,
) -> int:
    cursor.execute(
        """
        INSERT INTO workflow_rules (trigger_code, module, action_type, action_payload, active)
        VALUES (?, ?, ?, ?, 1)
        """,
        (trigger_code, module, action_type, action_payload),
    )
    conn.commit()
    return cursor.lastrowid


def get_workflow_rules(trigger_code: str = None, active_only: bool = True):
    query = "SELECT id, trigger_code, module, action_type, action_payload, active FROM workflow_rules WHERE 1=1"
    params = []
    if trigger_code:
        query += " AND trigger_code = ?"
        params.append(trigger_code)
    if active_only:
        query += " AND active = 1"
    cursor.execute(query, params)
    return cursor.fetchall()


def log_workflow_execution(
    trigger_code: str,
    user_id: int,
    module: str,
    action_type: str,
    entity_type: str = None,
    entity_id: int = None,
    status: str = "OK",
    details: str = None,
) -> int:
    cursor.execute(
        """
        INSERT INTO workflow_logs (
            trigger_code, module, user_id, entity_type, entity_id,
            action_type, status, details
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (trigger_code, module, user_id, entity_type, entity_id, action_type, status, details),
    )
    conn.commit()
    return cursor.lastrowid


# ==========================================================
# DASHBOARD / ANALYTICS
# ==========================================================

def get_dashboard_kpi(user_id: int) -> dict:
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status NOT IN ('DONE', 'CANCELLED')")
    active_requests = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM tasks WHERE status NOT IN ('DONE', 'CANCELLED') AND (creator_id = ? OR assignee_id = ?)",
        (user_id, user_id),
    )
    active_tasks = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM notifications WHERE user_id = ? AND (is_read = 0 OR status = 'NEW')",
        (user_id,),
    )
    unread_notifications = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM ai_projects WHERE user_id = ? AND status != 'deleted'",
        (user_id,),
    )
    active_projects = cursor.fetchone()[0]
    return {
        "active_requests": active_requests,
        "active_tasks": active_tasks,
        "unread_notifications": unread_notifications,
        "active_projects": active_projects,
    }


def format_dashboard_text(user_id: int) -> str:
    kpi = get_dashboard_kpi(user_id)
    return (
        "📊 Аналитика / KPI\n\n"
        f"📋 Активные заявки CRM: {kpi['active_requests']}\n"
        f"✅ Активные задачи: {kpi['active_tasks']}\n"
        f"📦 AI проекты: {kpi['active_projects']}\n"
        f"🔔 Непрочитанные уведомления: {kpi['unread_notifications']}\n\n"
        "Разделы: KPI · Продажи · Загрузка · Проекты · Уведомления · Задачи"
    )


def format_dashboard_section(user_id: int, section: str) -> str:
    if section == "kpi":
        return format_dashboard_text(user_id)
    if section == "sales":
        cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'DONE'")
        done = cursor.fetchone()[0]
        return f"📈 Продажи / заявки\n\n✅ Завершено заявок: {done}"
    if section == "workload":
        rows = get_tasks_by_user(user_id, scope="my", active_only=True, limit=10)
        lines = [f"📅 Загрузка сотрудника ({user_id})\n"]
        for r in rows:
            lines.append(f"  #{r[0]} {r[1]} · {r[8]}")
        return "\n".join(lines) if len(lines) > 1 else lines[0] + "\nЗадач нет."
    if section == "projects":
        return format_projects_text(user_id)
    if section == "notifications":
        return format_notifications_text(user_id, status="NEW", limit=10)
    if section == "tasks":
        return format_tasks_list_text(user_id, scope="my", active_only=True, limit=10)
    return format_dashboard_text(user_id)


# ==========================================================
# ENHANCED GLOBAL SEARCH
# ==========================================================

def search_requests(user_id: int, query: str, limit: int = 10):
    cursor.execute(
        """
        SELECT request_number, client_name, product, status, created_at
        FROM requests
        WHERE CAST(request_number AS TEXT) LIKE ?
           OR client_name LIKE ? OR product LIKE ? OR request_text LIKE ?
        ORDER BY id DESC LIMIT ?
        """,
        (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit),
    )
    return cursor.fetchall()


def search_notifications(user_id: int, query: str, limit: int = 10):
    cursor.execute(
        """
        SELECT id, title, message, COALESCE(module, category), priority, created_at
        FROM notifications
        WHERE user_id = ? AND (title LIKE ? OR message LIKE ?)
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, f"%{query}%", f"%{query}%", limit),
    )
    return cursor.fetchall()


def search_ai_dialogs(user_id: int, query: str, limit: int = 10):
    cursor.execute(
        """
        SELECT agent_code, role, substr(content, 1, 80), created_at
        FROM ai_dialogs
        WHERE user_id = ? AND content LIKE ?
        ORDER BY id DESC LIMIT ?
        """,
        (user_id, f"%{query}%", limit),
    )
    return cursor.fetchall()


def enhanced_global_search(user_id: int, query: str, limit: int = 10) -> dict:
    if not query:
        return {}
    return {
        "requests": search_requests(user_id, query, limit),
        "tasks": search_tasks(user_id, query, limit),
        "files": search_files(user_id, query, limit),
        "calendar": search_calendar_events(user_id, query, limit),
        "projects": search_projects(user_id, query, limit=limit),
        "users": search_users(user_id, query, limit),
        "notifications": search_notifications(user_id, query, limit),
        "ai_dialogs": search_ai_dialogs(user_id, query, limit),
        "deals": search_deals(user_id, query, limit=limit),
    }


def format_enhanced_search_results(results: dict, query: str) -> str:
    lines = [f"🔎 Результаты: «{query}»\n"]
    formatters = {
        "requests": ("📋 Заявки", lambda i: f"#{i[0]} {i[1]} · {i[2]}"),
        "tasks": ("✅ Задачи", lambda i: f"#{i[0]} {i[1]}"),
        "files": ("📁 Файлы", lambda i: f"#{i[0]} {i[2] or i[1]}"),
        "calendar": ("📅 Календарь", lambda i: f"#{i[0]} {i[1]} · {i[2]}"),
        "projects": ("📦 Проекты", lambda i: f"#{i[0]} {i[1]}"),
        "users": ("👥 Пользователи", lambda i: f"{i[1] or i[2]} (ID {i[0]})"),
        "notifications": ("🔔 Уведомления", lambda i: f"#{i[0]} {i[1]}"),
        "ai_dialogs": ("🤖 AI диалоги", lambda i: f"{i[0]} · {i[2]}"),
        "deals": ("🤝 Сделки", lambda i: str(i[0]) if i else "—"),
    }
    total = 0
    for key, (label, fmt) in formatters.items():
        items = results.get(key) or []
        if not items:
            continue
        total += len(items)
        lines.append(f"\n{label} ({len(items)}):")
        for item in items[:5]:
            try:
                lines.append(f"  · {fmt(item)}")
            except (IndexError, TypeError):
                lines.append(f"  · {item}")
    if total == 0:
        lines.append("\nНичего не найдено.")
    else:
        lines.append(f"\nВсего: {total}")
    return "\n".join(lines)