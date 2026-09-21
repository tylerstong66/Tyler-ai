import React, { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { RecipeCard } from '@/src/components/RecipeCard';
import { colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { RECIPES } from '@/src/data/recipes';
import { recommendRecipes, scoreRecipe } from '@/src/lib/recommendations';
import { MealCategory, TimeBucket } from '@/src/types';

const MEAL_FILTERS: { key: MealCategory | 'all'; label: string }[] = [
  { key: 'all', label: 'All meals' },
  { key: 'breakfast', label: 'Breakfast' },
  { key: 'lunch', label: 'Lunch' },
  { key: 'dinner', label: 'Dinner' },
  { key: 'snack', label: 'Snack' },
  { key: 'dessert', label: 'Dessert' }
];

const LIBRARY_FILTERS: { key: TimeBucket | 'all' | 'favorites' | 'ai' | 'never'; label: string }[] = [
  { key: 'all', label: 'All times' },
  { key: 'quick', label: '≤30 min' },
  { key: 'medium', label: '30 min–2 hr' },
  { key: 'long', label: '2+ hr' },
  { key: 'ai', label: 'AI creations' },
  { key: 'favorites', label: 'Favorites' },
  { key: 'never', label: 'Never again' }
];

export default function RecipesScreen() {
  const { state } = useApp();
  const [mealFilter, setMealFilter] = useState<MealCategory | 'all'>('all');
  const [libraryFilter, setLibraryFilter] = useState<(typeof LIBRARY_FILTERS)[number]['key']>('all');

  const recipes = useMemo(() => {
    const allRecipes = [...state.generatedRecipes, ...RECIPES];
    const category = mealFilter === 'all' ? undefined : mealFilter;

    if (libraryFilter === 'favorites') {
      return recommendRecipes(allRecipes.filter((r) => state.favorites.includes(r.id)), state, undefined, category);
    }
    if (libraryFilter === 'ai') {
      return recommendRecipes(state.generatedRecipes, state, undefined, category);
    }
    if (libraryFilter === 'never') {
      return allRecipes
        .filter((recipe) => state.recipeFeedback[recipe.id]?.rating === 'never')
        .filter((recipe) => !category || recipe.category === category)
        .map((recipe) => ({ recipe, ...scoreRecipe(recipe, state) }));
    }
    return recommendRecipes(allRecipes, state, libraryFilter === 'all' ? undefined : libraryFilter, category);
  }, [libraryFilter, mealFilter, state]);

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Text style={styles.intro}>Choose a meal category and cooking-time range, then Dinner AI ranks recipes against your kitchen inventory and food profile.</Text>

      <Text style={styles.filterLabel}>Meal</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters}>
        {MEAL_FILTERS.map((item) => {
          const active = item.key === mealFilter;
          return (
            <Pressable key={item.key} onPress={() => setMealFilter(item.key)} style={[styles.filter, active && styles.filterActive]}>
              <Text style={[styles.filterText, active && styles.filterTextActive]}>{item.label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <Text style={styles.filterLabel}>Time & saved lists</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.filters}>
        {LIBRARY_FILTERS.map((item) => {
          const active = item.key === libraryFilter;
          return (
            <Pressable key={item.key} onPress={() => setLibraryFilter(item.key)} style={[styles.filter, active && styles.filterActive]}>
              <Text style={[styles.filterText, active && styles.filterTextActive]}>{item.label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <View style={styles.list}>
        {recipes.length === 0 ? <Text style={styles.empty}>No recipes match these filters and your current food profile.</Text> : null}
        {recipes.map(({ recipe, matched, total }) => (
          <RecipeCard key={recipe.id} recipe={recipe} favorite={state.favorites.includes(recipe.id)} match={`${matched}/${total} ingredients on hand`} />
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 16, backgroundColor: colors.bg, paddingBottom: 42 },
  intro: { color: colors.muted, lineHeight: 22, fontSize: 14.5, marginBottom: 18 },
  filterLabel: { color: colors.text, fontWeight: '900', fontSize: 14, marginBottom: 9 },
  filters: { gap: 8, paddingBottom: 16, paddingRight: 10 },
  filter: { borderWidth: 1, borderColor: colors.border, paddingHorizontal: 15, paddingVertical: 10, borderRadius: 999, backgroundColor: colors.card },
  filterActive: { backgroundColor: colors.greenDark, borderColor: colors.greenDark },
  filterText: { color: colors.text, fontWeight: '800', fontSize: 13 },
  filterTextActive: { color: '#fff' },
  list: { gap: 14 },
  empty: { color: colors.muted, textAlign: 'center', paddingVertical: 32 }
});
