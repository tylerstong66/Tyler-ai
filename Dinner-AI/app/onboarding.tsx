import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { Pressable, SafeAreaView, StyleSheet, Text, View } from 'react-native';
import { PrimaryButton, colors } from '@/src/components/ui';
import { markOnboardingComplete, sendBetaEvent } from '@/src/lib/beta';

const STEPS = [
  {
    eyebrow: 'DINNER AI',
    emoji: '🍽️',
    title: 'Let your ingredients choose for you.',
    body: 'Dinner AI turns what is already in your kitchen into practical meal ideas, shopping help, and step-by-step cooking guidance.'
  },
  {
    eyebrow: 'START WITH YOUR KITCHEN',
    emoji: '📷',
    title: 'Scan it or add it yourself.',
    body: 'Scan your fridge, scan UPC barcodes, or add ingredients manually. You always review fridge-scan results before anything is saved.'
  },
  {
    eyebrow: 'COOK WITH CONFIDENCE',
    emoji: '👨‍🍳',
    title: 'From recommendation to finished meal.',
    body: 'Recipes include quantities, heat levels, cooking times, doneness cues, serving adjustments, and Cook Mode timers.'
  },
  {
    eyebrow: 'PRIVATE BETA',
    emoji: '🔒',
    title: 'A quick note before testing.',
    body: 'Your Kitchen, favorites, preferences, and recipe history stay on this device. Fridge photos are sent to the Dinner AI service and its AI provider only when you choose to scan them. AI can make mistakes—always verify serious allergies, labels, temperatures, and food safety.'
  }
];

export default function OnboardingScreen() {
  const router = useRouter();
  const [index, setIndex] = useState(0);
  const step = STEPS[index];
  const last = index === STEPS.length - 1;

  async function next() {
    if (!last) {
      setIndex((value) => value + 1);
      return;
    }
    await markOnboardingComplete();
    void sendBetaEvent('onboarding_completed', '/onboarding');
    router.replace('/beta-access');
  }

  return (
    <SafeAreaView style={styles.screen}>
      <View style={styles.top}>
        <View style={styles.dots}>
          {STEPS.map((_, i) => <View key={i} style={[styles.dot, i === index && styles.dotActive]} />)}
        </View>
        {index > 0 ? (
          <Pressable onPress={() => setIndex((value) => value - 1)} hitSlop={10}>
            <Text style={styles.back}>Back</Text>
          </Pressable>
        ) : <View />}
      </View>

      <View style={styles.hero}>
        <View style={styles.emojiCircle}><Text style={styles.emoji}>{step.emoji}</Text></View>
        <Text style={styles.eyebrow}>{step.eyebrow}</Text>
        <Text style={styles.title}>{step.title}</Text>
        <Text style={styles.body}>{step.body}</Text>
      </View>

      <View style={styles.bottom}>
        {last ? <Text style={styles.small}>By continuing, you acknowledge this is an early beta and recipes or AI detections may be imperfect.</Text> : null}
        <PrimaryButton label={last ? 'Continue to private beta' : 'Continue'} onPress={() => void next()} />
        <Text style={styles.stepText}>{index + 1} of {STEPS.length}</Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg, paddingHorizontal: 24, paddingTop: 16, paddingBottom: 20 },
  top: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  dots: { flexDirection: 'row', gap: 6 },
  dot: { width: 8, height: 8, borderRadius: 4, backgroundColor: colors.borderStrong },
  dotActive: { width: 26, backgroundColor: colors.green },
  back: { color: colors.greenDark, fontWeight: '900', fontSize: 13 },
  hero: { flex: 1, justifyContent: 'center', alignItems: 'flex-start', maxWidth: 600 },
  emojiCircle: { width: 82, height: 82, borderRadius: 28, backgroundColor: colors.greenSoft, alignItems: 'center', justifyContent: 'center', marginBottom: 28 },
  emoji: { fontSize: 38 },
  eyebrow: { color: colors.green, fontWeight: '900', fontSize: 11, letterSpacing: 1.8 },
  title: { color: colors.text, fontSize: 36, lineHeight: 42, fontWeight: '900', letterSpacing: -1, marginTop: 8 },
  body: { color: colors.muted, fontSize: 17, lineHeight: 26, marginTop: 16 },
  bottom: { gap: 12 },
  small: { color: colors.muted, fontSize: 12, lineHeight: 18, textAlign: 'center', paddingHorizontal: 8 },
  stepText: { color: colors.muted, textAlign: 'center', fontSize: 11, fontWeight: '800' }
});
