/**
 * Conversation / UI context remembered across voice turns.
 */
export interface VoiceContextState {
  currentPage: string;
  currentProject: string;
  currentSprint: string;
  selectedModule: string | null;
  selectedDocument: string | null;
  currentProvider: string;
  selectedAgent: string | null;
  lastIntent: string | null;
  conversation: Array<{
    role: "user" | "assistant" | "system";
    content: string;
    at: string;
  }>;
}

const DEFAULT_CONTEXT: VoiceContextState = {
  currentPage: "/dashboard",
  currentProject: "ADOS Enterprise OS",
  currentSprint: "ADOS OS 4.1",
  selectedModule: null,
  selectedDocument: null,
  currentProvider: "provider.cursor",
  selectedAgent: null,
  lastIntent: null,
  conversation: [],
};

export class VoiceContext {
  private state: VoiceContextState;

  constructor(initial?: Partial<VoiceContextState>) {
    this.state = {
      ...DEFAULT_CONTEXT,
      ...initial,
      conversation: [...(initial?.conversation ?? [])],
    };
  }

  get(): Readonly<VoiceContextState> {
    return {
      ...this.state,
      conversation: [...this.state.conversation],
    };
  }

  update(patch: Partial<VoiceContextState>): Readonly<VoiceContextState> {
    const { conversation: _c, ...rest } = patch;
    void _c;
    this.state = { ...this.state, ...rest };
    return this.get();
  }

  appendUser(content: string): void {
    this.state.conversation.push({
      role: "user",
      content,
      at: new Date().toISOString(),
    });
    this.trim();
  }

  appendAssistant(content: string): void {
    this.state.conversation.push({
      role: "assistant",
      content,
      at: new Date().toISOString(),
    });
    this.trim();
  }

  private trim(): void {
    if (this.state.conversation.length > 100) {
      this.state.conversation = this.state.conversation.slice(-100);
    }
  }
}

export function createVoiceContext(
  initial?: Partial<VoiceContextState>,
): VoiceContext {
  return new VoiceContext(initial);
}
