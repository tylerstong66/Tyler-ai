import { useLocalSearchParams, useRouter } from 'expo-router';
import React from 'react';
import { Alert, ScrollView, StyleSheet, Text, View } from 'react-native';
import { FeedbackButtons } from '@/src/components/FeedbackButtons';
import { Card, Pill, PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { RECIPES } from '@/src/data/recipes';
import { scoreRecipe } from '@/src/lib/recommendations';
import { RecipeFeedbackRating } from '@/src/types';

export default function RecipeDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { state, toggleFavorite, markRecipeChosen, setRecipeFeedback, addRecipeMissingToShoppingList } = useApp();
  const recipe = [...state.generatedRecipes, ...RECIPES].find((item) => item.id === id);

  if (!recipe) {
    return <View style={styles.center}><Text style={styles.title}>Recipe not found.</Text></View>;
  }

  const match = scoreRecipe(recipe, state);
  const favorite = state.favorites.includes(recipe.id);
  const feedback = state.recipeFeedback[recipe.id]?.rating;

  function chooseRecipe() {
    markRecipeChosen(recipe!);
    const missing = recipe!.missingIngredients?.length ?? 0;
    Alert.alert(
      `${recipe!.category.charAt(0).toUpperCase() + recipe!.category.slice(1)} selected`,
      missing
        ? 'Dinner AI added any missing ingredients that were not already on your shopping list.'
        : 'This meal was added to your learning history.'
    );
  }

  function addMissing() {
    addRecipeMissingToShoppingList(recipe!);
    Alert.alert('Shopping list updated', 'Missing ingredients were added without creating duplicates.');
  }

  function rateRecipe(rating: RecipeFeedbackRating) {
    setRecipeFeedback(recipe!, rating);
  }

  return (
    <ScrollView contentContainerStyle={styles.content}>
      <View>
        <View style={styles.badges}>
          {recipe.generated ? <Pill>AI creation</Pill> : null}
          <Pill>{recipe.category.charAt(0).toUpperCase() + recipe.category.slice(1)}</Pill>
          <Pill>{recipe.minutes} min</Pill>
          {recipe.servings ? <Pill>{recipe.servings} servings</Pill> : null}
        </View>
        <Text style={styles.title}>{recipe.title}</Text>
        <Text style={styles.description}>{recipe.description}</Text>
        <Text style={styles.match}>{match.matched}/{match.total} pantry ingredients matched</Text>
        {recipe.generationReason ? <Text style={styles.reason}>{recipe.generationReason}</Text> : null}
      </View>

      {recipe.missingIngredients?.length ? (
        <Card>
          <Text style={styles.section}>You may still need</Text>
          {recipe.missingIngredients.map((ingredient) => <Text key={ingredient} style={styles.line}>• {ingredient}</Text>)}
          <View style={styles.cardButton}><SecondaryButton label="🛒 Add missing items to shopping list" onPress={addMissing} /></View>
        </Card>
      ) : null}

      <Card>
        <Text style={styles.section}>Ingredients</Text>
        {recipe.ingredients.map((ingredient) => <Text key={ingredient} style={styles.line}>• {ingredient}</Text>)}
      </Card>

      <Card>
        <Text style={styles.section}>Directions</Text>
        {recipe.instructions.map((instruction, index) => (
          <View key={`${index}-${instruction}`} style={styles.step}><Text style={styles.number}>{index + 1}</Text><Text style={styles.stepText}>{instruction}</Text></View>
        ))}
      </Card>

      {recipe.allergens.length ? <Text style={styles.allergen}>Contains/flags: {recipe.allergens.join(', ')}. Verify labels and cross-contact risks yourself.</Text> : null}
      {recipe.safetyNotes ? <Text style={styles.allergen}>{recipe.safetyNotes}</Text> : null}
      {recipe.generated && state.profile.allergies.length ? <Text style={styles.allergen}>AI-generated recipes are not a medical allergy guarantee. Independently verify every ingredient.</Text> : null}

      <PrimaryButton label="I’m making this" onPress={chooseRecipe} />
      <SecondaryButton label={favorite ? 'Remove from favorites' : 'Save to favorites'} onPress={() => toggleFavorite(recipe.id)} />

      <Card style={styles.feedbackCard}>
        <Text style={styles.section}>How was it?</Text>
        <Text style={styles.feedbackHelp}>Your answer trains future recommendations. You can change it anytime.</Text>
        <FeedbackButtons value={feedback} onChange={rateRecipe} />
        {feedback === 'never' ? <Text style={styles.neverNote}>This exact recipe will no longer appear in your normal recommendations, and similar recipes will be ranked lower.</Text> : null}
      </Card>

      {state.shoppingList.length ? <SecondaryButton label="View shopping list" onPress={() => router.push('/(tabs)/shopping')} /> : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 18, gap: 14, backgroundColor: colors.bg, paddingBottom: 36 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
  badges: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 10 },
  title: { color: colors.text, fontSize: 30, fontWeight: '900' },
  description: { color: colors.muted, lineHeight: 22, fontSize: 16, marginTop: 7 },
  match: { color: colors.muted, fontWeight: '700', fontSize: 12, marginTop: 10 },
  reason: { color: colors.green, lineHeight: 20, fontSize: 13, fontWeight: '700', marginTop: 8 },
  section: { color: colors.text, fontSize: 19, fontWeight: '900', marginBottom: 10 },
  line: { color: colors.text, lineHeight: 25 },
  step: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  number: { width: 26, height: 26, borderRadius: 13, backgroundColor: colors.greenSoft, color: colors.green, textAlign: 'center', paddingTop: 3, fontWeight: '900' },
  stepText: { flex: 1, color: colors.text, lineHeight: 22 },
  allergen: { color: colors.danger, lineHeight: 20, fontSize: 13 },
  cardButton: { marginTop: 12 },
  feedbackCard: { gap: 10 },
  feedbackHelp: { color: colors.muted, lineHeight: 19, marginTop: -5, marginBottom: 2 },
  neverNote: { color: colors.orange, fontSize: 12, lineHeight: 18, fontWeight: '700' }
});
