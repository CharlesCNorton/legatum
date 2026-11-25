## 2026-11-22: Advisor collision checks need raw target bounds

- Cause: the ring checks `elementFromPoint` before drawing; when the advisor card covers a button, the hit test returns the card and the ring disappears.
- Evidence: `Advisor.tsx::targetRect` excludes controls whose centre is occluded, so checking only the visible ring cannot detect this placement error.
- Change: measure the target control and selected tile directly when placing the card, then let the ring's normal visibility check run after the card moves.
