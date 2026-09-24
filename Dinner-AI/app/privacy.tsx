import Constants from 'expo-constants';
import React from 'react';
import { ScrollView, StyleSheet, Text, View } from 'react-native';
import { colors } from '@/src/components/ui';

export default function PrivacyScreen() {
  const version = Constants.expoConfig?.version || 'beta';

  return (
    <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
      <Text style={styles.eyebrow}>BETA PRIVACY & SAFETY</Text>
      <Text style={styles.title}>How InDinecision handles your test data</Text>
      <Text style={styles.lead}>InDinecision v{version} is an early private beta. The goal is to collect enough information to find bugs and improve the experience without collecting unnecessary personal information.</Text>

      <Section title="What stays on your phone">
        Your Kitchen inventory, favorites, food preferences, recipe history, ratings, generated recipes, and shopping list are stored locally on this device. Uninstalling the app may erase that local data.
      </Section>

      <Section title="When you scan your fridge">
        The photo is sent to the InDinecision backend and an AI service so visible ingredients can be identified. InDinecision does not intentionally save the photo in its own app database. Service providers may process data under their own service terms. Only use the scan when you are comfortable sending the image for analysis.
      </Section>

      <Section title="Beta diagnostics">
        InDinecision may send limited technical events such as app version, platform, feature used, error message, and screen name. These events are intended to help identify crashes, failed scans, timeouts, and confusing workflows. Pantry contents and fridge images are not included in routine beta analytics.
      </Section>

      <Section title="Feedback you send">
        If you use Send Feedback, your category, message, app version, platform, and current screen are sent to the beta service so the issue can be reviewed. Do not include passwords, financial information, or other sensitive personal information in feedback.
      </Section>

      <Section title="Food safety and allergies">
        AI detections and recipes can be wrong. InDinecision is not a medical or allergy-safety service. For serious allergies, verify every ingredient label, cross-contact risk, internal temperature, storage condition, and food-safety decision yourself.
      </Section>

      <View style={styles.callout}>
        <Text style={styles.calloutTitle}>Private beta rule</Text>
        <Text style={styles.calloutText}>If something looks wrong, confusing, unsafe, or inconsistent, use the Feedback button instead of assuming the app is correct.</Text>
      </View>
    </ScrollView>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <View style={styles.section}>
      <Text style={styles.sectionTitle}>{title}</Text>
      <Text style={styles.body}>{children}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  content: { paddingHorizontal: 20, paddingTop: 18, paddingBottom: 48, backgroundColor: colors.bg },
  eyebrow: { color: colors.green, fontSize: 11, fontWeight: '900', letterSpacing: 1.7 },
  title: { color: colors.text, fontSize: 30, lineHeight: 36, fontWeight: '900', letterSpacing: -0.7, marginTop: 7 },
  lead: { color: colors.muted, fontSize: 15, lineHeight: 23, marginTop: 10, marginBottom: 26 },
  section: { marginBottom: 24 },
  sectionTitle: { color: colors.text, fontSize: 18, fontWeight: '900', marginBottom: 7 },
  body: { color: colors.muted, fontSize: 14.5, lineHeight: 22 },
  callout: { backgroundColor: colors.greenSoft, borderRadius: 20, padding: 17, marginTop: 2 },
  calloutTitle: { color: colors.greenDark, fontWeight: '900', fontSize: 15, marginBottom: 5 },
  calloutText: { color: colors.text, fontSize: 13.5, lineHeight: 20 }
});
