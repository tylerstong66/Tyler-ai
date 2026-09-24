import React, { useMemo, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';

export default function ShoppingScreen() {
  const { state, addShoppingItem, toggleShoppingItem, removeShoppingItem, clearPurchasedShoppingItems, clearShoppingList } = useApp();
  const [draft, setDraft] = useState('');

  const { active, purchased } = useMemo(() => ({
    active: state.shoppingList.filter((item) => !item.checked),
    purchased: state.shoppingList.filter((item) => item.checked)
  }), [state.shoppingList]);

  function addItem() {
    const value = draft.trim();
    if (!value) return;
    addShoppingItem(value);
    setDraft('');
  }

  function confirmClearAll() {
    if (!state.shoppingList.length) return;
    Alert.alert('Clear shopping list?', 'This removes every item from the list.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Clear all', style: 'destructive', onPress: clearShoppingList }
    ]);
  }

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>SHOP</Text>
        <Text style={styles.title}>Your shopping list</Text>
        <Text style={styles.sub}>InDinecision adds genuinely missing recipe ingredients automatically.</Text>
      </View>

      <View style={styles.addRow}>
        <TextInput
          value={draft}
          onChangeText={setDraft}
          onSubmitEditing={addItem}
          placeholder="Add an item"
          placeholderTextColor={colors.muted}
          style={styles.input}
          returnKeyType="done"
        />
        <Pressable onPress={addItem} disabled={!draft.trim()} style={({ pressed }) => [styles.addButton, !draft.trim() && styles.addDisabled, pressed && styles.addPressed]}>
          <Text style={styles.addText}>+</Text>
        </Pressable>
      </View>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>To buy</Text>
        <Text style={styles.count}>{active.length}</Text>
      </View>

      {active.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyEmoji}>🛒</Text>
          <Text style={styles.emptyTitle}>You’re all set</Text>
          <Text style={styles.emptyText}>Choose a recipe and anything you actually need will show up here.</Text>
        </View>
      ) : (
        <View style={styles.list}>
          {active.map((item, index) => (
            <ShoppingRow
              key={item.id}
              item={item}
              onToggle={() => toggleShoppingItem(item.id)}
              onRemove={() => removeShoppingItem(item.id)}
              showDivider={index < active.length - 1}
            />
          ))}
        </View>
      )}

      {purchased.length ? (
        <View style={styles.purchasedSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Purchased</Text>
            <Pressable onPress={clearPurchasedShoppingItems}>
              <Text style={styles.clearText}>Clear</Text>
            </Pressable>
          </View>
          <View style={styles.list}>
            {purchased.map((item, index) => (
              <ShoppingRow
                key={item.id}
                item={item}
                onToggle={() => toggleShoppingItem(item.id)}
                onRemove={() => removeShoppingItem(item.id)}
                showDivider={index < purchased.length - 1}
              />
            ))}
          </View>
        </View>
      ) : null}

      {state.shoppingList.length ? (
        <Pressable onPress={confirmClearAll} style={styles.clearAll}>
          <Text style={styles.clearAllText}>Clear entire list</Text>
        </Pressable>
      ) : null}
    </ScrollView>
  );
}

function ShoppingRow({
  item,
  onToggle,
  onRemove,
  showDivider
}: {
  item: { name: string; checked: boolean; recipeTitle?: string };
  onToggle: () => void;
  onRemove: () => void;
  showDivider: boolean;
}) {
  return (
    <View>
      <View style={styles.itemRow}>
        <Pressable onPress={onToggle} style={styles.itemMain}>
          <View style={[styles.checkbox, item.checked && styles.checkboxChecked]}>
            <Text style={styles.checkmark}>{item.checked ? '✓' : ''}</Text>
          </View>
          <View style={styles.itemTextWrap}>
            <Text style={[styles.itemName, item.checked && styles.itemNameChecked]}>{item.name}</Text>
            <Text style={styles.source}>{item.recipeTitle ? 'For ' + item.recipeTitle : 'Added manually'}</Text>
          </View>
        </Pressable>
        <Pressable onPress={onRemove} hitSlop={10}>
          <Text style={styles.remove}>×</Text>
        </Pressable>
      </View>
      {showDivider ? <View style={styles.divider} /> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 46, backgroundColor: colors.bg },
  header: { marginBottom: 19 },
  eyebrow: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.7 },
  title: { color: colors.text, fontSize: 30, lineHeight: 35, fontWeight: '900', letterSpacing: -0.7, marginTop: 6 },
  sub: { color: colors.muted, lineHeight: 21, marginTop: 7, fontSize: 14.5 },

  addRow: { flexDirection: 'row', gap: 9, marginBottom: 27 },
  input: {
    flex: 1, height: 52, backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border,
    borderRadius: 17, paddingHorizontal: 15, color: colors.text, fontSize: 15.5
  },
  addButton: {
    width: 52, height: 52, borderRadius: 17, backgroundColor: colors.greenDark,
    alignItems: 'center', justifyContent: 'center'
  },
  addDisabled: { opacity: 0.38 },
  addPressed: { opacity: 0.82, transform: [{ scale: 0.97 }] },
  addText: { color: '#FFFFFF', fontSize: 28, lineHeight: 29, fontWeight: '500' },

  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  sectionTitle: { color: colors.text, fontSize: 21, fontWeight: '900', letterSpacing: -0.25 },
  count: { color: colors.greenDark, fontSize: 13, fontWeight: '900', backgroundColor: colors.greenSoft, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 5, overflow: 'hidden' },
  clearText: { color: colors.greenDark, fontWeight: '900', fontSize: 13 },

  list: { backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 21, paddingHorizontal: 16 },
  itemRow: { minHeight: 70, flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 12 },
  itemMain: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 12 },
  checkbox: { width: 29, height: 29, borderRadius: 10, borderWidth: 2, borderColor: colors.green, alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { backgroundColor: colors.greenDark, borderColor: colors.greenDark },
  checkmark: { color: '#FFFFFF', fontWeight: '900' },
  itemTextWrap: { flex: 1 },
  itemName: { color: colors.text, fontWeight: '900', fontSize: 16 },
  itemNameChecked: { color: colors.muted, textDecorationLine: 'line-through' },
  source: { color: colors.muted, fontSize: 11.5, marginTop: 4 },
  remove: { color: colors.muted, fontSize: 27, lineHeight: 27 },
  divider: { height: 1, backgroundColor: colors.border },

  empty: { alignItems: 'center', paddingVertical: 40, paddingHorizontal: 24, marginBottom: 8 },
  emptyEmoji: { fontSize: 37 },
  emptyTitle: { color: colors.text, fontSize: 18, fontWeight: '900', marginTop: 8 },
  emptyText: { color: colors.muted, textAlign: 'center', lineHeight: 20, marginTop: 5 },
  purchasedSection: { marginTop: 26 },
  clearAll: { alignItems: 'center', paddingVertical: 20, marginTop: 10 },
  clearAllText: { color: colors.danger, fontWeight: '800', fontSize: 13 }
});
