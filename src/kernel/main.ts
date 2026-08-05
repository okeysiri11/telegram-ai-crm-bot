import { BootLoader, createKernel } from "./index.js";
import {
  createRuntimeServer,
  PLATFORM_VERSION,
} from "./runtime/index.js";
import { createOrchestratorService } from "@ados/orchestrator";
import { createProviderGatewayService } from "@ados/providers";
import { createChatBridgeService } from "@ados/chat-bridge";
import { createVoiceService } from "@ados/voice";
import { createMCPService } from "@ados/mcp";
import { createExecutionService } from "@ados/execution";

function printBanner(
  services: number,
  httpUrl: string,
  agents: number,
  providers: number,
): void {
  const lines = [
    "=================================",
    "ADOS Enterprise Operating System",
    `Version ${PLATFORM_VERSION}`,
    "",
    "Kernel ............... OK",
    "Event Bus ............ OK",
    "Service Mesh ......... OK",
    "Workflow Engine ...... OK",
    "AI Orchestrator ...... OK",
    "Collaboration Engine . OK",
    "Provider Gateway ..... OK",
    "ChatGPT Bridge ....... OK",
    "Voice Module ......... OK",
    "MCP Gateway .......... OK",
    "Execution Planner .... OK",
    "Runtime Server ....... OK",
    "",
    `Agents registered: ${agents}`,
    `Providers connected: ${providers}`,
    "Multi-Agent Collaboration: READY",
    "ChatGPT → Cursor Bridge: READY",
    "Enterprise Voice: READY",
    "MCP Gateway: READY",
    "Execution Planner: READY",
    "",
    "HTTP:",
    httpUrl,
    "",
    "System Status:",
    "READY",
    "=================================",
  ];
  for (const line of lines) {
    console.log(line);
  }
  void services;
}

async function main(): Promise<void> {
  console.log(
    "[ADOS] creating Kernel + Orchestrator + Providers + Chat Bridge + Voice + MCP + Execution…",
  );
  const providerGatewayService = createProviderGatewayService();
  const orchestratorService = createOrchestratorService();

  orchestratorService.orchestrator.setProviderGateway(
    providerGatewayService.gateway,
  );

  const chatBridgeService = createChatBridgeService({
    orchestrator: orchestratorService.orchestrator,
    gateway: providerGatewayService.gateway,
  });

  const voiceService = createVoiceService({
    bridge: chatBridgeService.bridge,
  });

  const mcpService = createMCPService({ loadDiskConfig: true });

  const executionService = createExecutionService({
    orchestrator: orchestratorService.orchestrator,
  });

  const kernel = createKernel({
    config: {
      environment: "production",
      failFast: true,
    },
    bootLoader: new BootLoader({
      extraServices: [
        providerGatewayService,
        orchestratorService,
        chatBridgeService,
        voiceService,
        mcpService,
        executionService,
      ],
    }),
  });

  console.log(
    "[ADOS] starting Kernel / Mesh / Workflow / Providers / Orchestrator / Chat Bridge / Voice / MCP / Execution…",
  );
  await kernel.start();

  console.log("[ADOS] starting Runtime Server…");
  const runtime = createRuntimeServer(kernel, {
    host: process.env["ADOS_HOST"] ?? "0.0.0.0",
    port: Number(process.env["ADOS_PORT"] ?? 3000),
    platformVersion: PLATFORM_VERSION,
  });
  await runtime.start();

  const agentCount = orchestratorService.orchestrator.listAgents().length;
  const providerCount = providerGatewayService.gateway.getStatus().connected;
  printBanner(
    kernel.registry.list().length,
    runtime.url,
    agentCount,
    providerCount,
  );
}

main().catch((error: unknown) => {
  const message =
    error instanceof Error ? `${error.message}\n${error.stack ?? ""}` : String(error);
  console.error("ADOS boot failed:");
  console.error(message);
  process.exitCode = 1;
});
