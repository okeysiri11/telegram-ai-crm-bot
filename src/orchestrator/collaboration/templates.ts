import type { WorkflowTemplate } from "./types.js";

const seq = (
  id: string,
  name: string,
  description: string,
  category: string,
  steps: WorkflowTemplate["steps"],
  estimatedMs: number,
): WorkflowTemplate => ({
  id,
  name,
  description,
  category,
  estimatedMs,
  steps,
});

/**
 * Enterprise workflow templates — multi-agent collaboration blueprints.
 */
export const WORKFLOW_TEMPLATES: readonly WorkflowTemplate[] = [
  seq(
    "tpl.software_development",
    "Software Development",
    "Architect → Research → Business → Developer → QA → Reviewer",
    "engineering",
    [
      { id: "architect", name: "Architecture", agentId: "agent.architect", estimatedMs: 800 },
      { id: "research", name: "Research", agentId: "agent.research", estimatedMs: 700 },
      { id: "business", name: "Business", agentId: "agent.business", estimatedMs: 600 },
      { id: "develop", name: "Implement", agentId: "agent.developer", estimatedMs: 1200 },
      { id: "qa", name: "QA", agentId: "agent.qa", estimatedMs: 700 },
      { id: "review", name: "Review", agentId: "agent.reviewer", estimatedMs: 600 },
    ],
    4600,
  ),
  seq(
    "tpl.bug_fix",
    "Bug Fix",
    "Research → Developer → QA → Reviewer",
    "engineering",
    [
      { id: "research", name: "Triage", agentId: "agent.research", estimatedMs: 500 },
      { id: "develop", name: "Fix", agentId: "agent.developer", estimatedMs: 900 },
      { id: "qa", name: "Verify", agentId: "agent.qa", estimatedMs: 500 },
      { id: "review", name: "Review", agentId: "agent.reviewer", estimatedMs: 400 },
    ],
    2300,
  ),
  seq(
    "tpl.code_review",
    "Code Review",
    "Developer → Reviewer → Architect",
    "engineering",
    [
      { id: "develop", name: "Prepare diff", agentId: "agent.developer", estimatedMs: 400 },
      { id: "review", name: "Review", agentId: "agent.reviewer", estimatedMs: 700 },
      { id: "architect", name: "Architecture check", agentId: "agent.architect", estimatedMs: 500 },
    ],
    1600,
  ),
  seq(
    "tpl.architecture_review",
    "Architecture Review",
    "Architect → Research → Reviewer",
    "architecture",
    [
      { id: "architect", name: "Design", agentId: "agent.architect", estimatedMs: 800 },
      { id: "research", name: "Validate", agentId: "agent.research", estimatedMs: 600 },
      { id: "review", name: "Review", agentId: "agent.reviewer", estimatedMs: 500 },
    ],
    1900,
  ),
  seq(
    "tpl.research",
    "Research",
    "Research → Business → Architect",
    "research",
    [
      { id: "research", name: "Investigate", agentId: "agent.research", estimatedMs: 900 },
      { id: "business", name: "Business impact", agentId: "agent.business", estimatedMs: 500 },
      { id: "architect", name: "Technical implications", agentId: "agent.architect", estimatedMs: 500 },
    ],
    1900,
  ),
  seq(
    "tpl.documentation",
    "Documentation",
    "Research → Developer → Reviewer → Automation",
    "docs",
    [
      { id: "research", name: "Gather", agentId: "agent.research", estimatedMs: 600 },
      { id: "develop", name: "Draft", agentId: "agent.developer", estimatedMs: 700 },
      { id: "review", name: "Review", agentId: "agent.reviewer", estimatedMs: 400 },
      { id: "automation", name: "Publish", agentId: "agent.automation", estimatedMs: 300 },
    ],
    2000,
  ),
  seq(
    "tpl.crm_generation",
    "CRM Generation",
    "Architect → Research → Business → Developer → QA → Reviewer",
    "vertical",
    [
      { id: "architect", name: "CRM architecture", agentId: "agent.architect", estimatedMs: 800 },
      { id: "research", name: "Domain research", agentId: "agent.research", estimatedMs: 700 },
      { id: "business", name: "CRM requirements", agentId: "agent.business", estimatedMs: 700 },
      { id: "develop", name: "Build CRM modules", agentId: "agent.developer", estimatedMs: 1400 },
      { id: "qa", name: "QA CRM", agentId: "agent.qa", estimatedMs: 700 },
      { id: "review", name: "Final review", agentId: "agent.reviewer", estimatedMs: 600 },
    ],
    4900,
  ),
  seq(
    "tpl.landing_page",
    "Landing Page",
    "Business → Research → Developer → QA → Reviewer",
    "marketing",
    [
      { id: "business", name: "Brief", agentId: "agent.business", estimatedMs: 500 },
      { id: "research", name: "Audience", agentId: "agent.research", estimatedMs: 500 },
      { id: "develop", name: "Build page", agentId: "agent.developer", estimatedMs: 1000 },
      { id: "qa", name: "QA", agentId: "agent.qa", estimatedMs: 400 },
      { id: "review", name: "Review", agentId: "agent.reviewer", estimatedMs: 400 },
    ],
    2800,
  ),
  seq(
    "tpl.presentation",
    "Presentation",
    "Research → Business → Developer → Reviewer",
    "content",
    [
      { id: "research", name: "Content research", agentId: "agent.research", estimatedMs: 600 },
      { id: "business", name: "Narrative", agentId: "agent.business", estimatedMs: 500 },
      { id: "develop", name: "Slides", agentId: "agent.developer", estimatedMs: 800 },
      { id: "review", name: "Polish", agentId: "agent.reviewer", estimatedMs: 400 },
    ],
    2300,
  ),
  seq(
    "tpl.enterprise_report",
    "Enterprise Report",
    "Research → Business → Architect → Reviewer → Automation",
    "analytics",
    [
      { id: "research", name: "Data research", agentId: "agent.research", estimatedMs: 800 },
      { id: "business", name: "Insights", agentId: "agent.business", estimatedMs: 600 },
      { id: "architect", name: "Structure", agentId: "agent.architect", estimatedMs: 500 },
      { id: "review", name: "Review", agentId: "agent.reviewer", estimatedMs: 400 },
      { id: "automation", name: "Distribute", agentId: "agent.automation", estimatedMs: 300 },
    ],
    2600,
  ),
];

export function listWorkflowTemplates(): readonly WorkflowTemplate[] {
  return WORKFLOW_TEMPLATES;
}

export function getWorkflowTemplate(id: string): WorkflowTemplate | undefined {
  return WORKFLOW_TEMPLATES.find((t) => t.id === id);
}
