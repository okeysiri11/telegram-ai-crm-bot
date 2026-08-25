export type CasinoVenue = {
  venue_id: string;
  slug: string;
  name: string;
  city_building_id: string;
  city_route: string;
  game: string;
  status: string;
  play_money_only: boolean;
  real_money: boolean;
};

export type CasinoLobby = {
  title: string;
  play_money_only: boolean;
  real_money_implemented: boolean;
  venues: CasinoVenue[];
  games: { id: string; name: string; demo: boolean }[];
  city_entry: { building_id: string; route: string; venue_route: string };
};
