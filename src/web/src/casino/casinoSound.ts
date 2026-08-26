/** Optional casino sound layer. Default muted. No autoplay. No looping ambience. */

export type CasinoRoomTone =
  | "entrance"
  | "lobby"
  | "roulette"
  | "blackjack"
  | "slots"
  | "poker"
  | "vip"
  | "bar"
  | "restaurant"
  | null;

class CasinoSound {
  muted = true;
  room: CasinoRoomTone = null;
  private ctx: AudioContext | null = null;

  setMuted(next: boolean) {
    this.muted = next;
    if (next) this.stopAmbience();
  }

  setRoom(room: CasinoRoomTone) {
    this.room = room;
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

  card() {
    this.beep(880, 0.04, 0.02);
  }

  spin() {
    this.beep(180, 0.2, 0.03);
  }

  slotStop() {
    this.beep(240, 0.08, 0.03);
  }

  tick() {
    this.beep(640, 0.03, 0.02);
  }

  hover() {
    this.beep(720, 0.04, 0.015);
  }

  click() {
    this.beep(380, 0.07, 0.03);
  }

  door() {
    this.beep(140, 0.28, 0.035);
    this.beep(220, 0.18, 0.02);
  }

  win() {
    this.beep(520, 0.12, 0.04);
  }

  /** Reserved. Never starts without unmute + future user gesture. */
  startAmbience() {
    return;
  }

  stopAmbience() {
    return;
  }
}

export const casinoSound = new CasinoSound();
