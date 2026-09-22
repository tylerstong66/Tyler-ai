import { Recipe } from '@/src/types';

export const BREAKFAST_RECIPES: Recipe[] = [
  {
    id:'soft-scrambled-eggs', title:'Soft Scrambled Eggs on Toast', description:'Slow, glossy curds finished with butter and chives over crisp sourdough.', minutes:12, category:'breakfast', servings:2,
    ingredients:['6 large eggs','2 tablespoons unsalted butter','2 slices sourdough bread','1 tablespoon chopped chives'],
    instructions:[
      'Toast the sourdough until crisp and keep warm.',
      'Whisk the eggs with a pinch of salt for 30 seconds. Melt 1 tablespoon butter in a nonstick skillet over medium-low heat.',
      'Add the eggs and cook 3 to 5 minutes, stirring almost constantly with a silicone spatula and scraping the bottom, until small soft curds form and the eggs remain slightly glossy.',
      'Remove from the heat just before they look fully done; stir in the remaining butter and chives for 20 seconds. For maximum food-safety assurance, egg dishes should reach 160°F.',
      'Spoon immediately over the warm toast and finish with black pepper.'
    ], tags:['breakfast','quick','eggs','vegetarian','chef technique'], allergens:['eggs','dairy','gluten']
  },
  {
    id:'buttermilk-pancakes', title:'Buttermilk Pancakes', description:'Tall, tender pancakes with crisp buttery edges and a soft center.', minutes:25, category:'breakfast', servings:4,
    ingredients:['2 cups all-purpose flour','2 tablespoons sugar','2 teaspoons baking powder','1/2 teaspoon baking soda','2 cups buttermilk','2 large eggs','4 tablespoons unsalted butter, melted'],
    instructions:[
      'Heat the oven to 200°F to hold finished pancakes. Whisk flour, sugar, baking powder, baking soda, and 1/2 teaspoon salt.',
      'Whisk buttermilk, eggs, and melted butter separately. Fold wet into dry just until no large dry pockets remain; small lumps are desirable. Rest 10 minutes.',
      'Heat a griddle or heavy skillet over medium heat until a drop of water dances, about 350°F surface temperature. Lightly butter the pan.',
      'Portion about 1/4 cup batter per pancake. Cook 2 to 3 minutes until bubbles form and edges look set; flip once and cook 1 to 2 minutes until golden and the center springs back.',
      'Hold on a rack in the 200°F oven while cooking the remaining batter.'
    ], tags:['breakfast','pancakes','vegetarian','family'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'crispy-waffles', title:'Crisp Buttermilk Waffles', description:'Deeply golden waffles with a crisp shell and fluffy interior.', minutes:30, category:'breakfast', servings:4,
    ingredients:['2 cups all-purpose flour','2 tablespoons sugar','1 tablespoon baking powder','1 3/4 cups buttermilk','2 large eggs','6 tablespoons unsalted butter, melted','1 teaspoon vanilla extract'],
    instructions:[
      'Heat the oven to 225°F and preheat the waffle iron fully, usually 5 to 10 minutes.',
      'Whisk flour, sugar, baking powder, and 1/2 teaspoon salt. In another bowl whisk buttermilk, eggs, melted butter, and vanilla.',
      'Fold wet into dry just until combined. Rest 5 minutes.',
      'Lightly grease the iron if needed. Add enough batter to cover about two-thirds of the grid, close, and cook 4 to 6 minutes until steam slows dramatically and the waffle is deeply golden.',
      'Transfer waffles directly to the oven rack so steam can escape and they stay crisp.'
    ], tags:['breakfast','waffles','vegetarian'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'custardy-french-toast', title:'Custardy Cinnamon French Toast', description:'Thick-cut bread soaked through with vanilla custard, then browned gently in butter.', minutes:25, category:'breakfast', servings:4,
    ingredients:['8 thick slices brioche or challah','4 large eggs','1 cup whole milk','2 tablespoons sugar','1 teaspoon vanilla extract','1/2 teaspoon ground cinnamon','3 tablespoons unsalted butter'],
    instructions:[
      'Heat the oven to 250°F. Whisk eggs, milk, sugar, vanilla, cinnamon, and a pinch of salt in a shallow dish.',
      'Soak bread 30 to 45 seconds per side for brioche, or up to 60 seconds per side for drier bread, so the custard reaches the center without making the slices collapse.',
      'Heat a large skillet over medium-low heat and melt 1 tablespoon butter. Cook in batches 3 to 4 minutes per side until evenly golden and the center feels hot and custardy.',
      'Transfer to a rack in the 250°F oven while cooking the rest. Egg-rich breakfast dishes should reach 160°F for maximum food-safety assurance.',
      'Serve immediately with fruit, maple syrup, or powdered sugar.'
    ], tags:['breakfast','french toast','vegetarian'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'breakfast-burritos', title:'Roasted Potato Breakfast Burritos', description:'Crisp potatoes, soft eggs, cheddar, avocado, and salsa wrapped in a toasted tortilla.', minutes:45, category:'breakfast', servings:4,
    ingredients:['1 pound Yukon Gold potatoes, diced 1/2 inch','8 large eggs','4 large flour tortillas','1 cup shredded cheddar cheese','1 avocado, sliced','1/2 cup salsa','1 tablespoon olive oil'],
    instructions:[
      'Heat the oven to 425°F. Toss potatoes with olive oil, salt, and pepper; roast 25 to 30 minutes, turning once after 15 minutes, until browned and tender.',
      'When potatoes are nearly done, whisk eggs with a pinch of salt. Cook in a buttered nonstick skillet over medium-low heat for 3 to 4 minutes, folding gently until soft curds form.',
      'Warm tortillas in a dry skillet over medium heat for 20 seconds per side.',
      'Divide potatoes, eggs, cheddar, avocado, and salsa among tortillas. Fold in the sides and roll tightly.',
      'Toast seam-side down in a dry skillet over medium heat for 1 to 2 minutes per side until lightly crisp.'
    ], tags:['breakfast','burrito','eggs','potato'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'shakshuka', title:'Tomato-Pepper Shakshuka', description:'Eggs gently poached in a deeply spiced tomato and sweet-pepper sauce.', minutes:40, category:'breakfast', servings:4,
    ingredients:['6 large eggs','1 28-ounce can crushed tomatoes','1 red bell pepper, sliced','1 yellow onion, sliced','3 garlic cloves, minced','1 teaspoon ground cumin','1 teaspoon smoked paprika','2 tablespoons olive oil','1/4 cup crumbled feta cheese'],
    instructions:[
      'Heat olive oil in a wide skillet over medium heat. Cook onion and pepper 8 to 10 minutes until soft and lightly caramelized.',
      'Add garlic, cumin, and paprika; cook 60 seconds. Add tomatoes and simmer over medium-low heat 12 to 15 minutes until thick enough to hold a spoon trail.',
      'Make six wells and crack an egg into each. Cover and cook over low heat 5 to 8 minutes until whites are set and yolks are cooked to your preference.',
      'For maximum food-safety assurance, eggs should reach 160°F. Scatter feta over the skillet and rest 2 minutes off heat.',
      'Serve directly from the pan with toasted bread.'
    ], tags:['breakfast','vegetarian','eggs','tomato','middle eastern-inspired'], allergens:['eggs','dairy']
  },
  {
    id:'avocado-poached-egg-toast', title:'Avocado Toast with Poached Eggs', description:'Creamy lemon avocado, crisp sourdough, and softly poached eggs with a flowing yolk.', minutes:20, category:'breakfast', servings:2,
    ingredients:['2 large eggs','2 slices sourdough bread','1 ripe avocado','1 teaspoon fresh lemon juice','1 teaspoon white vinegar'],
    instructions:[
      'Bring 3 inches of water to a bare simmer, about 180 to 190°F, in a small saucepan. Add vinegar; do not allow a rolling boil.',
      'Crack each egg into a small cup. Stir the water gently, slide in the eggs, and poach 3 1/2 to 4 1/2 minutes depending on desired yolk texture.',
      'Meanwhile toast the sourdough. Mash avocado with lemon juice and a pinch of salt, then spread over toast.',
      'Lift eggs with a slotted spoon and blot briefly on a towel. For maximum food-safety assurance, cook eggs to 160°F rather than serving a runny yolk.',
      'Set eggs on avocado toast and finish with black pepper.'
    ], tags:['breakfast','quick','avocado','eggs','vegetarian'], allergens:['eggs','gluten']
  },
  {
    id:'crispy-breakfast-potatoes', title:'Crispy Breakfast Potatoes', description:'Parboiled potatoes roasted hot for fluffy centers and shatteringly crisp edges.', minutes:50, category:'breakfast', servings:4,
    ingredients:['2 pounds Yukon Gold potatoes, cut into 1-inch pieces','1 small onion, diced','1 red bell pepper, diced','2 tablespoons olive oil','1 teaspoon smoked paprika'],
    instructions:[
      'Heat the oven to 450°F with a rimmed sheet pan inside. Bring a pot of salted water to a boil and parboil potatoes 6 to 8 minutes until the exterior is tender but centers are still firm.',
      'Drain very well and shake the potatoes in the pot for 15 seconds to roughen their surfaces.',
      'Toss potatoes, onion, pepper, olive oil, paprika, salt, and pepper. Carefully spread on the hot sheet pan in one layer.',
      'Roast 20 minutes without moving, then turn and roast 12 to 18 minutes more until deeply browned and crisp.',
      'Rest 2 minutes on the pan before serving so the crust sets.'
    ], tags:['breakfast','potato','vegan','vegetarian','roasted'], allergens:[]
  },
  {
    id:'spinach-mushroom-frittata', title:'Spinach-Mushroom Frittata', description:'A tender oven-finished egg custard with browned mushrooms, spinach, and Parmesan.', minutes:35, category:'breakfast', servings:6,
    ingredients:['8 large eggs','8 ounces cremini mushrooms, sliced','3 cups baby spinach','1/2 cup grated Parmesan cheese','1/4 cup whole milk','1 tablespoon olive oil','1 tablespoon unsalted butter'],
    instructions:[
      'Heat the oven to 375°F. Heat a 10-inch oven-safe skillet over medium-high heat, add olive oil, and brown mushrooms 5 to 6 minutes.',
      'Reduce to medium, add spinach, and cook 45 to 60 seconds until wilted. Add butter.',
      'Whisk eggs, milk, Parmesan, 1/2 teaspoon salt, and pepper. Pour into the skillet and cook undisturbed 2 minutes until the edges begin to set.',
      'Transfer to the oven and bake 8 to 12 minutes until the center is just set and reaches 160°F.',
      'Rest 5 minutes before slicing.'
    ], tags:['breakfast','frittata','eggs','vegetarian'], allergens:['eggs','dairy']
  },
  {
    id:'huevos-rancheros', title:'Huevos Rancheros', description:'Crisp-edged tortillas, smoky tomato-chile sauce, black beans, and fried eggs.', minutes:30, category:'breakfast', servings:4,
    ingredients:['8 corn tortillas','8 large eggs','1 15-ounce can black beans, drained','1 15-ounce can crushed tomatoes','1 jalapeño, minced','1/2 yellow onion, diced','1 teaspoon ground cumin','1 avocado','1 tablespoon olive oil'],
    instructions:[
      'Heat olive oil in a saucepan over medium heat. Cook onion and jalapeño 4 minutes; add cumin for 30 seconds, then tomatoes. Simmer 10 minutes until slightly thick.',
      'Warm black beans over low heat with 2 tablespoons water for 5 minutes.',
      'Toast tortillas in a dry skillet over medium-high heat for 20 to 30 seconds per side; keep warm under a towel.',
      'Fry eggs in a lightly oiled nonstick skillet over medium heat for 3 to 5 minutes, covered for the final minute if needed to set the whites. For maximum food-safety assurance, eggs should reach 160°F.',
      'Layer tortillas with beans, tomato sauce, eggs, and sliced avocado.'
    ], tags:['breakfast','mexican-inspired','eggs','beans','vegetarian'], allergens:['eggs']
  },
  {
    id:'sausage-egg-breakfast-sandwich', title:'Sausage, Egg & Cheddar Breakfast Sandwich', description:'A crisp sausage patty, folded egg, melted cheddar, and toasted English muffin.', minutes:25, category:'breakfast', servings:4,
    ingredients:['1 pound breakfast sausage','4 large eggs','4 English muffins','4 slices cheddar cheese','1 tablespoon unsalted butter'],
    instructions:[
      'Form sausage into four thin patties slightly wider than the muffins. Heat a skillet over medium heat and cook 4 to 5 minutes per side until browned and the center reaches 160°F for pork sausage.',
      'Split and toast English muffins.',
      'Melt butter in a nonstick skillet over medium-low heat. Add beaten eggs and cook 2 to 3 minutes, folding into four portions. Egg dishes should reach 160°F.',
      'Top each hot sausage patty with cheddar for 30 to 60 seconds until softened.',
      'Assemble sandwiches with egg, sausage, and cheese; serve immediately.'
    ], tags:['breakfast','sandwich','sausage','eggs'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'blueberry-lemon-yogurt-bowl', title:'Blueberry-Lemon Yogurt Bowl', description:'Cold Greek yogurt with macerated blueberries, lemon, toasted oats, and honey.', minutes:12, category:'breakfast', servings:2,
    ingredients:['2 cups Greek yogurt','1 cup blueberries','1 tablespoon honey','1 teaspoon fresh lemon juice','1/2 teaspoon lemon zest','1/2 cup rolled oats','1 tablespoon chopped almonds'],
    instructions:[
      'Heat a dry skillet over medium heat. Toast oats and almonds 3 to 4 minutes, stirring often, until fragrant; transfer to a plate to cool.',
      'Toss blueberries with honey, lemon juice, and zest. Rest 5 minutes so a little juice develops.',
      'Divide cold yogurt between bowls.',
      'Spoon berries and their juices over the yogurt, then add toasted oats and almonds just before serving for crunch.'
    ], tags:['breakfast','quick','yogurt','fruit','vegetarian'], allergens:['dairy','tree nuts']
  },
  {
    id:'savory-breakfast-quiche', title:'Spinach, Bacon & Gruyère Quiche', description:'A silky baked custard with crisp bacon, spinach, and nutty cheese in a flaky crust.', minutes:80, category:'breakfast', servings:8,
    ingredients:['1 9-inch pie crust','6 slices bacon, chopped','3 cups baby spinach','5 large eggs','1 1/2 cups half-and-half','1 cup shredded Gruyère cheese','1/4 teaspoon ground nutmeg'],
    instructions:[
      'Heat the oven to 375°F. Fit crust into a 9-inch pie plate, line with parchment and weights, and blind-bake 15 minutes. Remove weights and bake 5 minutes more.',
      'Meanwhile cook bacon in a skillet over medium heat 6 to 8 minutes until crisp. Drain all but 1 teaspoon fat; add spinach and cook 45 seconds until wilted.',
      'Whisk eggs, half-and-half, nutmeg, 1/2 teaspoon salt, and pepper. Scatter bacon, spinach, and Gruyère in the warm crust.',
      'Pour in custard and bake at 350°F for 35 to 45 minutes until edges are set, center has only a slight wobble, and internal temperature reaches 160°F.',
      'Cool at least 15 minutes before slicing.'
    ], tags:['breakfast','quiche','bacon','eggs','brunch'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'apple-cinnamon-overnight-oats', title:'Apple-Cinnamon Overnight Oats', description:'Creamy no-cook oats with grated apple, yogurt, cinnamon, and toasted walnuts.', minutes:8, category:'breakfast', servings:2,
    ingredients:['1 cup rolled oats','1 cup milk','1/2 cup Greek yogurt','1 apple, grated','1 tablespoon maple syrup','1/2 teaspoon ground cinnamon','1/4 cup chopped walnuts'],
    instructions:[
      'Stir oats, milk, yogurt, grated apple, maple syrup, cinnamon, and a pinch of salt in a covered container.',
      'Refrigerate at least 6 hours and up to overnight so the oats fully hydrate.',
      'Toast walnuts in a dry skillet over medium heat for 3 to 4 minutes until fragrant; cool completely.',
      'Stir the oats before serving and loosen with a splash of milk if desired. Top with walnuts at the last moment.'
    ], tags:['breakfast','overnight oats','vegetarian','make ahead'], allergens:['dairy','tree nuts']
  }
];
