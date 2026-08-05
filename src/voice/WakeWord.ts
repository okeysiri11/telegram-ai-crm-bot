/**
 * Configurable wake-word detector. Default phrase is "Hey ADOS" but never hardcoded in logic.
 */
export class WakeWord {
  private phrase: string;
  private enabled: boolean;

  constructor(phrase: string, enabled = true) {
    this.phrase = normalize(phrase);
    this.enabled = enabled;
    if (!this.phrase) throw new Error("Wake word phrase must not be empty");
  }

  getPhrase(): string {
    return this.phrase;
  }

  isEnabled(): boolean {
    return this.enabled;
  }

  configure(phrase: string, enabled?: boolean): void {
    const next = normalize(phrase);
    if (!next) throw new Error("Wake word phrase must not be empty");
    this.phrase = next;
    if (enabled !== undefined) this.enabled = enabled;
  }

  /**
   * Returns whether the transcript contains the configured wake word.
   * When disabled, always matches (pass-through).
   */
  match(transcript: string): { matched: boolean; remainder: string } {
    if (!this.enabled) {
      return { matched: true, remainder: transcript.trim() };
    }
    const text = transcript.trim();
    const lower = text.toLowerCase();
    const phrase = this.phrase.toLowerCase();
    const idx = lower.indexOf(phrase);
    if (idx < 0) return { matched: false, remainder: text };
    const after = text.slice(idx + phrase.length).replace(/^[,.\s]+/, "");
    return { matched: true, remainder: after || text };
  }
}

function normalize(phrase: string): string {
  return phrase.trim().replace(/\s+/g, " ");
}

export function createWakeWord(phrase: string, enabled = true): WakeWord {
  return new WakeWord(phrase, enabled);
}
