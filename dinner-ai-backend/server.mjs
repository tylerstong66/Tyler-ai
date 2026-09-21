import http from 'node:http';

const PORT = Number(process.env.PORT || 8787);
const KEY = process.env.OPENAI_API_KEY || '';
const VISION_MODEL = process.env.OPENAI_VISION_MODEL || 'gpt-5.6-luna';
const RECIPE_MODEL = process.env.OPENAI_RECIPE_MODEL || 'gpt-5.6-luna';
const MAX_BODY = 15 * 1024 * 1024;

const server = http.createServer(async (req, res) => {
  cors(res);
  if (req.method === 'OPTIONS') return json(res, 204, {});
  if (req.method === 'GET' && req.url === '/health') {
    return json(res, 200, { ok: true, hasApiKey: Boolean(KEY), visionModel: VISION_MODEL, recipeModel: RECIPE_MODEL });
  }
  if (!KEY && req.method === 'POST') return json(res, 503, { error: 'OPENAI_API_KEY is not configured on the server.' });

  try {
    if (req.method === 'POST' && req.url === '/analyze-fridge') {
      const body = await readBody(req);
      const imageBase64 = typeof body.imageBase64 === 'string' ? body.imageBase64 : '';
      if (imageBase64.length < 100) return json(res, 400, { error: 'A fridge image is required.' });
      const mime = body.mimeType === 'image/png' ? 'image/png' : 'image/jpeg';
      const result = await callOpenAI(VISION_MODEL, [
        { role: 'user', content: [
          { type: 'input_text', text: 'Identify visible food ingredients in this refrigerator or pantry photo. Use practical ingredient names, do not invent hidden contents, ignore non-food items, and lower confidence for ambiguous items.' },
          { type: 'input_image', image_url: 'data:' + mime + ';base64,' + imageBase64, detail: 'high' }
        ] }
      ], fridgeFormat());
      const items = Array.isArray(result.ingredients) ? result.ingredients : [];
      return json(res, 200, { ingredients: items.slice(0, 30), model: VISION_MODEL });
    }

    if (req.method === 'POST' && req.url === '/generate-recipe') {
      const body = normalizeRecipeRequest(await readBody(req));
      if (!body.pantry.length) return json(res, 400, { error: 'Add at least one kitchen item first.' });
      const instruction = [
        'Create one practical home-cooking recipe.',
        'The meal category must be exactly ' + body.mealCategory + '.',
        'The cooking time must fit ' + timeText(body.timeBucket) + '.',
        'Treat allergies and avoid-items as hard constraints.',
        'Prefer kitchen inventory; list only genuinely missing items in missingIngredients.',
        'Use feedback as taste preference only, never as an allergy signal.',
        'Return realistic quantities and safe cooking directions.'
      ].join(' ');
      const result = await callOpenAI(RECIPE_MODEL, [
        { role: 'system', content: [{ type: 'input_text', text: instruction }] },
        { role: 'user', content: [{ type: 'input_text', text: JSON.stringify(body) }] }
      ], recipeFormat(), { effort: 'low' });
      validateRecipe(result, body);
      result.id = 'ai-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);
      result.generated = true;
      result.generatedAt = Date.now();
      return json(res, 200, { recipe: result, model: RECIPE_MODEL });
    }

    return json(res, 404, { error: 'Not found' });
  } catch (error) {
    return json(res, error && error.code === 'BODY_TOO_LARGE' ? 413 : 500, { error: error && error.message ? error.message : 'Request failed.' });
  }
});

server.listen(PORT, '0.0.0.0', () => console.log('Dinner AI backend listening on port ' + PORT));

async function callOpenAI(model, input, format, reasoning) {
  const payload = { model, input, text: { format } };
  if (reasoning) payload.reasoning = reasoning;
  const response = await fetch('https://api.openai.com/v1/responses', {
    method: 'POST',
    headers: { Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await response.json();
  if (!response.ok) throw new Error((data.error && data.error.message) || 'OpenAI request failed (' + response.status + ').');
  const text = outputText(data);
  if (!text) throw new Error('The AI service returned no structured data.');
  try { return JSON.parse(text); } catch { throw new Error('The AI service returned malformed structured data.'); }
}

function fridgeFormat() {
  return {
    type: 'json_schema', name: 'fridge_ingredients', strict: true,
    schema: {
      type: 'object', additionalProperties: false, required: ['ingredients'],
      properties: { ingredients: { type: 'array', items: {
        type: 'object', additionalProperties: false,
        required: ['name', 'quantity', 'confidence', 'notes'],
        properties: {
          name: { type: 'string' }, quantity: { type: 'string' },
          confidence: { type: 'number', minimum: 0, maximum: 1 }, notes: { type: 'string' }
        }
      } } }
    }
  };
}

function recipeFormat() {
  return {
    type: 'json_schema', name: 'meal_recipe', strict: true,
    schema: {
      type: 'object', additionalProperties: false,
      required: ['title','description','minutes','category','servings','ingredients','instructions','tags','allergens','pantryIngredientsUsed','missingIngredients','safetyNotes','generationReason'],
      properties: {
        title: { type: 'string' }, description: { type: 'string' },
        minutes: { type: 'integer', minimum: 5, maximum: 480 },
        category: { type: 'string', enum: ['breakfast','lunch','dinner','snack'] },
        servings: { type: 'integer', minimum: 1, maximum: 12 },
        ingredients: { type: 'array', items: { type: 'string' }, minItems: 2, maxItems: 30 },
        instructions: { type: 'array', items: { type: 'string' }, minItems: 2, maxItems: 20 },
        tags: { type: 'array', items: { type: 'string' }, maxItems: 12 },
        allergens: { type: 'array', items: { type: 'string' }, maxItems: 12 },
        pantryIngredientsUsed: { type: 'array', items: { type: 'string' }, maxItems: 30 },
        missingIngredients: { type: 'array', items: { type: 'string' }, maxItems: 12 },
        safetyNotes: { type: 'string' }, generationReason: { type: 'string' }
      }
    }
  };
}

function normalizeRecipeRequest(body) {
  const pantry = Array.isArray(body.pantry) ? body.pantry.slice(0, 80).filter(x => x && typeof x.name === 'string' && x.name.trim()).map(x => ({
    name: x.name.trim(), quantity: typeof x.quantity === 'string' ? x.quantity.trim() : '',
    storage: ['refrigerator','freezer','pantry','seasoning'].includes(x.storage) ? x.storage : 'pantry'
  })) : [];
  const profile = body.profile && typeof body.profile === 'object' ? body.profile : {};
  return {
    pantry,
    profile: {
      likes: strings(profile.likes, 30), dislikes: strings(profile.dislikes, 30), allergies: strings(profile.allergies, 30),
      dietaryNotes: typeof profile.dietaryNotes === 'string' ? profile.dietaryNotes.slice(0, 1000) : ''
    },
    timeBucket: ['quick','medium','long'].includes(body.timeBucket) ? body.timeBucket : 'quick',
    mealCategory: ['breakfast','lunch','dinner','snack'].includes(body.mealCategory) ? body.mealCategory : 'dinner',
    chosenRecipes: Array.isArray(body.chosenRecipes) ? body.chosenRecipes.slice(0, 10) : [],
    ratedRecipes: Array.isArray(body.ratedRecipes) ? body.ratedRecipes.slice(0, 15) : []
  };
}

function validateRecipe(recipe, request) {
  if (!recipe || recipe.category !== request.mealCategory) throw new Error('Generated recipe did not match the requested meal category.');
  const m = Number(recipe.minutes);
  if (request.timeBucket === 'quick' && m > 30) throw new Error('Generated recipe exceeded the requested cooking time.');
  if (request.timeBucket === 'medium' && !(m > 30 && m <= 120)) throw new Error('Generated recipe did not match the requested cooking time.');
  if (request.timeBucket === 'long' && m <= 120) throw new Error('Generated recipe did not match the requested cooking time.');
  const text = strings(recipe.ingredients, 30).concat(strings(recipe.allergens, 12)).join(' ').toLowerCase();
  const conflict = request.profile.allergies.find(x => x && text.includes(x.toLowerCase()));
  if (conflict) throw new Error('Generated recipe conflicted with an avoid-item (' + conflict + ').');
  const notes = String(request.profile.dietaryNotes || '').toLowerCase();
  const meat = ['chicken','beef','pork','turkey','lamb','sausage','bacon','ham','fish','salmon','tuna','shrimp','shellfish'];
  const animal = meat.concat(['egg','milk','cheese','butter','cream','yogurt','honey']);
  if (notes.includes('vegan') && animal.some(x => text.includes(x))) throw new Error('Generated recipe conflicted with the saved vegan preference.');
  if (notes.includes('vegetarian') && meat.some(x => text.includes(x))) throw new Error('Generated recipe conflicted with the saved vegetarian preference.');
  if ((notes.includes('no pork') || notes.includes('pork-free') || notes.includes('pork free')) && /pork|bacon|ham/.test(text)) throw new Error('Generated recipe conflicted with the saved pork-free preference.');
}

function timeText(bucket) {
  if (bucket === 'medium') return '31 to 120 minutes total';
  if (bucket === 'long') return 'more than 120 minutes total';
  return '30 minutes or less total';
}

function strings(value, max) {
  return Array.isArray(value) ? value.filter(x => typeof x === 'string').map(x => x.trim()).filter(Boolean).slice(0, max) : [];
}

function outputText(data) {
  if (typeof data.output_text === 'string') return data.output_text;
  for (const item of data.output || []) for (const c of item.content || []) if (c.type === 'output_text' && typeof c.text === 'string') return c.text;
  return '';
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let body = ''; let bytes = 0;
    req.on('data', chunk => {
      bytes += chunk.length;
      if (bytes > MAX_BODY) { const e = new Error('Photo payload is too large.'); e.code = 'BODY_TOO_LARGE'; reject(e); req.destroy(); return; }
      body += chunk;
    });
    req.on('end', () => { try { resolve(JSON.parse(body || '{}')); } catch { reject(new Error('Invalid JSON request.')); } });
    req.on('error', reject);
  });
}

function cors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
}

function json(res, status, value) {
  res.writeHead(status, { 'Content-Type': 'application/json; charset=utf-8' });
  res.end(status === 204 ? '' : JSON.stringify(value));
}
