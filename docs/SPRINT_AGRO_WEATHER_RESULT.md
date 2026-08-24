# AGRO WEATHER SPRINT RESULT

## STATUS

**COMPLETE.** Existing Agro → Погода (`?view=weather`) is now an Agro Weather Intelligence Dashboard. No second AGRO app, no parallel mock page, navigation and `/api/agro-ops/v1` namespace preserved.

Health: **`agro-2.0`**. Pipeline: **`AGRO_1_9`**. UX: **`AGRO_2_0`**. Live org: `org-agro-live-14`.

UI: http://127.0.0.1:5180/workspace/agro?view=weather  
Settings: http://127.0.0.1:5180/workspace/agro?view=settings&tab=weather

---

## 1. Что найдено в существующей архитектуре

- Route: `AgroBusinessPage` nav **Погода** → `?view=weather` → `AgroWeatherPanel`.
- Backend: `services/agro_ops/weather.py` (`UA_OBLASTS`, `MACRO_REGIONS`, Open-Meteo), observations in `weather_observation`.
- Provider: `weather_provider` = Open-Meteo. World Bank / Copernicus / NASA POWER **не** используются как live weather (нет рабочего weather-парсера).
- Карта 2.0 была **белой SVG-заглушкой** + кружки по lat/lon. Leaflet/MapLibre в `src/web` нет.
- Design tokens: dark navy `#0b1220` / `#121a2a`, teal `#3ecfad`.
- Культуры: `GET /crops/directory` (`DEFAULT_CROPS` + записи хозяйства).
- Технический шум уже уводился в Настройки → Диагностика (AGRO 2.0).

## 2. Какие файлы изменены

**Backend:** `services/agro_ops/weather.py`, `services/agro_ops/weather_intel.py` (новый), `services/agro_ops/series_parsers.py`, `applications/agro_enterprise/api/register.py`, `applications/agro_enterprise/api/ops_handlers.py`

**Frontend:** `src/web/workspace/agro/AgroWeatherPanel.tsx`, `AgroUkraineMap.tsx`, `agroWeather.css`, `data/ukraine-oblasts.geojson`, `data/ukraineOblastPaths.ts`, `AgroBusinessPage.tsx`, `AgroSettingsPanel.tsx`

**Tests / docs:** `tests/test_sprint_agro_weather.py`, `src/web/workspace/agro/sprint_agro_weather.test.tsx`, `sprint_agro_2_0.test.tsx` (клик «30 дней» scoped в историю), этот файл.

## 3. Какие API используются

Namespace `/api/agro-ops/v1` (не `/api/agro/weather`):

| Method | Path |
| --- | --- |
| GET | `/weather/dashboard` (расширен, контракт 2.0 сохранён) |
| GET | `/weather/overview?crop=` |
| GET | `/weather/regions` |
| GET | `/weather/regions/{oblast_id}` |
| GET | `/weather/oblasts/{oblast_id}` |
| GET | `/weather/forecast?region=&days=7` |
| GET | `/weather/outlook?region=&days=30` |
| GET | `/weather/agro-risk?region=&crop=` |
| GET | `/weather/recommendations?region=&crop=` |
| POST | `/weather/refresh` |
| GET | `/crops/directory` |

## 4. Какие реальные weather providers подключены

**Open-Meteo only** (`weather_provider`). Запрос: current (temp, humidity, precip, weather_code, wind m/s, pressure) + daily max/min/precip/probability/wind/weather_code, горизонт до **16** суток.

World Bank / FAO / Copernicus / NASA POWER на этом экране не вызываются.

## 5. Откуда берётся GeoJSON Украины

Упрощённая геометрия OSM → `src/web/workspace/agro/data/ukraine-oblasts.geojson` (~32KB, 25 features). В UI рендерится как SVG-path (`ukraineOblastPaths.ts`), не белый полигон-заглушка.

## 6. Как реализованы области

Центральный справочник `UA_OBLASTS` (lat/lon seats). Карта: path `data-testid=agro-weather-oblast-{id}`. Hover tooltip, click → `GET /weather/regions/{id}` и правая панель.

## 7. Как реализованы 5 агрорегионов

`MACRO_REGIONS` + `macro` на каждой области: south / center / west / north / east. Крым в `south`. Карточки под картой и `GET /weather/regions`. Клик карточки выбирает макрорегион и обновляет панель.

## 8. Как рассчитывается agro-risk

`agro_risk_from_metrics`: tmax, precip_7, humidity, wind, tmin, опционально культура (`crop_cell`). Уровни Low / Medium / High. Цвет карты = агро-риск (или выбранный слой), не декоративный.

## 9. Как рассчитывается confidence

Источники (сейчас 1) + freshness + completeness метрик + health `CONNECTED`. При одном источнике score ≤ 82. Текст: «Прогноз основан на данных N источников». Не hardcode.

## 10. Как формируются рекомендации

`recommendations_from_forecast`: сбор, техника, опрыскивание, удобрения, полив, посев, обработка почвы, защита. Если культура не выбрана — `general: true` («Общий погодный агро-индикатор»). Культуры из `/crops/directory`. Фаза роста / почва / хозяйство — слоты в `context_ru`, данных нет.

## 11. Какие fallback-механизмы работают

- Нет метрики → «нет данных», значение не выдумывается.
- 30 дней: агрегат по доступному горизонту Open-Meteo (до 16 суток), **без климатической нормы**. Иначе «Недостаточно данных для уверенного прогноза».
- Provider down при наличии наблюдений: dashboard остаётся ok, banner «Свежие погодные данные временно недоступны…».
- Карта GeoJSON всегда на экране (нет белого полигона).
- Почва: только если API вернул `soil_temp` (сейчас не запрашиваем hourly — поле «нет данных»).

## 12. Какие кнопки/действия проверены

Карта / области (Одесса, Львов, Харьков live) / регионы south+west / слои / вкладки / refresh API / crop selector / 7 дней / 30 дней / рекомендации / настройки → `?view=settings&tab=weather`. Live Open-Meteo 18.08.2026: Одесса 25.9°C / Львов 18.1°C / Киев 23.9°C, humidity и wind в м/с.

## 13. Backend tests

**71 passed / 0 failed** (`tests/test_sprint_agro*.py` включая operations/live/production + weather). Из них weather-specific: 6 новых в `test_sprint_agro_weather.py`; 2.0 suite зелёный.

## 14. Frontend tests

**48 passed / 0 failed** (`src/web` `workspace/agro`). Было 45; +3 weather intelligence.

## 15. Build status

`vitest` agro green. `tsc -b` в `src/web` падает на **предсуществующих** ошибках вне Agro weather (`ai_command_center`, `hercules`, `AgroDossierDrawer`, `chartProvider`). Новых TS-ошибок в weather-файлах нет.

## 16. Browser smoke test

- API restarted: `scripts/run_api_local.py` → health `agro-2.0`.
- Vite `:5180` `/workspace/agro?view=weather` → **200**.
- Live `GET /weather/overview` org-agro-live-14 → **200**, Open-Meteo CONNECTED, 5 region cards, 7-day forecast, 16-day outlook horizon.
- Полный клик-тур в GUI (все слои вручную в Safari) зависит от HMR; логика покрыта vitest + live HTTP.

## 17. Console errors

Автоматический захват browser console не выполнялся (нет Playwright в этом прогоне). Страница отдаётся 200; API JSON валидный. Технические HTTP/pipeline строки на экране Погоды не показываются.

## 18. Оставшиеся реальные ограничения

- **Нет 30-суточного суточного прогноза** у бесплатного Open-Meteo (max 16). Outlook — агрегат, не 30 точек «по дням».
- **Климатическая норма 30 лет не подключена** — сравнение с нормой честно недоступно.
- **Температура почвы** не запрашивается (hourly утяжеляет ответ) → empty state.
- **Один live weather source** — agreement между источниками измерить нельзя.
- Copernicus / NASA POWER **не интегрированы** как weather; подключать отдельно, не мокать.
- Фаза роста, дата посева, тип почвы, влажность почвы, хозяйство — в архитектуре рекомендаций, данных нет.
- Refresh обновляет до 12 representative областей, не все 25 за один клик (клик области догружает её).
- `src/web` `npm run lint` всё ещё красный из-за чужих модулей.

---

## Architectural decisions

- Расширяем `services/agro_ops`, не новый `platform_*`.
- SVG choropleth из GeoJSON вместо Leaflet: корректная геометрия Украины + jsdom-тесты без карты-библиотеки.
- Additive Open-Meteo parse: старый `tmax`/`precip` контракт 1.6/2.0 сохранён.
- Health/pipeline **не** bump.
- Ветер: `wind_speed_unit=ms`; значения >18 трактуются как km/h от старого default Open-Meteo.

Rejected: фейковый 30-дневный daily forecast; декоративные цвета карты; второй weather app; mock температуры.
