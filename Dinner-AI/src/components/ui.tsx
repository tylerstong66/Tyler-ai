import React, { PropsWithChildren } from 'react';
import { Pressable, StyleProp, StyleSheet, Text, View, ViewStyle } from 'react-native';

export const colors = {
  bg: '#F5F7F4',
  card: '#FFFFFF',
  surface: '#FAFCFA',
  surfaceGreen: '#F1F7F3',
  text: '#17221B',
  muted: '#6E7A72',
  green: '#2D6A4F',
  greenDark: '#204C39',
  greenSoft: '#E6F1EA',
  greenFaint: '#F2F7F4',
  orange: '#B66A3C',
  border: '#E2E8E3',
  borderStrong: '#D3DDD6',
  danger: '#A94444',
  shadow: '#1A2B21'
};

export const radii = {
  small: 12,
  medium: 16,
  large: 22,
  pill: 999
};

export function Screen({ children }: PropsWithChildren) {
  return <View style={styles.screen}>{children}</View>;
}

export function Card({ children, style }: PropsWithChildren<{ style?: StyleProp<ViewStyle> }>) {
  return <View style={[styles.card, style]}>{children}</View>;
}

export function Pill({ children }: PropsWithChildren) {
  return <View style={styles.pill}><Text style={styles.pillText}>{children}</Text></View>;
}

export function PrimaryButton({ label, onPress, disabled = false }: { label: string; onPress: () => void; disabled?: boolean }) {
  return (
    <Pressable
      style={({ pressed }) => [
        styles.primary,
        pressed && !disabled && styles.primaryPressed,
        disabled && styles.disabled
      ]}
      onPress={onPress}
      disabled={disabled}
    >
      <Text style={styles.primaryText}>{label}</Text>
    </Pressable>
  );
}

export function SecondaryButton({ label, onPress }: { label: string; onPress: () => void }) {
  return (
    <Pressable
      style={({ pressed }) => [styles.secondary, pressed && styles.secondaryPressed]}
      onPress={onPress}
    >
      <Text style={styles.secondaryText}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: colors.bg },
  card: {
    backgroundColor: colors.card,
    borderRadius: radii.large,
    borderWidth: 1,
    borderColor: colors.border,
    padding: 18,
    shadowColor: colors.shadow,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.055,
    shadowRadius: 14,
    elevation: 2
  },
  pill: {
    alignSelf: 'flex-start',
    backgroundColor: colors.greenSoft,
    paddingHorizontal: 11,
    paddingVertical: 6,
    borderRadius: radii.pill
  },
  pillText: { color: colors.greenDark, fontWeight: '800', fontSize: 12 },
  primary: {
    minHeight: 52,
    backgroundColor: colors.green,
    borderRadius: radii.medium,
    paddingVertical: 14,
    paddingHorizontal: 18,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: colors.greenDark,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12,
    shadowRadius: 8,
    elevation: 2
  },
  primaryPressed: { opacity: 0.9, transform: [{ scale: 0.99 }] },
  primaryText: { color: '#FFFFFF', fontWeight: '800', fontSize: 16, letterSpacing: 0.1 },
  secondary: {
    minHeight: 50,
    backgroundColor: colors.greenFaint,
    borderWidth: 1,
    borderColor: colors.borderStrong,
    borderRadius: radii.medium,
    paddingVertical: 13,
    paddingHorizontal: 18,
    alignItems: 'center',
    justifyContent: 'center'
  },
  secondaryPressed: { backgroundColor: colors.greenSoft, transform: [{ scale: 0.99 }] },
  secondaryText: { color: colors.greenDark, fontWeight: '800', fontSize: 15 },
  disabled: { opacity: 0.42, shadowOpacity: 0, elevation: 0 }
});
