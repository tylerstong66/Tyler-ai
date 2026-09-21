import { useRouter } from 'expo-router';
import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { Recipe } from '@/src/types';
import { Card, Pill, colors } from './ui';

export function RecipeCard({ recipe, match, favorite }: { recipe: Recipe; match?: string; favorite?: boolean }) {
  const router = useRouter();
  return (
    <Pressable onPress={() => router.push(`/recipe/${recipe.id}`)}>
      <Card style={styles.card}>
        <View style={styles.row}>
          <View style={styles.titleWrap}>
            <View style={styles.titleLine}><Text style={styles.title}>{recipe.title}</Text>{recipe.generated ? <Text style={styles.aiBadge}>AI</Text> : null}</View>
            <Text style={styles.description}>{recipe.description}</Text>
          </View>
          <Text style={styles.heart}>{favorite ? '♥' : '♡'}</Text>
        </View>
        <View style={styles.meta}>
          <View style={styles.pills}><Pill>{recipe.category.charAt(0).toUpperCase() + recipe.category.slice(1)}</Pill><Pill>{recipe.minutes} min</Pill></View>
          {match ? <Text style={styles.match}>{match}</Text> : null}
        </View>
      </Card>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: { gap: 12 },
  row: { flexDirection: 'row', gap: 12 },
  titleWrap: { flex: 1 },
  titleLine: { flexDirection: 'row', alignItems: 'center', gap: 7, marginBottom: 5 },
  title: { flexShrink: 1, color: colors.text, fontSize: 18, fontWeight: '800' },
  aiBadge: { color: colors.green, backgroundColor: colors.greenSoft, fontSize: 10, fontWeight: '900', paddingHorizontal: 6, paddingVertical: 3, borderRadius: 99 },
  description: { color: colors.muted, lineHeight: 20 },
  heart: { fontSize: 24, color: colors.orange },
  meta: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', gap: 8 },
  pills: { flexDirection: 'row', gap: 6, flexWrap: 'wrap' },
  match: { color: colors.muted, fontWeight: '600', fontSize: 12 }
});
