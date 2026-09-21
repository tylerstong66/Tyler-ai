import React, { useEffect, useState } from 'react';
import { Alert, ScrollView, StyleSheet, Text, TextInput } from 'react-native';
import { Card, PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';

const splitTerms = (value: string) => value.split(',').map((v) => v.trim()).filter(Boolean);

export default function ProfileScreen() {
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
    updateProfile({ likes: splitTerms(likes), dislikes: splitTerms(dislikes), allergies: splitTerms(allergies), dietaryNotes: notes.trim() });
    Alert.alert('Saved', 'Your food profile will now guide recommendations.');
  }

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Card style={styles.card}>
        <Text style={styles.title}>Foods you like</Text>
        <Text style={styles.help}>Comma-separated. Example: chicken, spicy food, Italian</Text>
        <TextInput value={likes} onChangeText={setLikes} style={styles.input} placeholder="Add favorites" placeholderTextColor={colors.muted} multiline />
      </Card>

      <Card style={styles.card}>
        <Text style={styles.title}>Foods you dislike</Text>
        <Text style={styles.help}>These are heavily penalized in recommendations.</Text>
        <TextInput value={dislikes} onChangeText={setDislikes} style={styles.input} placeholder="e.g. mushrooms, olives" placeholderTextColor={colors.muted} multiline />
      </Card>

      <Card style={styles.card}>
        <Text style={styles.title}>Allergies / ingredients to avoid</Text>
        <Text style={styles.warning}>Recipes containing matching terms are hidden. Always verify ingredient labels yourself for serious allergies.</Text>
        <TextInput value={allergies} onChangeText={setAllergies} style={styles.input} placeholder="e.g. peanuts, shellfish, dairy" placeholderTextColor={colors.muted} multiline />
      </Card>

      <Card style={styles.card}>
        <Text style={styles.title}>Other food preferences</Text>
        <TextInput value={notes} onChangeText={setNotes} style={[styles.input, styles.notes]} placeholder="Vegetarian on weekdays, low sodium, toddler-friendly, etc." placeholderTextColor={colors.muted} multiline />
      </Card>

      <PrimaryButton label="Save food profile" onPress={save} />
      <SecondaryButton label="Reset prototype data" onPress={() => Alert.alert('Reset Dinner AI?', 'This removes pantry items, favorites, preferences, and learning history.', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Reset', style: 'destructive', onPress: resetData }
      ])} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 18, gap: 12, backgroundColor: colors.bg, paddingBottom: 36 },
  card: { gap: 8 },
  title: { color: colors.text, fontSize: 18, fontWeight: '800' },
  help: { color: colors.muted, lineHeight: 19, fontSize: 13 },
  warning: { color: colors.danger, lineHeight: 19, fontSize: 13 },
  input: { minHeight: 48, borderWidth: 1, borderColor: colors.border, borderRadius: 12, padding: 12, color: colors.text, backgroundColor: '#fff', textAlignVertical: 'top' },
  notes: { minHeight: 90 }
});
