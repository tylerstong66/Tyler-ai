import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { ActivityIndicator, Image, KeyboardAvoidingView, Platform, StyleSheet, Text, TextInput, View } from 'react-native';
import { PrimaryButton, colors } from '@/src/components/ui';
import { redeemBetaCode, sendBetaEvent } from '@/src/lib/beta';

export default function BetaAccessScreen() {
  const router = useRouter();
  const [code, setCode] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  async function unlock() {
    const value = code.trim();
    if (!value || busy) return;
    setBusy(true);
    setError('');
    try {
      await redeemBetaCode(value);
      void sendBetaEvent('beta_access_granted', '/beta-access');
      router.replace('/(tabs)');
    } catch (e: any) {
      setError(e?.message || 'That access code did not work.');
    } finally {
      setBusy(false);
    }
  }

  return (
    <KeyboardAvoidingView style={styles.screen} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <View style={styles.card}>
        <Image source={require('../assets/indinecision-icon.png')} style={styles.icon} />
        <Text style={styles.eyebrow}>PRIVATE TEST</Text>
        <Text style={styles.title}>Welcome to InDinecision</Text>
        <Text style={styles.body}>Enter the beta code you were given. This helps us protect the AI service while a small group tests the app.</Text>

        <TextInput
          value={code}
          onChangeText={(value) => { setCode(value.toUpperCase()); setError(''); }}
          onSubmitEditing={() => void unlock()}
          autoCapitalize="characters"
          autoCorrect={false}
          placeholder="Beta access code"
          placeholderTextColor={colors.muted}
          style={styles.input}
          returnKeyType="done"
        />

        {error ? <Text style={styles.error}>{error}</Text> : null}
        {busy ? <ActivityIndicator color={colors.green} /> : null}
        <PrimaryButton label={busy ? 'Checking…' : 'Enter beta'} onPress={() => void unlock()} disabled={busy || !code.trim()} />
        <Text style={styles.help}>The code is only for invited testers. No account or personal information is required.</Text>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, justifyContent: 'center', paddingHorizontal: 24, backgroundColor: colors.bg },
  card: { backgroundColor: colors.card, borderWidth: 1, borderColor: colors.border, borderRadius: 28, padding: 24, gap: 14 },
  icon: { width: 62, height: 62, borderRadius: 21 },
  eyebrow: { color: colors.green, fontWeight: '900', fontSize: 10, letterSpacing: 1.7, marginTop: 4 },
  title: { color: colors.text, fontSize: 30, lineHeight: 35, fontWeight: '900', letterSpacing: -0.7 },
  body: { color: colors.muted, fontSize: 15, lineHeight: 22 },
  input: { height: 54, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.borderStrong, borderRadius: 17, paddingHorizontal: 16, color: colors.text, fontSize: 18, fontWeight: '900', letterSpacing: 1.5 },
  error: { color: colors.danger, lineHeight: 19, fontWeight: '700', fontSize: 13 },
  help: { color: colors.muted, textAlign: 'center', fontSize: 11.5, lineHeight: 17 }
});
