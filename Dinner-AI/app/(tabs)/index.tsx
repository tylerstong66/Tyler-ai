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
  { key: 'snack', label: 'Snack' }
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
        <Text style={styles.sub}>Use what you already have, match your tastes, and get ideas for breakfast, lunch, dinner, or a snack.</Text>
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
  content: { padding: 18, gap: 16, backgroundColor: colors.bg, paddingBottom: 36 },
  eyebrow: { color: colors.green, fontWeight: '900', letterSpacing: 1.4, fontSize: 12, marginTop: 4 },
  hero: { color: colors.text, fontSize: 32, lineHeight: 37, fontWeight: '900', marginTop: 6 },
  sub: { color: colors.muted, fontSize: 16, lineHeight: 23, marginTop: 8 },
  scanCard: { gap: 12 },
  surpriseCard: { gap: 12, marginTop: 4 },
  cardTitle: { color: colors.text, fontSize: 19, fontWeight: '800' },
  cardBody: { color: colors.muted, lineHeight: 21 },
  row: { flexDirection: 'row', gap: 10 },
  flex: { flex: 1 },
  filterTitle: { color: colors.text, fontWeight: '900', marginBottom: 8 },
  mealFilters: { gap: 8 },
  mealFilter: { borderWidth: 1, borderColor: colors.border, backgroundColor: '#fff', borderRadius: 99, paddingHorizontal: 14, paddingVertical: 9 },
  mealFilterActive: { backgroundColor: colors.green, borderColor: colors.green },
  mealFilterText: { color: colors.text, fontWeight: '800' },
  mealFilterTextActive: { color: '#fff' },
  sectionHeader: { marginTop: 4, flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 10 },
  sectionTitle: { color: colors.text, fontSize: 22, fontWeight: '900', textTransform: 'capitalize' },
  small: { color: colors.muted, marginTop: 3 },
  count: { color: colors.green, fontWeight: '800', fontSize: 12 },
  empty: { color: colors.muted, textAlign: 'center', paddingVertical: 20 }
});
