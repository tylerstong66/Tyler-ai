import React, { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { RecipeCard } from '@/src/components/RecipeCard';
import { colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { RECIPES } from '@/src/data/recipes';
import { recommendRecipes, scoreRecipe } from '@/src/lib/recommendations';
import { MealCategory, TimeBucket } from '@/src/types';

const MEAL_FILTERS: { key: MealCategory | 'all'; label: string; emoji: string }[] = [
  { key: 'all', label: 'All', emoji: '✨' },
  { key: 'breakfast', label: 'Breakfast', emoji: '☀️' },
  { key: 'lunch', label: 'Lunch', emoji: '🥪' },
  { key: 'dinner', label: 'Dinner', emoji: '🍽️' },
  { key: 'snack', label: 'Snack', emoji: '🍎' },
  { key: 'dessert', label: 'Dessert', emoji: '🍰' }
];

const LIBRARY_FILTERS: { key: TimeBucket | 'all' | 'favorites' | 'ai' | 'never'; label: string }[] = [
  { key: 'all', label: 'All recipes' },
  { key: 'quick', label: '≤30 min' },
  { key: 'medium', label: '30m–2h' },
  { key: 'long', label: '2h+' },
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
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>DISCOVER</Text>
        <Text style={styles.title}>Recipes for your kitchen</Text>
        <Text style={styles.sub}>Browse by meal, time, favorites, or recipes Dinner AI created for you.</Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.mealRow}>
        {MEAL_FILTERS.map((item) => {
          const active = item.key === mealFilter;
          return (
            <Pressable
              key={item.key}
              onPress={() => setMealFilter(item.key)}
              style={[styles.mealChip, active && styles.mealChipActive]}
            >
              <Text style={styles.mealEmoji}>{item.emoji}</Text>
              <Text style={[styles.mealText, active && styles.mealTextActive]}>{item.label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.libraryRow}>
        {LIBRARY_FILTERS.map((item) => {
          const active = item.key === libraryFilter;
          return (
            <Pressable
              key={item.key}
              onPress={() => setLibraryFilter(item.key)}
              style={[styles.libraryChip, active && styles.libraryChipActive]}
            >
              <Text style={[styles.libraryText, active && styles.libraryTextActive]}>{item.label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      <View style={styles.resultHeader}>
        <Text style={styles.resultTitle}>{recipes.length} {recipes.length === 1 ? 'recipe' : 'recipes'}</Text>
        <Text style={styles.resultSub}>Best matches first</Text>
      </View>

      <View style={styles.list}>
        {recipes.length === 0 ? (
          <View style={styles.empty}>
            <Text style={styles.emptyEmoji}>🍽️</Text>
            <Text style={styles.emptyTitle}>Nothing here yet</Text>
            <Text style={styles.emptyText}>Try another filter or add more ingredients to your Kitchen.</Text>
          </View>
        ) : null}

        {recipes.map(({ recipe, matched, total }) => (
          <RecipeCard
            key={recipe.id}
            recipe={recipe}
            favorite={state.favorites.includes(recipe.id)}
            match={matched + '/' + total + ' on hand'}
          />
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 44, backgroundColor: colors.bg },
  header: { marginBottom: 18 },
  eyebrow: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.7 },
  title: { color: colors.text, fontSize: 30, lineHeight: 35, fontWeight: '900', letterSpacing: -0.7, marginTop: 6 },
  sub: { color: colors.muted, fontSize: 14.5, lineHeight: 21, marginTop: 7, maxWidth: 520 },

  mealRow: { gap: 9, paddingRight: 12, marginBottom: 13 },
  mealChip: {
    flexDirection: 'row', alignItems: 'center', gap: 6,
    backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border,
    borderRadius: 999, paddingHorizontal: 14, paddingVertical: 10
  },
  mealChipActive: { backgroundColor: colors.greenDark, borderColor: colors.greenDark },
  mealEmoji: { fontSize: 14 },
  mealText: { color: colors.text, fontSize: 13, fontWeight: '800' },
  mealTextActive: { color: '#FFFFFF' },

  libraryRow: { gap: 8, paddingRight: 12, marginBottom: 23 },
  libraryChip: { backgroundColor: 'transparent', borderRadius: 999, paddingHorizontal: 12, paddingVertical: 8 },
  libraryChipActive: { backgroundColor: colors.greenSoft },
  libraryText: { color: colors.muted, fontSize: 12.5, fontWeight: '800' },
  libraryTextActive: { color: colors.greenDark },

  resultHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 13 },
  resultTitle: { color: colors.text, fontSize: 21, fontWeight: '900', letterSpacing: -0.25 },
  resultSub: { color: colors.muted, fontSize: 12.5, fontWeight: '700' },

  list: { gap: 14 },
  empty: { alignItems: 'center', paddingVertical: 44, paddingHorizontal: 28 },
  emptyEmoji: { fontSize: 34, marginBottom: 9 },
  emptyTitle: { color: colors.text, fontSize: 18, fontWeight: '900' },
  emptyText: { color: colors.muted, textAlign: 'center', lineHeight: 20, marginTop: 5 }
});
