# Voice Mode

**Epic:** 45.1 Dual Experience  
**Package:** `platform_modes`

## Purpose

Все возможности AI Mode + непрерывный голосовой диалог.

## Features

- Слушает команды
- Озвучивает ответы
- Промежуточный результат на экране
- Voice interruption / push-to-talk
- Wake word — **будущий этап**

## Stop phrases

- `Стоп` · `Отключись` · `Работаем вручную` · `Выключить AI` · `VOICE OFF`

## Indicator

`🎙 VOICE ACTIVE` (+ анимация микрофона в Web/Desktop)

## API

`POST /api/v1/mode/voice` — `{ "enabled": true|false }`
