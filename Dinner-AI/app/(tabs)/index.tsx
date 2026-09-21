import { useRouter } from 'expo-router';
import React, { useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { RecipeCard } from '@/src/components/RecipeCard';
import { Card, PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { RECIPES } from '@/src/data/recipes';
import { recommendRecipes } from '@/src/lib/recommendations';
import { MealCategory } from '@/src/types';

const MEALS: { key: MealCategory; label: string }[] = [
  { key: 'breakfast', label: 'Breakfast' },
  { key: 'lunch', label: 'Lunch' },
  { key: 'dinner', label: 'Dinner' },
  { key: 'snack', label: 'Snack' },
  { key: 'dessert', label: 'Dessert' }
];

export default function HomeScreen() {
  const router = useRouter();
  const { state } = useApp();
  const [mealCategory, setMealCategory] = useState<MealCategory>('dinner');
  const allRecipes = useMemo(() => [...state.generatedRecipes, ...RECIPES], [state.generatedRecipes]);
  const recs = useMemo(() => recommendRecipes(allRecipes, state, undefined, mealCategory).slice(0, 3), [allRecipes, mealCategory, state]);

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View>
        <Text style={styles.eyebrow}>DINNER AI</Text>
        <Text style={styles.hero}>What should we make?</Text>
        <Text style={styles.sub}>Use what you already have, match your tastes, and get ideas for breakfast, lunch, dinner, snacks, or dessert.</Text>
      </View>

      <Card style={styles.scanCard}>
        <Text style={styles.cardTitle}>Start with your kitchen</Text>
        <Text style={styles.cardBody}>Scan your fridge or a packaged food, then save each ingredient under Refrigerator, Freezer, Pantry, or Seasoning.</Text>
        <View style={styles.row}>
          <View style={styles.flex}><PrimaryButton label="📷 Scan fridge" onPress={() => router.push('/scan-fridge')} /></View>
          <View style={styles.flex}><SecondaryButton label="▦ Scan UPC" onPress={() => router.push('/scan-upc')} /></View>
        </View>
      </Card>

      <View>
        <Text style={styles.filterTitle}>What are you looking for?</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.mealFilters}>
          {MEALS.map((meal) => {
            const active = meal.key === mealCategory;
            return (
              <Pressable key={meal.key} onPress={() => setMealCategory(meal.key)} style={[styles.mealFilter, active && styles.mealFilterActive]}>
                <Text style={[styles.mealFilterText, active && styles.mealFilterTextActive]}>{meal.label}</Text>
              </Pressable>
            );
          })}
        </ScrollView>
      </View>

      <View style={styles.sectionHeader}>
        <View>
          <Text style={styles.sectionTitle}>Best {mealCategory} matches</Text>
          <Text style={styles.small}>Based on your kitchen inventory and food profile</Text>
        </View>
        <Text style={styles.count}>{state.pantry.length} items</Text>
      </View>

      {recs.length ? recs.map(({ recipe, matched, total }) => (
        <RecipeCard
          key={recipe.id}
          recipe={recipe}
          favorite={state.favorites.includes(recipe.id)}
          match={`${matched}/${total} ingredients on hand`}
        />
      )) : <Text style={styles.empty}>No {mealCategory} recipes match your profile yet.</Text>}

      <Card style={styles.surpriseCard}>
        <Text style={styles.cardTitle}>Can’t decide?</Text>
        <Text style={styles.cardBody}>Generate something new for any meal category using your inventory, food profile, feedback, and available time.</Text>
        <PrimaryButton label="🎲 Surprise me" onPress={() => router.push('/surprise')} />
      </Card>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 16, gap: 20, backgroundColor: colors.bg, paddingBottom: 42 },
  eyebrow: { color: colors.green, fontWeight: '900', letterSpacing: 1.7, fontSize: 11, marginTop: 2 },
  hero: { color: colors.text, fontSize: 32, lineHeight: 38, fontWeight: '900', marginTop: 7, letterSpacing: -0.6 },
  sub: { color: colors.muted, fontSize: 16, lineHeight: 24, marginTop: 9, maxWidth: 560 },
  scanCard: { gap: 14, backgroundColor: colors.greenFaint, borderColor: colors.borderStrong },
  surpriseCard: { gap: 13, marginTop: 2 },
  cardTitle: { color: colors.text, fontSize: 20, lineHeight: 25, fontWeight: '900' },
  cardBody: { color: colors.muted, lineHeight: 22, fontSize: 14.5 },
  row: { flexDirection: 'row', gap: 10 },
  flex: { flex: 1 },
  filterTitle: { color: colors.text, fontWeight: '900', fontSize: 15, marginBottom: 10 },
  mealFilters: { gap: 8, paddingRight: 10 },
  mealFilter: { borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, borderRadius: 999, paddingHorizontal: 16, paddingVertical: 10 },
  mealFilterActive: { backgroundColor: colors.greenDark, borderColor: colors.greenDark },
  mealFilterText: { color: colors.text, fontWeight: '800', fontSize: 13 },
  mealFilterTextActive: { color: '#fff' },
  sectionHeader: { marginTop: 2, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 12 },
  sectionTitle: { color: colors.text, fontSize: 23, lineHeight: 28, fontWeight: '900', textTransform: 'capitalize', letterSpacing: -0.3 },
  small: { color: colors.muted, marginTop: 4, lineHeight: 19 },
  count: { color: colors.greenDark, backgroundColor: colors.greenSoft, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6, fontWeight: '900', fontSize: 11, overflow: 'hidden' },
  empty: { color: colors.muted, textAlign: 'center', paddingVertical: 26, lineHeight: 21 }
});
