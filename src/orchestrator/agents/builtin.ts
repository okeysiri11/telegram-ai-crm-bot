import { BaseAgent } from "../BaseAgent.js";
import type { AgentTaskInput, ProviderId } from "../types.js";

export class DeveloperAgent extends BaseAgent {
  constructor() {
    super({
      id: "agent.developer",
      name: "Developer Agent",
      role: "developer",
      provider: "cursor",
      memory: "shared-workflow",
      version: "3.0.0",
      skills: ["implement", "refactor", "fix"],
      capabilities: [
        { id: "code.implement", description: "Implement features and fixes" },
        { id: "code.review", description: "Prepare code for review" },
      ],
    });
  }

  protected handle(input: AgentTaskInput, provider: ProviderId): unknown {
    return {
      agent: this.name,
      role: this.role,
      action: "implement",
      provider,
      summary: `Implemented solution for ${input.type}`,
      input: input.payload,
    };
  }
}

export class ResearchAgent extends BaseAgent {
  constructor() {
    super({
      id: "agent.research",
      name: "Research Agent",
      role: "research",
      provider: "openai",
      memory: "shared-workflow",
      version: "3.0.0",
      skills: ["analyze", "summarize", "domain-research"],
      capabilities: [
        { id: "research.analyze", description: "Research & analysis" },
        { id: "research.summarize", description: "Summaries" },
      ],
    });
  }

  protected handle(input: AgentTaskInput, provider: ProviderId): unknown {
    return {
      agent: this.name,
      role: this.role,
      action: "research",
      provider,
      summary: `Research findings for ${input.type}`,
      input: input.payload,
    };
  }
}

export class BusinessAgent extends BaseAgent {
  constructor() {
    super({
      id: "agent.business",
      name: "Business Agent",
      role: "business",
      provider: "openai",
      memory: "shared-workflow",
      version: "3.0.0",
      skills: ["requirements", "ops", "roi"],
      capabilities: [
        { id: "business.plan", description: "Business planning" },
        { id: "business.ops", description: "Operations decisions" },
      ],
    });
  }

  protected handle(input: AgentTaskInput, provider: ProviderId): unknown {
    return {
      agent: this.name,
      role: this.role,
      action: "plan",
      provider,
      summary: `Business plan for ${input.type}`,
      input: input.payload,
    };
  }
}

export class ArchitectAgent extends BaseAgent {
  constructor() {
    super({
      id: "agent.architect",
      name: "Architect Agent",
      role: "architect",
      provider: "claude",
      memory: "shared-workflow",
      version: "3.0.0",
      skills: ["architecture", "boundaries", "adr"],
      capabilities: [
        { id: "architecture.design", description: "System architecture" },
        { id: "architecture.review", description: "Architecture review" },
      ],
    });
  }

  protected handle(input: AgentTaskInput, provider: ProviderId): unknown {
    return {
      agent: this.name,
      role: this.role,
      action: "architect",
      provider,
      summary: `Architecture for ${input.type}`,
      input: input.payload,
    };
  }
}

export class ReviewerAgent extends BaseAgent {
  constructor() {
    super({
      id: "agent.reviewer",
      name: "Reviewer Agent",
      role: "reviewer",
      provider: "claude",
      memory: "shared-workflow",
      version: "3.0.0",
      skills: ["review", "quality", "standards"],
      capabilities: [
        { id: "review.code", description: "Code/content review" },
        { id: "review.approve", description: "Approval recommendation" },
      ],
    });
  }

  protected handle(input: AgentTaskInput, provider: ProviderId): unknown {
    return {
      agent: this.name,
      role: this.role,
      action: "review",
      provider,
      summary: `Review completed for ${input.type}`,
      approved: true,
      input: input.payload,
    };
  }
}

export class QaAgent extends BaseAgent {
  constructor() {
    super({
      id: "agent.qa",
      name: "QA Agent",
      role: "qa",
      provider: "local",
      memory: "shared-workflow",
      version: "3.0.0",
      skills: ["test", "regression", "acceptance"],
      capabilities: [
        { id: "qa.test", description: "Test execution" },
        { id: "qa.validate", description: "Acceptance validation" },
      ],
    });
  }

  protected handle(input: AgentTaskInput, provider: ProviderId): unknown {
    return {
      agent: this.name,
      role: this.role,
      action: "qa",
      provider,
      summary: `QA passed for ${input.type}`,
      passed: true,
      input: input.payload,
    };
  }
}

export class AutomationAgent extends BaseAgent {
  constructor() {
    super({
      id: "agent.automation",
      name: "Automation Agent",
      role: "automation",
      provider: "github",
      memory: "shared-workflow",
      version: "3.0.0",
      skills: ["deploy", "pipeline", "publish"],
      capabilities: [
        { id: "automation.deploy", description: "Deploy & release" },
        { id: "automation.publish", description: "Publish artifacts" },
      ],
    });
  }

  protected handle(input: AgentTaskInput, provider: ProviderId): unknown {
    return {
      agent: this.name,
      role: this.role,
      action: "automation",
      provider,
      summary: `Automation completed for ${input.type}`,
      input: input.payload,
    };
  }
}

/** Collaboration agent set (7) — auto-registered at Orchestrator start. */
export function createBuiltinAgents() {
  return [
    new DeveloperAgent(),
    new ResearchAgent(),
    new BusinessAgent(),
    new ArchitectAgent(),
    new ReviewerAgent(),
    new QaAgent(),
    new AutomationAgent(),
  ] as const;
}
