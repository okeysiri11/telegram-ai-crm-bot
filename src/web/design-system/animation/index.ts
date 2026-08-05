import { motion } from "../tokens";

/** Motion Design Language presets — EP-03 (CSS class names only). */
export const animationEngine = {
  durations: motion,
  presets: {
    fade: "eds-anim-fade",
    slide: "eds-anim-slide",
    scale: "eds-anim-scale",
    collapse: "eds-anim-collapse",
    expand: "eds-anim-expand",
    pageTransition: "edm-page",
    loading: "eds-anim-loading",
    skeleton: "edm-skeleton",
    micro: "eds-anim-micro",
    stagger: "edm-stagger",
    cardEnter: "edm-card-enter",
    cardRefresh: "edm-card-refresh",
    aiLive: "edm-ai-live",
    aiAnalyzing: "edm-ai-analyzing",
    aiSuggest: "edm-ai-suggest",
    stream: "edm-stream-bar",
    refreshing: "edm-refreshing",
    partialUpdate: "edm-partial-update",
    kpiUpdate: "edm-kpi",
    toast: "edm-toast",
    overlay: "edm-overlay-panel",
  },
  rules: {
    maxContinuousLoops: ["edm-ai-live", "edm-bg-update", "edm-stream-bar", "ec-ai-dot"],
    forbidden: ["bounce", "spin-on-page", "parallax-scroll", "autoplay-carousel"],
  },
} as const;
