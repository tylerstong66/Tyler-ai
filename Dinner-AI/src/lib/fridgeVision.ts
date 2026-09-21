import { Platform } from 'react-native';
import { DetectedIngredient } from '@/src/types';

const configuredBaseUrl = process.env.EXPO_PUBLIC_AI_BASE_URL?.replace(/\/$/, '');
const DEV_WEB_BASE_URL = Platform.OS === 'web' ? 'http://localhost:8787' : '';
const API_BASE_URL = configuredBaseUrl || DEV_WEB_BASE_URL;

export type FridgeVisionResult = {
  ingredients: DetectedIngredient[];
  model?: string;
};

export async function analyzeFridgePhoto(imageBase64: string, mimeType = 'image/jpeg'): Promise<FridgeVisionResult> {
  if (!API_BASE_URL) {
    throw new Error('AI_BACKEND_NOT_CONFIGURED');
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 90_000);

  try {
    const response = await fetch(`${API_BASE_URL}/analyze-fridge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ imageBase64, mimeType }),
      signal: controller.signal
    });

    const body = await response.json().catch(() => null) as any;
    if (!response.ok) {
      const message = typeof body?.error === 'string' ? body.error : `Vision request failed (${response.status}).`;
      throw new Error(message);
    }

    const ingredients = Array.isArray(body?.ingredients)
      ? body.ingredients
          .map(normalizeDetectedIngredient)
          .filter((item: DetectedIngredient | null): item is DetectedIngredient => Boolean(item))
      : [];

    return { ingredients, model: typeof body?.model === 'string' ? body.model : undefined };
  } catch (error: any) {
    if (error?.name === 'AbortError') throw new Error('The fridge scan timed out. Please try again.');
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function normalizeDetectedIngredient(value: any): DetectedIngredient | null {
  if (!value || typeof value.name !== 'string' || !value.name.trim()) return null;
  const confidence = typeof value.confidence === 'number'
    ? Math.max(0, Math.min(1, value.confidence))
    : 0.5;

  return {
    id: `detected-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
    name: value.name.trim(),
    quantity: typeof value.quantity === 'string' && value.quantity.trim() ? value.quantity.trim() : undefined,
    confidence,
    notes: typeof value.notes === 'string' && value.notes.trim() ? value.notes.trim() : undefined,
    selected: confidence >= 0.72,
    storage: 'refrigerator'
  };
}
