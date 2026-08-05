import type { VoiceIntent } from "./types.js";

export interface IntentMatch {
  readonly intent: VoiceIntent;
  readonly confidence: number;
  readonly entities: Readonly<Record<string, string>>;
}

const PATTERNS: Array<{
  intent: VoiceIntent;
  re: RegExp;
  confidence: number;
  entity?: (m: RegExpMatchArray) => Record<string, string>;
}> = [
  {
    intent: "create_project",
    re: /(?:create|new|start)\s+(?:a\s+)?project(?:\s+(?:called|named)\s+(.+))?/i,
    confidence: 0.92,
    entity: (m) => (m[1] ? { name: m[1].trim() } : {}),
  },
  {
    intent: "create_task",
    re: /(?:create|add|new)\s+(?:a\s+)?task(?:\s+(?:to|for|:)\s+(.+))?/i,
    confidence: 0.9,
    entity: (m) => (m[1] ? { task: m[1].trim() } : {}),
  },
  {
    intent: "open_crm",
    re: /open\s+(?:the\s+)?crm/i,
    confidence: 0.95,
  },
  {
    intent: "open_erp",
    re: /open\s+(?:the\s+)?erp/i,
    confidence: 0.95,
  },
  {
    intent: "open_ai_studio",
    re: /open\s+(?:the\s+)?(?:ai\s+)?studio/i,
    confidence: 0.93,
  },
  {
    intent: "open_marketplace",
    re: /open\s+(?:the\s+)?marketplace/i,
    confidence: 0.93,
  },
  {
    intent: "open_module",
    re: /open\s+(?:the\s+)?(?:module\s+)?([\w\s/-]+)/i,
    confidence: 0.82,
    entity: (m) => (m[1] ? { module: m[1].trim() } : {}),
  },
  {
    intent: "search",
    re: /(?:search|find|look\s+up)\s+(?:for\s+)?(.+)/i,
    confidence: 0.88,
    entity: (m) => (m[1] ? { query: m[1].trim() } : {}),
  },
  {
    intent: "run_workflow",
    re: /(?:run|start|execute)\s+(?:the\s+)?workflow(?:\s+(.+))?/i,
    confidence: 0.9,
    entity: (m) => (m[1] ? { workflow: m[1].trim() } : {}),
  },
  {
    intent: "generate_code",
    re: /(?:generate|write|implement|build)\s+(?:code|feature|component|function)(?:\s+(?:for|to)\s+(.+))?/i,
    confidence: 0.91,
    entity: (m) => (m[1] ? { topic: m[1].trim() } : {}),
  },
  {
    intent: "review_code",
    re: /(?:review|check)\s+(?:the\s+)?code(?:\s+(?:in|for)\s+(.+))?/i,
    confidence: 0.9,
    entity: (m) => (m[1] ? { target: m[1].trim() } : {}),
  },
  {
    intent: "explain_code",
    re: /explain\s+(?:the\s+)?code(?:\s+(?:in|for)\s+(.+))?/i,
    confidence: 0.9,
    entity: (m) => (m[1] ? { target: m[1].trim() } : {}),
  },
  {
    intent: "create_document",
    re: /(?:create|write|draft)\s+(?:a\s+)?(?:document|doc|readme|guide)(?:\s+(?:about|on|for)\s+(.+))?/i,
    confidence: 0.88,
    entity: (m) => (m[1] ? { topic: m[1].trim() } : {}),
  },
  {
    intent: "generate_report",
    re: /(?:generate|create|make)\s+(?:a\s+)?report(?:\s+(?:on|for|about)\s+(.+))?/i,
    confidence: 0.89,
    entity: (m) => (m[1] ? { topic: m[1].trim() } : {}),
  },
  {
    intent: "run_agent",
    re: /(?:run|ask|invoke)\s+(?:the\s+)?(?:agent\s+)?([\w.\s]+?)(?:\s+to\s+(.+))?$/i,
    confidence: 0.86,
    entity: (m) => {
      const out: Record<string, string> = {};
      if (m[1]) out["agent"] = m[1].trim();
      if (m[2]) out["task"] = m[2].trim();
      return out;
    },
  },
  {
    intent: "execute_command",
    re: /(?:execute|run)\s+(?:command\s+)?(.+)/i,
    confidence: 0.8,
    entity: (m) => (m[1] ? { command: m[1].trim() } : {}),
  },
];

/**
 * Maps free-form transcript text to a structured enterprise voice intent.
 */
export class IntentDetector {
  detect(text: string): IntentMatch {
    const trimmed = text.trim();
    if (!trimmed) {
      return { intent: "unknown", confidence: 0, entities: {} };
    }
    for (const p of PATTERNS) {
      const m = trimmed.match(p.re);
      if (m) {
        return {
          intent: p.intent,
          confidence: p.confidence,
          entities: p.entity?.(m) ?? {},
        };
      }
    }
    return {
      intent: "unknown",
      confidence: 0.35,
      entities: { raw: trimmed },
    };
  }
}

export function createIntentDetector(): IntentDetector {
  return new IntentDetector();
}
