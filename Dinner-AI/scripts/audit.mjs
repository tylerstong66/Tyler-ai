import fs from 'node:fs';
import path from 'node:path';

const root = process.cwd();
const recipeFiles = [
  'src/data/recipes.ts',
  'src/data/recipesBreakfast.ts',
  'src/data/recipesLunch.ts',
  'src/data/recipesDinnerA.ts',
  'src/data/recipesDinnerB.ts',
  'src/data/recipesSnackDessert.ts'
];

const recipeIds = [];
const recipeTitles = [];
for (const relative of recipeFiles) {
  const source = fs.readFileSync(path.join(root, relative), 'utf8');
  for (const match of source.matchAll(/id:\s*'([^']+)'/g)) recipeIds.push(match[1]);
  for (const match of source.matchAll(/title:\s*'([^']+)'/g)) recipeTitles.push(match[1]);
}

assert(recipeIds.length === 100, `Expected 100 built-in recipes, found ${recipeIds.length}.`);
assert(new Set(recipeIds).size === recipeIds.length, 'Built-in recipe IDs must be unique.');
assert(new Set(recipeTitles).size === recipeTitles.length, 'Built-in recipe titles must be unique.');

const photoSource = fs.readFileSync(path.join(root, 'src/components/RecipePhoto.tsx'), 'utf8');
const photoMatch = photoSource.match(/const RECIPE_IDS = (\[[^;]+\]);/s);
assert(photoMatch, 'Could not find recipe photo atlas mapping.');
const photoIds = JSON.parse(photoMatch[1]);
assert(photoIds.length === 100, `Expected 100 photo atlas entries, found ${photoIds.length}.`);
assert(new Set(photoIds).size === photoIds.length, 'Photo atlas recipe IDs must be unique.');

const missingPhotos = recipeIds.filter((id) => !photoIds.includes(id));
const unknownPhotos = photoIds.filter((id) => !recipeIds.includes(id));
assert(!missingPhotos.length, `Recipes missing atlas photos: ${missingPhotos.join(', ')}`);
assert(!unknownPhotos.length, `Atlas has unknown recipe IDs: ${unknownPhotos.join(', ')}`);

const app = JSON.parse(fs.readFileSync(path.join(root, 'app.json'), 'utf8'));
const pkg = JSON.parse(fs.readFileSync(path.join(root, 'package.json'), 'utf8'));
assert(app.expo?.version === pkg.version, `app.json version (${app.expo?.version}) does not match package.json (${pkg.version}).`);
assert(Number.isInteger(app.expo?.android?.versionCode) && app.expo.android.versionCode > 0, 'Android versionCode must be a positive integer.');
assert(/^\d+$/.test(String(app.expo?.ios?.buildNumber || '')), 'iOS buildNumber must be numeric.');

const atlasPath = path.join(root, 'assets/recipe-atlas.jpg');
assert(fs.existsSync(atlasPath), 'Recipe photo atlas is missing.');
assert(fs.statSync(atlasPath).size < 3_000_000, 'Recipe photo atlas is unexpectedly large.');
assert(app.expo?.name === 'InDinecision', 'Display name must match the beta brand.');
assert(app.expo?.android?.package === 'com.dinnerai.app', 'Changing the Android package would break beta upgrades.');
for (const asset of ['assets/indinecision-icon.png', 'assets/indinecision-logo.png']) {
  assert(fs.existsSync(path.join(root, asset)), `Missing brand asset: ${asset}`);
}

console.log(`InDinecision audit passed: ${recipeIds.length} recipes, ${photoIds.length} mapped photos, version ${pkg.version}.`);

function assert(condition, message) {
  if (!condition) {
    console.error('AUDIT FAILED:', message);
    process.exit(1);
  }
}
