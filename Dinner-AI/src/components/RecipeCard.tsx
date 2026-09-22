import { useRouter } from 'expo-router';
import React from 'react';
import { Image, Pressable, StyleSheet, Text, View } from 'react-native';
import { Recipe } from '@/src/types';
import { colors } from './ui';
import { hasRecipePhoto, RecipePhoto } from './RecipePhoto';

const CATEGORY_EMOJI: Record<Recipe['category'], string> = {
  breakfast: '☀️',
  lunch: '🥪',
  dinner: '🍽️',
  snack: '🍎',
  dessert: '🍰'
};

export function RecipeCard({ recipe, match, favorite }: { recipe: Recipe; match?: string; favorite?: boolean }) {
  const router = useRouter();

  return (
    <Pressable
      onPress={() => router.push(`/recipe/${recipe.id}`)}
      style={({ pressed }) => [styles.card, pressed && styles.pressed]}
    >
      {recipe.imageUrl ? (
        <Image source={{ uri: recipe.imageUrl }} style={styles.image} resizeMode="cover" />
      ) : hasRecipePhoto(recipe.id) ? (
        <RecipePhoto recipeId={recipe.id} height={168} />
      ) : (
        <View style={styles.imageFallback}>
          <Text style={styles.fallbackEmoji}>{CATEGORY_EMOJI[recipe.category]}</Text>
          <Text style={styles.fallbackText}>{recipe.category}</Text>
        </View>
      )}

      <View style={styles.body}>
        <View style={styles.titleRow}>
          <View style={styles.titleWrap}>
            <View style={styles.labelRow}>
              <Text style={styles.category}>{recipe.category.toUpperCase()}</Text>
              {recipe.generated ? <Text style={styles.aiBadge}>AI</Text> : null}
            </View>
            <Text style={styles.title} numberOfLines={2}>{recipe.title}</Text>
          </View>
          <Text style={[styles.heart, favorite && styles.heartActive]}>{favorite ? '♥' : '♡'}</Text>
        </View>

        <Text style={styles.description} numberOfLines={2}>{recipe.description}</Text>

        <View style={styles.metaRow}>
          <Text style={styles.meta}>{recipe.minutes} min</Text>
          {match ? <Text style={styles.dot}>•</Text> : null}
          {match ? <Text style={styles.match}>{match}</Text> : null}
        </View>
      </View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.card,
    borderRadius: 22,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: colors.border,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 5 },
    shadowOpacity: 0.05,
    shadowRadius: 13,
    elevation: 2
  },
  pressed: { opacity: 0.94, transform: [{ scale: 0.995 }] },
  image: { width: '100%', height: 168, backgroundColor: colors.greenSoft },
  imageFallback: {
    width: '100%', height: 150, backgroundColor: colors.greenSoft,
    alignItems: 'center', justifyContent: 'center'
  },
  fallbackEmoji: { fontSize: 34, marginBottom: 6 },
  fallbackText: { color: colors.greenDark, fontWeight: '900', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1.2 },
  body: { padding: 16, gap: 8 },
  titleRow: { flexDirection: 'row', alignItems: 'flex-start', gap: 12 },
  titleWrap: { flex: 1 },
  labelRow: { flexDirection: 'row', alignItems: 'center', gap: 7, marginBottom: 5 },
  category: { color: colors.green, fontWeight: '900', fontSize: 10, letterSpacing: 1.1 },
  aiBadge: { color: colors.greenDark, backgroundColor: colors.greenSoft, fontSize: 9, fontWeight: '900', paddingHorizontal: 6, paddingVertical: 3, borderRadius: 999, overflow: 'hidden' },
  title: { color: colors.text, fontSize: 19, lineHeight: 24, fontWeight: '900', letterSpacing: -0.25 },
  heart: { color: colors.muted, fontSize: 24, lineHeight: 25 },
  heartActive: { color: colors.orange },
  description: { color: colors.muted, fontSize: 14, lineHeight: 20 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: 2 },
  meta: { color: colors.text, fontWeight: '800', fontSize: 12 },
  dot: { color: colors.borderStrong, fontWeight: '900' },
  match: { color: colors.greenDark, fontWeight: '800', fontSize: 12 }
});
