/**
 * Creative Factory — Sprint 36.9.
 * Creative Dashboard · Campaign Builder · Brand Center · Media Library · Prompt Studio · Publishing Hub · Analytics
 */

import { useCallback, useEffect, useState } from "react";
import { Badge, Button, Card, Input } from "@/ui";
import { PlatformBuilderLayout } from "../../platform-builder/layouts/PlatformBuilderLayout";

export const CREATIVE_API = "/api/creative";
export const CAMPAIGNS_API = "/api/campaigns";
export const MEDIA_API = "/api/media";

type SectionId =
  | "creative-dashboard"
  | "campaign-builder"
  | "brand-center"
  | "media-library"
  | "prompt-studio"
  | "publishing-hub"
  | "analytics";

const SECTIONS: Array<{ id: SectionId; label: string }> = [
  { id: "creative-dashboard", label: "Creative Dashboard" },
  { id: "campaign-builder", label: "Campaign Builder" },
  { id: "brand-center", label: "Brand Center" },
  { id: "media-library", label: "Media Library" },
  { id: "prompt-studio", label: "Prompt Studio" },
  { id: "publishing-hub", label: "Publishing Hub" },
  { id: "analytics", label: "Analytics" },
];

async function api<T>(base: string, path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${base}${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok || body.success === false) {
    throw new Error(body.error || body.errors?.[0] || `Request failed (${res.status})`);
  }
  return body.data as T;
}

export function CreativeFactoryPage() {
  const [section, setSection] = useState<SectionId>("creative-dashboard");
  const [stats, setStats] = useState<Record<string, unknown> | null>(null);
  const [assets, setAssets] = useState<Array<Record<string, unknown>>>([]);
  const [campaigns, setCampaigns] = useState<Array<Record<string, unknown>>>([]);
  const [brands, setBrands] = useState<Array<Record<string, unknown>>>([]);
  const [media, setMedia] = useState<Array<Record<string, unknown>>>([]);
  const [templates, setTemplates] = useState<Array<Record<string, unknown>>>([]);
  const [jobs, setJobs] = useState<Array<Record<string, unknown>>>([]);
  const [analytics, setAnalytics] = useState<Record<string, unknown> | null>(null);
  const [topic, setTopic] = useState("Enterprise AI Operating System");
  const [prompt, setPrompt] = useState("Create a social post about {{topic}} for decision makers");
  const [channel, setChannel] = useState("telegram");
  const [lastAsset, setLastAsset] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    const [st, as, cp, br, md, tpl, jb, an] = await Promise.all([
      api<Record<string, unknown>>(CREATIVE_API, "/statistics"),
      api<{ assets: Array<Record<string, unknown>> }>(CREATIVE_API, "/assets"),
      api<{ campaigns: Array<Record<string, unknown>> }>(CAMPAIGNS_API, ""),
      api<{ brands: Array<Record<string, unknown>> }>(CREATIVE_API, "/brands"),
      api<{ media: Array<Record<string, unknown>> }>(MEDIA_API, ""),
      api<{ templates: Array<Record<string, unknown>> }>(CREATIVE_API, "/templates"),
      api<{ jobs: Array<Record<string, unknown>> }>(CREATIVE_API, "/publish/jobs"),
      api<Record<string, unknown>>(CREATIVE_API, "/analytics"),
    ]);
    setStats(st);
    setAssets(as.assets || []);
    setCampaigns(cp.campaigns || []);
    setBrands(br.brands || []);
    setMedia(md.media || []);
    setTemplates(tpl.templates || []);
    setJobs(jb.jobs || []);
    setAnalytics(an);
  }, []);

  useEffect(() => {
    refresh().catch((e) => setError(String(e.message || e)));
  }, [refresh]);

  const generate = async (creativeType = "social_post") => {
    setBusy(true);
    try {
      const data = await api<Record<string, unknown>>(CREATIVE_API, "/generate", {
        method: "POST",
        body: JSON.stringify({
          creative_type: creativeType,
          topic,
          prompt: prompt.replace("{{topic}}", topic),
          modality: "text",
          audience: "decision makers",
        }),
      });
      setLastAsset(data);
      await refresh();
      setSection("creative-dashboard");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const createCampaign = async () => {
    setBusy(true);
    try {
      await api(CAMPAIGNS_API, "", {
        method: "POST",
        body: JSON.stringify({
          name: `Campaign: ${topic.slice(0, 40)}`,
          objective: "awareness",
          audience: "decision makers",
          channels: ["telegram", "linkedin", "x"],
          budget: 5000,
          creative_ids: lastAsset?.asset_id ? [lastAsset.asset_id] : [],
        }),
      });
      await refresh();
      setSection("campaign-builder");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  const publishLast = async () => {
    if (!lastAsset?.asset_id) {
      setError("Generate an asset first");
      return;
    }
    setBusy(true);
    try {
      await api(CREATIVE_API, "/publish", {
        method: "POST",
        body: JSON.stringify({ asset_id: lastAsset.asset_id, channel }),
      });
      await refresh();
      setSection("publishing-hub");
    } catch (e) {
      setError(String((e as Error).message || e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <PlatformBuilderLayout title="Creative Factory" subtitle="Enterprise content production">
      <div className="space-y-4" data-testid="creative-factory-console">
        <div className="flex flex-wrap gap-2">
          {SECTIONS.map((s) => (
            <Button
              key={s.id}
              variant={section === s.id ? "primary" : "secondary"}
              size="sm"
              onClick={() => setSection(s.id)}
            >
              {s.label}
            </Button>
          ))}
        </div>

        {error && (
          <Card className="border-red-300 bg-red-50 p-3 text-sm text-red-800">{error}</Card>
        )}

        {section === "creative-dashboard" && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <Badge>assets {String(stats?.assets ?? 0)}</Badge>
              <Badge>campaigns {String(stats?.campaigns ?? 0)}</Badge>
              <Badge>media {String(stats?.media ?? 0)}</Badge>
              <Badge>publishes {String(stats?.publishes ?? 0)}</Badge>
            </div>
            <div className="flex gap-2">
              <Button disabled={busy} onClick={() => generate("social_post")}>
                Generate Social Post
              </Button>
              <Button disabled={busy} variant="secondary" onClick={() => generate("blog_article")}>
                Generate Blog
              </Button>
              <Button disabled={busy} variant="secondary" onClick={refresh}>
                Refresh
              </Button>
            </div>
            {lastAsset && (
              <Card className="p-4 space-y-1">
                <div className="font-medium">{String(lastAsset.title)}</div>
                <div className="text-sm opacity-80 whitespace-pre-wrap">{String(lastAsset.content)}</div>
              </Card>
            )}
            <div className="grid gap-2">
              {assets.slice(0, 8).map((a) => (
                <Card key={String(a.asset_id)} className="p-3 text-sm">
                  <div className="font-medium">{String(a.title)}</div>
                  <div className="opacity-70">
                    {String(a.creative_type)} · {String(a.status)} · v{String(a.version)}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {section === "campaign-builder" && (
          <div className="space-y-3">
            <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Campaign topic" />
            <Button disabled={busy} onClick={createCampaign}>
              Create Campaign
            </Button>
            <div className="grid gap-2">
              {campaigns.map((c) => (
                <Card key={String(c.campaign_id)} className="p-3 text-sm">
                  <div className="font-medium">{String(c.name)}</div>
                  <div className="opacity-70">
                    {String(c.objective)} · {String(c.status)} · budget {String(c.budget)}
                  </div>
                  <div className="opacity-60">{(c.channels as string[] | undefined)?.join(", ")}</div>
                </Card>
              ))}
            </div>
          </div>
        )}

        {section === "brand-center" && (
          <div className="grid gap-2">
            {brands.map((b) => (
              <Card key={String(b.brand_id)} className="p-4 space-y-1">
                <div className="font-medium">{String(b.name)}</div>
                <div className="text-sm opacity-70">Tone: {String(b.tone_of_voice)}</div>
                <div className="text-sm opacity-70">
                  Colors: {JSON.stringify(b.colors || {})}
                </div>
                <div className="text-sm opacity-70">
                  Typography: {JSON.stringify(b.typography || {})}
                </div>
              </Card>
            ))}
          </div>
        )}

        {section === "media-library" && (
          <div className="grid gap-2">
            {media.slice(0, 12).map((m) => (
              <Card key={String(m.media_id)} className="p-3 text-sm">
                <div className="font-medium">{String(m.title)}</div>
                <div className="opacity-70">
                  {String(m.modality)} · {String(m.url)}
                </div>
              </Card>
            ))}
            {!media.length && <div className="text-sm opacity-60">Generate creatives to populate the library.</div>}
          </div>
        )}

        {section === "prompt-studio" && (
          <div className="space-y-3">
            <Input value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="Topic" />
            <textarea
              className="w-full min-h-[120px] rounded border p-3 text-sm"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
            />
            <div className="text-sm opacity-70">Templates: {templates.length}</div>
            <div className="flex flex-wrap gap-2">
              {["landing_page", "advertisement", "email_campaign", "sales_proposal", "presentation"].map((t) => (
                <Button key={t} size="sm" variant="secondary" disabled={busy} onClick={() => generate(t)}>
                  {t.replace(/_/g, " ")}
                </Button>
              ))}
            </div>
          </div>
        )}

        {section === "publishing-hub" && (
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {["facebook", "instagram", "tiktok", "telegram", "linkedin", "x", "youtube"].map((ch) => (
                <Button
                  key={ch}
                  size="sm"
                  variant={channel === ch ? "primary" : "secondary"}
                  onClick={() => setChannel(ch)}
                >
                  {ch}
                </Button>
              ))}
            </div>
            <Button disabled={busy} onClick={publishLast}>
              Publish to {channel}
            </Button>
            <div className="grid gap-2">
              {jobs.map((j) => (
                <Card key={String(j.job_id)} className="p-3 text-sm">
                  {String(j.channel)} · {String(j.status)} · {String(j.external_id || j.job_id)}
                </Card>
              ))}
            </div>
          </div>
        )}

        {section === "analytics" && (
          <Card className="p-4">
            <pre className="text-xs whitespace-pre-wrap overflow-auto max-h-[480px]">
              {JSON.stringify(analytics, null, 2)}
            </pre>
          </Card>
        )}
      </div>
    </PlatformBuilderLayout>
  );
}
