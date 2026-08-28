/** Local visual assets for facade cards. Paths can be swapped without changing card logic. */
export const CARD_VISUALS: Record<string, { src: string; position: string; alt: string }> = {
  roulette: { src: "/casino/roulette/wheel.svg", position: "center 42%", alt: "Рулетка Odessa Prime" },
  blackjack: { src: "/casino/blackjack/felt.svg", position: "center", alt: "Blackjack стол" },
  poker: { src: "/casino/poker/felt.svg", position: "center", alt: "Покерный стол" },
  slots: { src: "/casino/slots/cabinet.svg", position: "center 18%", alt: "Игровой автомат" },
  live: { src: "/casino/entrance/hall.svg", position: "center", alt: "Live-казино" },
  tournaments: { src: "/casino/vip/lounge.svg", position: "center", alt: "Турниры" },
};
