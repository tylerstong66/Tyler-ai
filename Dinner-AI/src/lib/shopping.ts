import { PantryItem, Recipe, ShoppingItem } from '@/src/types';

export function mergeRecipeMissingIngredients(list: ShoppingItem[], recipe: Recipe, pantry: PantryItem[] = []) {
  return mergeShoppingItems(list, deriveRecipeMissingIngredients(recipe, pantry), recipe);
}

export function deriveRecipeMissingIngredients(recipe: Recipe, pantry: PantryItem[] = []) {
  const pantryNames = pantry.map((item) => item.name).filter(Boolean);
  const explicit = (recipe.missingIngredients ?? [])
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item) => !isCommonStapleIngredient(item));

  const inferred = recipe.ingredients
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item) => !isCommonStapleIngredient(item))
    .filter((ingredient) => !pantryNames.some((pantryName) => ingredientsMatch(ingredient, pantryName)));

  const result: string[] = [];
  const seen = new Set<string>();

  for (const item of [...explicit, ...inferred]) {
    const key = canonicalIngredient(item);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    result.push(item);
  }

  return result;
}

export function mergeShoppingItems(list: ShoppingItem[], names: string[], recipe?: Recipe) {
  if (!names.length) return list;
  const now = Date.now();
  const next = [...list];

  for (const rawName of names) {
    const name = rawName.trim();
    if (!name) continue;
    const key = canonicalIngredient(name) || normalizeShoppingName(name);
    const existingIndex = next.findIndex((item) => {
      const existingKey = canonicalIngredient(item.name) || normalizeShoppingName(item.name);
      return existingKey === key || ingredientsMatch(item.name, name);
    });

    if (existingIndex >= 0) {
      if (next[existingIndex].checked) {
        next[existingIndex] = {
          ...next[existingIndex],
          checked: false,
          recipeId: recipe?.id ?? next[existingIndex].recipeId,
          recipeTitle: recipe?.title ?? next[existingIndex].recipeTitle
        };
      }
      continue;
    }

    next.unshift({
      id: `shop-${now}-${Math.random().toString(36).slice(2, 8)}`,
      name,
      checked: false,
      addedAt: now,
      recipeId: recipe?.id,
      recipeTitle: recipe?.title
    });
  }

  return next;
}

export function normalizeShoppingName(value: string) {
  return value.trim().toLowerCase().replace(/\s+/g, ' ');
}

export function isCommonStapleIngredient(value: string) {
  const text = normalizeShoppingName(value)
    .replace(/[.,]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (!text) return false;

  return [
    /\bwater\b/,
    /\bsalt\b/,
    /\bblack pepper\b/,
    /\bground pepper\b/,
    /\bpepper\b/,
    /\bcooking oil\b/,
    /\bolive oil\b/,
    /\bvegetable oil\b/,
    /\bcanola oil\b/,
    /\bavocado oil\b/,
    /\bflour\b/,
    /\bsugar\b/
  ].some((pattern) => pattern.test(text));
}

export function ingredientsMatch(a: string, b: string) {
  const left = canonicalIngredient(a);
  const right = canonicalIngredient(b);
  if (!left || !right) return false;
  if (left === right || left.includes(right) || right.includes(left)) return true;

  const leftTokens = new Set(left.split(' ').filter(Boolean));
  const rightTokens = new Set(right.split(' ').filter(Boolean));
  const smaller = leftTokens.size <= rightTokens.size ? leftTokens : rightTokens;
  const larger = leftTokens.size <= rightTokens.size ? rightTokens : leftTokens;
  let overlap = 0;
  smaller.forEach((token) => { if (larger.has(token)) overlap += 1; });

  return overlap >= 2 && overlap / Math.max(1, smaller.size) >= 0.66;
}

export function canonicalIngredient(value: string) {
  const stopWords = new Set([
    'a','an','the','of','and','or','to','taste','optional',
    'cup','cups','tbsp','tablespoon','tablespoons','tsp','teaspoon','teaspoons',
    'oz','ounce','ounces','lb','lbs','pound','pounds','g','gram','grams','kg',
    'ml','l','can','cans','package','packages','pkg','clove','cloves',
    'slice','slices','piece','pieces','pinch','dash',
    'small','medium','large','fresh','finely','roughly','chopped','diced','minced',
    'sliced','grated','shredded','melted','softened','divided','boneless','skinless'
  ]);

  return normalizeShoppingName(value)
    .replace(/[¼½¾⅓⅔⅛⅜⅝⅞]/g, ' ')
    .replace(/\([^)]*\)/g, ' ')
    .replace(/\b\d+(?:[./]\d+)?\b/g, ' ')
    .replace(/[^a-z0-9\s-]/g, ' ')
    .replace(/-/g, ' ')
    .split(/\s+/)
    .map((word) => singularize(word))
    .filter((word) => word && !stopWords.has(word))
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function singularize(word: string) {
  if (word.length > 4 && word.endsWith('ies')) return word.slice(0, -3) + 'y';
  if (word.length > 4 && word.endsWith('oes')) return word.slice(0, -2);
  if (word.length > 4 && word.endsWith('ses')) return word.slice(0, -2);
  if (word.length > 3 && word.endsWith('s') && !word.endsWith('ss')) return word.slice(0, -1);
  return word;
}
