import { usePathname, useRouter } from 'expo-router';
import React, { useEffect } from 'react';
import { Pressable, StyleSheet, Text } from 'react-native';
import { reportClientError, sendBetaEvent } from '@/src/lib/beta';
import { colors } from './ui';

const HIDDEN = ['/onboarding', '/beta-access', '/feedback'];

export function BetaOverlay() {
  const pathname = usePathname();
  const router = useRouter();

  useEffect(() => {
    void sendBetaEvent('screen_view', pathname || 'unknown');

    const errorUtils = (globalThis as any).ErrorUtils;
    if (!errorUtils?.getGlobalHandler || !errorUtils?.setGlobalHandler) return;

    const previous = errorUtils.getGlobalHandler();
    errorUtils.setGlobalHandler((error: unknown, fatal?: boolean) => {
      void reportClientError(error, pathname || 'unknown', Boolean(fatal));
      if (typeof previous === 'function') previous(error, fatal);
    });

    return () => {
      if (typeof previous === 'function') errorUtils.setGlobalHandler(previous);
    };
  }, [pathname]);

  if (HIDDEN.some((path) => pathname?.startsWith(path))) return null;

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel="Send beta feedback"
      onPress={() => router.push({ pathname: '/feedback', params: { from: pathname || '' } })}
      style={({ pressed }) => [styles.button, pressed && styles.pressed]}
    >
      <Text style={styles.icon}>✎</Text>
      <Text style={styles.text}>Feedback</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  button: {
    position: 'absolute',
    right: 14,
    bottom: 88,
    zIndex: 1000,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    backgroundColor: colors.greenDark,
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 9,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.16,
    shadowRadius: 7,
    elevation: 6
  },
  pressed: { opacity: 0.82, transform: [{ scale: 0.98 }] },
  icon: { color: '#fff', fontSize: 12, fontWeight: '900' },
  text: { color: '#fff', fontSize: 11.5, fontWeight: '900' }
});
