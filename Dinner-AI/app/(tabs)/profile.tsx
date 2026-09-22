import React, { useEffect, useState } from 'react';
import { useRouter } from 'expo-router';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { PrimaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';

const splitTerms = (value: string) => value.split(',').map((v) => v.trim()).filter(Boolean);

export default function ProfileScreen() {
  const router = useRouter();
  const { state, updateProfile, resetData } = useApp();
  const [likes, setLikes] = useState(state.profile.likes.join(', '));
  const [dislikes, setDislikes] = useState(state.profile.dislikes.join(', '));
  const [allergies, setAllergies] = useState(state.profile.allergies.join(', '));
  const [notes, setNotes] = useState(state.profile.dietaryNotes);

  useEffect(() => {
    setLikes(state.profile.likes.join(', '));
    setDislikes(state.profile.dislikes.join(', '));
    setAllergies(state.profile.allergies.join(', '));
    setNotes(state.profile.dietaryNotes);
  }, [state.profile]);

  function save() {
    updateProfile({
      likes: splitTerms(likes),
      dislikes: splitTerms(dislikes),
      allergies: splitTerms(allergies),
      dietaryNotes: notes.trim()
    });
    Alert.alert('Saved', 'Your food profile will now guide recommendations.');
  }

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>YOUR TASTE</Text>
        <Text style={styles.title}>Make Dinner AI yours</Text>
        <Text style={styles.sub}>Tell it what you enjoy, what to avoid, and anything else that should shape your recipes.</Text>
      </View>

      <PreferenceSection
        emoji="😍"
        title="Foods you like"
        help="These get a boost in future recommendations."
        value={likes}
        onChangeText={setLikes}
        placeholder="Chicken, spicy food, Italian…"
      />

      <PreferenceSection
        emoji="🙅"
        title="Foods you dislike"
        help="Dinner AI will strongly avoid these."
        value={dislikes}
        onChangeText={setDislikes}
        placeholder="Mushrooms, olives…"
      />

      <PreferenceSection
        emoji="⚠️"
        title="Allergies / avoid"
        help="Matching recipes are filtered out. Always verify labels for serious allergies."
        value={allergies}
        onChangeText={setAllergies}
        placeholder="Peanuts, shellfish, dairy…"
        warning
      />

      <PreferenceSection
        emoji="📝"
        title="Other preferences"
        help="Diet, family needs, nutrition goals, or anything else."
        value={notes}
        onChangeText={setNotes}
        placeholder="Toddler-friendly, vegetarian weekdays, low sodium…"
        tall
      />

      <PrimaryButton label="Save food profile" onPress={save} />

      <View style={styles.betaPanel}>
        <Text style={styles.betaEyebrow}>PRIVATE BETA</Text>
        <Text style={styles.betaTitle}>Help make Dinner AI better</Text>
        <Text style={styles.help}>Report anything broken, confusing, unsafe, or missing. Feedback includes the app version and current screen.</Text>
        <Pressable onPress={() => router.push({ pathname: '/feedback', params: { from: '/(tabs)/profile' } })} style={styles.betaLink}>
          <Text style={styles.betaLinkText}>Send beta feedback</Text>
          <Text style={styles.betaArrow}>›</Text>
        </Pressable>
        <Pressable onPress={() => router.push('/privacy')} style={styles.betaLink}>
          <Text style={styles.betaLinkText}>Privacy & safety</Text>
          <Text style={styles.betaArrow}>›</Text>
        </Pressable>
      </View>

      <Pressable
        onPress={() => Alert.alert(
          'Reset Dinner AI?',
          'This removes pantry items, favorites, preferences, and learning history.',
          [
            { text: 'Cancel', style: 'cancel' },
            { text: 'Reset', style: 'destructive', onPress: resetData }
          ]
        )}
        style={styles.reset}
      >
        <Text style={styles.resetText}>Reset app data</Text>
      </Pressable>
    </ScrollView>
  );
}

function PreferenceSection({
  emoji,
  title,
  help,
  value,
  onChangeText,
  placeholder,
  warning = false,
  tall = false
}: {
  emoji: string;
  title: string;
  help: string;
  value: string;
  onChangeText: (value: string) => void;
  placeholder: string;
  warning?: boolean;
  tall?: boolean;
}) {
  return (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <View style={styles.iconCircle}><Text style={styles.icon}>{emoji}</Text></View>
        <View style={styles.sectionCopy}>
          <Text style={styles.sectionTitle}>{title}</Text>
          <Text style={[styles.help, warning && styles.warning]}>{help}</Text>
        </View>
      </View>

      <TextInput
        value={value}
        onChangeText={onChangeText}
        style={[styles.input, tall && styles.inputTall]}
        placeholder={placeholder}
        placeholderTextColor={colors.muted}
        multiline
      />
    </View>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 46, backgroundColor: colors.bg },
  header: { marginBottom: 24 },
  eyebrow: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.7 },
  title: { color: colors.text, fontSize: 30, lineHeight: 35, fontWeight: '900', letterSpacing: -0.7, marginTop: 6 },
  sub: { color: colors.muted, lineHeight: 21, marginTop: 7, fontSize: 14.5, maxWidth: 540 },

  section: { marginBottom: 25 },
  sectionHeader: { flexDirection: 'row', gap: 12, alignItems: 'flex-start', marginBottom: 10 },
  iconCircle: { width: 40, height: 40, borderRadius: 14, backgroundColor: colors.greenSoft, alignItems: 'center', justifyContent: 'center' },
  icon: { fontSize: 18 },
  sectionCopy: { flex: 1 },
  sectionTitle: { color: colors.text, fontSize: 17, fontWeight: '900', lineHeight: 22 },
  help: { color: colors.muted, fontSize: 12.5, lineHeight: 18, marginTop: 2 },
  warning: { color: colors.danger },
  input: {
    minHeight: 58,
    backgroundColor: colors.card,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 17,
    paddingHorizontal: 15,
    paddingVertical: 13,
    color: colors.text,
    fontSize: 15,
    lineHeight: 21,
    textAlignVertical: 'top'
  },
  inputTall: { minHeight: 92 },
  betaPanel: { backgroundColor: colors.greenFaint, borderWidth: 1, borderColor: colors.borderStrong, borderRadius: 20, padding: 16, marginTop: 22, marginBottom: 8 },
  betaEyebrow: { color: colors.green, fontSize: 10, fontWeight: '900', letterSpacing: 1.4 },
  betaTitle: { color: colors.text, fontSize: 18, fontWeight: '900', marginTop: 4, marginBottom: 4 },
  betaLink: { minHeight: 48, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', borderTopWidth: 1, borderTopColor: colors.border, marginTop: 10, paddingTop: 10 },
  betaLinkText: { color: colors.greenDark, fontWeight: '900', fontSize: 14 },
  betaArrow: { color: colors.greenDark, fontSize: 26, lineHeight: 27 },
  reset: { alignItems: 'center', paddingVertical: 22, marginTop: 3 },
  resetText: { color: colors.danger, fontWeight: '800', fontSize: 13 }
});
