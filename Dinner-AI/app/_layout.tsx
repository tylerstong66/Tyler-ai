import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppProvider } from '@/src/context/AppContext';
import { colors } from '@/src/components/ui';
import { BetaOverlay } from '@/src/components/BetaOverlay';

export default function RootLayout() {
  return (
    <SafeAreaProvider>
      <AppProvider>
        <StatusBar style="dark" />
        <Stack
          screenOptions={{
            headerStyle: { backgroundColor: colors.bg },
            headerShadowVisible: false,
            headerTintColor: colors.text,
            headerTitleStyle: { fontWeight: '900', color: colors.text },
            contentStyle: { backgroundColor: colors.bg }
          }}
        >
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="onboarding" options={{ headerShown: false }} />
        <Stack.Screen name="beta-access" options={{ headerShown: false }} />
        <Stack.Screen name="feedback" options={{ title: 'Beta Feedback' }} />
        <Stack.Screen name="privacy" options={{ title: 'Privacy & Safety' }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="scan-upc" options={{ title: 'Scan a UPC' }} />
        <Stack.Screen name="scan-fridge" options={{ title: 'Scan Your Fridge' }} />
        <Stack.Screen name="recipe/[id]" options={{ title: 'Recipe' }} />
        <Stack.Screen name="cook/[id]" options={{ title: 'Cook Mode', headerBackTitle: 'Recipe' }} />
        <Stack.Screen name="surprise" options={{ title: 'Surprise Me' }} />
        </Stack>
        <BetaOverlay />
      </AppProvider>
    </SafeAreaProvider>
  );
}
