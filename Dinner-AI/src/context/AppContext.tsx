import AsyncStorage from '@react-native-async-storage/async-storage';
import React, { createContext, PropsWithChildren, useContext, useEffect, useMemo, useState } from 'react';
import { AppState, PantryItem, PantryStorage, Recipe, RecipeFeedbackRating, UserProfile } from '@/src/types';
import { isCommonStapleIngredient, mergeRecipeMissingIngredients, mergeShoppingItems } from '@/src/lib/shopping';

const STORAGE_KEY = 'dinner-ai-state-v1';
const MAX_GENERATED_RECIPES = 25;

const initialState: AppState = {
  pantry: [],
  favorites: [],
  profile: { likes: [], dislikes: [], allergies: [], dietaryNotes: '' },
  recipeSelections: {},
  recipeFeedback: {},
  generatedRecipes: [],
  shoppingList: []
};

type NewPantryItem = Omit<PantryItem, 'id' | 'addedAt'>;

type AppContextValue = {
  state: AppState;
  hydrated: boolean;
  addPantryItem: (item: NewPantryItem) => void;
  addPantryItems: (items: NewPantryItem[]) => void;
  removePantryItem: (id: string) => void;
  toggleFavorite: (recipeId: string) => void;
  updateProfile: (profile: UserProfile) => void;
  saveGeneratedRecipe: (recipe: Recipe) => void;
  markRecipeChosen: (recipe: Recipe) => void;
  setRecipeFeedback: (recipe: Recipe, rating: RecipeFeedbackRating) => void;
  addRecipeMissingToShoppingList: (recipe: Recipe) => void;
  addShoppingItem: (name: string) => void;
  toggleShoppingItem: (id: string) => void;
  removeShoppingItem: (id: string) => void;
  clearPurchasedShoppingItems: () => void;
  clearShoppingList: () => void;
  resetData: () => void;
};

const AppContext = createContext<AppContextValue | null>(null);

export function AppProvider({ children }: PropsWithChildren) {
  const [state, setState] = useState<AppState>(initialState);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((saved) => {
        if (!saved) return;
        try { setState(normalizeLoadedState(JSON.parse(saved))); }
        catch { setState(initialState); }
      })
      .catch(() => undefined)
      .finally(() => setHydrated(true));
  }, []);

  useEffect(() => {
    if (!hydrated) return;
    AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(state)).catch(() => undefined);
  }, [state, hydrated]);

  const value = useMemo<AppContextValue>(() => ({
    state,
    hydrated,
    addPantryItem: (item) => setState((current) => ({
      ...current,
      pantry: [{ ...item, id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`, addedAt: Date.now() }, ...current.pantry]
    })),
    addPantryItems: (items) => {
      const clean = items.filter((item) => item && item.name?.trim()).map((item) => ({ ...item, name: item.name.trim(), quantity: item.quantity?.trim() || undefined }));
      if (!clean.length) return;
      setState((current) => ({
        ...current,
        pantry: [...clean.map((item, index) => ({ ...item, id: `${Date.now()}-${index}-${Math.random().toString(36).slice(2, 6)}`, addedAt: Date.now() })), ...current.pantry]
      }));
    },
    removePantryItem: (id) => setState((current) => ({ ...current, pantry: current.pantry.filter((item) => item.id !== id) })),
    toggleFavorite: (recipeId) => setState((current) => ({
      ...current,
      favorites: current.favorites.includes(recipeId) ? current.favorites.filter((id) => id !== recipeId) : [...current.favorites, recipeId]
    })),
    updateProfile: (profile) => setState((current) => ({ ...current, profile })),
    saveGeneratedRecipe: (recipe) => {
      if (!recipe.generated) return;
      setState((current) => ({ ...current, generatedRecipes: upsertGeneratedRecipe(current.generatedRecipes, recipe) }));
    },
    markRecipeChosen: (recipe) => setState((current) => ({
      ...current,
      generatedRecipes: recipe.generated ? upsertGeneratedRecipe(current.generatedRecipes, recipe) : current.generatedRecipes,
      recipeSelections: { ...current.recipeSelections, [recipe.id]: (current.recipeSelections[recipe.id] ?? 0) + 1 },
      shoppingList: mergeRecipeMissingIngredients(current.shoppingList, recipe, current.pantry)
    })),
    setRecipeFeedback: (recipe, rating) => setState((current) => ({
      ...current,
      recipeFeedback: {
        ...current.recipeFeedback,
        [recipe.id]: { rating, title: recipe.title, tags: recipe.tags, ingredients: recipe.ingredients, category: recipe.category, updatedAt: Date.now() }
      }
    })),
    addRecipeMissingToShoppingList: (recipe) => setState((current) => ({ ...current, shoppingList: mergeRecipeMissingIngredients(current.shoppingList, recipe, current.pantry) })),
    addShoppingItem: (name) => {
      const clean = name.trim();
      if (!clean) return;
      setState((current) => ({ ...current, shoppingList: mergeShoppingItems(current.shoppingList, [clean]) }));
    },
    toggleShoppingItem: (id) => setState((current) => ({ ...current, shoppingList: current.shoppingList.map((item) => item.id === id ? { ...item, checked: !item.checked } : item) })),
    removeShoppingItem: (id) => setState((current) => ({ ...current, shoppingList: current.shoppingList.filter((item) => item.id !== id) })),
    clearPurchasedShoppingItems: () => setState((current) => ({ ...current, shoppingList: current.shoppingList.filter((item) => !item.checked) })),
    clearShoppingList: () => setState((current) => ({ ...current, shoppingList: [] })),
    resetData: () => setState(initialState)
  }), [state, hydrated]);

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) throw new Error('useApp must be used inside AppProvider');
  return context;
}

function upsertGeneratedRecipe(recipes: Recipe[], recipe: Recipe) {
  const withTimestamp: Recipe = { ...recipe, generated: true, generatedAt: recipe.generatedAt ?? Date.now() };
  return [withTimestamp, ...recipes.filter((item) => item.id !== recipe.id)].slice(0, MAX_GENERATED_RECIPES);
}

function isPantryStorage(value: unknown): value is PantryStorage {
  return ['refrigerator', 'freezer', 'pantry', 'seasoning'].includes(String(value));
}

function isMealCategory(value: unknown) {
  return ['breakfast', 'lunch', 'dinner', 'snack', 'dessert'].includes(String(value));
}

function normalizeLoadedState(value: Partial<AppState> | null | undefined): AppState {
  const rawGeneratedRecipes = Array.isArray(value?.generatedRecipes)
    ? value.generatedRecipes.filter((recipe) => recipe && typeof (recipe as any).title === 'string')
    : [];
  const trialRecipeIds = new Set(
    rawGeneratedRecipes
      .filter((recipe) => isCreamyOreganoTrialRecipe(recipe as Recipe))
      .map((recipe) => String((recipe as any).id || ''))
      .filter(Boolean)
  );

  const rawFeedback = value?.recipeFeedback && typeof value.recipeFeedback === 'object' ? value.recipeFeedback : {};
  const recipeFeedback = Object.fromEntries(
    Object.entries(rawFeedback).flatMap(([id, entry]) => {
      if (trialRecipeIds.has(id)) return [];
      if (!entry || typeof entry !== 'object') return [];
      const rating = (entry as any).rating;
      if (!['love', 'okay', 'never'].includes(rating)) return [];
      return [[id, {
        rating,
        title: typeof (entry as any).title === 'string' ? (entry as any).title : '',
        tags: Array.isArray((entry as any).tags) ? (entry as any).tags.filter((item: unknown) => typeof item === 'string') : [],
        ingredients: Array.isArray((entry as any).ingredients) ? (entry as any).ingredients.filter((item: unknown) => typeof item === 'string') : [],
        category: isMealCategory((entry as any).category) ? (entry as any).category : undefined,
        updatedAt: Number((entry as any).updatedAt) || Date.now()
      }]];
    })
  );

  const pantry = Array.isArray(value?.pantry)
    ? value.pantry
        .filter((item) => item && typeof (item as any).name === 'string')
        .filter((item) => !String((item as any).id || '').startsWith('starter-'))
        .map((item) => ({
          ...item,
          storage: isPantryStorage((item as any).storage) ? (item as any).storage : 'pantry'
        })) as PantryItem[]
    : initialState.pantry;

  const generatedRecipes = rawGeneratedRecipes
    .filter((recipe) => !trialRecipeIds.has(String((recipe as any).id || '')))
    .map((recipe) => ({
      ...recipe,
      category: isMealCategory((recipe as any).category) ? (recipe as any).category : 'dinner'
    }))
    .slice(0, MAX_GENERATED_RECIPES) as Recipe[];

  return {
    pantry,
    favorites: Array.isArray(value?.favorites) ? value.favorites.filter((id) => !trialRecipeIds.has(id)) : [],
    profile: {
      likes: Array.isArray(value?.profile?.likes) ? value.profile.likes : [],
      dislikes: Array.isArray(value?.profile?.dislikes) ? value.profile.dislikes : [],
      allergies: Array.isArray(value?.profile?.allergies) ? value.profile.allergies : [],
      dietaryNotes: typeof value?.profile?.dietaryNotes === 'string' ? value.profile.dietaryNotes : ''
    },
    recipeSelections: value?.recipeSelections && typeof value.recipeSelections === 'object'
      ? Object.fromEntries(Object.entries(value.recipeSelections).filter(([id]) => !trialRecipeIds.has(id)))
      : {},
    recipeFeedback,
    generatedRecipes,
    shoppingList: Array.isArray(value?.shoppingList)
      ? value.shoppingList
          .filter((item) => item && typeof item.name === 'string')
          .filter((item) => !((item as any).recipeId && trialRecipeIds.has(String((item as any).recipeId))))
          .filter((item) => !((item as any).recipeId && isCommonStapleIngredient((item as any).name)))
          .map((item) => ({ ...item, checked: Boolean(item.checked), addedAt: Number(item.addedAt) || Date.now() }))
      : []
  };
}


function isCreamyOreganoTrialRecipe(recipe: Recipe) {
  if (!recipe?.generated) return false;
  const text = [
    recipe.title,
    recipe.description,
    ...(Array.isArray(recipe.ingredients) ? recipe.ingredients : []),
    ...(Array.isArray(recipe.tags) ? recipe.tags : [])
  ].join(' ').toLowerCase();

  return /\bcreamy\b/.test(text) && /\boregano\b/.test(text);
}
