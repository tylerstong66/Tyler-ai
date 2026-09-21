import { Platform } from 'react-native';
import { AppState, MealCategory, Recipe, TimeBucket } from '@/src/types';
import { RECIPES } from '@/src/data/recipes';

const configuredBaseUrl = process.env.EXPO_PUBLIC_AI_BASE_URL?.replace(/\/$/, '');
const DEV_WEB_BASE_URL = Platform.OS === 'web' ? 'http://localhost:8787' : '';
const API_BASE_URL = configuredBaseUrl || DEV_WEB_BASE_URL;

export type GenerateRecipeResult = {
  recipe: Recipe;
  model?: string;
};

export async function generateAIRecipe(state: AppState, timeBucket: TimeBucket, mealCategory: MealCategory): Promise<GenerateRecipeResult> {
  if (!API_BASE_URL) throw new Error('AI_BACKEND_NOT_CONFIGURED');

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 75_000);

  const knownRecipes = [...state.generatedRecipes, ...RECIPES];
  const chosenRecipes = Object.entries(state.recipeSelections)
    .filter(([, count]) => count > 0)
    .map(([id, count]) => {
      const recipe = knownRecipes.find((item) => item.id === id);
      return recipe ? { title: recipe.title, tags: recipe.tags, category: recipe.category, count } : null;
    })
    .filter((item): item is { title: string; tags: string[]; category: MealCategory; count: number } => Boolean(item))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10);

  const ratedRecipes = Object.values(state.recipeFeedback)
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .slice(0, 15)
    .map(({ rating, title, tags, category }) => ({ rating, title, tags, category }));

  try {
    const response = await fetch(`${API_BASE_URL}/generate-recipe`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pantry: state.pantry.map(({ name, quantity, storage }) => ({ name, quantity: quantity ?? '', storage })),
        profile: state.profile,
        timeBucket,
        mealCategory,
        chosenRecipes,
        ratedRecipes
      }),
      signal: controller.signal
    });

    const body = await response.json().catch(() => null) as any;
    if (!response.ok) {
      const message = typeof body?.error === 'string' ? body.error : `Recipe request failed (${response.status}).`;
      throw new Error(message);
    }

    const recipe = normalizeRecipe(body?.recipe, mealCategory);
    if (!recipe) throw new Error('The recipe service returned invalid recipe data.');

    return { recipe, model: typeof body?.model === 'string' ? body.model : undefined };
  } catch (error: any) {
    if (error?.name === 'AbortError') throw new Error('Recipe generation timed out. Please try again.');
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function normalizeRecipe(value: any, requestedCategory: MealCategory): Recipe | null {
  if (!value || typeof value.title !== 'string' || !value.title.trim()) return null;
  const ingredients = cleanStringArray(value.ingredients);
  const instructions = cleanStringArray(value.instructions);
  if (!ingredients.length || !instructions.length) return null;
  const category: MealCategory = ['breakfast', 'lunch', 'dinner', 'snack'].includes(value.category)
    ? value.category
    : requestedCategory;

  return {
    id: typeof value.id === 'string' && value.id.trim() ? value.id : `ai-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`,
    title: value.title.trim(),
    description: typeof value.description === 'string' ? value.description.trim() : '',
    minutes: clampInt(value.minutes, 5, 480, 30),
    category,
    servings: clampInt(value.servings, 1, 12, 4),
    ingredients,
    instructions,
    tags: cleanStringArray(value.tags),
    allergens: cleanStringArray(value.allergens),
    generated: true,
    generatedAt: Date.now(),
    pantryIngredientsUsed: cleanStringArray(value.pantryIngredientsUsed),
    missingIngredients: cleanStringArray(value.missingIngredients),
    safetyNotes: typeof value.safetyNotes === 'string' ? value.safetyNotes.trim() : undefined,
    generationReason: typeof value.generationReason === 'string' ? value.generationReason.trim() : undefined
  };
}

function cleanStringArray(value: any): string[] {
  return Array.isArray(value)
    ? value.filter((item) => typeof item === 'string').map((item) => item.trim()).filter(Boolean)
    : [];
}

function clampInt(value: any, min: number, max: number, fallback: number) {
  const number = Number(value);
  return Number.isFinite(number) ? Math.round(Math.min(max, Math.max(min, number))) : fallback;
}
