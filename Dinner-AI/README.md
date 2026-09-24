# InDinecision v0.9.5

Phone-ready Expo/React Native app for meal recommendations, kitchen inventory, fridge-photo scanning, UPC scanning, AI-generated recipes, favorites, meal feedback, and shopping lists.

The preview EAS profile builds an installable Android APK and points to the deployed backend:

https://dinner-ai-backend.onrender.com

The OpenAI API key stays on Render and is not committed here.

## Build from cloud tooling

Use the `Dinner-AI` directory as the project root, then run:

`eas build --platform android --profile preview`

The approved logo and launcher icon are included in `assets/`. Version 0.9.5 keeps the existing `com.dinnerai.app` application ID and local storage keys so it can update the existing beta installation without clearing saved data.

The app requires an authenticated Expo account to run the EAS build. Use the same Expo project already configured in `app.json`; the build produces the APK download link.
