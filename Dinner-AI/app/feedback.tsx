import { useLocalSearchParams, useRouter } from 'expo-router';
import React, { useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { PrimaryButton, colors } from '@/src/components/ui';
import { appVersion, sendBetaFeedback, sendBetaEvent } from '@/src/lib/beta';

const CATEGORIES = ['Something broke', 'Recipe issue', 'Suggestion', 'I’m confused'] as const;

export default function FeedbackScreen() {
  const { from } = useLocalSearchParams<{ from?: string }>();
  const router = useRouter();
  const [category, setCategory] = useState<(typeof CATEGORIES)[number]>('Something broke');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  async function submit() {
    const clean = message.trim();
    if (!clean || busy) return;
    setBusy(true);
    try {
      await sendBetaFeedback({ category, message: clean, screen: from || '' });
      void sendBetaEvent('feedback_sent', from || '/feedback', { category });
      Alert.alert('Thanks for the feedback', 'It was sent with the app version and screen name so we can investigate it.', [
        { text: 'Done', onPress: () => router.back() }
      ]);
      setMessage('');
    } catch (e: any) {
      Alert.alert('Could not send feedback', e?.message || 'Please try again when you have an internet connection.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
      <Text style={styles.eyebrow}>PRIVATE BETA</Text>
      <Text style={styles.title}>Send feedback</Text>
      <Text style={styles.sub}>Tell us what happened in your own words. InDinecision automatically includes the beta version and the screen you came from.</Text>

      <Text style={styles.label}>What kind of feedback?</Text>
      <View style={styles.chips}>
        {CATEGORIES.map((item) => {
          const active = item === category;
          return (
            <Pressable key={item} onPress={() => setCategory(item)} style={[styles.chip, active && styles.chipActive]}>
              <Text style={[styles.chipText, active && styles.chipTextActive]}>{item}</Text>
            </Pressable>
          );
        })}
      </View>

      <Text style={styles.label}>What should we know?</Text>
      <TextInput
        value={message}
        onChangeText={setMessage}
        placeholder="Example: I tapped Start Cook Mode and the timer covered the Next button…"
        placeholderTextColor={colors.muted}
        multiline
        textAlignVertical="top"
        style={styles.input}
      />

      <View style={styles.meta}>
        <Text style={styles.metaText}>Version: {appVersion()}</Text>
        <Text style={styles.metaText}>Screen: {from || 'Not provided'}</Text>
      </View>

      <PrimaryButton label={busy ? 'Sending…' : 'Send feedback'} onPress={() => void submit()} disabled={busy || !message.trim()} />
      <Text style={styles.note}>Please do not include passwords, financial information, or other sensitive personal information.</Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 46, backgroundColor: colors.bg },
  eyebrow: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.7 },
  title: { color: colors.text, fontSize: 30, lineHeight: 35, fontWeight: '900', letterSpacing: -0.7, marginTop: 6 },
  sub: { color: colors.muted, fontSize: 14.5, lineHeight: 21, marginTop: 7, marginBottom: 24 },
  label: { color: colors.text, fontSize: 15, fontWeight: '900', marginBottom: 9 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8, marginBottom: 23 },
  chip: { backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 999, paddingHorizontal: 13, paddingVertical: 9 },
  chipActive: { backgroundColor: colors.greenDark, borderColor: colors.greenDark },
  chipText: { color: colors.text, fontSize: 12.5, fontWeight: '800' },
  chipTextActive: { color: '#fff' },
  input: { minHeight: 180, backgroundColor: colors.card, borderWidth: 1, borderColor: colors.borderStrong, borderRadius: 20, padding: 15, color: colors.text, fontSize: 15, lineHeight: 22, marginBottom: 14 },
  meta: { backgroundColor: colors.greenFaint, borderRadius: 16, padding: 12, marginBottom: 18, gap: 3 },
  metaText: { color: colors.muted, fontSize: 11.5, fontWeight: '700' },
  note: { color: colors.muted, fontSize: 11.5, lineHeight: 17, textAlign: 'center', marginTop: 12, paddingHorizontal: 8 }
});
