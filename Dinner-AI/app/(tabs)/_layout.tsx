import { Tabs } from 'expo-router';
import React from 'react';
import { Text } from 'react-native';
import { colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';

function EmojiIcon({ emoji, focused }: { emoji: string; focused: boolean }) {
  return <Text style={{ fontSize: focused ? 22 : 20, opacity: focused ? 1 : 0.65 }}>{emoji}</Text>;
}

export default function TabsLayout() {
  const { state } = useApp();
  const shoppingCount = state.shoppingList.filter((item) => !item.checked).length;

  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg },
        headerShadowVisible: false,
        headerTitleStyle: { color: colors.text, fontWeight: '800' },
        tabBarActiveTintColor: colors.green,
        tabBarInactiveTintColor: colors.muted,
        tabBarStyle: { height: 68, paddingBottom: 9, paddingTop: 6 }
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
