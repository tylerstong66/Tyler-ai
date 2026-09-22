import http from 'node:http';
import crypto from 'node:crypto';

const PORT = Number(process.env.PORT || 8787);
const KEY = process.env.OPENAI_API_KEY || '';
const VISION_MODEL = process.env.OPENAI_VISION_MODEL || 'gpt-5.6-luna';
const RECIPE_MODEL = process.env.OPENAI_RECIPE_MODEL || 'gpt-5.6-luna';
const BETA_CODE = process.env.DINNER_AI_BETA_CODE || '';
const BETA_SECRET = process.env.DINNER_AI_BETA_SECRET || '';
const BETA_AUTH_ENABLED = Boolean(BETA_CODE && BETA_SECRET);
const MAX_BODY = 15 * 1024 * 1024;
const DAY = 24 * 60 * 60 * 1000;
const HOUR = 60 * 60 * 1000;
const rateBuckets = new Map();

const LIMITS = {
  '/analyze-fridge': { limit: 12, windowMs: DAY, label: 'fridge scans' },
  '/generate-recipe': { limit: 25, windowMs: DAY, label: 'AI recipes' },
  '/feedback': { limit: 50, windowMs: DAY, label: 'feedback reports' },
  '/event': { limit: 600, windowMs: DAY, label: 'beta events' },
  '/client-error': { limit: 120, windowMs: DAY, label: 'error reports' }
};

const PROTECTED_POSTS = new Set(Object.keys(LIMITS));

const server = http.createServer(async (req, res) => {
  cors(res);
  if (req.method === 'OPTIONS') return json(res, 204, {});

  if (req.method === 'GET' && req.url === '/health') {
    return json(res, 200, {
      ok: true,
      hasApiKey: Boolean(KEY),
      visionModel: VISION_MODEL,
      recipeModel: RECIPE_MODEL,
      betaProtected: BETA_AUTH_ENABLED
    });
  }

  try {
    if (req.method === 'POST' && req.url === '/beta/access') {
      const ip = clientIp(req);
      const accessLimit = takeRate('access:' + ip, 40, HOUR);
      if (!accessLimit.allowed) {
        return json(res, 429, { error: 'Too many beta access attempts. Please try again later.', retryAfterSeconds: accessLimit.retryAfterSeconds });
      }

      const body = await readBody(req);
      const code = typeof body.code === 'string' ? body.code.trim() : '';

      if (!BETA_AUTH_ENABLED) {
        return json(res, 200, { token: 'development-beta-token', expiresInDays: 30 });
      }

      if (!code || !safeEqualText(code.toUpperCase(), BETA_CODE.toUpperCase())) {
        return json(res, 403, { error: 'That beta access code is not valid.' });
      }

      const token = issueBetaToken();
      console.log('BETA_ACCESS ' + JSON.stringify({
        at: new Date().toISOString(),
        appVersion: cleanText(body.appVersion, 30),
        platform: cleanText(body.platform, 30)
      }));
      return json(res, 200, { token, expiresInDays: 30 });
    }

    let betaSession = null;
    if (req.method === 'POST' && PROTECTED_POSTS.has(req.url || '')) {
      const verified = verifyBetaRequest(req);
      if (!verified.ok) return json(res, 401, { error: 'Beta access expired. Re-enter the beta access code.' });
      betaSession = verified.session;

      const config = LIMITS[req.url];
      const rate = takeRate(betaSession.id + ':' + req.url, config.limit, config.windowMs);
      if (!rate.allowed) {
        const daily = config.windowMs >= DAY;
        return json(res, 429, {
          error: (daily ? 'Daily beta limit reached for ' : 'Beta limit reached for ') + config.label + '. Please try again later.',
          retryAfterSeconds: rate.retryAfterSeconds
        });
      }
    }

    if (req.method === 'POST' && req.url === '/event') {
      const body = await readBody(req);
      console.log('BETA_EVENT ' + JSON.stringify({
        at: new Date().toISOString(),
        betaSession: betaSession?.id || '',
        sessionId: cleanText(body.sessionId, 80),
        event: cleanText(body.event, 80),
        screen: cleanText(body.screen, 120),
        appVersion: cleanText(body.appVersion, 30),
        platform: cleanText(body.platform, 30),
        details: cleanDetails(body.details)
      }));
      return json(res, 200, { ok: true });
    }

    if (req.method === 'POST' && req.url === '/feedback') {
      const body = await readBody(req);
      const message = cleanText(body.message, 4000);
      if (!message) return json(res, 400, { error: 'Feedback message is required.' });

      console.log('BETA_FEEDBACK ' + JSON.stringify({
        at: new Date().toISOString(),
        betaSession: betaSession?.id || '',
        sessionId: cleanText(body.sessionId, 80),
        category: cleanText(body.category, 80),
        message,
        screen: cleanText(body.screen, 120),
        appVersion: cleanText(body.appVersion, 30),
        platform: cleanText(body.platform, 30)
      }));
      return json(res, 200, { ok: true });
    }

    if (req.method === 'POST' && req.url === '/client-error') {
      const body = await readBody(req);
      console.error('BETA_CLIENT_ERROR ' + JSON.stringify({
        at: new Date().toISOString(),
        betaSession: betaSession?.id || '',
        sessionId: cleanText(body.sessionId, 80),
        message: cleanText(body.message, 700),
        stack: cleanText(body.stack, 2500),
        screen: cleanText(body.screen, 120),
        fatal: Boolean(body.fatal),
        appVersion: cleanText(body.appVersion, 30),
        platform: cleanText(body.platform, 30)
      }));
      return json(res, 200, { ok: true });
    }

    if (req.method === 'POST' && req.url === '/analyze-fridge') {
      if (!KEY) return json(res, 503, { error: 'The AI service is temporarily unavailable.' });

      const body = await readBody(req);
      const imageBase64 = typeof body.imageBase64 === 'string' ? body.imageBase64 : '';
      if (imageBase64.length < 100) return json(res, 400, { error: 'A fridge image is required.' });
      const mime = body.mimeType === 'image/png' ? 'image/png' : 'image/jpeg';
      const image = { type: 'input_image', image_url: 'data:' + mime + ';base64,' + imageBase64, detail: 'high' };
      const firstPassPrompt = [
        'Create a thorough inventory of every visible food or beverage in this refrigerator or pantry photo.',
        'Inspect the image systematically from top to bottom and left to right, including door shelves and partially visible containers.',
        'Prioritize readable label or package text over container color, shape, or food color.',
        'Do not guess a specific product just because a bottle or jar resembles a familiar condiment.',
        'Explicitly check for milk and other beverage jugs, sauces, dressings, condiments, jars, squeeze bottles, and small containers.',
        'Use practical ingredient names rather than brand names unless the brand helps identify the food.',
        'If an item is visible but cannot be identified confidently, use a generic name such as "unknown condiment" or "bottled sauce" and give it low confidence instead of inventing a specific food.',
        'Do not invent hidden contents or include non-food items.'
      ].join(' ');

      const draft = await callOpenAI(VISION_MODEL, [
        { role: 'user', content: [
          { type: 'input_text', text: firstPassPrompt },
          image
        ] }
      ], fridgeFormat(), { effort: 'low' });

      const draftItems = Array.isArray(draft.ingredients) ? draft.ingredients : [];
      const auditPrompt = [
        'Audit this refrigerator/pantry photo a second time and return a corrected FINAL inventory.',
        'The first-pass draft is provided below. Do not blindly trust it.',
        'Correct misidentifications, remove unsupported guesses, and add foods the draft missed.',
        'Read visible labels carefully. Never decide between similar-looking products from color alone.',
        'Pay special attention to beverage containers (including milk jugs), sauces, salsa, dressings, mustard-like squeeze bottles, lemon/lime juice bottles, jars, and door-shelf condiments.',
        'A yellow bottle could be lemon juice rather than mustard; a red or tan jar could be salsa or another sauce rather than nut butter. Use label evidence whenever possible.',
        'If the label is unreadable or evidence conflicts, prefer a generic low-confidence item with a note saying what is uncertain.',
        'Return the complete final list, not just changes.',
        'FIRST-PASS DRAFT:',
        JSON.stringify(draftItems)
      ].join(' ');

      const reviewed = await callOpenAI(VISION_MODEL, [
        { role: 'user', content: [
          { type: 'input_text', text: auditPrompt },
          image
        ] }
      ], fridgeFormat(), { effort: 'medium' });

      const items = Array.isArray(reviewed.ingredients) ? reviewed.ingredients : draftItems;
      return json(res, 200, { ingredients: items.slice(0, 50), model: VISION_MODEL, passes: 2 });
    }

    if (req.method === 'POST' && req.url === '/generate-recipe') {
      if (!KEY) return json(res, 503, { error: 'The AI service is temporarily unavailable.' });

      const body = normalizeRecipeRequest(await readBody(req));
      if (!body.pantry.length) return json(res, 400, { error: 'Add at least one kitchen item first.' });
      const instruction = [
        'Create one original, polished home-cooking recipe at the standard of a professional test kitchen or fine restaurant, while keeping it practical for a home cook.',
        'Do not copy or imitate the wording of any published chef or recipe.',
        'The meal category must be exactly ' + body.mealCategory + '.',
        'The total cooking time must fit ' + timeText(body.timeBucket) + '.',
        'Treat allergies and avoid-items as hard constraints.',
        'Prefer the user\'s kitchen inventory and list only genuinely missing items in missingIngredients.',
        'Use feedback as taste preference only, never as an allergy signal.',
        'Every ingredient must include a useful quantity or count, except salt and pepper when they are truly to taste.',
        'Instructions must be chronological and precise. For every active cooking step, specify the burner heat level or oven temperature, an estimated time range, and a sensory doneness cue such as color, texture, reduction, or tenderness.',
        'When meat, poultry, seafood, eggs, casseroles, or reheated leftovers are involved, include an appropriate safe internal temperature in the relevant instruction and summarize critical safety information in safetyNotes.',
        'Use USDA-style minimum safety targets: poultry 165°F, ground beef/pork/lamb/veal 160°F, fish and whole beef/pork/lamb/veal cuts 145°F with a 3-minute rest for whole cuts, and egg dishes/casseroles 160°F or 165°F as appropriate.',
        'Include resting time when it materially affects texture or safety.',
        'Use professional technique: browning before braising, controlled simmering rather than violent boiling, proper pan preheating, finishing pasta in sauce where appropriate, resting proteins, and adding delicate herbs/acids at the right time.',
        'Keep the directions concise enough to cook from on a phone, but never omit temperatures, timing, or doneness information that affects success.'
      ].join(' ');

      const result = await callOpenAI(RECIPE_MODEL, [
        { role: 'system', content: [{ type: 'input_text', text: instruction }] },
        { role: 'user', content: [{ type: 'input_text', text: JSON.stringify(body) }] }
      ], recipeFormat(), { effort: 'medium' });
      validateRecipe(result, body);
      result.id = 'ai-' + Date.now() + '-' + Math.random().toString(36).slice(2, 8);
      result.generated = true;
      result.generatedAt = Date.now();
      return json(res, 200, { recipe: result, model: RECIPE_MODEL });
    }

    return json(res, 404, { error: 'Not found' });
  } catch (error) {
    console.error('DINNER_AI_SERVER_ERROR', error);
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
  if (!response.ok) throw new Error((data.error && data.error.message) || 'The AI provider returned an error (' + response.status + ').');
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
        category: { type: 'string', enum: ['breakfast','lunch','dinner','snack','dessert'] },
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
    mealCategory: ['breakfast','lunch','dinner','snack','dessert'].includes(body.mealCategory) ? body.mealCategory : 'dinner',
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

function issueBetaToken() {
  const id = crypto.randomUUID();
  const expires = Date.now() + 30 * DAY;
  const payload = id + '.' + expires;
  const signature = crypto.createHmac('sha256', BETA_SECRET).update(payload).digest('base64url');
  return payload + '.' + signature;
}

function verifyBetaRequest(req) {
  if (!BETA_AUTH_ENABLED) return { ok: true, session: { id: 'development' } };
  const auth = typeof req.headers.authorization === 'string' ? req.headers.authorization : '';
  if (!auth.startsWith('Bearer ')) return { ok: false };
  const token = auth.slice(7).trim();
  const parts = token.split('.');
  if (parts.length !== 3) return { ok: false };
  const [id, expiresText, signature] = parts;
  const expires = Number(expiresText);
  if (!id || !Number.isFinite(expires) || expires <= Date.now()) return { ok: false };
  const expected = crypto.createHmac('sha256', BETA_SECRET).update(id + '.' + expiresText).digest('base64url');
  if (!safeEqualText(signature, expected)) return { ok: false };
  return { ok: true, session: { id, expires } };
}

function takeRate(key, limit, windowMs) {
  const now = Date.now();
  const existing = rateBuckets.get(key);
  if (!existing || now >= existing.resetAt) {
    rateBuckets.set(key, { count: 1, resetAt: now + windowMs });
    return { allowed: true, retryAfterSeconds: 0 };
  }
  if (existing.count >= limit) {
    return { allowed: false, retryAfterSeconds: Math.max(1, Math.ceil((existing.resetAt - now) / 1000)) };
  }
  existing.count += 1;
  return { allowed: true, retryAfterSeconds: 0 };
}

function safeEqualText(a, b) {
  const left = Buffer.from(String(a));
  const right = Buffer.from(String(b));
  return left.length === right.length && crypto.timingSafeEqual(left, right);
}

function clientIp(req) {
  const forwarded = req.headers['x-forwarded-for'];
  if (typeof forwarded === 'string' && forwarded.trim()) return forwarded.split(',')[0].trim();
  return req.socket?.remoteAddress || 'unknown';
}

function cleanText(value, max) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}

function cleanDetails(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  const result = {};
  for (const [key, item] of Object.entries(value).slice(0, 15)) {
    const cleanKey = cleanText(key, 50);
    if (!cleanKey) continue;
    if (typeof item === 'string') result[cleanKey] = item.slice(0, 120);
    else if (typeof item === 'number' && Number.isFinite(item)) result[cleanKey] = item;
    else if (typeof item === 'boolean' || item === null) result[cleanKey] = item;
  }
  return result;
}

function cors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
}

function json(res, status, value) {
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store'
  });
  res.end(status === 204 ? '' : JSON.stringify(value));
}
