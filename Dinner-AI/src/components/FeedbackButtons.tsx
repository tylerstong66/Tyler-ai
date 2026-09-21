import React from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { colors } from '@/src/components/ui';
import { RecipeFeedbackRating } from '@/src/types';

const OPTIONS: { rating: RecipeFeedbackRating; emoji: string; label: string }[] = [
  { rating: 'love', emoji: '😍', label: 'Love it' },
  { rating: 'okay', emoji: '🙂', label: 'It was okay' },
  { rating: 'never', emoji: '🚫', label: 'Never again' }
];

export function FeedbackButtons({ value, onChange }: { value?: RecipeFeedbackRating; onChange: (rating: RecipeFeedbackRating) => void }) {
  return (
    <View style={styles.row}>
      {OPTIONS.map((option) => {
        const active = value === option.rating;
        return (
          <Pressable key={option.rating} onPress={() => onChange(option.rating)} style={[styles.button, active && styles.buttonActive]}>
            <Text style={styles.emoji}>{option.emoji}</Text>
            <Text style={[styles.label, active && styles.labelActive]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: 8 },
  button: { flex: 1, minHeight: 66, borderWidth: 1, borderColor: colors.border, borderRadius: 14, backgroundColor: '#fff', alignItems: 'center', justifyContent: 'center', paddingHorizontal: 6, paddingVertical: 9 },
  buttonActive: { borderColor: colors.green, backgroundColor: colors.greenSoft },
  emoji: { fontSize: 20, marginBottom: 4 },
  label: { color: colors.muted, fontWeight: '800', fontSize: 11, textAlign: 'center' },
  labelActive: { color: colors.green }
});
