import { useRouter } from 'expo-router';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Recipe } from '@/src/types';
import { Card, Pill, colors } from './ui';

export function RecipeCard({ recipe, match, favorite }: { recipe: Recipe; match?: string; favorite?: boolean }) {
  const router = useRouter();

  return (
    <Pressable
      onPress={() => router.push(`/recipe/${recipe.id}`)}
      style={({ pressed }) => pressed ? styles.pressed : undefined}
    >
      <Card style={styles.card}>
        <View style={styles.topRow}>
          <View style={styles.titleWrap}>
            <View style={styles.titleLine}>
              <Text style={styles.title}>{recipe.title}</Text>
              {recipe.generated ? <Text style={styles.aiBadge}>AI</Text> : null}
            </View>
            <Text style={styles.description} numberOfLines={3}>{recipe.description}</Text>
          </View>
          <View style={[styles.favoriteCircle, favorite && styles.favoriteCircleActive]}>
            <Text style={[styles.heart, favorite && styles.heartActive]}>{favorite ? '♥' : '♡'}</Text>
          </View>
        </View>

        <View style={styles.footer}>
          <View style={styles.pills}>
            <Pill>{recipe.category.charAt(0).toUpperCase() + recipe.category.slice(1)}</Pill>
            <Pill>{recipe.minutes} min</Pill>
          </View>
          {match ? <Text style={styles.match}>{match}</Text> : null}
        </View>
      </Card>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  pressed: { opacity: 0.92, transform: [{ scale: 0.995 }] },
  card: { gap: 15 },
  topRow: { flexDirection: 'row', gap: 14, alignItems: 'flex-start' },
  titleWrap: { flex: 1 },
  titleLine: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 7 },
  title: { flexShrink: 1, color: colors.text, fontSize: 19, lineHeight: 24, fontWeight: '900' },
  aiBadge: {
    color: colors.greenDark,
    backgroundColor: colors.greenSoft,
    fontSize: 10,
    fontWeight: '900',
    paddingHorizontal: 7,
    paddingVertical: 4,
    borderRadius: 999,
    overflow: 'hidden'
  },
  description: { color: colors.muted, lineHeight: 21, fontSize: 14.5 },
  favoriteCircle: {
    width: 38,
    height: 38,
    borderRadius: 19,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center'
  },
  favoriteCircleActive: { backgroundColor: '#FFF2EA', borderColor: '#F1D7C8' },
  heart: { fontSize: 21, color: colors.muted, lineHeight: 23 },
  heartActive: { color: colors.orange },
  footer: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 10 },
  pills: { flexDirection: 'row', gap: 7, flexWrap: 'wrap', flexShrink: 1 },
  match: {
    color: colors.greenDark,
    backgroundColor: colors.greenFaint,
    borderRadius: 999,
    paddingHorizontal: 9,
    paddingVertical: 6,
    fontWeight: '800',
    fontSize: 11,
    overflow: 'hidden'
  }
});
