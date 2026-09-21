import React, { useMemo, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Card, PrimaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { PantryStorage } from '@/src/types';

const STORAGE_OPTIONS: { key: PantryStorage; label: string; icon: string }[] = [
  { key: 'refrigerator', label: 'Refrigerator', icon: '❄️' },
  { key: 'freezer', label: 'Freezer', icon: '🧊' },
  { key: 'pantry', label: 'Pantry', icon: '🥫' },
  { key: 'seasoning', label: 'Seasoning', icon: '🧂' }
];

export default function PantryScreen() {
  const { state, addPantryItem, removePantryItem } = useApp();
  const [name, setName] = useState('');
  const [quantity, setQuantity] = useState('');
  const [storage, setStorage] = useState<PantryStorage>('refrigerator');

  const grouped = useMemo(() => Object.fromEntries(
    STORAGE_OPTIONS.map((option) => [option.key, state.pantry.filter((item) => item.storage === option.key)])
  ) as Record<PantryStorage, typeof state.pantry>, [state.pantry]);

  function add() {
    if (!name.trim()) return;
    addPantryItem({ name: name.trim(), quantity: quantity.trim() || undefined, storage });
    setName('');
    setQuantity('');
  }

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Card style={styles.form}>
        <Text style={styles.title}>Add an ingredient</Text>
        <TextInput value={name} onChangeText={setName} placeholder="e.g. chicken breast" style={styles.input} placeholderTextColor={colors.muted} />
        <TextInput value={quantity} onChangeText={setQuantity} placeholder="Quantity (optional)" style={styles.input} placeholderTextColor={colors.muted} />
        <Text style={styles.label}>Stored in</Text>
        <View style={styles.storageWrap}>
          {STORAGE_OPTIONS.map((option) => {
            const active = option.key === storage;
            return (
              <Pressable key={option.key} onPress={() => setStorage(option.key)} style={[styles.storageButton, active && styles.storageButtonActive]}>
                <Text style={[styles.storageText, active && styles.storageTextActive]}>{option.icon} {option.label}</Text>
              </Pressable>
            );
          })}
        </View>
        <PrimaryButton label={`Add to ${STORAGE_OPTIONS.find((item) => item.key === storage)?.label}`} onPress={add} disabled={!name.trim()} />
      </Card>

      <View style={styles.header}>
        <View>
          <Text style={styles.title}>Kitchen inventory</Text>
          <Text style={styles.meta}>Ingredients organized by where you keep them</Text>
        </View>
        <Text style={styles.count}>{state.pantry.length}</Text>
      </View>

      {state.pantry.length === 0 ? <Text style={styles.empty}>Nothing here yet. Add ingredients or scan your kitchen.</Text> : null}

      {STORAGE_OPTIONS.map((section) => {
        const items = grouped[section.key];
        return (
          <View key={section.key} style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>{section.icon} {section.label}</Text>
              <Text style={styles.sectionCount}>{items.length} item{items.length === 1 ? '' : 's'}</Text>
            </View>
            {items.length === 0 ? (
              <Card style={styles.emptySection}><Text style={styles.emptySectionText}>No ingredients stored here yet.</Text></Card>
            ) : items.map((item) => (
              <Card key={item.id} style={styles.item}>
                <View style={styles.itemText}>
                  <Text style={styles.itemName}>{item.name}</Text>
                  <Text style={styles.itemMeta}>{[item.brand, item.quantity, item.barcode ? `UPC ${item.barcode}` : undefined].filter(Boolean).join(' · ') || section.label}</Text>
                </View>
                <Pressable onPress={() => Alert.alert('Remove item?', item.name, [
                  { text: 'Cancel', style: 'cancel' },
                  { text: 'Remove', style: 'destructive', onPress: () => removePantryItem(item.id) }
                ])}>
                  <Text style={styles.remove}>Remove</Text>
                </Pressable>
              </Card>
            ))}
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { padding: 18, gap: 14, backgroundColor: colors.bg, paddingBottom: 36 },
  form: { gap: 10 },
  input: { backgroundColor: '#fff', borderWidth: 1, borderColor: colors.border, borderRadius: 12, paddingHorizontal: 13, paddingVertical: 12, color: colors.text, fontSize: 16 },
  label: { color: colors.text, fontWeight: '800', marginTop: 2 },
  storageWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  storageButton: { borderWidth: 1, borderColor: colors.border, backgroundColor: '#fff', borderRadius: 99, paddingHorizontal: 11, paddingVertical: 8 },
  storageButtonActive: { backgroundColor: colors.green, borderColor: colors.green },
  storageText: { color: colors.text, fontWeight: '700', fontSize: 12 },
  storageTextActive: { color: '#fff' },
  header: { marginTop: 8, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-end', gap: 12 },
  title: { color: colors.text, fontSize: 20, fontWeight: '900' },
  meta: { color: colors.muted, marginTop: 3, lineHeight: 18 },
  count: { color: colors.green, fontWeight: '900', fontSize: 18 },
  section: { gap: 8, marginTop: 3 },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 6 },
  sectionTitle: { color: colors.text, fontSize: 17, fontWeight: '900' },
  sectionCount: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  item: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  itemText: { flex: 1 },
  itemName: { color: colors.text, fontSize: 17, fontWeight: '800', textTransform: 'capitalize' },
  itemMeta: { color: colors.muted, marginTop: 3, fontSize: 12 },
  remove: { color: colors.danger, fontWeight: '800', fontSize: 12 },
  empty: { color: colors.muted, paddingVertical: 20, textAlign: 'center' },
  emptySection: { paddingVertical: 12 },
  emptySectionText: { color: colors.muted, fontSize: 12 }
});
