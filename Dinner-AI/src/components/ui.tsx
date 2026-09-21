import React, { PropsWithChildren } from 'react';
import { Pressable, StyleSheet, Text, View, ViewStyle } from 'react-native';

export const colors = {
  bg: '#F7F6F2',
  card: '#FFFFFF',
  text: '#1F2A24',
  muted: '#69756E',
  green: '#2F6B4F',
  greenSoft: '#E5F0E9',
  orange: '#B95F2B',
  border: '#DDE3DF',
  danger: '#A23C3C'
};

export function Screen({ children }: PropsWithChildren) {
  return <View style={styles.screen}>{children}</View>;
}

export function Card({ children, style }: PropsWithChildren<{ style?: ViewStyle }>) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Pill({ children }: PropsWithChildren) {
  return <View style={styles.pill}><Text style={styles.pillText}>{children}</Text></View>;
}

export function PrimaryButton({ label, onPress, disabled = false }: { label: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable style={({ pressed }) => [styles.primary, pressed && styles.pressed, disabled && styles.disabled]} onPress={onPress} disabled={disabled}>
      <Text style={styles.primaryText}>{label}</Text>
    </Pressable>
  );
}

export function SecondaryButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable style={({ pressed }) => [styles.secondary, pressed && styles.pressed]} onPress={onPress}>
      <Text style={styles.secondaryText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  card: {
    backgroundColor: colors.card,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 16
  },
  pill: { alignSelf: 'flex-start', backgroundColor: colors.greenSoft, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 99 },
  pillText: { color: colors.green, fontWeight: '700', fontSize: 12 },
  primary: { backgroundColor: colors.green, borderRadius: 14, paddingVertical: 14, paddingHorizontal: 18, alignItems: 'center' },
  primaryText: { color: '#fff', fontWeight: '800', fontSize: 16 },
  secondary: { borderWidth: 1, borderColor: colors.green, borderRadius: 14, paddingVertical: 13, paddingHorizontal: 18, alignItems: 'center' },
  secondaryText: { color: colors.green, fontWeight: '800', fontSize: 15 },
  pressed: { opacity: 0.78 },
  disabled: { opacity: 0.45 }
});
