/**
 * Sprint 50.5 — specialist settings panel + signal create form.
 */
import { useState } from "react";
import { Button, Card, Input } from "@/ui";

export type SpecialistSettings = {
  enabled: boolean;
  instruments: string[];
  timeframes: string[];
  weight: number;
  minimum_confidence: number;
  include_in_chief_consensus: boolean;
  allow_signal_generation: boolean;
  alert_level: string;
  // agent-specific
  indicators?: Record<string, boolean>;
  dxy_enabled?: boolean;
  sensitivity?: string;
  divergence_monitoring?: boolean;
  inverse_eurusd_relation?: boolean;
  correlation_threshold?: number;
  impact?: string[];
  currencies?: string[];
  events?: string[];
  max_risk_per_trade_pct?: number;
  max_daily_loss?: number;
  max_open_positions?: number;
  minimum_rr?: number;
  stop_after_n_losses?: number;
  max_drawdown_threshold?: number;
  strict?: boolean;
};

export function defaultSpecialistSettings(id: string): SpecialistSettings {
  const base: SpecialistSettings = {
    enabled: true,
    instruments: ["EUR/USD", "DXY"],
    timeframes: ["1H"],
    weight: 1,
    minimum_confidence: 0.3,
    include_in_chief_consensus: true,
    allow_signal_generation: true,
    alert_level: "medium",
  };
  if (id === "technical") {
    return {
      ...base,
      timeframes: ["15m", "1H", "4H", "1D"],
      indicators: { ema: true, sma: true, rsi: true, macd: true, bollinger: true, atr: true, support_resistance: true },
    };
  }
  if (id === "dxy") {
    return {
      ...base,
      instruments: ["DXY"],
      dxy_enabled: true,
      sensitivity: "medium",
      divergence_monitoring: true,
      inverse_eurusd_relation: true,
      correlation_threshold: 0.5,
    };
  }
  if (id === "macro") {
    return { ...base, impact: ["medium", "high"], currencies: ["EUR", "USD"], events: ["ECB", "FED", "CPI", "NFP"] };
  }
  if (id === "risk") {
    return {
      ...base,
      max_risk_per_trade_pct: 1,
      max_daily_loss: 500,
      max_open_positions: 5,
      minimum_rr: 1.5,
      stop_after_n_losses: 3,
      max_drawdown_threshold: 5,
      strict: false,
    };
  }
  return base;
}

export function SpecialistSettingsPanel({
  agentId,
  agentName,
  value,
  onSave,
  onClose,
}: {
  agentId: string;
  agentName: string;
  value: SpecialistSettings;
  onSave: (next: SpecialistSettings) => void;
  onClose: () => void;
}) {
  const [cfg, setCfg] = useState(value);
  return (
    <Card title={`Настройки · ${agentName}`} data-testid={`specialist-settings-${agentId}`}>
      <div className="grid gap-2 sm:grid-cols-2 eds-type-small">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={cfg.enabled} onChange={(e) => setCfg({ ...cfg, enabled: e.target.checked })} />
          Включён
        </label>
        <label>
          Вес
          <Input className="mt-1" type="number" step="0.1" value={String(cfg.weight)} onChange={(e) => setCfg({ ...cfg, weight: Number(e.target.value) || 1 })} />
        </label>
        <label>
          Мин. уверенность
          <Input
            className="mt-1"
            type="number"
            step="0.05"
            value={String(cfg.minimum_confidence)}
            onChange={(e) => setCfg({ ...cfg, minimum_confidence: Number(e.target.value) || 0 })}
          />
        </label>
        <label>
          Уровень алерта
          <select className="mt-1 w-full rounded border px-2 py-1" value={cfg.alert_level} onChange={(e) => setCfg({ ...cfg, alert_level: e.target.value })}>
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={cfg.include_in_chief_consensus}
            onChange={(e) => setCfg({ ...cfg, include_in_chief_consensus: e.target.checked })}
          />
          Участвует в Chief consensus
        </label>
        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={cfg.allow_signal_generation}
            onChange={(e) => setCfg({ ...cfg, allow_signal_generation: e.target.checked })}
          />
          Разрешить генерацию сигналов
        </label>
        <label className="sm:col-span-2">
          Инструменты (через запятую)
          <Input
            className="mt-1"
            value={cfg.instruments.join(", ")}
            onChange={(e) =>
              setCfg({
                ...cfg,
                instruments: e.target.value
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean),
              })
            }
          />
        </label>
        <label className="sm:col-span-2">
          Таймфреймы (через запятую)
          <Input
            className="mt-1"
            value={cfg.timeframes.join(", ")}
            onChange={(e) =>
              setCfg({
                ...cfg,
                timeframes: e.target.value
                  .split(",")
                  .map((x) => x.trim())
                  .filter(Boolean),
              })
            }
          />
        </label>
        {agentId === "technical" && cfg.indicators ? (
          <div className="sm:col-span-2 flex flex-wrap gap-3">
            {Object.keys(cfg.indicators).map((k) => (
              <label key={k} className="flex items-center gap-1">
                <input
                  type="checkbox"
                  checked={!!cfg.indicators?.[k]}
                  onChange={(e) => setCfg({ ...cfg, indicators: { ...cfg.indicators, [k]: e.target.checked } })}
                />
                {k.toUpperCase()}
              </label>
            ))}
          </div>
        ) : null}
        {agentId === "dxy" ? (
          <>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={!!cfg.dxy_enabled} onChange={(e) => setCfg({ ...cfg, dxy_enabled: e.target.checked })} />
              DXY enabled
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!cfg.divergence_monitoring}
                onChange={(e) => setCfg({ ...cfg, divergence_monitoring: e.target.checked })}
              />
              Divergence monitoring
            </label>
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={!!cfg.inverse_eurusd_relation}
                onChange={(e) => setCfg({ ...cfg, inverse_eurusd_relation: e.target.checked })}
              />
              Inverse EUR/USD relation
            </label>
            <label>
              Correlation threshold
              <Input
                className="mt-1"
                type="number"
                step="0.05"
                value={String(cfg.correlation_threshold ?? 0.5)}
                onChange={(e) => setCfg({ ...cfg, correlation_threshold: Number(e.target.value) })}
              />
            </label>
          </>
        ) : null}
        {agentId === "risk" ? (
          <>
            <label>
              Max risk per trade %
              <Input
                className="mt-1"
                type="number"
                value={String(cfg.max_risk_per_trade_pct ?? 1)}
                onChange={(e) => setCfg({ ...cfg, max_risk_per_trade_pct: Number(e.target.value) })}
              />
            </label>
            <label>
              Minimum R/R
              <Input
                className="mt-1"
                type="number"
                step="0.1"
                value={String(cfg.minimum_rr ?? 1.5)}
                onChange={(e) => setCfg({ ...cfg, minimum_rr: Number(e.target.value) })}
              />
            </label>
            <label>
              Max open positions
              <Input
                className="mt-1"
                type="number"
                value={String(cfg.max_open_positions ?? 5)}
                onChange={(e) => setCfg({ ...cfg, max_open_positions: Number(e.target.value) })}
              />
            </label>
            <label className="flex items-center gap-2">
              <input type="checkbox" checked={!!cfg.strict} onChange={(e) => setCfg({ ...cfg, strict: e.target.checked })} />
              Strict (блокировать paper trade)
            </label>
          </>
        ) : null}
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          size="sm"
          className="ews-primary-cta"
          onClick={() => {
            onSave(cfg);
            onClose();
          }}
        >
          Сохранить
        </Button>
        <Button size="sm" variant="secondary" onClick={onClose}>
          Закрыть
        </Button>
      </div>
    </Card>
  );
}

const SOUND_PROFILES = [
  { id: "standard", label: "Стандартный" },
  { id: "eurusd", label: "EUR/USD" },
  { id: "dxy", label: "DXY" },
  { id: "analysis", label: "Анализ" },
  { id: "important", label: "Важное событие" },
  { id: "silent", label: "Без звука" },
];

const SIGNAL_KINDS = [
  { id: "price_alert", label: "Price alert" },
  { id: "analysis_result", label: "Analysis result" },
  { id: "agent_event", label: "Agent event" },
  { id: "scheduled_event", label: "Scheduled event" },
  { id: "macro_alert", label: "Macro alert" },
];

export function SignalCreateForm({
  defaults,
  onSubmit,
  onCancel,
}: {
  defaults?: Partial<Record<string, string | number | boolean>>;
  onSubmit: (body: Record<string, unknown>) => void;
  onCancel: () => void;
}) {
  const [title, setTitle] = useState(String(defaults?.title || "Сигнал EUR/USD"));
  const [instrument, setInstrument] = useState(String(defaults?.instrument || "EUR/USD"));
  const [kind, setKind] = useState(String(defaults?.kind || "price_alert"));
  const [condition, setCondition] = useState(String(defaults?.condition || "cross"));
  const [value, setValue] = useState(String(defaults?.value ?? ""));
  const [source, setSource] = useState(String(defaults?.source || "manual"));
  const [sound, setSound] = useState(String(defaults?.sound_profile || "standard"));
  const [channel, setChannel] = useState("in_app");
  const [active, setActive] = useState(true);
  const [expires, setExpires] = useState("");
  const [cooldown, setCooldown] = useState("0");

  return (
    <Card title="Создать сигнал" data-testid="signal-create-form">
      <div className="grid gap-2 sm:grid-cols-2 eds-type-small">
        <label>
          Название
          <Input className="mt-1" value={title} onChange={(e) => setTitle(e.target.value)} />
        </label>
        <label>
          Инструмент
          <select className="mt-1 w-full rounded border px-2 py-1" value={instrument} onChange={(e) => setInstrument(e.target.value)}>
            <option>EUR/USD</option>
            <option>DXY</option>
          </select>
        </label>
        <label>
          Тип
          <select className="mt-1 w-full rounded border px-2 py-1" value={kind} onChange={(e) => setKind(e.target.value)}>
            {SIGNAL_KINDS.map((k) => (
              <option key={k.id} value={k.id}>
                {k.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Условие
          <select className="mt-1 w-full rounded border px-2 py-1" value={condition} onChange={(e) => setCondition(e.target.value)}>
            <option value="above">above</option>
            <option value="below">below</option>
            <option value="cross">crosses</option>
          </select>
        </label>
        <label>
          Значение
          <Input className="mt-1" value={value} onChange={(e) => setValue(e.target.value)} />
        </label>
        <label>
          Источник
          <Input className="mt-1" value={source} onChange={(e) => setSource(e.target.value)} />
        </label>
        <label>
          Звук
          <select className="mt-1 w-full rounded border px-2 py-1" value={sound} onChange={(e) => setSound(e.target.value)}>
            {SOUND_PROFILES.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Канал уведомлений
          <select className="mt-1 w-full rounded border px-2 py-1" value={channel} onChange={(e) => setChannel(e.target.value)}>
            <option value="in_app">В приложении</option>
          </select>
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={active} onChange={(e) => setActive(e.target.checked)} />
          Active
        </label>
        <label>
          Expires (ISO)
          <Input className="mt-1" value={expires} onChange={(e) => setExpires(e.target.value)} placeholder="опционально" />
        </label>
        <label>
          Cooldown (сек)
          <Input className="mt-1" value={cooldown} onChange={(e) => setCooldown(e.target.value)} />
        </label>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        <Button
          size="sm"
          className="ews-primary-cta"
          onClick={() =>
            onSubmit({
              title,
              instrument,
              kind,
              type: kind,
              condition,
              value: value ? Number(value) : undefined,
              source,
              sound_profile: sound,
              notification_channel: channel,
              active,
              expires: expires || undefined,
              cooldown: Number(cooldown) || 0,
              signal: "WAIT",
              analysis_run_id: defaults?.analysis_run_id,
            })
          }
        >
          Сохранить сигнал
        </Button>
        <Button size="sm" variant="secondary" onClick={onCancel}>
          Отмена
        </Button>
      </div>
    </Card>
  );
}
