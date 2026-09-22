export type TimeBucket = 'quick' | 'medium' | 'long';
export type RecipeFeedbackRating = 'love' | 'okay' | 'never';
export type PantryStorage = 'refrigerator' | 'freezer' | 'pantry' | 'seasoning';
export type MealCategory = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'dessert';

export type PantryItem = {
  id: string;
  name: string;
  quantity?: string;
  storage: PantryStorage;
  barcode?: string;
  brand?: string;
  imageUrl?: string;
  addedAt: number;
};

export type ShoppingItem = {
  id: string;
  name: string;
  checked: boolean;
  addedAt: number;
  recipeId?: string;
  recipeTitle?: string;
};

export type DetectedIngredient = {
  id: string;
  name: string;
  quantity?: string;
  confidence: number;
  notes?: string;
  selected: boolean;
  storage: PantryStorage;
};

export type Recipe = {
  id: string;
  title: string;
  description: string;
  imageUrl?: string;
  minutes: number;
  category: MealCategory;
  servings?: number;
  ingredients: string[];
  instructions: string[];
  tags: string[];
  allergens: string[];
  generated?: boolean;
  generatedAt?: number;
  pantryIngredientsUsed?: string[];
  missingIngredients?: string[];
  safetyNotes?: string;
  generationReason?: string;
};

export type RecipeFeedbackEntry = {
  rating: RecipeFeedbackRating;
  title: string;
  tags: string[];
  ingredients: string[];
  category?: MealCategory;
  updatedAt: number;
};

export type UserProfile = {
  likes: string[];
  dislikes: string[];
  allergies: string[];
  dietaryNotes: string;
};

export type AppState = {
  pantry: PantryItem[];
  favorites: string[];
  profile: UserProfile;
  recipeSelections: Record<string, number>;
  recipeFeedback: Record<string, RecipeFeedbackEntry>;
  generatedRecipes: Recipe[];
  shoppingList: ShoppingItem[];
};
