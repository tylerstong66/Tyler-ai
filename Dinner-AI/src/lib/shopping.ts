import { Recipe, ShoppingItem } from '@/src/types';

export function mergeRecipeMissingIngredients(list: ShoppingItem[], recipe: Recipe) {
  const missing = (recipe.missingIngredients ?? [])
    .map((item) => item.trim())
    .filter(Boolean)
    .filter((item) => !isCommonStapleIngredient(item));
  return mergeShoppingItems(list, missing, recipe);
}

export function mergeShoppingItems(list: ShoppingItem[], names: string[], recipe?: Recipe) {
  if (!names.length) return list;
  const now = Date.now();
  const next = [...list];

  for (const rawName of names) {
    const name = rawName.trim();
    if (!name) continue;
    const key = normalizeShoppingName(name);
    const existingIndex = next.findIndex((item) => normalizeShoppingName(item.name) === key);

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
    /\bcanola oil\b/
  ].some((pattern) => pattern.test(text));
}
