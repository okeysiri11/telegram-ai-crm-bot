/**
 * Sprint 31.2 — Enterprise provider registry (declarative).
 * AI calls go through APH; credentials via ESH vault. No parallel hub.
 */

export type ProviderCategory =
  | "ai"
  | "image"
  | "video"
  | "audio"
  | "automation"
  | "crm"
  | "storage"
  | "payments"
  | "observability"
  | "orchestration";

export type ProviderEntry = {
  id: string;
  title: string;
  category: ProviderCategory;
  /** true = wired or bootstrap-ready via APH / platform_integrations */
  ready: boolean;
  via: "aph" | "platform_integrations" | "n8n_bridge" | "enterprise_obs" | "local";
  costHintUsdPer1k?: number;
  failoverPriority?: number;
};

export const PROVIDER_REGISTRY: ProviderEntry[] = [
  // AI
  { id: "openai", title: "OpenAI", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0.15, failoverPriority: 10 },
  { id: "anthropic", title: "Anthropic Claude", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0.25, failoverPriority: 20 },
  { id: "google_gemini", title: "Google Gemini", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0.1, failoverPriority: 25 },
  { id: "openrouter", title: "OpenRouter", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0.12, failoverPriority: 30 },
  { id: "deepseek", title: "DeepSeek", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0.05, failoverPriority: 35 },
  { id: "mistral", title: "Mistral", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0.08, failoverPriority: 40 },
  { id: "groq", title: "Groq", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0.04, failoverPriority: 15 },
  { id: "xai", title: "xAI (Grok)", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0.2, failoverPriority: 45 },
  { id: "ollama", title: "Ollama (local)", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0, failoverPriority: 85 },
  { id: "litellm", title: "LiteLLM gateway", category: "ai", ready: true, via: "aph", costHintUsdPer1k: 0, failoverPriority: 5 },
  // Image
  { id: "openai_images", title: "OpenAI Images", category: "image", ready: false, via: "aph", costHintUsdPer1k: 4 },
  { id: "flux", title: "Flux", category: "image", ready: false, via: "aph", costHintUsdPer1k: 3 },
  { id: "stable_diffusion", title: "Stable Diffusion", category: "image", ready: false, via: "aph" },
  { id: "ideogram", title: "Ideogram", category: "image", ready: false, via: "aph" },
  { id: "recraft", title: "Recraft", category: "image", ready: false, via: "aph" },
  { id: "fal_ai", title: "Fal.ai", category: "image", ready: false, via: "aph" },
  { id: "comfyui", title: "ComfyUI", category: "image", ready: false, via: "local" },
  { id: "automatic1111", title: "Automatic1111", category: "image", ready: false, via: "local" },
  // Video
  { id: "runway", title: "Runway", category: "video", ready: false, via: "aph" },
  { id: "kling", title: "Kling", category: "video", ready: false, via: "aph" },
  { id: "pika", title: "Pika", category: "video", ready: false, via: "aph" },
  { id: "luma", title: "Luma Dream Machine", category: "video", ready: false, via: "aph" },
  { id: "veo", title: "Veo", category: "video", ready: false, via: "aph" },
  { id: "minimax", title: "Minimax", category: "video", ready: false, via: "aph" },
  // Audio
  { id: "elevenlabs", title: "ElevenLabs", category: "audio", ready: false, via: "aph" },
  { id: "cartesia", title: "Cartesia", category: "audio", ready: false, via: "aph" },
  { id: "openai_voice", title: "OpenAI Voice", category: "audio", ready: false, via: "aph" },
  { id: "azure_speech", title: "Azure Speech", category: "audio", ready: false, via: "aph" },
  { id: "whisper", title: "Whisper", category: "audio", ready: true, via: "aph" },
  // Automation
  { id: "telegram", title: "Telegram", category: "automation", ready: true, via: "platform_integrations" },
  { id: "whatsapp", title: "WhatsApp", category: "automation", ready: false, via: "platform_integrations" },
  { id: "discord", title: "Discord", category: "automation", ready: false, via: "platform_integrations" },
  { id: "slack", title: "Slack", category: "automation", ready: false, via: "platform_integrations" },
  { id: "email", title: "Email", category: "automation", ready: true, via: "platform_integrations" },
  { id: "sms", title: "SMS", category: "automation", ready: true, via: "platform_integrations" },
  { id: "google_calendar", title: "Google Calendar", category: "automation", ready: false, via: "platform_integrations" },
  { id: "google_drive", title: "Google Drive", category: "automation", ready: false, via: "platform_integrations" },
  { id: "google_docs", title: "Google Docs", category: "automation", ready: false, via: "platform_integrations" },
  { id: "microsoft_365", title: "Microsoft 365", category: "automation", ready: false, via: "platform_integrations" },
  { id: "notion", title: "Notion", category: "automation", ready: false, via: "platform_integrations" },
  { id: "github", title: "GitHub", category: "automation", ready: false, via: "platform_integrations" },
  { id: "gitlab", title: "GitLab", category: "automation", ready: false, via: "platform_integrations" },
  { id: "jira", title: "Jira", category: "automation", ready: false, via: "platform_integrations" },
  { id: "linear", title: "Linear", category: "automation", ready: false, via: "platform_integrations" },
  // CRM
  { id: "hubspot", title: "HubSpot", category: "crm", ready: false, via: "platform_integrations" },
  { id: "salesforce", title: "Salesforce", category: "crm", ready: false, via: "platform_integrations" },
  { id: "bitrix24", title: "Bitrix24", category: "crm", ready: false, via: "platform_integrations" },
  { id: "pipedrive", title: "Pipedrive", category: "crm", ready: false, via: "platform_integrations" },
  { id: "zoho", title: "Zoho", category: "crm", ready: false, via: "platform_integrations" },
  // Storage
  { id: "s3", title: "S3", category: "storage", ready: false, via: "platform_integrations" },
  { id: "minio", title: "MinIO", category: "storage", ready: false, via: "platform_integrations" },
  { id: "cloudflare_r2", title: "Cloudflare R2", category: "storage", ready: false, via: "platform_integrations" },
  { id: "dropbox", title: "Dropbox", category: "storage", ready: false, via: "platform_integrations" },
  { id: "onedrive", title: "OneDrive", category: "storage", ready: false, via: "platform_integrations" },
  // Payments
  { id: "stripe", title: "Stripe", category: "payments", ready: false, via: "platform_integrations" },
  { id: "wayforpay", title: "WayForPay", category: "payments", ready: false, via: "platform_integrations" },
  { id: "liqpay", title: "LiqPay", category: "payments", ready: false, via: "platform_integrations" },
  { id: "fondy", title: "Fondy", category: "payments", ready: false, via: "platform_integrations" },
  { id: "paypal", title: "PayPal", category: "payments", ready: false, via: "platform_integrations" },
  { id: "crypto_wallets", title: "Crypto Wallets", category: "payments", ready: false, via: "platform_integrations" },
  // Observability
  { id: "grafana", title: "Grafana", category: "observability", ready: false, via: "enterprise_obs" },
  { id: "prometheus", title: "Prometheus", category: "observability", ready: false, via: "enterprise_obs" },
  { id: "loki", title: "Loki", category: "observability", ready: false, via: "enterprise_obs" },
  { id: "sentry", title: "Sentry", category: "observability", ready: false, via: "enterprise_obs" },
  { id: "opentelemetry", title: "OpenTelemetry", category: "observability", ready: false, via: "enterprise_obs" },
  // Orchestration
  { id: "n8n", title: "n8n", category: "orchestration", ready: true, via: "n8n_bridge", failoverPriority: 1 },
];

export function providersByCategory(category: ProviderCategory | "all"): ProviderEntry[] {
  if (category === "all") return PROVIDER_REGISTRY.slice();
  return PROVIDER_REGISTRY.filter((p) => p.category === category);
}

export function getProvider(id: string): ProviderEntry | undefined {
  return PROVIDER_REGISTRY.find((p) => p.id === id);
}

export function aiFailoverChain(): ProviderEntry[] {
  return PROVIDER_REGISTRY.filter((p) => p.category === "ai" && p.ready)
    .slice()
    .sort((a, b) => (a.failoverPriority ?? 99) - (b.failoverPriority ?? 99));
}

/** Rough cost estimate for N tokens (presentation over APH cost track). */
export function estimateCostUsd(providerId: string, tokens: number): number {
  const p = getProvider(providerId);
  const per1k = p?.costHintUsdPer1k ?? 0.1;
  return (tokens / 1000) * per1k;
}

export const PROVIDER_REGISTRY_META = {
  vault: "enterprise_esh",
  aiGateway: "enterprise_aph",
  systemOfRecord: "platform_runtime",
  externalOrchestrator: "n8n",
  promptFirewall: true,
  rateLimits: true,
} as const;
