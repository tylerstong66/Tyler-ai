import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { ActivityIndicator, Alert, Linking, Pressable, StyleSheet, Text, View } from 'react-native';
import { Card, PrimaryButton, SecondaryButton, colors } from '@/src/components/ui';
import { useApp } from '@/src/context/AppContext';
import { BarcodeProduct, lookupBarcode } from '@/src/lib/openFoodFacts';
import { PantryStorage } from '@/src/types';
import { reportClientError, sendBetaEvent } from '@/src/lib/beta';

const STORAGE_OPTIONS: { key: PantryStorage; label: string }[] = [
  { key: 'refrigerator', label: 'Refrigerator' },
  { key: 'freezer', label: 'Freezer' },
  { key: 'pantry', label: 'Pantry' },
  { key: 'seasoning', label: 'Seasoning' }
];

export default function ScanUpcScreen() {
  const router = useRouter();
  const { addPantryItem } = useApp();
  const [permission, requestPermission] = useCameraPermissions();
  const [locked, setLocked] = useState(false);
  const [loading, setLoading] = useState(false);
  const [product, setProduct] = useState<BarcodeProduct | null>(null);
  const [lastBarcode, setLastBarcode] = useState<string | null>(null);
  const [storage, setStorage] = useState<PantryStorage>('pantry');

  async function handleScan(data: string) {
    if (locked) return;
    setLocked(true);
    setLastBarcode(data);
    setLoading(true);
    try {
      const found = await lookupBarcode(data);
      setProduct(found);
      void sendBetaEvent('upc_scan_completed', '/scan-upc', { found: Boolean(found) });
      if (!found) Alert.alert('Product not found', 'The barcode scanned correctly, but this product was not found in the food database.');
    } catch (error) {
      void reportClientError(error, '/scan-upc');
      void sendBetaEvent('upc_scan_failed', '/scan-upc');
      Alert.alert('Lookup failed', error instanceof Error ? error.message : 'Please try again.');
    } finally {
      setLoading(false);
    }
  }

  function addProduct() {
    if (!product) return;
    addPantryItem({ name: product.name, brand: product.brand, barcode: product.barcode, imageUrl: product.imageUrl, storage });
    const label = STORAGE_OPTIONS.find((item) => item.key === storage)?.label ?? 'Pantry';
    Alert.alert(`Added to ${label}`, product.name, [{ text: 'Done', onPress: () => router.back() }]);
  }

  function scanAgain() {
    setProduct(null);
    setLastBarcode(null);
    setStorage('pantry');
    setLocked(false);
  }

  if (!permission) return <View style={styles.center}><ActivityIndicator /></View>;
  if (!permission.granted) {
    return (
      <View style={styles.permission}>
        <Text style={styles.title}>Camera permission needed</Text>
        <Text style={styles.help}>InDinecision uses the camera only when you choose to scan food or your fridge.</Text>
        <PrimaryButton
          label={permission.canAskAgain ? "Allow camera" : "Open phone settings"}
          onPress={() => permission.canAskAgain ? void requestPermission() : void Linking.openSettings()}
        />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {!locked ? (
        <CameraView
          style={styles.camera}
          facing="back"
          barcodeScannerSettings={{ barcodeTypes: ['ean13', 'ean8', 'upc_a', 'upc_e'] }}
          onBarcodeScanned={({ data }) => handleScan(data)}
        >
          <View style={styles.overlay}>
            <View style={styles.frame} />
            <Text style={styles.scanText}>Center the UPC barcode in the box</Text>
          </View>
        </CameraView>
      ) : (
        <View style={styles.resultWrap}>
          {loading ? (
            <View style={styles.center}><ActivityIndicator size="large" /><Text style={styles.help}>Looking up {lastBarcode}…</Text></View>
          ) : product ? (
            <Card style={styles.card}>
              <Text style={styles.kicker}>FOUND</Text>
              <Text style={styles.title}>{product.name}</Text>
              {product.brand ? <Text style={styles.help}>{product.brand}</Text> : null}
              <Text style={styles.barcode}>UPC: {product.barcode}</Text>
              <Text style={styles.storageLabel}>Where do you keep it?</Text>
              <View style={styles.storageWrap}>
                {STORAGE_OPTIONS.map((option) => {
                  const active = storage === option.key;
                  return (
                    <Pressable key={option.key} onPress={() => setStorage(option.key)} style={[styles.storageButton, active && styles.storageButtonActive]}>
                      <Text style={[styles.storageText, active && styles.storageTextActive]}>{option.label}</Text>
                    </Pressable>
                  );
                })}
              </View>
              <PrimaryButton label={`Add to ${STORAGE_OPTIONS.find((item) => item.key === storage)?.label}`} onPress={addProduct} />
              <SecondaryButton label="Scan another" onPress={scanAgain} />
            </Card>
          ) : (
            <Card style={styles.card}>
              <Text style={styles.title}>Not in the database</Text>
              <Text style={styles.help}>Scan another item, or add the ingredient manually from Kitchen.</Text>
              <PrimaryButton label="Scan another" onPress={scanAgain} />
            </Card>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111' },
  camera: { flex: 1 },
  overlay: { flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.18)' },
  frame: { width: '82%', height: 190, borderWidth: 3, borderColor: '#fff', borderRadius: 26 },
  scanText: { color: '#fff', fontWeight: '800', marginTop: 18, backgroundColor: 'rgba(0,0,0,0.52)', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 999, overflow: 'hidden' },
  resultWrap: { flex: 1, backgroundColor: colors.bg, justifyContent: 'center', paddingHorizontal: 20, paddingVertical: 24 },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', gap: 12, backgroundColor: colors.bg },
  permission: { flex: 1, justifyContent: 'center', gap: 14, padding: 24, backgroundColor: colors.bg },
  card: { gap: 13 },
  kicker: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.4 },
  title: { color: colors.text, fontSize: 26, lineHeight: 32, fontWeight: '900', letterSpacing: -0.35 },
  help: { color: colors.muted, lineHeight: 21 },
  barcode: { color: colors.muted, fontSize: 12, fontWeight: '700' },
  storageLabel: { color: colors.text, fontWeight: '900', marginTop: 6 },
  storageWrap: { flexDirection: 'row', flexWrap: 'wrap', gap: 7 },
  storageButton: { borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface, paddingHorizontal: 12, paddingVertical: 9, borderRadius: 999 },
  storageButtonActive: { borderColor: colors.greenDark, backgroundColor: colors.greenDark },
  storageText: { color: colors.text, fontSize: 12, fontWeight: '700' },
  storageTextActive: { color: '#fff' }
});
