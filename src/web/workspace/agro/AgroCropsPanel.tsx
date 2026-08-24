/**
 * AGRO 1.2 — crop directory with availability / demand / gap.
 */

import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Button, Card, Input } from "@/ui";
import { agroOpsGet, agroOpsPost, pick } from "../business-ops/opsApi";

type Row = Record<string, unknown>;

export function AgroCropsPanel(props: {
  headers: Record<string, string>;
  canCreate: boolean;
  counterparties: Row[];
  onChanged: () => void;
  onOpen: (kind: string, id: string) => void;
}) {
  const [items, setItems] = useState<Row[]>([]);
  const [detail, setDetail] = useState<Row | null>(null);
  const [params] = useSearchParams();
  const focusCrop = String(params.get("crop") || "").trim();
  const [form, setForm] = useState<Row>({ commodity: "Пшеница", quantity: "1000", region: "Одесская обл." });
  const [msg, setMsg] = useState("");

  const [weatherCrops, setWeatherCrops] = useState<Row[]>([]);
  const [cropWx, setCropWx] = useState<Row | null>(null);

  async function reload() {
    const r = await agroOpsGet("/crops/directory", props.headers);
    setItems(((r.json as { items?: Row[] })?.items || []) as Row[]);
    const w = await agroOpsGet("/weather/dashboard", props.headers);
    setWeatherCrops((((w.json as { crops?: Row[] })?.crops) || []) as Row[]);
  }

  useEffect(() => {
    void reload();
  }, [props.headers]);

  useEffect(() => {
    if (!focusCrop || !items.length) return;
    const match = items.find((c) => String(c.name || "").toLowerCase().includes(focusCrop.toLowerCase()));
    if (!match) return;
    void (async () => {
      if (match.crop_id) {
        const r = await agroOpsGet(`/crops/${match.crop_id}/balance`, props.headers);
        setDetail((r.json as { item?: Row }).item || match);
        props.onOpen("crop", String(match.crop_id));
      } else {
        setDetail(match);
      }
    })();
  }, [focusCrop, items]);

  async function save(kind: "crop" | "availability" | "demand") {
    const body =
      kind === "crop"
        ? { name: form.commodity || form.name }
        : {
            commodity: form.commodity,
            quantity: form.quantity,
            region: form.region,
            counterparty_id: form.counterparty_id,
            crop_id: form.crop_id,
          };
    const res = await agroOpsPost(`/entities/${kind}`, body, props.headers);
    const j = res.json as { ok?: boolean; message_ru?: string };
    setMsg(j.ok ? "Сохранено" : j.message_ru || "Ошибка");
    if (j.ok) {
      props.onChanged();
      await reload();
    }
  }

  return (
    <div className="grid gap-3" data-testid="agro-crops-panel">
      <Card title="Справочник культур">
        <p className="eds-type-small mb-2">Каталог виден даже при нулевых остатках. Цифры — только из внесённых предложений и спроса.</p>
        <table className="w-full eds-type-small" data-testid="agro-crop-directory">
          <thead>
            <tr>
              <th className="text-left">Культура</th>
              <th>Предложение</th>
              <th>Спрос</th>
              <th>Разрыв</th>
            </tr>
          </thead>
          <tbody>
            {items.map((c) => (
              <tr key={String(c.name)} className={focusCrop && String(c.name).toLowerCase().includes(focusCrop.toLowerCase()) ? "bg-[var(--ew-surface-2)]" : undefined}>
                <td>
                  {c.crop_id ? (
                    <button
                      type="button"
                      className="underline"
                      onClick={async () => {
                        const r = await agroOpsGet(`/crops/${c.crop_id}/balance`, props.headers);
                        setDetail((r.json as { item?: Row }).item || c);
                        props.onOpen("crop", String(c.crop_id));
                      }}
                    >
                      {String(c.name)}
                    </button>
                  ) : (
                    String(c.name)
                  )}
                </td>
                <td>{String(c.available ?? 0)}</td>
                <td>{String(c.demand ?? 0)}</td>
                <td>{Number(c.gap) > 0 ? `+${c.gap}` : String(c.gap ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
      {weatherCrops.length ? (
        <Card title="Погода по культурам">
          <div className="eds-type-small" data-testid="agro-crop-weather">
            {weatherCrops.map((crop) => (
              <div key={String(crop.id)} className="mb-2">
                <div className="font-medium">{String(crop.label_ru).toUpperCase()}</div>
                <div className="flex flex-wrap gap-2">
                  {((crop.regions as Row[]) || []).map((reg) => (
                    <button
                      key={String(reg.macro_id)}
                      type="button"
                      className="rounded border border-[var(--ew-border)] px-2 py-1"
                      onClick={() => setCropWx({ crop: crop.label_ru, ...reg })}
                    >
                      {String(reg.short_ru)}: {String(reg.label_ru)}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>
          {cropWx ? (
            <p className="eds-type-small mt-2" data-testid="agro-crop-weather-explain">
              {String(cropWx.crop)} · {String(cropWx.short_ru)}: {String(cropWx.explanation_ru)}
            </p>
          ) : null}
        </Card>
      ) : null}
      {detail ? (
        <Card title={`Карточка: ${String(detail.name)}`}>
          <p className="eds-type-small" data-testid="agro-crop-balance">
            Предложение {String(detail.available)} · спрос {String(detail.demand)} · разрыв {Number(detail.gap) > 0 ? "+" : ""}
            {String(detail.gap)}
          </p>
        </Card>
      ) : null}
      {props.canCreate ? (
        <Card title="Добавить культуру / позицию">
          <div className="grid gap-2 sm:grid-cols-2">
            <Input placeholder="Культура" value={String(form.commodity || "")} onChange={(e) => setForm((f) => ({ ...f, commodity: e.target.value }))} />
            <Input placeholder="Объём, т" value={String(form.quantity || "")} onChange={(e) => setForm((f) => ({ ...f, quantity: e.target.value }))} />
            <Input placeholder="Регион" value={String(form.region || "")} onChange={(e) => setForm((f) => ({ ...f, region: e.target.value }))} />
            <select className="rounded-md border border-[var(--ew-border)] bg-transparent px-2 py-1 eds-type-small" value={String(form.counterparty_id || "")} onChange={(e) => setForm((f) => ({ ...f, counterparty_id: e.target.value }))}>
              <option value="">Контрагент</option>
              {props.counterparties.map((c) => (
                <option key={pick(c, "id")} value={pick(c, "id")}>
                  {pick(c, "name")}
                </option>
              ))}
            </select>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            <Button size="sm" onClick={() => void save("crop")}>Создать культуру</Button>
            <Button size="sm" variant="ghost" onClick={() => void save("availability")}>Добавить предложение</Button>
            <Button size="sm" variant="ghost" onClick={() => void save("demand")}>Добавить спрос</Button>
          </div>
        </Card>
      ) : null}
      {msg ? <p className="eds-type-small">{msg}</p> : null}
    </div>
  );
}
