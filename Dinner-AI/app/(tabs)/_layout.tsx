import { Tabs } from 'expo-router';
import React from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';

function EmojiIcon({ emoji, focused }: { emoji: string; focused: boolean }) {
  return (
    <View style={[styles.iconWrap, focused && styles.iconWrapFocused]}>
      <Text style={[styles.icon, !focused && styles.iconMuted]}>{emoji}</Text>
    </View>
  );
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
          height: 64 + insets.bottom,
          paddingBottom: Math.max(insets.bottom, 8),
          paddingTop: 7,
          backgroundColor: colors.card,
          borderTopWidth: 1,
          borderTopColor: colors.border,
          shadowColor: colors.shadow,
          shadowOffset: { width: 0, height: -4 },
          shadowOpacity: 0.05,
          shadowRadius: 12,
          elevation: 10
        },
        tabBarItemStyle: { paddingTop: 1 },
        tabBarLabelStyle: {
          paddingBottom: insets.bottom > 0 ? 2 : 0,
          fontSize: 11,
          fontWeight: '700'
        }
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


const styles = StyleSheet.create({
  iconWrap: {
    minWidth: 34,
    height: 30,
    paddingHorizontal: 7,
    borderRadius: 11,
    alignItems: 'center',
    justifyContent: 'center'
  },
  iconWrapFocused: { backgroundColor: colors.greenSoft },
  icon: { fontSize: 19 },
  iconMuted: { opacity: 0.58 }
});
