import { empireOfPlayer } from '../empires';
import { goalCitiesAt, goalCityBannerPart } from '../goalCities';
import type { CityView, PlayerView } from '../types';

/** The parts of a drawn banner, in their visual order: a goal city's seal (left end), population, owner, name, the capital's star (right end). */
export function bannerTooltip(view: Pick<PlayerView, 'players'> & Partial<Pick<PlayerView, 'colonias' | 'royal_tombs'>>, city: CityView): string {
  const goals = goalCitiesAt(view, city.id).map((g) => goalCityBannerPart(view, g));
  const parts = [...goals, `Population ${city.visible ? city.population : 'unknown'}`, empireOfPlayer(view, city.owner), city.name];
  if (city.original_capital) {
    const founder = empireOfPlayer(view, city.original_capital_of ?? city.owner);
    parts.push(`Original capital of ${founder} · a rival scores 1 VP while it holds it`);
  }
  return parts.join(' · ');
}
