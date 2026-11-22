/** Roman numerals for Ages and ranks. Kept apart from ornaments.tsx so plain modules (and the e2e tour, which loads them in Node) need no asset imports. */
const ROMAN = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI', 'XII'];
export const roman = (n: number) => ROMAN[n - 1] ?? String(n);
