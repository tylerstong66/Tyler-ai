import { canonicalIngredient } from '@/src/lib/shopping';

const FRACTIONS: Record<string, number> = {
  '¼': 0.25, '½': 0.5, '¾': 0.75, '⅓': 1/3, '⅔': 2/3,
  '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875
};

export function scaleIngredient(ingredient: string, fromServings: number, toServings: number) {
  if (!fromServings || fromServings === toServings) return ingredient;
  const ratio = toServings / fromServings;

  return ingredient.replace(
    /^\s*((?:\d+\s+)?[¼½¾⅓⅔⅛⅜⅝⅞]|\d+\s+\d+\/\d+|\d+\/\d+|\d+(?:\.\d+)?)/,
    (match) => {
      const parsed = parseAmount(match.trim());
      if (parsed == null) return match;
      return formatAmount(parsed * ratio);
    }
  );
}

export function scaledIngredients(ingredients: string[], fromServings: number, toServings: number) {
  return ingredients.map((item) => scaleIngredient(item, fromServings, toServings));
}

export function ingredientsForStep(ingredients: string[], step: string) {
  const stepTokens = new Set(canonicalIngredient(step).split(' ').filter((token) => token.length > 2));
  const matches = ingredients.filter((ingredient) => {
    const key = canonicalIngredient(ingredient);
    if (!key) return false;
    const tokens = key.split(' ').filter((token) => token.length > 2);
    return tokens.some((token) => stepTokens.has(token));
  });
  return matches.slice(0, 8);
}

export function suggestedTimerSeconds(step: string) {
  const matches = [...step.matchAll(/(\d+)\s*(?:to|-|–)?\s*(\d+)?\s*(seconds?|secs?|minutes?|mins?|hours?|hrs?)/gi)];
  if (!matches.length) return null;
  const match = matches[0];
  const amount = Number(match[2] || match[1]);
  const unit = match[3].toLowerCase();
  if (unit.startsWith('hour') || unit.startsWith('hr')) return amount * 3600;
  if (unit.startsWith('min')) return amount * 60;
  return amount;
}

function parseAmount(value: string) {
  const mixedGlyph = value.match(/^(\d+)\s+([¼½¾⅓⅔⅛⅜⅝⅞])$/);
  if (mixedGlyph) return Number(mixedGlyph[1]) + (FRACTIONS[mixedGlyph[2]] || 0);

  const mixedAscii = value.match(/^(\d+)\s+(\d+)\/(\d+)$/);
  if (mixedAscii) {
    const denominator = Number(mixedAscii[3]);
    if (!denominator) return null;
    return Number(mixedAscii[1]) + Number(mixedAscii[2]) / denominator;
  }

  if (FRACTIONS[value] != null) return FRACTIONS[value];

  const fraction = value.match(/^(\d+)\/(\d+)$/);
  if (fraction) {
    const denominator = Number(fraction[2]);
    return denominator ? Number(fraction[1]) / denominator : null;
  }

  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function formatAmount(value: number) {
  if (!Number.isFinite(value)) return '';
  const whole = Math.floor(value);
  const fraction = value - whole;
  const glyphs: [number, string][] = [
    [0.125, '⅛'], [0.25, '¼'], [1 / 3, '⅓'], [0.375, '⅜'],
    [0.5, '½'], [0.625, '⅝'], [2 / 3, '⅔'], [0.75, '¾'], [0.875, '⅞']
  ];
  const glyph = glyphs.find(([amount]) => Math.abs(fraction - amount) < 0.025)?.[1];
  if (glyph) return whole ? `${whole} ${glyph}` : glyph;

  const rounded = Number(value.toFixed(2));
  return Number.isInteger(rounded) ? String(rounded) : String(rounded);
}
