import React, { useMemo, useState } from 'react';
import { Alert, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { PrimaryButton, colors } from '@/src/components/ui';
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
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled" showsVerticalScrollIndicator={false}>
      <View style={styles.header}>
        <Text style={styles.eyebrow}>YOUR KITCHEN</Text>
        <View style={styles.headerRow}>
          <View style={styles.headerCopy}>
            <Text style={styles.title}>What you have</Text>
            <Text style={styles.sub}>Keep this current and InDinecision can make smarter recommendations.</Text>
          </View>
          <View style={styles.totalBubble}>
            <Text style={styles.totalNumber}>{state.pantry.length}</Text>
            <Text style={styles.totalLabel}>items</Text>
          </View>
        </View>
      </View>

      <View style={styles.addPanel}>
        <Text style={styles.addTitle}>Add something</Text>
        <View style={styles.inputRow}>
          <TextInput
            value={name}
            onChangeText={setName}
            placeholder="Ingredient"
            style={[styles.input, styles.nameInput]}
            placeholderTextColor={colors.muted}
          />
          <TextInput
            value={quantity}
            onChangeText={setQuantity}
            placeholder="Qty"
            style={[styles.input, styles.qtyInput]}
            placeholderTextColor={colors.muted}
          />
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.storageWrap}>
          {STORAGE_OPTIONS.map((option) => {
            const active = option.key === storage;
            return (
              <Pressable
                key={option.key}
                onPress={() => setStorage(option.key)}
                style={[styles.storageButton, active && styles.storageButtonActive]}
              >
                <Text style={styles.storageEmoji}>{option.icon}</Text>
                <Text style={[styles.storageText, active && styles.storageTextActive]}>{option.label}</Text>
              </Pressable>
            );
          })}
        </ScrollView>

        <PrimaryButton
          label={'Add to ' + (STORAGE_OPTIONS.find((item) => item.key === storage)?.label ?? 'Kitchen')}
          onPress={add}
          disabled={!name.trim()}
        />
      </View>

      {state.pantry.length === 0 ? (
        <View style={styles.empty}>
          <Text style={styles.emptyEmoji}>🥕</Text>
          <Text style={styles.emptyTitle}>Your kitchen is empty</Text>
          <Text style={styles.emptyText}>Scan your fridge or add a few ingredients to get started.</Text>
        </View>
      ) : null}

      {STORAGE_OPTIONS.map((section) => {
        const items = grouped[section.key];
        if (!items.length) return null;

        return (
          <View key={section.key} style={styles.section}>
            <View style={styles.sectionHeader}>
              <View style={styles.sectionNameRow}>
                <Text style={styles.sectionEmoji}>{section.icon}</Text>
                <Text style={styles.sectionTitle}>{section.label}</Text>
              </View>
              <Text style={styles.sectionCount}>{items.length}</Text>
            </View>

            <View style={styles.itemGroup}>
              {items.map((item, index) => (
                <View key={item.id}>
                  <View style={styles.itemRow}>
                    <View style={styles.itemText}>
                      <Text style={styles.itemName}>{item.name}</Text>
                      <Text style={styles.itemMeta}>
                        {[item.brand, item.quantity, item.barcode ? 'UPC ' + item.barcode : undefined].filter(Boolean).join(' · ') || 'Saved ingredient'}
                      </Text>
                    </View>
                    <Pressable
                      hitSlop={10}
                      onPress={() => Alert.alert('Remove item?', item.name, [
                        { text: 'Cancel', style: 'cancel' },
                        { text: 'Remove', style: 'destructive', onPress: () => removePantryItem(item.id) }
                      ])}
                    >
                      <Text style={styles.remove}>Remove</Text>
                    </Pressable>
                  </View>
                  {index < items.length - 1 ? <View style={styles.divider} /> : null}
                </View>
              ))}
            </View>
          </View>
        );
      })}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 46, backgroundColor: colors.bg },
  header: { marginBottom: 20 },
  eyebrow: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.7 },
  headerRow: { flexDirection: 'row', alignItems: 'flex-end', justifyContent: 'space-between', gap: 18, marginTop: 6 },
  headerCopy: { flex: 1 },
  title: { color: colors.text, fontSize: 30, lineHeight: 35, fontWeight: '900', letterSpacing: -0.7 },
  sub: { color: colors.muted, marginTop: 7, lineHeight: 21, fontSize: 14.5 },
  totalBubble: { minWidth: 62, alignItems: 'center', backgroundColor: colors.greenSoft, borderRadius: 20, paddingHorizontal: 12, paddingVertical: 10 },
  totalNumber: { color: colors.greenDark, fontSize: 20, lineHeight: 22, fontWeight: '900' },
  totalLabel: { color: colors.greenDark, fontSize: 10, fontWeight: '800', marginTop: 2 },

  addPanel: { backgroundColor: colors.card, borderRadius: 22, padding: 17, marginBottom: 28, borderWidth: 1, borderColor: colors.border },
  addTitle: { color: colors.text, fontSize: 17, fontWeight: '900', marginBottom: 11 },
  inputRow: { flexDirection: 'row', gap: 9 },
  input: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderRadius: 14, paddingHorizontal: 13, paddingVertical: 12, color: colors.text, fontSize: 15 },
  nameInput: { flex: 1 },
  qtyInput: { width: 88 },
  storageWrap: { gap: 8, paddingVertical: 12, paddingRight: 8 },
  storageButton: { flexDirection: 'row', alignItems: 'center', gap: 5, borderRadius: 999, backgroundColor: colors.surface, paddingHorizontal: 11, paddingVertical: 8 },
  storageButtonActive: { backgroundColor: colors.greenSoft },
  storageEmoji: { fontSize: 13 },
  storageText: { color: colors.muted, fontWeight: '800', fontSize: 11.5 },
  storageTextActive: { color: colors.greenDark },

  empty: { alignItems: 'center', paddingVertical: 36, paddingHorizontal: 24 },
  emptyEmoji: { fontSize: 36 },
  emptyTitle: { color: colors.text, fontSize: 18, fontWeight: '900', marginTop: 8 },
  emptyText: { color: colors.muted, textAlign: 'center', lineHeight: 20, marginTop: 5 },

  section: { marginBottom: 26 },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 9 },
  sectionNameRow: { flexDirection: 'row', alignItems: 'center', gap: 7 },
  sectionEmoji: { fontSize: 17 },
  sectionTitle: { color: colors.text, fontSize: 19, fontWeight: '900', letterSpacing: -0.2 },
  sectionCount: { color: colors.muted, fontSize: 12, fontWeight: '800' },
  itemGroup: { backgroundColor: colors.card, borderRadius: 20, paddingHorizontal: 16, borderWidth: 1, borderColor: colors.border },
  itemRow: { minHeight: 68, flexDirection: 'row', alignItems: 'center', gap: 14, paddingVertical: 12 },
  itemText: { flex: 1 },
  itemName: { color: colors.text, fontSize: 16, fontWeight: '900', textTransform: 'capitalize' },
  itemMeta: { color: colors.muted, fontSize: 11.5, marginTop: 4 },
  remove: { color: colors.danger, fontWeight: '800', fontSize: 12 },
  divider: { height: 1, backgroundColor: colors.border }
});
