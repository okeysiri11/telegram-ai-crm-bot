export const RUNTIME_HTTP =
  import.meta.env.VITE_RUNTIME_URL?.replace(/\/$/, "") || "http://localhost:3000";

export const RUNTIME_WS =
  import.meta.env.VITE_RUNTIME_WS ||
  RUNTIME_HTTP.replace(/^http/, "ws") + "/ws";

export class RuntimeApiError extends Error {
  readonly status: number;
  constructor(message: string, status: number) {
    super(message);
    this.name = "RuntimeApiError";
    this.status = status;
  }
}

async function runtimeFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${RUNTIME_HTTP}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  const body = (await response.json()) as T & { error?: string };
  if (!response.ok) {
    throw new RuntimeApiError(body.error || response.statusText, response.status);
  }
  return body;
}

export interface StatusDto {
  version: string;
  kernel: string;
  eventBus: string;
  serviceMesh: string;
  workflowEngine: string;
  runtimeServer?: string;
  orchestrator?: string;
  providerGateway?: string;
  chatBridge?: string;
  voice?: string;
  mcp?: string;
  execution?: string;
  services: number;
  agents?: number;
  providers?: number;
  providersConnected?: number;
  runningTasks?: number;
  queueSize?: number;
  systemStatus?: string;
}

export interface MetricsDto {
  uptimeSec: number;
  memory: { rss: number; heapUsed: number; heapTotal: number; external: number };
  cpu: { userMicros: number; systemMicros: number };
  startedAt: string;
}

export interface ServiceDto {
  id: string;
  version: string;
  kind: string;
  lifecycle: string;
  uptimeMs: number;
  health: string;
  dependencies: string[];
}

export interface WorkflowDto {
  id: string;
  name: string;
  version: string;
  start: string;
  steps: number;
}

export interface WorkflowInstanceDto {
  id: string;
  definitionId: string;
  status: string;
  activeSteps: string[];
  updatedAt: string;
}

export interface KernelDto {
  version: string;
  platformVersion: string;
  state: string;
  startedAt: string;
  uptimeMs: number;
  modules: string[];
  services: number;
  health: string;
}

export interface EventDto {
  id: string;
  type: string;
  at: string;
  payload?: unknown;
}

export interface LogDto {
  id: string;
  at: string;
  level: "info" | "warn" | "error";
  message: string;
  source?: string;
}

export interface AgentDto {
  id: string;
  name?: string;
  role: string;
  status: string;
  provider: string;
  memory: string;
  skills?: string[];
  version?: string;
  lastExecution?: string | null;
  currentTask?: string | null;
  queueSize?: number;
  runningTasks: number;
  responseTimeMs?: number;
  health?: string;
  metrics?: {
    tasksCompleted: number;
    successes: number;
    errors: number;
    avgResponseTimeMs: number;
    load: number;
  };
}

export interface CollaborationWorkflowDto {
  id: string;
  templateId: string;
  name: string;
  status: string;
  priority: number;
  estimatedMs: number;
  elapsedMs: number;
  currentStepIds: string[];
  steps: Array<{
    id: string;
    agentId: string;
    status: string;
    attempts: number;
    durationMs?: number;
    error?: string;
  }>;
  graph: {
    nodes: Array<{ id: string; agentId: string; label: string }>;
    edges: Array<{ from: string; to: string }>;
  };
  contextKeys: string[];
  artifactCount: number;
}

export interface WorkflowTemplateDto {
  id: string;
  name: string;
  description: string;
  category: string;
  estimatedMs: number;
  steps: Array<{ id: string; name: string; agentId: string }>;
}

export interface AgentLogDto {
  id: string;
  at: string;
  agentId: string;
  level: "info" | "warn" | "error";
  message: string;
  taskId?: string;
}

export interface ProviderDto {
  id: string;
  name: string;
  status: string;
  connected: boolean;
  health: { status: string; message?: string; checkedAt: string };
  capabilities: Array<{ id: string; description: string }>;
  currentRequests: number;
  averageResponseTimeMs: number;
  totalRequests: number;
  errors: number;
}

export const runtimeApi = {
  health: () => runtimeFetch<{ status: string }>("/health"),
  status: () => runtimeFetch<StatusDto>("/status"),
  metrics: () => runtimeFetch<MetricsDto>("/metrics"),
  kernel: () => runtimeFetch<KernelDto>("/kernel"),
  services: () => runtimeFetch<{ services: ServiceDto[] }>("/services"),
  workflows: () =>
    runtimeFetch<{
      workflows: WorkflowDto[];
      instances: WorkflowInstanceDto[];
      collaboration?: CollaborationWorkflowDto[];
      templates?: WorkflowTemplateDto[];
      overview?: Record<string, number> | null;
    }>("/workflow"),
  startCollaboration: (body: {
    templateId?: string;
    name?: string;
    payload?: unknown;
    priority?: number;
  }) =>
    runtimeFetch<CollaborationWorkflowDto>("/workflow/start", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  pauseCollaboration: (id: string) =>
    runtimeFetch<CollaborationWorkflowDto>("/workflow/pause", {
      method: "POST",
      body: JSON.stringify({ id }),
    }),
  resumeCollaboration: (id: string) =>
    runtimeFetch<CollaborationWorkflowDto>("/workflow/resume", {
      method: "POST",
      body: JSON.stringify({ id }),
    }),
  cancelCollaboration: (id: string) =>
    runtimeFetch<CollaborationWorkflowDto>("/workflow/cancel", {
      method: "POST",
      body: JSON.stringify({ id }),
    }),
  workflowTemplates: () =>
    runtimeFetch<{ templates: WorkflowTemplateDto[] }>("/workflow/templates"),
  collaborationOverview: () =>
    runtimeFetch<{
      workflows: number;
      running: number;
      completed: number;
      failed: number;
      agents: number;
      queueSize: number;
      avgResponseTimeMs: number;
      successRate: number;
      templates: number;
    }>("/collaboration/overview"),
  memoryList: () =>
    runtimeFetch<{
      memories: Array<{
        workflowId: string;
        templateId: string;
        status: string;
        contextKeys: string[];
        artifactCount: number;
      }>;
    }>("/memory"),
  memory: (id: string) => runtimeFetch<Record<string, unknown>>(`/memory/${id}`),
  timeline: (params?: { workflowId?: string; agentId?: string }) => {
    const sp = new URLSearchParams();
    if (params?.workflowId) sp.set("workflowId", params.workflowId);
    if (params?.agentId) sp.set("agentId", params.agentId);
    sp.set("limit", "200");
    return runtimeFetch<{
      events: Array<{
        id: string;
        at: string;
        type: string;
        workflowId?: string;
        agentId?: string;
        durationMs?: number;
        message?: string;
        error?: string;
      }>;
    }>(`/timeline?${sp.toString()}`);
  },
  queue: () =>
    runtimeFetch<{
      totalQueued: number;
      queues: Array<{
        agentId: string;
        name: string;
        status: string;
        queueLength: number;
        runningTask: string | null;
        avgResponseMs: number;
      }>;
    }>("/queue"),
  tasks: () =>
    runtimeFetch<{
      running: Array<{
        workflowId: string;
        workflowName: string;
        stepId: string;
        agentId: string;
        status: string;
        durationMs?: number;
        error?: string;
      }>;
      completed: Array<{
        workflowId: string;
        workflowName: string;
        stepId: string;
        agentId: string;
        status: string;
        durationMs?: number;
        error?: string;
      }>;
      failed: Array<{
        workflowId: string;
        workflowName: string;
        stepId: string;
        agentId: string;
        status: string;
        durationMs?: number;
        error?: string;
      }>;
    }>("/tasks"),
  events: (q?: string) =>
    runtimeFetch<{ events: EventDto[] }>(
      `/events?limit=200${q ? `&q=${encodeURIComponent(q)}` : ""}`,
    ),
  logs: (params?: { level?: string; q?: string }) => {
    const sp = new URLSearchParams();
    if (params?.level) sp.set("level", params.level);
    if (params?.q) sp.set("q", params.q);
    sp.set("limit", "300");
    return runtimeFetch<{ logs: LogDto[] }>(`/logs?${sp.toString()}`);
  },
  agents: () => runtimeFetch<{ agents: AgentDto[] }>("/agents"),
  agentsStatus: () =>
    runtimeFetch<{
      orchestrator: {
        health: string;
        agents: number;
        runningTasks: number;
        queueSize: number;
        liveStatus: string;
      };
      agents: AgentDto[];
    }>("/agents/status"),
  agentLogs: (params?: { agentId?: string; level?: string }) => {
    const sp = new URLSearchParams();
    if (params?.agentId) sp.set("agentId", params.agentId);
    if (params?.level) sp.set("level", params.level);
    sp.set("limit", "200");
    return runtimeFetch<{ logs: AgentLogDto[] }>(`/agents/logs?${sp.toString()}`);
  },
  agentMetrics: () =>
    runtimeFetch<{
      tasksCompleted: number;
      successes: number;
      errors: number;
      avgResponseTimeMs: number;
      agents: Record<string, unknown>;
    }>("/agents/metrics"),
  runAgent: (body: {
    agentId: string;
    type?: string;
    task?: string;
    payload?: unknown;
  }) =>
    runtimeFetch<Record<string, unknown>>("/agents/run", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  orchestratorTask: (body: {
    task?: string;
    type?: string;
    payload?: unknown;
    preferredAgent?: string;
    capability?: string;
  }) =>
    runtimeFetch<Record<string, unknown>>("/orchestrator/task", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  providers: () =>
    runtimeFetch<{
      gateway: {
        health: string;
        providers: number;
        connected: number;
        currentRequests: number;
      };
      providers: ProviderDto[];
      metrics: {
        activeConnections: number;
        avgResponseTimeMs: number;
        successes: number;
        errors: number;
        totalRequests: number;
      };
    }>("/providers"),
  providerStatus: () => runtimeFetch<Record<string, unknown>>("/providers/status"),
  providerCapabilities: () =>
    runtimeFetch<{ capabilities: Record<string, Array<{ id: string; description: string }>> }>(
      "/providers/capabilities",
    ),
  connectProvider: (providerId?: string) =>
    runtimeFetch<{ providers: ProviderDto[] }>("/providers/connect", {
      method: "POST",
      body: JSON.stringify(providerId ? { providerId } : {}),
    }),
  disconnectProvider: (providerId?: string) =>
    runtimeFetch<{ providers: ProviderDto[] }>("/providers/disconnect", {
      method: "POST",
      body: JSON.stringify(providerId ? { providerId } : {}),
    }),
  executeProvider: (body: {
    providerId?: string;
    preferredAlias?: string;
    capability: string;
    payload?: unknown;
  }) =>
    runtimeFetch<Record<string, unknown>>("/providers/execute", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  chatStatus: () =>
    runtimeFetch<{
      id: string;
      name: string;
      health: string;
      voiceReady: boolean;
      queue: {
        total: number;
        queued: number;
        running: number;
        done: number;
        failed: number;
      };
      currentPrompt: string | null;
      currentTask: ChatTaskDto | null;
      currentProvider: string;
      currentAgent: string | null;
      generatedFiles: string[];
      sessionId: string;
    }>("/chat/status"),
  chatTasks: () =>
    runtimeFetch<{
      queue: {
        total: number;
        queued: number;
        running: number;
        waiting: number;
        review: number;
        done: number;
        failed: number;
        cancelled: number;
      };
      tasks: ChatTaskDto[];
    }>("/chat/tasks"),
  chatHistory: (limit = 100) =>
    runtimeFetch<{
      history: Array<{
        id: string;
        at: string;
        prompt: string;
        provider: string;
        status: string;
        durationMs?: number;
        taskId?: string;
        agentId?: string;
      }>;
    }>(`/chat/history?limit=${limit}`),
  chatSession: (id?: string) =>
    runtimeFetch<{
      session: {
        id: string;
        conversation: Array<{ role: string; content: string; at: string }>;
        generatedFiles: string[];
        affectedModules: string[];
        previousPrompts: string[];
        architectureDecisions: string[];
        projectContext: Record<string, unknown>;
        taskIds: string[];
      };
    }>(id ? `/chat/session?id=${encodeURIComponent(id)}` : "/chat/session"),
  chatCreateTask: (body: {
    prompt: string;
    autoRun?: boolean;
    provider?: string;
    sessionId?: string;
  }) =>
    runtimeFetch<{ task: ChatTaskDto }>("/chat/task", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  chatRun: (taskId?: string) =>
    runtimeFetch<{ task: ChatTaskDto }>("/chat/run", {
      method: "POST",
      body: JSON.stringify(taskId ? { taskId } : {}),
    }),
  chatCancel: (taskId: string) =>
    runtimeFetch<{ task: ChatTaskDto }>("/chat/cancel", {
      method: "POST",
      body: JSON.stringify({ taskId }),
    }),
  chatRollback: (taskId: string) =>
    runtimeFetch<{ task: ChatTaskDto }>("/chat/rollback", {
      method: "POST",
      body: JSON.stringify({ taskId }),
    }),
  voiceStatus: () =>
    runtimeFetch<{
      id: string;
      name: string;
      health: string;
      implemented: boolean;
      microphone: {
        recording: boolean;
        permissionGranted: boolean;
        voiceDetected: boolean;
      };
      session: { id: string; state: string; active: boolean } | null;
      speechProvider: string;
      currentAgent: string | null;
      wakeWord: string;
      lastCommand: {
        text: string;
        intent: string;
        confidence: number;
        status: string;
        responseText?: string;
      } | null;
    }>("/voice/status"),
  voiceHistory: (limit = 100) =>
    runtimeFetch<{
      history: Array<{
        id: string;
        at: string;
        text: string;
        intent: string;
        confidence: number;
        status: string;
        provider: string;
        responseText?: string;
      }>;
    }>(`/voice/history?limit=${limit}`),
  voiceSettings: () =>
    runtimeFetch<{
      settings: {
        language: string;
        microphoneId: string;
        wakeWord: string;
        wakeWordEnabled: boolean;
        voiceProvider: string;
        speechProvider: string;
        ttsProvider: string;
        autoExecute: boolean;
        pushToTalk: boolean;
        continuousListening: boolean;
        voiceSpeed: number;
        voiceVolume: number;
      };
    }>("/voice/settings"),
  voiceUpdateSettings: (patch: Record<string, unknown>) =>
    runtimeFetch<{ settings: Record<string, unknown> }>("/voice/settings", {
      method: "POST",
      body: JSON.stringify(patch),
    }),
  voiceStart: (language?: string) =>
    runtimeFetch<{ session: unknown }>("/voice/start", {
      method: "POST",
      body: JSON.stringify(language ? { language } : {}),
    }),
  voiceStop: (sessionId?: string) =>
    runtimeFetch<{ session: unknown }>("/voice/stop", {
      method: "POST",
      body: JSON.stringify(sessionId ? { sessionId } : {}),
    }),
  voiceProcess: (body: {
    text?: string;
    audioBase64?: string;
    bypassWakeWord?: boolean;
    autoExecute?: boolean;
  }) =>
    runtimeFetch<{
      intent: string;
      confidence: number;
      executed: boolean;
      responseText: string;
      chatTaskId?: string;
      transcription: { text: string; confidence: number; providerId: string };
      command: { status: string };
      speech?: { audioBase64: string };
    }>("/voice/process", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  mcpStatus: () =>
    runtimeFetch<{
      id: string;
      name: string;
      health: string;
      enabled: boolean;
      transport: string;
      runtimeBound: boolean;
      connectedClients: number;
      tools: number;
      resources: number;
      prompts: number;
      requests: number;
      errors: number;
      permissions: string[];
      sessions: Array<{
        id: string;
        clientId: string;
        permission: string;
        requestCount: number;
        active: boolean;
      }>;
      recentLogs: Array<{ id: string; kind: string; message: string }>;
    }>("/mcp/status"),
  mcpTools: () =>
    runtimeFetch<{
      tools: Array<{ name: string; description: string; permission: string }>;
    }>("/mcp/tools"),
  mcpResources: () =>
    runtimeFetch<{
      resources: Array<{
        uri: string;
        name: string;
        description: string;
        permission: string;
      }>;
    }>("/mcp/resources"),
  mcpPrompts: () =>
    runtimeFetch<{
      prompts: Array<{ name: string; description: string; permission: string }>;
    }>("/mcp/prompts"),
  mcpConnect: (clientId?: string) =>
    runtimeFetch<{ session: unknown }>("/mcp/connect", {
      method: "POST",
      body: JSON.stringify({ clientId: clientId ?? "control-center" }),
    }),
  executionStatus: () =>
    runtimeFetch<{
      id: string;
      name: string;
      health: string;
      currentPlan: {
        id: string;
        status: string;
        progress: number;
        blockedCount: number;
        tasks: Array<{
          id: string;
          title: string;
          role: string;
          agentId: string;
          status: string;
          progress: number;
        }>;
        graph: {
          nodes: Array<{ id: string; role: string; status: string }>;
          edges: Array<{ from: string; to: string }>;
        };
      } | null;
      runningAgents: string[];
      blockedTasks: string[];
      logs: string[];
      lastReport: {
        summary: string;
        buildStatus: string;
        testStatus: string;
        completedTasks: string[];
        failedTasks: string[];
      } | null;
    }>("/execution/status"),
  executionHistory: (limit = 50) =>
    runtimeFetch<{
      history: Array<{
        id: string;
        planId: string;
        status: string;
        progress: number;
        at: string;
      }>;
    }>(`/execution/history?limit=${limit}`),
  executionReport: (planId?: string) =>
    runtimeFetch<{
      report: {
        summary: string;
        buildStatus: string;
        testStatus: string;
        completedTasks: string[];
        failedTasks: string[];
        warnings: string[];
        filesChanged: string[];
        nextRecommendations: string[];
      };
    }>(
      planId
        ? `/execution/report?planId=${encodeURIComponent(planId)}`
        : "/execution/report",
    ),
  executionPlan: (body: {
    specification?: Record<string, unknown>;
    autoRun?: boolean;
    mission?: string;
    objective?: string;
    requirements?: string[];
    files?: string[];
    modules?: string[];
    tests?: string[];
    acceptanceCriteria?: string[];
  }) =>
    runtimeFetch<{
      plan: { id: string; status: string; tasks: unknown[] };
      report: { summary: string } | null;
    }>("/execution/plan", {
      method: "POST",
      body: JSON.stringify(body),
    }),
  stopService: (id: string) =>
    runtimeFetch<{ id: string; lifecycle: string }>(`/services/${id}/stop`, {
      method: "POST",
    }),
  restartService: (id: string) =>
    runtimeFetch<{ id: string; lifecycle: string }>(`/services/${id}/restart`, {
      method: "POST",
    }),
  runWorkflow: (id: string) =>
    runtimeFetch<Record<string, unknown>>(`/workflow/${id}/run`, { method: "POST" }),
  pauseWorkflow: (id: string) =>
    runtimeFetch<Record<string, unknown>>(`/workflow/instances/${id}/pause`, {
      method: "POST",
    }),
  resumeWorkflow: (id: string) =>
    runtimeFetch<Record<string, unknown>>(`/workflow/instances/${id}/resume`, {
      method: "POST",
    }),
  cancelWorkflow: (id: string) =>
    runtimeFetch<Record<string, unknown>>(`/workflow/instances/${id}/cancel`, {
      method: "POST",
    }),
  workflowHistory: (id: string) =>
    runtimeFetch<{ history: unknown[] }>(`/workflow/instances/${id}/history`),
};

export interface ChatTaskDto {
  id: string;
  title: string;
  description: string;
  kind: string;
  status: string;
  priority: number;
  provider: string;
  preferredAgent: string;
  rawPrompt: string;
  files: string[];
  generatedFiles: string[];
  durationMs?: number;
  error?: string;
  createdAt: string;
  updatedAt: string;
  context: {
    project: string;
    repository: string;
    sprint: string;
    affectedModules: string[];
    relatedFiles: string[];
    dependencies: string[];
  };
}
