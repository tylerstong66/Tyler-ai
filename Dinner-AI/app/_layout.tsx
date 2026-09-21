import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import React from 'react';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { AppProvider } from '@/src/context/AppContext';
import { colors } from '@/src/components/ui';

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
          contentStyle: { backgroundColor: colors.bg }
        }}
      >
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="scan-upc" options={{ title: 'Scan a UPC' }} />
        <Stack.Screen name="scan-fridge" options={{ title: 'Scan Your Fridge' }} />
        <Stack.Screen name="recipe/[id]" options={{ title: 'Recipe' }} />
        <Stack.Screen name="surprise" options={{ title: 'Surprise Me' }} />
        </Stack>
      </AppProvider>
    </SafeAreaProvider>
  );
}
