import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

const configuredBaseUrl = process.env.EXPO_PUBLIC_AI_BASE_URL?.replace(/\/$/, '');
const DEV_WEB_BASE_URL = Platform.OS === 'web' ? 'http://localhost:8787' : '';
export const API_BASE_URL = configuredBaseUrl || DEV_WEB_BASE_URL;

export const BETA_TOKEN_KEY = 'dinner-ai-beta-token-v1';
export const ONBOARDING_KEY = 'dinner-ai-onboarding-v1';
const SESSION_KEY = 'dinner-ai-beta-session-v1';

export async function getBetaToken() {
  return AsyncStorage.getItem(BETA_TOKEN_KEY);
}

export async function hasCompletedOnboarding() {
  return (await AsyncStorage.getItem(ONBOARDING_KEY)) === 'yes';
}

export async function markOnboardingComplete() {
  await AsyncStorage.setItem(ONBOARDING_KEY, 'yes');
}

export async function redeemBetaCode(code: string) {
  if (!API_BASE_URL) throw new Error('InDinecision beta service is not configured.');

  const response = await fetchWithTimeout(`${API_BASE_URL}/beta/access`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      code: code.trim(),
      appVersion: appVersion(),
      platform: Platform.OS
    })
  }, 15_000);
  const body = await response.json().catch(() => null) as any;
  if (!response.ok || typeof body?.token !== 'string') {
    throw new Error(typeof body?.error === 'string' ? body.error : 'That beta access code did not work.');
  }
  await AsyncStorage.setItem(BETA_TOKEN_KEY, body.token);
  return body.token as string;
}

export async function clearBetaToken() {
  await AsyncStorage.removeItem(BETA_TOKEN_KEY);
}

export async function betaFetch(path: string, init: RequestInit = {}, timeoutMs = 15_000) {
  if (!API_BASE_URL) throw new Error('InDinecision beta service is not configured.');
  const token = await getBetaToken();
  if (!token) throw new Error('BETA_ACCESS_REQUIRED');

  const headers = new Headers(init.headers || {});
  headers.set('Authorization', `Bearer ${token}`);
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json');

  const response = await fetchWithTimeout(`${API_BASE_URL}${path}`, { ...init, headers }, timeoutMs);
  if (response.status === 401) {
    await clearBetaToken();
    throw new Error('BETA_ACCESS_REQUIRED');
  }
  return response;
}

export async function sendBetaEvent(event: string, screen?: string, details?: Record<string, string | number | boolean | null>) {
  try {
    const sessionId = await getSessionId();
    await betaFetch('/event', {
      method: 'POST',
      body: JSON.stringify({
        event,
        screen: screen || '',
        details: details || {},
        appVersion: appVersion(),
        platform: Platform.OS,
        sessionId
      })
    }, 7_000);
  } catch {
    // Analytics should never interrupt the app.
  }
}

export async function sendBetaFeedback(input: { category: string; message: string; screen?: string }) {
  const sessionId = await getSessionId();
  const response = await betaFetch('/feedback', {
    method: 'POST',
    body: JSON.stringify({
      category: input.category,
      message: input.message,
      screen: input.screen || '',
      appVersion: appVersion(),
      platform: Platform.OS,
      sessionId
    })
  }, 15_000);
  const body = await response.json().catch(() => null) as any;
  if (!response.ok) throw new Error(typeof body?.error === 'string' ? body.error : 'Feedback could not be sent.');
  return body;
}

export async function reportClientError(error: unknown, screen?: string, fatal = false) {
  try {
    const value = error instanceof Error ? error : new Error(String(error));
    const sessionId = await getSessionId();
    await betaFetch('/client-error', {
      method: 'POST',
      body: JSON.stringify({
        message: value.message.slice(0, 700),
        stack: typeof value.stack === 'string' ? value.stack.slice(0, 2500) : '',
        screen: screen || '',
        fatal,
        appVersion: appVersion(),
        platform: Platform.OS,
        sessionId
      })
    }, 7_000);
  } catch {
    // Error reporting must not create another user-facing error.
  }
}

export function friendlyBetaError(error: any, fallback: string) {
  const message = typeof error?.message === 'string' ? error.message : '';
  if (message === 'BETA_ACCESS_REQUIRED') return 'Your beta session has expired. Reopen InDinecision and enter the beta access code again.';
  if (/rate limit|too many|daily limit/i.test(message)) return message;
  if (/timed out|timeout/i.test(message)) return 'InDinecision took too long to respond. Please try again.';
  if (/network request failed|failed to fetch|network/i.test(message)) return 'InDinecision could not reach the service. Check your internet connection and try again.';
  return message || fallback;
}

export function appVersion() {
  return Constants.expoConfig?.version || 'beta';
}

async function getSessionId() {
  let value = await AsyncStorage.getItem(SESSION_KEY);
  if (value) return value;
  value = `session-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  await AsyncStorage.setItem(SESSION_KEY, value);
  return value;
}


async function fetchWithTimeout(url: string, init: RequestInit, timeoutMs: number) {
  if (init.signal) return fetch(url, init);

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } catch (error: any) {
    if (error?.name === 'AbortError') throw new Error('InDinecision request timed out. Please try again.');
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
