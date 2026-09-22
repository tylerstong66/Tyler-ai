import { useRouter } from 'expo-router';
import React, { useMemo, useState } from 'react';
import { Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { RecipeCard } from '@/src/components/RecipeCard';
import { colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { RECIPES } from '@/src/data/recipes';
import { recommendRecipes } from '@/src/lib/recommendations';
import { MealCategory } from '@/src/types';

const MEALS: { key: MealCategory; label: string; emoji: string }[] = [
  { key: 'breakfast', label: 'Breakfast', emoji: '☀️' },
  { key: 'lunch', label: 'Lunch', emoji: '🥪' },
  { key: 'dinner', label: 'Dinner', emoji: '🍽️' },
  { key: 'snack', label: 'Snack', emoji: '🍎' },
  { key: 'dessert', label: 'Dessert', emoji: '🍰' }
];

export default function HomeScreen() {
  const router = useRouter();
  const { state } = useApp();
  const [mealCategory, setMealCategory] = useState<MealCategory>('dinner');
  const allRecipes = useMemo(() => [...state.generatedRecipes, ...RECIPES], [state.generatedRecipes]);
  const recs = useMemo(
    () => recommendRecipes(allRecipes, state, undefined, mealCategory).slice(0, 6),
    [allRecipes, mealCategory, state]
  );
  const featured = recs[0];
  const more = recs.slice(1);

  return (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <View style={styles.top}>
        <Text style={styles.brand}>DINNER AI</Text>
        <Text style={styles.hero}>What sounds good today?</Text>
        <Text style={styles.sub}>Ideas built around what you have and what you actually like.</Text>
      </View>

      <View style={styles.quickRow}>
        <QuickAction icon="📷" label="Scan fridge" onPress={() => router.push('/scan-fridge')} />
        <QuickAction icon="▦" label="Scan UPC" onPress={() => router.push('/scan-upc')} />
        <QuickAction icon="✨" label="Surprise me" onPress={() => router.push('/surprise')} />
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.mealFilters}>
        {MEALS.map((meal) => {
          const active = meal.key === mealCategory;
          return (
            <Pressable
              key={meal.key}
              onPress={() => setMealCategory(meal.key)}
              style={[styles.mealFilter, active && styles.mealFilterActive]}
            >
              <Text style={styles.mealEmoji}>{meal.emoji}</Text>
              <Text style={[styles.mealFilterText, active && styles.mealFilterTextActive]}>{meal.label}</Text>
            </Pressable>
          );
        })}
      </ScrollView>

      {featured ? (
        <Pressable
          onPress={() => router.push(`/recipe/${featured.recipe.id}`)}
          style={({ pressed }) => [styles.feature, pressed && styles.featurePressed]}
        >
          {featured.recipe.imageUrl ? (
            <Image source={{ uri: featured.recipe.imageUrl }} style={styles.featureImage} resizeMode="cover" />
          ) : null}
          <View style={featured.recipe.imageUrl ? styles.featureOverlay : styles.featureInner}>
          <View style={styles.featureTop}>
            <View style={styles.featureLabelWrap}>
              <Text style={styles.featureEyebrow}>TOP MATCH</Text>
              {featured.recipe.generated ? <Text style={styles.aiChip}>AI</Text> : null}
            </View>
            <Text style={styles.featureArrow}>›</Text>
          </View>
          <Text style={styles.featureTitle}>{featured.recipe.title}</Text>
          <Text style={styles.featureDescription} numberOfLines={2}>{featured.recipe.description}</Text>
          <View style={styles.featureMeta}>
            <Text style={styles.featurePill}>{featured.recipe.minutes} min</Text>
            <Text style={styles.featurePill}>{featured.matched}/{featured.total} on hand</Text>
          </View>
          </View>
        </Pressable>
      ) : (
        <View style={styles.emptyFeature}>
          <Text style={styles.emptyTitle}>Add a few kitchen items</Text>
          <Text style={styles.emptyText}>Dinner AI will start ranking recipes around what you already have.</Text>
        </View>
      )}

      <View style={styles.sectionHeading}>
        <View>
          <Text style={styles.sectionTitle}>More for you</Text>
          <Text style={styles.sectionSub}>Personalized {mealCategory} ideas</Text>
        </View>
        <Pressable onPress={() => router.push('/(tabs)/recipes')} hitSlop={8}>
          <Text style={styles.seeAll}>See all</Text>
        </Pressable>
      </View>

      <View style={styles.recipeList}>
        {more.length
          ? more.map(({ recipe, matched, total }) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                favorite={state.favorites.includes(recipe.id)}
                match={`${matched}/${total} on hand`}
              />
            ))
          : <Text style={styles.emptyText}>No more {mealCategory} ideas match your profile yet.</Text>}
      </View>
    </ScrollView>
  );
}

function QuickAction({ icon, label, onPress }: { icon: string; label: string; onPress: () => void }) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.quickAction, pressed && styles.quickPressed]}>
      <View style={styles.quickIcon}><Text style={styles.quickIconText}>{icon}</Text></View>
      <Text style={styles.quickLabel}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 44, backgroundColor: colors.bg },
  top: { marginBottom: 20 },
  brand: { color: colors.green, fontWeight: '900', fontSize: 11, letterSpacing: 1.9 },
  hero: { color: colors.text, fontSize: 34, lineHeight: 39, fontWeight: '900', letterSpacing: -0.9, marginTop: 7 },
  sub: { color: colors.muted, fontSize: 15.5, lineHeight: 22, marginTop: 8, maxWidth: 520 },

  quickRow: { flexDirection: 'row', gap: 10, marginBottom: 22 },
  quickAction: { flex: 1, alignItems: 'center', gap: 8 },
  quickPressed: { opacity: 0.72, transform: [{ scale: 0.98 }] },
  quickIcon: {
    width: 58, height: 58, borderRadius: 19, backgroundColor: colors.card,
    borderWidth: 1, borderColor: colors.border, alignItems: 'center', justifyContent: 'center',
    shadowColor: colors.shadow, shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.04, shadowRadius: 8, elevation: 1
  },
  quickIconText: { fontSize: 22 },
  quickLabel: { color: colors.text, fontWeight: '800', fontSize: 12, textAlign: 'center' },

  mealFilters: { gap: 8, paddingRight: 12, marginBottom: 20 },
  mealFilter: {
    flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: colors.card,
    borderWidth: 1, borderColor: colors.border, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 10
  },
  mealFilterActive: { backgroundColor: colors.greenDark, borderColor: colors.greenDark },
  mealEmoji: { fontSize: 14 },
  mealFilterText: { color: colors.text, fontWeight: '800', fontSize: 13 },
  mealFilterTextActive: { color: '#FFFFFF' },

  feature: {
    backgroundColor: colors.greenDark,
    borderRadius: 26,
    minHeight: 214,
    overflow: 'hidden',
    marginBottom: 27,
    shadowColor: colors.greenDark,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.16,
    shadowRadius: 18,
    elevation: 5
  },
  featureImage: { width: '100%', height: 245 },
  featureOverlay: {
    position: 'absolute',
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
    padding: 22,
    justifyContent: 'space-between',
    backgroundColor: 'rgba(19,49,35,0.56)'
  },
  featureInner: { padding: 22, minHeight: 214, justifyContent: 'space-between' },
  featurePressed: { opacity: 0.94, transform: [{ scale: 0.995 }] },
  featureTop: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  featureLabelWrap: { flexDirection: 'row', gap: 8, alignItems: 'center' },
  featureEyebrow: { color: '#D8EADF', fontSize: 10, fontWeight: '900', letterSpacing: 1.5 },
  aiChip: {
    color: colors.greenDark, backgroundColor: '#DDEFE4', fontSize: 9, fontWeight: '900',
    paddingHorizontal: 7, paddingVertical: 4, borderRadius: 999, overflow: 'hidden'
  },
  featureArrow: { color: '#FFFFFF', fontSize: 33, lineHeight: 33, fontWeight: '300' },
  featureTitle: { color: '#FFFFFF', fontSize: 28, lineHeight: 32, fontWeight: '900', letterSpacing: -0.6, marginTop: 25 },
  featureDescription: { color: '#DCE8E0', fontSize: 14.5, lineHeight: 21, marginTop: 8 },
  featureMeta: { flexDirection: 'row', gap: 8, marginTop: 18 },
  featurePill: {
    color: '#FFFFFF', backgroundColor: 'rgba(255,255,255,0.13)', borderRadius: 999,
    paddingHorizontal: 11, paddingVertical: 7, fontSize: 11.5, fontWeight: '800', overflow: 'hidden'
  },

  emptyFeature: { backgroundColor: colors.greenSoft, borderRadius: 24, padding: 22, marginBottom: 27 },
  emptyTitle: { color: colors.text, fontWeight: '900', fontSize: 19 },
  emptyText: { color: colors.muted, lineHeight: 21, marginTop: 6 },

  sectionHeading: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 13 },
  sectionTitle: { color: colors.text, fontSize: 23, fontWeight: '900', letterSpacing: -0.35 },
  sectionSub: { color: colors.muted, marginTop: 3, fontSize: 13 },
  seeAll: { color: colors.greenDark, fontWeight: '900', fontSize: 13 },
  recipeList: { gap: 13 }
});
