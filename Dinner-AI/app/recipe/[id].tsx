import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useMemo, useState } from 'react';
import { Alert, Image, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { FeedbackButtons } from '@/src/components/FeedbackButtons';
import { hasRecipePhoto, RecipePhoto } from '@/src/components/RecipePhoto';
import { Card, Pill, PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { RECIPES } from '@/src/data/recipes';
import { scoreRecipe } from '@/src/lib/recommendations';
import { scaledIngredients } from '@/src/lib/servings';
import { deriveRecipeMissingIngredients } from '@/src/lib/shopping';
import { RecipeFeedbackRating } from '@/src/types';

export default function RecipeDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  const { state, toggleFavorite, markRecipeChosen, setRecipeFeedback, addRecipeMissingToShoppingList } = useApp();
  const recipe = [...state.generatedRecipes, ...RECIPES].find((item) => item.id === id);
  const baseServings = recipe?.servings || 4;
  const [servings, setServings] = useState(baseServings);

  const ingredients = useMemo(
    () => recipe ? scaledIngredients(recipe.ingredients, baseServings, servings) : [],
    [recipe, baseServings, servings]
  );

  if (!recipe) {
    return <View style={styles.center}><Text style={styles.title}>Recipe not found.</Text></View>;
  }

  const scaledRecipe = { ...recipe, servings, ingredients };
  const match = scoreRecipe(recipe, state);
  const favorite = state.favorites.includes(recipe.id);
  const feedback = state.recipeFeedback[recipe.id]?.rating;
  const missingIngredients = deriveRecipeMissingIngredients(scaledRecipe, state.pantry);

  function chooseRecipe() {
    markRecipeChosen(scaledRecipe);
    const missing = missingIngredients.length;
    Alert.alert(
      `${recipe!.category.charAt(0).toUpperCase() + recipe!.category.slice(1)} selected`,
      missing
        ? 'InDinecision added the missing ingredients to your shopping list.'
        : 'This meal was added to your learning history.'
    );
  }

  function startCookMode() {
    markRecipeChosen(scaledRecipe);
    router.push({ pathname: '/cook/[id]', params: { id: recipe!.id, servings: String(servings) } });
  }

  function addMissing() {
    addRecipeMissingToShoppingList(scaledRecipe);
    Alert.alert('Shopping list updated', 'Missing ingredients were added without creating duplicates.');
  }

  function rateRecipe(rating: RecipeFeedbackRating) {
    setRecipeFeedback(recipe!, rating);
  }

  return (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      {recipe.imageUrl ? (
        <Image source={{ uri: recipe.imageUrl }} style={styles.heroImage} resizeMode="cover" />
      ) : hasRecipePhoto(recipe.id) ? (
        <RecipePhoto recipeId={recipe.id} height={240} style={styles.heroImage} />
      ) : (
        <View style={styles.heroFallback}>
          <Text style={styles.heroFallbackEmoji}>
            {recipe.category === 'dessert' ? '🍰' : recipe.category === 'breakfast' ? '☀️' : recipe.category === 'lunch' ? '🥪' : recipe.category === 'snack' ? '🍎' : '🍽️'}
          </Text>
        </View>
      )}

      <View>
        <View style={styles.badges}>
          {recipe.generated ? <Pill>AI creation</Pill> : null}
          <Pill>{recipe.category.charAt(0).toUpperCase() + recipe.category.slice(1)}</Pill>
          <Pill>{recipe.minutes} min</Pill>
        </View>
        <Text style={styles.title}>{recipe.title}</Text>
        <Text style={styles.description}>{recipe.description}</Text>
        <Text style={styles.match}>{match.matched}/{match.total} pantry ingredients matched</Text>
        {recipe.generationReason ? <Text style={styles.reason}>{recipe.generationReason}</Text> : null}
      </View>

      <View style={styles.servingPanel}>
        <View>
          <Text style={styles.servingLabel}>SERVINGS</Text>
          <Text style={styles.servingHelp}>Ingredient amounts update automatically.</Text>
        </View>
        <View style={styles.servingControls}>
          <Pressable onPress={() => setServings((value) => Math.max(1, value - 1))} style={styles.servingButton}>
            <Text style={styles.servingButtonText}>−</Text>
          </Pressable>
          <Text style={styles.servingNumber}>{servings}</Text>
          <Pressable onPress={() => setServings((value) => Math.min(12, value + 1))} style={styles.servingButton}>
            <Text style={styles.servingButtonText}>+</Text>
          </Pressable>
        </View>
      </View>

      {missingIngredients.length ? (
        <Card>
          <Text style={styles.section}>You may still need</Text>
          {missingIngredients.map((ingredient) => <Text key={ingredient} style={styles.line}>• {ingredient}</Text>)}
          <View style={styles.cardButton}><SecondaryButton label="🛒 Add missing items to shopping list" onPress={addMissing} /></View>
        </Card>
      ) : null}

      <Card>
        <Text style={styles.section}>Ingredients · {servings} servings</Text>
        {ingredients.map((ingredient) => <Text key={ingredient} style={styles.line}>• {ingredient}</Text>)}
      </Card>

      <Card>
        <Text style={styles.section}>Directions</Text>
        {recipe.instructions.map((instruction, index) => (
          <View key={`${index}-${instruction}`} style={styles.step}>
            <Text style={styles.number}>{index + 1}</Text>
            <Text style={styles.stepText}>{instruction}</Text>
          </View>
        ))}
      </Card>

      {recipe.allergens.length ? <Text style={styles.allergen}>Contains/flags: {recipe.allergens.join(', ')}. Verify labels and cross-contact risks yourself.</Text> : null}
      {recipe.safetyNotes ? <Text style={styles.allergen}>{recipe.safetyNotes}</Text> : null}
      {recipe.generated && state.profile.allergies.length ? <Text style={styles.allergen}>AI-generated recipes are not a medical allergy guarantee. Independently verify every ingredient.</Text> : null}

      <PrimaryButton label="👨‍🍳 Start Cook Mode" onPress={startCookMode} />
      <SecondaryButton label="I’m making this" onPress={chooseRecipe} />
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
  content: { paddingHorizontal: 20, paddingTop: 16, gap: 16, backgroundColor: colors.bg, paddingBottom: 44 },
  heroImage: { width: '100%', height: 240, borderRadius: 24, backgroundColor: colors.greenSoft },
  heroFallback: { width: '100%', height: 190, borderRadius: 24, backgroundColor: colors.greenSoft, alignItems: 'center', justifyContent: 'center' },
  heroFallbackEmoji: { fontSize: 44 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
  badges: { flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 12 },
  title: { color: colors.text, fontSize: 31, lineHeight: 37, fontWeight: '900', letterSpacing: -0.5 },
  description: { color: colors.muted, lineHeight: 23, fontSize: 15.5, marginTop: 8 },
  match: { alignSelf: 'flex-start', color: colors.greenDark, backgroundColor: colors.greenSoft, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 6, fontWeight: '900', fontSize: 11.5, marginTop: 12, overflow: 'hidden' },
  reason: { color: colors.greenDark, lineHeight: 20, fontSize: 13, fontWeight: '700', marginTop: 10 },
  servingPanel: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 16, backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 20, padding: 16 },
  servingLabel: { color: colors.green, fontSize: 10, fontWeight: '900', letterSpacing: 1.3 },
  servingHelp: { color: colors.muted, fontSize: 12, marginTop: 4 },
  servingControls: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  servingButton: { width: 38, height: 38, borderRadius: 13, backgroundColor: colors.greenSoft, alignItems: 'center', justifyContent: 'center' },
  servingButtonText: { color: colors.greenDark, fontSize: 23, lineHeight: 25, fontWeight: '700' },
  servingNumber: { minWidth: 24, textAlign: 'center', color: colors.text, fontSize: 20, fontWeight: '900' },
  section: { color: colors.text, fontSize: 19, lineHeight: 24, fontWeight: '900', marginBottom: 11 },
  line: { color: colors.text, lineHeight: 26, fontSize: 15 },
  step: { flexDirection: 'row', gap: 11, marginBottom: 14 },
  number: { width: 29, height: 29, borderRadius: 15, backgroundColor: colors.greenSoft, color: colors.greenDark, textAlign: 'center', paddingTop: 4, fontWeight: '900' },
  stepText: { flex: 1, color: colors.text, lineHeight: 23, fontSize: 15 },
  allergen: { color: colors.danger, lineHeight: 20, fontSize: 13 },
  cardButton: { marginTop: 12 },
  feedbackCard: { gap: 11, backgroundColor: colors.surfaceGreen, borderColor: colors.borderStrong },
  feedbackHelp: { color: colors.muted, lineHeight: 19, marginTop: -5, marginBottom: 2 },
  neverNote: { color: colors.orange, fontSize: 12, lineHeight: 18, fontWeight: '700' }
});
