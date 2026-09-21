import React, { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { FeedbackButtons } from '@/src/components/FeedbackButtons';
import { Card, Pill, PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { generateAIRecipe } from '@/src/lib/aiRecipes';
import { createPantrySurprise } from '@/src/lib/recommendations';
import { MealCategory, Recipe, RecipeFeedbackRating, TimeBucket } from '@/src/types';

const TIMES: { key: TimeBucket; label: string }[] = [
  { key: 'quick', label: '≤30 min' },
  { key: 'medium', label: '30 min–2 hr' },
  { key: 'long', label: '2+ hr' }
];
const MEALS: MealCategory[] = ['breakfast', 'lunch', 'dinner', 'snack', 'dessert'];

export default function SurpriseScreen() {
  const { state, markRecipeChosen, saveGeneratedRecipe, setRecipeFeedback, addRecipeMissingToShoppingList } = useApp();
  const fallback = useMemo(() => createPantrySurprise(state, 'quick', 'dinner'), []);
  const [recipe, setRecipe] = useState<Recipe>(fallback);
  const [time, setTime] = useState<TimeBucket>('quick');
  const [meal, setMeal] = useState<MealCategory>('dinner');
  const [loading, setLoading] = useState(false);
  const [source, setSource] = useState<'local' | 'ai'>('local');
  const [message, setMessage] = useState('');
  const [chosen, setChosen] = useState(false);

  useEffect(() => { void generate('quick', 'dinner', false); }, []);

  async function generate(nextTime = time, nextMeal = meal, notify = true) {
    if (!state.pantry.length) {
      if (notify) Alert.alert('Kitchen inventory is empty', 'Add or scan a few ingredients first.');
      return;
    }
    setLoading(true);
    setMessage('');
    try {
      const result = await generateAIRecipe(state, nextTime, nextMeal);
      setRecipe(result.recipe);
      saveGeneratedRecipe(result.recipe);
      setSource('ai');
      setChosen(false);
    } catch (e: any) {
      const text = e?.message === 'AI_BACKEND_NOT_CONFIGURED' ? 'AI backend is not configured, so Dinner AI used its local fallback.' : (e?.message || 'AI generation is unavailable right now.');
      setMessage(text);
      setRecipe(createPantrySurprise(state, nextTime, nextMeal));
      setSource('local');
      setChosen(false);
      if (notify) Alert.alert('Using fallback recipe', text);
    } finally {
      setLoading(false);
    }
  }

  function choose() {
    markRecipeChosen(recipe);
    setChosen(true);
    Alert.alert('Meal selected', recipe.missingIngredients?.length ? 'Missing items were added to your shopping list.' : 'This choice was added to Dinner AI’s learning history.');
  }

  function rate(rating: RecipeFeedbackRating) {
    setRecipeFeedback(recipe, rating);
  }

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <Text style={styles.kicker}>AI MEAL GENERATOR</Text>
      <Text style={styles.heading}>Choose a meal</Text>
      <View style={styles.rowWrap}>
        {MEALS.map((option) => {
          const active = option === meal;
          return <Pressable key={option} onPress={() => setMeal(option)} style={[styles.choice, active && styles.choiceActive]}><Text style={[styles.choiceText, active && styles.choiceTextActive]}>{cap(option)}</Text></Pressable>;
        })}
      </View>

      <Text style={styles.heading}>How much time?</Text>
      <View style={styles.timeRow}>
        {TIMES.map((option) => {
          const active = option.key === time;
          return <Pressable key={option.key} onPress={() => setTime(option.key)} style={[styles.time, active && styles.choiceActive]}><Text style={[styles.choiceText, active && styles.choiceTextActive]}>{option.label}</Text></Pressable>;
        })}
      </View>

      <PrimaryButton label={loading ? 'Creating…' : `✨ Generate ${meal}`} onPress={() => void generate()} disabled={loading} />
      {loading ? <ActivityIndicator color={colors.green} /> : null}
      {message ? <Text style={styles.warning}>{message}</Text> : null}

      <View style={styles.rowWrap}>
        <Pill>{cap(recipe.category)}</Pill><Pill>{source === 'ai' ? 'AI generated' : 'Local fallback'}</Pill><Pill>{recipe.minutes} min</Pill>
      </View>
      <Text style={styles.title}>{recipe.title}</Text>
      <Text style={styles.description}>{recipe.description}</Text>
      {recipe.generationReason ? <Text style={styles.reason}>{recipe.generationReason}</Text> : null}

      {recipe.missingIngredients?.length ? (
        <Card>
          <Text style={styles.section}>You may still need</Text>
          {recipe.missingIngredients.map((x) => <Text key={x} style={styles.line}>• {x}</Text>)}
          <View style={styles.topGap}><SecondaryButton label="🛒 Add these to shopping list" onPress={() => addRecipeMissingToShoppingList(recipe)} /></View>
        </Card>
      ) : null}

      <Card><Text style={styles.section}>Ingredients</Text>{recipe.ingredients.map((x) => <Text key={x} style={styles.line}>• {x}</Text>)}</Card>
      <Card>
        <Text style={styles.section}>Directions</Text>
        {recipe.instructions.map((step, i) => <View key={`${i}-${step}`} style={styles.step}><Text style={styles.number}>{i + 1}</Text><Text style={styles.stepText}>{step}</Text></View>)}
      </Card>

      {state.profile.allergies.length ? <Text style={styles.allergy}>AI allergy filtering is not a medical guarantee. Verify labels, ingredients, and cross-contact yourself.</Text> : null}
      <PrimaryButton label="I’ll make this" onPress={choose} disabled={loading} />
      {chosen || state.recipeFeedback[recipe.id] ? (
        <Card>
          <Text style={styles.section}>How was it?</Text>
          <FeedbackButtons value={state.recipeFeedback[recipe.id]?.rating} onChange={rate} />
        </Card>
      ) : null}
      <SecondaryButton label="Give me another" onPress={() => void generate()} />
    </ScrollView>
  );
}

const cap = (v: string) => v.charAt(0).toUpperCase() + v.slice(1);

const styles = StyleSheet.create({
  content: { padding: 18, gap: 14, backgroundColor: colors.bg, paddingBottom: 36 },
  kicker: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.2 },
  heading: { color: colors.text, fontSize: 20, fontWeight: '900' },
  rowWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  choice: { borderWidth: 1, borderColor: colors.border, borderRadius: 99, paddingHorizontal: 14, paddingVertical: 9, backgroundColor: '#fff' },
  choiceActive: { backgroundColor: colors.green, borderColor: colors.green },
  choiceText: { color: colors.text, fontWeight: '800' },
  choiceTextActive: { color: '#fff' },
  timeRow: { flexDirection: 'row', gap: 8 },
  time: { flex: 1, alignItems: 'center', borderWidth: 1, borderColor: colors.border, borderRadius: 13, paddingVertical: 12, backgroundColor: '#fff' },
  warning: { color: colors.orange, fontSize: 12, lineHeight: 18 },
  title: { color: colors.text, fontSize: 30, lineHeight: 35, fontWeight: '900' },
  description: { color: colors.muted, lineHeight: 22, fontSize: 16 },
  reason: { color: colors.green, lineHeight: 20, fontSize: 13, fontWeight: '700' },
  section: { color: colors.text, fontSize: 19, fontWeight: '900', marginBottom: 10 },
  line: { color: colors.text, lineHeight: 25 },
  step: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  number: { width: 26, height: 26, borderRadius: 13, backgroundColor: colors.greenSoft, color: colors.green, textAlign: 'center', paddingTop: 3, fontWeight: '900' },
  stepText: { flex: 1, color: colors.text, lineHeight: 22 },
  allergy: { color: colors.danger, fontSize: 12, lineHeight: 18, fontWeight: '600' },
  topGap: { marginTop: 12 }
});
