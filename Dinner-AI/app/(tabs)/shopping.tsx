import React, { useMemo, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Card, PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
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
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <View>
        <Text style={styles.heading}>Shopping list</Text>
        <Text style={styles.sub}>Missing recipe ingredients are added automatically when you choose a recipe.</Text>
      </View>

      <Card style={styles.addCard}>
        <TextInput value={draft} onChangeText={setDraft} onSubmitEditing={addItem} placeholder="Add milk, lemons, tortillas…" placeholderTextColor={colors.muted} style={styles.input} returnKeyType="done" />
        <PrimaryButton label="Add item" onPress={addItem} disabled={!draft.trim()} />
      </Card>

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>To buy</Text>
        <Text style={styles.count}>{active.length}</Text>
      </View>

      {active.length === 0 ? (
        <Card><Text style={styles.empty}>Nothing to buy right now. Choose a recipe with missing ingredients or add an item above.</Text></Card>
      ) : active.map((item) => (
        <ShoppingRow key={item.id} item={item} onToggle={() => toggleShoppingItem(item.id)} onRemove={() => removeShoppingItem(item.id)} />
      ))}

      {purchased.length ? (
        <>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Purchased</Text>
            <Text style={styles.count}>{purchased.length}</Text>
          </View>
          {purchased.map((item) => (
            <ShoppingRow key={item.id} item={item} onToggle={() => toggleShoppingItem(item.id)} onRemove={() => removeShoppingItem(item.id)} />
          ))}
          <SecondaryButton label="Clear purchased" onPress={clearPurchasedShoppingItems} />
        </>
      ) : null}

      {state.shoppingList.length ? <SecondaryButton label="Clear entire list" onPress={confirmClearAll} /> : null}
    </ScrollView>
  );
}

function ShoppingRow({ item, onToggle, onRemove }: { item: { name: string; checked: boolean; recipeTitle?: string }; onToggle: () => void; onRemove: () => void }) {
  return (
    <Card style={styles.itemCard}>
      <Pressable onPress={onToggle} style={styles.itemMain}>
        <View style={[styles.checkbox, item.checked && styles.checkboxChecked]}>
          <Text style={styles.checkmark}>{item.checked ? '✓' : ''}</Text>
        </View>
        <View style={styles.itemTextWrap}>
          <Text style={[styles.itemName, item.checked && styles.itemNameChecked]}>{item.name}</Text>
          {item.recipeTitle ? <Text style={styles.source}>For {item.recipeTitle}</Text> : <Text style={styles.source}>Added manually</Text>}
        </View>
      </Pressable>
      <Pressable onPress={onRemove} hitSlop={10}><Text style={styles.remove}>×</Text></Pressable>
    </Card>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 16, gap: 14, backgroundColor: colors.bg, paddingBottom: 44 },
  heading: { color: colors.text, fontSize: 30, lineHeight: 36, fontWeight: '900', letterSpacing: -0.5 },
  sub: { color: colors.muted, lineHeight: 22, marginTop: 6, fontSize: 14.5 },
  addCard: { gap: 11, backgroundColor: colors.surfaceGreen, borderColor: colors.borderStrong },
  input: { borderWidth: 1, borderColor: colors.border, backgroundColor: colors.card, color: colors.text, borderRadius: 16, paddingHorizontal: 15, paddingVertical: 14, fontSize: 16 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginTop: 6 },
  sectionTitle: { color: colors.text, fontSize: 21, fontWeight: '900', letterSpacing: -0.2 },
  count: { color: colors.greenDark, backgroundColor: colors.greenSoft, borderRadius: 999, paddingHorizontal: 10, paddingVertical: 5, fontWeight: '900', overflow: 'hidden' },
  empty: { color: colors.muted, lineHeight: 21, textAlign: 'center' },
  itemCard: { flexDirection: 'row', alignItems: 'center', gap: 11, paddingVertical: 14 },
  itemMain: { flex: 1, flexDirection: 'row', alignItems: 'center', gap: 11 },
  checkbox: { width: 28, height: 28, borderRadius: 9, borderWidth: 2, borderColor: colors.green, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
  checkboxChecked: { backgroundColor: colors.green },
  checkmark: { color: '#fff', fontWeight: '900' },
  itemTextWrap: { flex: 1 },
  itemName: { color: colors.text, fontWeight: '900', fontSize: 16 },
  itemNameChecked: { color: colors.muted, textDecorationLine: 'line-through' },
  source: { color: colors.muted, fontSize: 11.5, marginTop: 4, lineHeight: 16 },
  remove: { color: colors.danger, fontSize: 27, lineHeight: 27, fontWeight: '500' }
});
