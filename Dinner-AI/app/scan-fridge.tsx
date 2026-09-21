import { CameraCapturedPicture, CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import React, { useRef, useState } from 'react';
import { ActivityIndicator, Alert, Image, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { Card, PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { analyzeFridgePhoto } from '@/src/lib/fridgeVision';
import { DetectedIngredient, PantryStorage } from '@/src/types';

const STORAGE: { key: PantryStorage; label: string }[] = [
  { key: 'refrigerator', label: 'Fridge' },
  { key: 'freezer', label: 'Freezer' },
  { key: 'pantry', label: 'Pantry' },
  { key: 'seasoning', label: 'Seasoning' }
];

export default function ScanFridgeScreen() {
  const router = useRouter();
  const { addPantryItems } = useApp();
  const [permission, requestPermission] = useCameraPermissions();
  const cameraRef = useRef<CameraView | null>(null);
  const [photo, setPhoto] = useState<CameraCapturedPicture | null>(null);
  const [items, setItems] = useState<DetectedIngredient[]>([]);
  const [busy, setBusy] = useState(false);
  const [manual, setManual] = useState('');
  const [error, setError] = useState('');

  async function capture() {
    if (!cameraRef.current || busy) return;
    setBusy(true);
    setError('');
    try {
      const shot = await cameraRef.current.takePictureAsync({ quality: 0.55, base64: true });
      if (!shot?.base64) throw new Error('The photo did not include image data.');
      setPhoto(shot);
      const result = await analyzeFridgePhoto(shot.base64, 'image/jpeg');
      setItems(result.ingredients);
      if (!result.ingredients.length) setError('No ingredients were confidently identified. You can retake the photo or add items manually.');
    } catch (e: any) {
      setError(e?.message === 'AI_BACKEND_NOT_CONFIGURED' ? 'AI scanning is not configured yet. Add items manually below.' : (e?.message || 'The scan failed.'));
    } finally {
      setBusy(false);
    }
  }

  function patch(id: string, update: Partial<DetectedIngredient>) {
    setItems((current) => current.map((item) => item.id === id ? { ...item, ...update } : item));
  }

  function addManual() {
    const name = manual.trim();
    if (!name) return;
    setItems((current) => [...current, { id: `manual-${Date.now()}`, name, confidence: 1, selected: true, storage: 'refrigerator', notes: 'Added manually' }]);
    setManual('');
  }

  function save() {
    const selected = items.filter((item) => item.selected && item.name.trim());
    if (!selected.length) return Alert.alert('Nothing selected', 'Choose at least one ingredient.');
    addPantryItems(selected.map((item) => ({ name: item.name.trim(), quantity: item.quantity?.trim() || undefined, storage: item.storage })));
    Alert.alert('Kitchen updated', `${selected.length} ingredient${selected.length === 1 ? '' : 's'} added.`, [{ text: 'Done', onPress: () => router.replace('/(tabs)/pantry') }]);
  }

  function retake() {
    setPhoto(null);
    setItems([]);
    setError('');
  }

  if (!permission) return <View style={styles.center}><ActivityIndicator /></View>;
  if (!permission.granted) return (
    <View style={styles.permission}>
      <Text style={styles.title}>Camera permission needed</Text>
      <Text style={styles.muted}>Dinner AI needs camera access only when you choose to scan your fridge.</Text>
      <PrimaryButton label="Allow camera" onPress={requestPermission} />
    </View>
  );

  if (!photo) return (
    <View style={styles.cameraPage}>
      <CameraView ref={cameraRef} style={styles.camera} facing="back">
        <View style={styles.cameraOverlay}>
          <Text style={styles.cameraHint}>Fit as much of the fridge or pantry as possible in the frame</Text>
          <Pressable disabled={busy} onPress={capture} style={styles.shutterOuter}><View style={styles.shutterInner} /></Pressable>
        </View>
      </CameraView>
    </View>
  );

  return (
    <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
      <Image source={{ uri: photo.uri }} style={styles.preview} />
      {busy ? <Card style={styles.centerCard}><ActivityIndicator size="large" color={colors.green} /><Text style={styles.muted}>Looking for ingredients…</Text></Card> : null}
      {error ? <Text style={styles.error}>{error}</Text> : null}
      {!busy && items.some((item) => item.confidence < 0.72) ? (
        <Card style={styles.reviewCard}>
          <Text style={styles.reviewTitle}>Review uncertain items</Text>
          <Text style={styles.muted}>Low-confidence detections are left unchecked so Dinner AI does not add a guess to your Kitchen without you confirming it.</Text>
        </Card>
      ) : null}

      {items.map((item) => (
        <Card key={item.id} style={[styles.itemCard, !item.selected && styles.dim]}>
          <Pressable onPress={() => patch(item.id, { selected: !item.selected })} style={styles.selectRow}>
            <View style={[styles.checkbox, item.selected && styles.checked]}><Text style={styles.check}>{item.selected ? '✓' : ''}</Text></View>
            <TextInput value={item.name} onChangeText={(name) => patch(item.id, { name })} style={styles.nameInput} />
            <Text style={[styles.confidence, item.confidence < 0.72 && styles.reviewConfidence]}>{Math.round(item.confidence * 100)}%{item.confidence < 0.72 ? ' · REVIEW' : ''}</Text>
          </Pressable>
          {item.notes ? <Text style={styles.notes}>{item.notes}</Text> : null}
          <TextInput
            value={item.quantity || ''}
            onChangeText={(quantity) => patch(item.id, { quantity })}
            placeholder="Quantity (optional)"
            placeholderTextColor={colors.muted}
            style={styles.qtyInput}
          />
          <View style={styles.storageRow}>
            {STORAGE.map((option) => {
              const active = item.storage === option.key;
              return (
                <Pressable key={option.key} onPress={() => patch(item.id, { storage: option.key })} style={[styles.storage, active && styles.storageActive]}>
                  <Text style={[styles.storageText, active && styles.storageTextActive]}>{option.label}</Text>
                </Pressable>
              );
            })}
          </View>
        </Card>
      ))}

      <Card style={styles.manualCard}>
        <Text style={styles.section}>AI missed something?</Text>
        <View style={styles.manualRow}>
          <TextInput value={manual} onChangeText={setManual} onSubmitEditing={addManual} placeholder="Add an ingredient" placeholderTextColor={colors.muted} style={styles.manualInput} />
          <Pressable onPress={addManual} style={styles.addButton}><Text style={styles.addText}>Add</Text></Pressable>
        </View>
      </Card>

      <PrimaryButton label="Add selected to Kitchen" onPress={save} disabled={busy || !items.some((item) => item.selected)} />
      <SecondaryButton label="Retake photo" onPress={retake} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  cameraPage: { flex: 1, backgroundColor: '#000' },
  camera: { flex: 1 },
  cameraOverlay: { flex: 1, justifyContent: 'space-between', alignItems: 'center', padding: 26, paddingTop: 40, backgroundColor: 'rgba(0,0,0,0.12)' },
  cameraHint: { color: '#fff', fontWeight: '800', textAlign: 'center', backgroundColor: 'rgba(0,0,0,0.55)', borderRadius: 14, padding: 12 },
  shutterOuter: { width: 82, height: 82, borderRadius: 41, borderWidth: 5, borderColor: '#fff', alignItems: 'center', justifyContent: 'center' },
  shutterInner: { width: 62, height: 62, borderRadius: 31, backgroundColor: '#fff' },
  permission: { flex: 1, justifyContent: 'center', gap: 14, padding: 24, backgroundColor: colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: colors.bg },
  content: { padding: 18, gap: 12, backgroundColor: colors.bg, paddingBottom: 36 },
  preview: { width: '100%', height: 190, borderRadius: 18, backgroundColor: '#ddd' },
  centerCard: { alignItems: 'center', gap: 10 },
  title: { color: colors.text, fontSize: 25, fontWeight: '900' },
  muted: { color: colors.muted, lineHeight: 20 },
  error: { color: colors.danger, lineHeight: 20, fontWeight: '700' },
  reviewCard: { gap: 5, borderColor: '#D7B56D', backgroundColor: '#FFF9E8' },
  reviewTitle: { color: colors.text, fontWeight: '900', fontSize: 16 },
  itemCard: { gap: 10 },
  dim: { opacity: 0.55 },
  selectRow: { flexDirection: 'row', alignItems: 'center', gap: 9 },
  checkbox: { width: 27, height: 27, borderRadius: 8, borderWidth: 2, borderColor: colors.green, alignItems: 'center', justifyContent: 'center' },
  checked: { backgroundColor: colors.green },
  check: { color: '#fff', fontWeight: '900' },
  nameInput: { flex: 1, color: colors.text, fontSize: 16, fontWeight: '800', borderBottomWidth: 1, borderBottomColor: colors.border, paddingVertical: 5 },
  confidence: { color: colors.muted, fontSize: 11, fontWeight: '700' },
  reviewConfidence: { color: colors.orange },
  notes: { color: colors.muted, fontSize: 12, lineHeight: 17 },
  qtyInput: { borderWidth: 1, borderColor: colors.border, borderRadius: 10, paddingHorizontal: 11, paddingVertical: 9, color: colors.text },
  storageRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 6 },
  storage: { borderWidth: 1, borderColor: colors.border, borderRadius: 99, paddingHorizontal: 9, paddingVertical: 7 },
  storageActive: { backgroundColor: colors.green, borderColor: colors.green },
  storageText: { color: colors.text, fontSize: 11, fontWeight: '700' },
  storageTextActive: { color: '#fff' },
  manualCard: { gap: 9 },
  section: { color: colors.text, fontSize: 17, fontWeight: '900' },
  manualRow: { flexDirection: 'row', gap: 8 },
  manualInput: { flex: 1, borderWidth: 1, borderColor: colors.border, borderRadius: 10, paddingHorizontal: 11, paddingVertical: 10, color: colors.text },
  addButton: { backgroundColor: colors.green, borderRadius: 10, paddingHorizontal: 15, justifyContent: 'center' },
  addText: { color: '#fff', fontWeight: '900' }
});
