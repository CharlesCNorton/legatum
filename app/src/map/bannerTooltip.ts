import { empireOfPlayer } from '../empires';
import { goalCitiesAt, goalCityBannerPart, tombSiteAt, tombSiteLine } from '../goalCities';
import type { CityView, PlayerView } from '../types';

/** The parts of a drawn banner, in their visual order: a goal city's seal (left end), population, owner, name, the capital's star (right end). */
export function bannerTooltip(view: Pick<PlayerView, 'players'> & Partial<Pick<PlayerView, 'me' | 'colonias' | 'royal_tombs' | 'tomb_sites'>>, city: CityView): string {
  const site = tombSiteAt(view, city.id);
  const goals = [...goalCitiesAt(view, city.id).map((g) => goalCityBannerPart(view, g)), ...(site ? [tombSiteLine({ me: view.me ?? -1, players: view.players }, site).replace(/\.$/, '')] : [])];
  const parts = [...goals, `Population ${city.visible ? city.population : 'unknown'}`, empireOfPlayer(view, city.owner), city.name];
  if (city.original_capital) {
    const founder = empireOfPlayer(view, city.original_capital_of ?? city.owner);
    parts.push(`Original capital of ${founder} · a rival scores 1 VP while it holds it`);
  }
  return parts.join(' · ');
}
