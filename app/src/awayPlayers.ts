// Online: the other human players whose computers are not connected right now. Their seats do not hold
// up the turn (the host ends it without them, and their empires get no orders), so the game says who is
// away and asks before a Ready that would end the turn without them.
import type { State } from './store';

export function awayPlayers(s: Pick<State, 'client' | 'net' | 'views' | 'seat'>): string[] {
  if (s.client?.kind !== 'remote' || !s.net || s.net.conn !== 'open') return [];
  const view = s.views?.[s.seat];
  return s.net.seats
    .filter((st) => st.seat !== s.net!.mySeat && !st.connected)
    .filter((st) => view?.players.find((p) => p.id === st.player)?.alive !== false)
    .map((st) => st.name || 'A player');
}

/** "Alice", "Alice and Bo", "Alice, Bo and Cy". */
export function namesList(names: string[]): string {
  return names.length <= 1 ? (names[0] ?? '') : `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
}
