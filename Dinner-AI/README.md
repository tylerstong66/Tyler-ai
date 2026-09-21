# Dinner AI v0.6

Phone-ready Expo/React Native app for meal recommendations, kitchen inventory, fridge-photo scanning, UPC scanning, AI-generated recipes, favorites, meal feedback, and shopping lists.

The preview EAS profile builds an installable Android APK and points to the deployed backend:

https://dinner-ai-backend.onrender.com

The OpenAI API key stays on Render and is not committed here.

## Build from cloud tooling

Use the `Dinner-AI` directory as the project root, then run:

`eas build --platform android --profile preview`

This GitHub copy omits custom icon/splash image assets so cloud upload is text-only; Expo can use platform defaults for a test APK. Custom artwork can be restored before store release.
