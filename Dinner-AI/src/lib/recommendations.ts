import { AppState, MealCategory, Recipe, TimeBucket } from '@/src/types';
import { isCommonStapleIngredient } from '@/src/lib/shopping';

export function bucketForMinutes(minutes: number): TimeBucket {
  if (minutes <= 30) return 'quick';
  if (minutes <= 120) return 'medium';
  return 'long';
}

const normalize = (value: string) => value.trim().toLowerCase();

function includesTerm(texts: string[], term: string) {
  const needle = normalize(term);
  return needle.length > 0 && texts.some((value) => normalize(value).includes(needle));
}

export function isRecipeSafe(recipe: Recipe, allergies: string[]) {
  if (!allergies.length) return true;
  const searchable = [...recipe.ingredients, ...recipe.allergens, ...recipe.tags, recipe.title];
  return !allergies.some((allergy) => includesTerm(searchable, allergy));
}

function meetsDietaryNotes(recipe: Recipe, notes: string) {
  const note = normalize(notes);
  if (!note) return true;
  const searchable = [...recipe.ingredients, ...recipe.allergens, ...recipe.tags, recipe.title].map(normalize);
  const has = (term: string) => searchable.some((value) => value.includes(term));

  if (note.includes('vegetarian') && !recipe.tags.includes('vegetarian')) return false;
  if (note.includes('vegan') && !recipe.tags.includes('vegan')) return false;
  if ((note.includes('no pork') || note.includes('pork-free') || note.includes('pork free')) && has('pork')) return false;
  if ((note.includes('gluten-free') || note.includes('gluten free')) && recipe.allergens.includes('gluten')) return false;
  if ((note.includes('dairy-free') || note.includes('dairy free')) && recipe.allergens.includes('dairy')) return false;
  return true;
}

export function scoreRecipe(recipe: Recipe, state: AppState) {
  const pantryNames = state.pantry.map((item) => normalize(item.name));
  const recipeIngredients = recipe.ingredients
    .filter((ingredient) => !isCommonStapleIngredient(ingredient))
    .map(normalize);
  const matched = recipeIngredients.filter((ingredient) =>
    pantryNames.some((pantry) => pantry.includes(ingredient) || ingredient.includes(pantry))
  ).length;

  const coverage = recipeIngredients.length ? matched / recipeIngredients.length : 0;
  let score = coverage * 60;

  const searchable = [...recipe.ingredients, ...recipe.tags, recipe.title];
  for (const like of state.profile.likes) {
    if (includesTerm(searchable, like)) score += 8;
  }
  for (const dislike of state.profile.dislikes) {
    if (includesTerm(searchable, dislike)) score -= 25;
  }

  if (state.favorites.includes(recipe.id)) score += 7;
  score += Math.min(state.recipeSelections[recipe.id] ?? 0, 5) * 2;

  const directFeedback = state.recipeFeedback[recipe.id]?.rating;
  if (directFeedback === 'love') score += 22;
  if (directFeedback === 'okay') score += 4;
  if (directFeedback === 'never') score -= 1000;

  for (const [feedbackRecipeId, feedback] of Object.entries(state.recipeFeedback)) {
    if (feedbackRecipeId === recipe.id) continue;
    const similarity = recipeSimilarity(recipe, feedback.tags, feedback.ingredients, feedback.category);
    if (!similarity) continue;
    if (feedback.rating === 'love') score += Math.min(12, similarity);
    if (feedback.rating === 'never') score -= Math.min(12, similarity * 0.8);
  }

  return { score, matched, total: recipeIngredients.length, coverage };
}

export function recommendRecipes(recipes: Recipe[], state: AppState, bucket?: TimeBucket, category?: MealCategory) {
  return recipes
    .filter((recipe) => (!bucket ? true : bucketForMinutes(recipe.minutes) === bucket))
    .filter((recipe) => (!category ? true : recipe.category === category))
    .filter((recipe) => isRecipeSafe(recipe, state.profile.allergies))
    .filter((recipe) => meetsDietaryNotes(recipe, state.profile.dietaryNotes))
    .filter((recipe) => state.recipeFeedback[recipe.id]?.rating !== 'never')
    .map((recipe) => ({ recipe, ...scoreRecipe(recipe, state) }))
    .sort((a, b) => b.score - a.score);
}

export function createPantrySurprise(state: AppState, bucket: TimeBucket = 'quick', category: MealCategory = 'dinner'): Recipe {
  const avoid = state.profile.allergies.map(normalize).filter(Boolean);
  const allowed = (value: string) => !avoid.some((term) => normalize(value).includes(term));
  const available = state.pantry.map((item) => item.name).filter(Boolean).filter(allowed);
  const defaultsByCategory: Record<MealCategory, string[]> = {
    breakfast: ['oats', 'eggs', 'banana', 'toast', 'fruit'],
    lunch: ['rice', 'vegetables', 'beans', 'greens', 'tortilla'],
    dinner: ['rice', 'vegetables', 'onion', 'potato', 'beans'],
    snack: ['fruit', 'yogurt', 'cucumber', 'hummus', 'crackers'],
    dessert: ['fruit', 'chocolate', 'yogurt', 'oats', 'cinnamon']
  };
  const defaults = defaultsByCategory[category].filter(allowed);
  const base = available[0] ?? defaults[0] ?? 'a verified allergy-safe staple';
  const second = available[1] ?? defaults[1] ?? 'a verified allergy-safe ingredient';
  const third = available[2] ?? defaults[2] ?? 'a second verified allergy-safe ingredient';
  const optionalStaples = ['olive oil', 'garlic', 'salt', 'black pepper'].filter(allowed);
  const id = `generated-${Date.now()}`;
  const minutes = bucket === 'quick' ? 30 : bucket === 'medium' ? 75 : 150;
  const categoryLabel = category.charAt(0).toUpperCase() + category.slice(1);

  return {
    id,
    title: `${titleCase(base)} ${categoryLabel} Remix`,
    description: `An experimental ${category} idea built from ${base}, ${second}, and ${third}.`,
    minutes,
    category,
    ingredients: [base, second, third, ...optionalStaples],
    instructions: [
      `Prep ${base}, ${second}, and ${third} as needed.`,
      'Cook the longest-cooking ingredient first using an allergy-safe method and cooking fat if needed.',
      'Add the remaining ingredients, season, and cook until everything is tender and safely cooked.',
      `Adjust the portion and presentation so it works as a ${category}, then taste and serve.`
    ],
    tags: ['generated', 'pantry', bucket, category],
    allergens: [],
    generated: true,
    generatedAt: Date.now(),
    pantryIngredientsUsed: [base, second, third],
    missingIngredients: optionalStaples.filter((item) => !available.some((pantry) => normalize(pantry).includes(normalize(item)))),
    safetyNotes: state.profile.allergies.length ? 'Check every ingredient label and cross-contact risk against your saved allergies before cooking.' : undefined,
    generationReason: `Built locally from the first ingredients currently in your kitchen for a ${category}.`
  };
}

function recipeSimilarity(recipe: Recipe, feedbackTags: string[], feedbackIngredients: string[], feedbackCategory?: MealCategory) {
  const recipeTags = new Set(recipe.tags.map(normalize));
  const recipeIngredients = recipe.ingredients.map(normalize);
  const sharedTags = feedbackTags.map(normalize).filter((tag) => tag && recipeTags.has(tag)).length;
  const sharedIngredients = feedbackIngredients.map(normalize).filter((ingredient) =>
    ingredient && recipeIngredients.some((candidate) => candidate.includes(ingredient) || ingredient.includes(candidate))
  ).length;
  const categoryMatch = feedbackCategory && feedbackCategory === recipe.category ? 1 : 0;
  return sharedTags * 2 + Math.min(sharedIngredients, 6) + categoryMatch;
}

function titleCase(value: string) {
  return value.replace(/\b\w/g, (char) => char.toUpperCase());
}
