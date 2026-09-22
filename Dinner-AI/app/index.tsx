import { useRouter } from 'expo-router';
import React, { useEffect } from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';
import { colors } from '@/src/components/ui';
import { getBetaToken, hasCompletedOnboarding, sendBetaEvent } from '@/src/lib/beta';

export default function Index() {
  const router = useRouter();

  useEffect(() => {
    let active = true;
    (async () => {
      const [onboarded, token] = await Promise.all([hasCompletedOnboarding(), getBetaToken()]);
      if (!active) return;
      void sendBetaEvent('app_opened', '/');
      if (!onboarded) router.replace('/onboarding');
      else if (!token) router.replace('/beta-access');
      else router.replace('/(tabs)');
    })().catch(() => {
      if (active) router.replace('/onboarding');
    });
    return () => { active = false; };
  }, [router]);

  return <View style={styles.center}><ActivityIndicator color={colors.green} size="large" /></View>;
}

const styles = StyleSheet.create({
  center: { flex: 1, backgroundColor: colors.bg, alignItems: 'center', justifyContent: 'center' }
});
