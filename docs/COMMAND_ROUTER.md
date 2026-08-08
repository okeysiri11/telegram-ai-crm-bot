# Command Router

`platform_ai_command/router/command_router.py`

Определяет:

- тип задачи (`TaskKind`)
- вертикаль (через Vertical Router)
- агентов
- инструменты
- подсказку провайдеров (`hercules`, `unified_pipeline`)
- уровень доступа
- оценку стоимости
- необходимость уточнения

Не вызывает вендоров напрямую.
