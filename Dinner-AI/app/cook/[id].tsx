import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';
import { PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { RECIPES } from '@/src/data/recipes';
import { ingredientsForStep, scaledIngredients, suggestedTimerSeconds } from '@/src/lib/servings';

export default function CookModeScreen() {
  const { id, servings: servingsParam } = useLocalSearchParams<{ id: string; servings?: string }>();
  const router = useRouter();
  const { state, setRecipeFeedback } = useApp();
  const recipe = [...state.generatedRecipes, ...RECIPES].find((item) => item.id === id);
  const baseServings = recipe?.servings || 4;
  const requestedServings = Math.max(1, Math.min(12, Number(servingsParam) || baseServings));
  const [stepIndex, setStepIndex] = useState(0);
  const [remaining, setRemaining] = useState(0);
  const [initialTimer, setInitialTimer] = useState(0);
  const [running, setRunning] = useState(false);
  const completedRef = useRef(false);

  const ingredients = useMemo(
    () => recipe ? scaledIngredients(recipe.ingredients, baseServings, requestedServings) : [],
    [recipe, baseServings, requestedServings]
  );
  const step = recipe?.instructions[stepIndex] || '';
  const currentIngredients = useMemo(() => ingredientsForStep(ingredients, step), [ingredients, step]);

  useEffect(() => {
    const seconds = suggestedTimerSeconds(step) || 0;
    setInitialTimer(seconds);
    setRemaining(seconds);
    setRunning(false);
    completedRef.current = false;
  }, [stepIndex, step]);

  useEffect(() => {
    if (!running || remaining <= 0) return;
    const id = setInterval(() => {
      setRemaining((current) => {
        if (current <= 1) {
          setRunning(false);
          if (!completedRef.current) {
            completedRef.current = true;
            setTimeout(() => Alert.alert('Timer finished', 'This cooking step is ready for your attention.'), 50);
          }
          return 0;
        }
        return current - 1;
      });
    }, 1000);
    return () => clearInterval(id);
  }, [running, remaining]);

  if (!recipe) {
    return <View style={styles.center}><Text style={styles.title}>Recipe not found.</Text></View>;
  }

  const totalSteps = recipe.instructions.length;
  const isLast = stepIndex === totalSteps - 1;

  function resetTimer(seconds = initialTimer) {
    completedRef.current = false;
    setRemaining(seconds);
    setRunning(false);
  }

  function finishCooking() {
    Alert.alert('Dinner is ready', 'How did this recipe turn out?', [
      { text: 'Love it', onPress: () => { setRecipeFeedback(recipe!, 'love'); router.back(); } },
      { text: 'It was okay', onPress: () => { setRecipeFeedback(recipe!, 'okay'); router.back(); } },
      { text: 'Rate later', style: 'cancel', onPress: () => router.back() }
    ]);
  }

  return (
    <View style={styles.screen}>
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: ((stepIndex + 1) / totalSteps * 100) + '%' }]} />
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.topRow}>
          <Text style={styles.kicker}>COOK MODE</Text>
          <Text style={styles.progressText}>Step {stepIndex + 1} of {totalSteps}</Text>
        </View>

        <Text style={styles.recipeTitle}>{recipe.title}</Text>

        <View style={styles.stepCard}>
          <View style={styles.stepNumber}><Text style={styles.stepNumberText}>{stepIndex + 1}</Text></View>
          <Text style={styles.stepText}>{step}</Text>
        </View>

        <View style={styles.ingredientsBlock}>
          <Text style={styles.sectionTitle}>For this step</Text>
          {currentIngredients.length ? currentIngredients.map((item) => (
            <Text key={item} style={styles.ingredient}>• {item}</Text>
          )) : (
            <Text style={styles.helper}>Continue with the ingredients already in use. Check the full list below if needed.</Text>
          )}
        </View>

        {initialTimer > 0 ? (
          <View style={styles.timerCard}>
            <Text style={styles.timerLabel}>STEP TIMER</Text>
            <Text style={styles.timer}>{formatClock(remaining)}</Text>
            <View style={styles.timerButtons}>
              <Pressable onPress={() => setRunning((value) => !value)} style={styles.timerPrimary}>
                <Text style={styles.timerPrimaryText}>{running ? 'Pause' : remaining === 0 ? 'Restart' : 'Start'}</Text>
              </Pressable>
              <Pressable onPress={() => resetTimer()} style={styles.timerSecondary}>
                <Text style={styles.timerSecondaryText}>Reset</Text>
              </Pressable>
              <Pressable onPress={() => { const next = remaining + 60; setRemaining(next); if (!initialTimer) setInitialTimer(next); }} style={styles.timerSecondary}>
                <Text style={styles.timerSecondaryText}>+1 min</Text>
              </Pressable>
            </View>
          </View>
        ) : (
          <Pressable onPress={() => { setInitialTimer(300); setRemaining(300); }} style={styles.addTimer}>
            <Text style={styles.addTimerText}>＋ Add a 5-minute timer</Text>
          </Pressable>
        )}

        {recipe.safetyNotes ? (
          <View style={styles.safety}>
            <Text style={styles.safetyTitle}>Temperature & safety</Text>
            <Text style={styles.safetyText}>{recipe.safetyNotes}</Text>
          </View>
        ) : null}

        <View style={styles.fullIngredients}>
          <Text style={styles.sectionTitle}>Full ingredient list · {requestedServings} servings</Text>
          {ingredients.map((item) => <Text key={item} style={styles.ingredient}>• {item}</Text>)}
        </View>
      </ScrollView>

      <View style={styles.footer}>
        <View style={styles.footerHalf}>
          <SecondaryButton
            label={stepIndex === 0 ? 'Recipe' : 'Back'}
            onPress={() => stepIndex === 0 ? router.back() : setStepIndex((value) => value - 1)}
          />
        </View>
        <View style={styles.footerHalf}>
          <PrimaryButton
            label={isLast ? 'Finish cooking' : 'Next step'}
            onPress={() => isLast ? finishCooking() : setStepIndex((value) => value + 1)}
          />
        </View>
      </View>
    </View>
  );
}

function formatClock(seconds: number) {
  const safe = Math.max(0, seconds);
  const hours = Math.floor(safe / 3600);
  const minutes = Math.floor((safe % 3600) / 60);
  const secs = safe % 60;
  if (hours) return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  progressTrack: { height: 4, backgroundColor: colors.greenSoft },
  progressFill: { height: 4, backgroundColor: colors.green },
  content: { paddingHorizontal: 20, paddingTop: 20, paddingBottom: 130 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
  topRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  kicker: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.7 },
  progressText: { color: colors.muted, fontSize: 12, fontWeight: '800' },
  recipeTitle: { color: colors.text, fontSize: 24, lineHeight: 29, fontWeight: '900', letterSpacing: -0.4, marginTop: 8, marginBottom: 22 },
  title: { color: colors.text, fontSize: 24, fontWeight: '900' },
  stepCard: { backgroundColor: colors.card, borderRadius: 25, borderWidth: 1, borderColor: colors.border, padding: 20, gap: 15 },
  stepNumber: { width: 38, height: 38, borderRadius: 19, backgroundColor: colors.greenDark, alignItems: 'center', justifyContent: 'center' },
  stepNumberText: { color: '#fff', fontSize: 16, fontWeight: '900' },
  stepText: { color: colors.text, fontSize: 20, lineHeight: 30, fontWeight: '800' },
  ingredientsBlock: { marginTop: 24 },
  sectionTitle: { color: colors.text, fontSize: 17, fontWeight: '900', marginBottom: 10 },
  ingredient: { color: colors.text, fontSize: 15, lineHeight: 25 },
  helper: { color: colors.muted, fontSize: 14, lineHeight: 21 },
  timerCard: { marginTop: 24, padding: 20, backgroundColor: colors.greenDark, borderRadius: 24, alignItems: 'center' },
  timerLabel: { color: '#CFE3D6', fontSize: 10, fontWeight: '900', letterSpacing: 1.4 },
  timer: { color: '#fff', fontSize: 50, lineHeight: 60, fontWeight: '900', fontVariant: ['tabular-nums'], marginTop: 5, marginBottom: 14 },
  timerButtons: { flexDirection: 'row', gap: 8, width: '100%' },
  timerPrimary: { flex: 1.2, minHeight: 44, borderRadius: 14, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  timerPrimaryText: { color: colors.greenDark, fontWeight: '900' },
  timerSecondary: { flex: 1, minHeight: 44, borderRadius: 14, backgroundColor: 'rgba(255,255,255,0.12)', alignItems: 'center', justifyContent: 'center' },
  timerSecondaryText: { color: '#fff', fontWeight: '800', fontSize: 12 },
  addTimer: { marginTop: 22, alignSelf: 'flex-start', backgroundColor: colors.greenSoft, borderRadius: 999, paddingHorizontal: 14, paddingVertical: 10 },
  addTimerText: { color: colors.greenDark, fontSize: 13, fontWeight: '900' },
  safety: { marginTop: 24, backgroundColor: '#FFF7EB', borderRadius: 18, padding: 16 },
  safetyTitle: { color: colors.orange, fontSize: 14, fontWeight: '900', marginBottom: 5 },
  safetyText: { color: colors.text, fontSize: 13, lineHeight: 20 },
  fullIngredients: { marginTop: 28, paddingBottom: 20 },
  footer: { position: 'absolute', left: 0, right: 0, bottom: 0, paddingHorizontal: 20, paddingTop: 12, paddingBottom: 18, flexDirection: 'row', gap: 10, backgroundColor: colors.bg, borderTopWidth: 1, borderTopColor: colors.border },
  footerHalf: { flex: 1 }
});
