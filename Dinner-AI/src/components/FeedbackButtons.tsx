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
          <Pressable
            key={option.rating}
            onPress={() => onChange(option.rating)}
            style={({ pressed }) => [
              styles.button,
              active && styles.buttonActive,
              pressed && styles.buttonPressed
            ]}
          >
            <Text style={styles.emoji}>{option.emoji}</Text>
            <Text style={[styles.label, active && styles.labelActive]}>{option.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', gap: 9 },
  button: {
    flex: 1,
    minHeight: 74,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 18,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 7,
    paddingVertical: 11
  },
  buttonActive: { borderColor: colors.borderStrong, backgroundColor: colors.greenSoft },
  buttonPressed: { transform: [{ scale: 0.985 }], opacity: 0.92 },
  emoji: { fontSize: 22, marginBottom: 5 },
  label: { color: colors.muted, fontWeight: '800', fontSize: 11.5, textAlign: 'center' },
  labelActive: { color: colors.greenDark }
});
