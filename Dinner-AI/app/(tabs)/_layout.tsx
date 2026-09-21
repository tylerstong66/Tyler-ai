import { Tabs } from 'expo-router';
import React from 'react';
import { Text } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';

function EmojiIcon({ emoji, focused }: { emoji: string; focused: boolean }) {
  return <Text style={{ fontSize: focused ? 22 : 20, opacity: focused ? 1 : 0.65 }}>{emoji}</Text>;
}

export default function TabsLayout() {
  const { state } = useApp();
  const insets = useSafeAreaInsets();
  const shoppingCount = state.shoppingList.filter((item) => !item.checked).length;

  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg },
        headerShadowVisible: false,
        headerTitleStyle: { color: colors.text, fontWeight: '800' },
        tabBarActiveTintColor: colors.green,
        tabBarInactiveTintColor: colors.muted,
        tabBarHideOnKeyboard: true,
        tabBarStyle: {
          height: 60 + insets.bottom,
          paddingBottom: Math.max(insets.bottom, 8),
          paddingTop: 8
        },
        tabBarLabelStyle: { paddingBottom: insets.bottom > 0 ? 2 : 0 }
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Home', tabBarIcon: ({ focused }) => <EmojiIcon emoji="🍽️" focused={focused} /> }} />
      <Tabs.Screen name="pantry" options={{ title: 'Kitchen', tabBarIcon: ({ focused }) => <EmojiIcon emoji="🥫" focused={focused} /> }} />
      <Tabs.Screen name="recipes" options={{ title: 'Recipes', tabBarIcon: ({ focused }) => <EmojiIcon emoji="📖" focused={focused} /> }} />
      <Tabs.Screen name="shopping" options={{ title: 'Shop', tabBarBadge: shoppingCount || undefined, tabBarIcon: ({ focused }) => <EmojiIcon emoji="🛒" focused={focused} /> }} />
      <Tabs.Screen name="profile" options={{ title: 'Profile', tabBarIcon: ({ focused }) => <EmojiIcon emoji="⚙️" focused={focused} /> }} />
    </Tabs>
  );
}
