import { motion } from "../tokens";

export const animationEngine = {
  durations: motion,
  presets: {
    fade: "eds-anim-fade",
    slide: "eds-anim-slide",
    scale: "eds-anim-scale",
    collapse: "eds-anim-collapse",
    expand: "eds-anim-expand",
    pageTransition: "eds-anim-page",
    loading: "eds-anim-loading",
    skeleton: "eds-anim-skeleton",
    micro: "eds-anim-micro",
  },
} as const;
