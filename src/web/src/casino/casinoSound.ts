/** Optional casino sound layer. Default muted. No required audio assets. */

class CasinoSound {
  muted = true;
  private ctx: AudioContext | null = null;

  setMuted(next: boolean) {
    this.muted = next;
  }

  private context(): AudioContext | null {
    if (this.muted || typeof window === "undefined") return null;
    const Ctor = window.AudioContext || (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
    if (!Ctor) return null;
    if (!this.ctx) this.ctx = new Ctor();
    return this.ctx;
  }

  private beep(freq: number, duration = 0.08, gain = 0.04) {
    const ctx = this.context();
    if (!ctx) return;
    const osc = ctx.createOscillator();
    const node = ctx.createGain();
    osc.frequency.value = freq;
    node.gain.value = gain;
    osc.connect(node);
    node.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + duration);
  }

  chip() {
    this.beep(420, 0.05, 0.03);
  }

  spin() {
    this.beep(180, 0.2, 0.03);
  }

  tick() {
    this.beep(640, 0.03, 0.02);
  }

  win() {
    this.beep(520, 0.12, 0.04);
  }
}

export const casinoSound = new CasinoSound();
