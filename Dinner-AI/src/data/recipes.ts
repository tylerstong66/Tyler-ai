import { Recipe } from '@/src/types';
import { BREAKFAST_RECIPES } from '@/src/data/recipesBreakfast';
import { LUNCH_RECIPES } from '@/src/data/recipesLunch';
import { DINNER_RECIPES_A } from '@/src/data/recipesDinnerA';
import { DINNER_RECIPES_B } from '@/src/data/recipesDinnerB';
import { SNACK_DESSERT_RECIPES } from '@/src/data/recipesSnackDessert';

const CORE_RECIPES: Recipe[] = [
  {
    id: 'veggie-omelet',
    title: 'French-Style Garden Omelet',
    description: 'Soft, tender eggs folded around sautéed vegetables and sharp cheddar, finished with the fast pan technique used for classic French omelets.',
    minutes: 15,
    category: 'breakfast',
    servings: 1,
    ingredients: [
      '3 large eggs',
      '1/4 cup diced bell pepper',
      '2 tablespoons finely diced onion',
      '1/2 cup baby spinach',
      '1/4 cup shredded cheddar cheese',
      '1 teaspoon unsalted butter',
      '1 teaspoon olive oil'
    ],
    instructions: [
      'Heat an 8- to 10-inch nonstick skillet over medium-high heat for about 1 minute. Add the olive oil, bell pepper, and onion; cook 3 to 4 minutes, stirring often, until just tender. Add the spinach and cook 30 to 45 seconds until wilted. Transfer the vegetables to a plate.',
      'Whisk the eggs vigorously with a pinch of salt for 20 to 30 seconds, just until the whites and yolks are completely blended.',
      'Wipe the skillet clean, reduce to medium heat, and add the butter. When it foams but has not browned, pour in the eggs. Stir continuously with a silicone spatula for 20 to 30 seconds to form very small soft curds, then spread the eggs into an even layer.',
      'Cook 30 to 60 seconds more, until the bottom is set and the surface is still slightly glossy. Scatter the vegetables and cheddar over one half.',
      'Fold the omelet over the filling and cook 30 to 60 seconds, just until the cheese melts and the eggs are set. For maximum food-safety assurance, egg dishes should reach 160°F in the center. Slide onto a warm plate and serve immediately.'
    ],
    tags: ['breakfast', 'quick', 'vegetarian', 'eggs', 'chef technique'],
    allergens: ['eggs', 'dairy']
  },
  {
    id: 'banana-oatmeal',
    title: 'Caramelized Banana Cinnamon Oatmeal',
    description: 'Creamy rolled oats with banana, cinnamon, maple, and a small pinch of salt for a balanced, restaurant-style breakfast.',
    minutes: 12,
    category: 'breakfast',
    servings: 2,
    ingredients: [
      '1 cup old-fashioned rolled oats',
      '1 cup milk',
      '1 cup water',
      '1 large ripe banana, sliced',
      '1/2 teaspoon ground cinnamon',
      '1 tablespoon maple syrup',
      '1 teaspoon unsalted butter'
    ],
    instructions: [
      'Combine the milk, water, and a small pinch of salt in a saucepan. Bring to a gentle simmer over medium-high heat, 2 to 3 minutes; do not let the milk boil hard.',
      'Stir in the oats, reduce the heat to low, and maintain a gentle simmer for 5 minutes, stirring every 30 to 45 seconds so the oats cook evenly and turn creamy.',
      'Meanwhile, melt the butter in a small skillet over medium heat. Add half of the banana slices and cook 1 to 2 minutes per side until lightly caramelized.',
      'Stir the cinnamon, maple syrup, and remaining raw banana into the oats. Cook over low heat for 1 minute, then remove from the heat and rest 2 minutes to thicken.',
      'Divide between warm bowls and top with the caramelized banana. Add a splash of warm milk if you prefer a looser texture.'
    ],
    tags: ['breakfast', 'quick', 'vegetarian', 'oats'],
    allergens: ['dairy']
  },
  {
    id: 'chicken-salad-wrap',
    title: 'Lemon-Herb Chicken Salad Wrap',
    description: 'Juicy roasted chicken, crisp celery, greens, and a bright lemon-herb dressing rolled into a warm tortilla.',
    minutes: 35,
    category: 'lunch',
    servings: 4,
    ingredients: [
      '1 pound boneless skinless chicken breasts',
      '4 large flour tortillas',
      '2 cups shredded romaine lettuce',
      '1 cup diced tomato',
      '1/2 cup diced celery',
      '1/3 cup mayonnaise',
      '2 tablespoons plain Greek yogurt',
      '1 tablespoon fresh lemon juice',
      '1 tablespoon chopped fresh parsley',
      '1 teaspoon Dijon mustard',
      '1 tablespoon olive oil'
    ],
    instructions: [
      'Heat the oven to 425°F. Pat the chicken dry, rub with olive oil, and season with salt and pepper. Roast on a sheet pan for 18 to 22 minutes, or until the thickest part reaches 165°F.',
      'Rest the chicken for 5 minutes before cutting it into 1/2-inch pieces. Resting keeps the juices in the meat instead of in the dressing.',
      'Whisk mayonnaise, Greek yogurt, lemon juice, parsley, Dijon, and a few grinds of black pepper in a bowl. Fold in the warm chicken and celery and let the mixture stand 3 minutes so the chicken absorbs the dressing.',
      'Warm the tortillas in a dry skillet over medium heat for 15 to 20 seconds per side, just until flexible.',
      'Layer each tortilla with romaine, tomato, and chicken salad. Fold in the sides, roll tightly, and serve while the tortilla is still warm.'
    ],
    tags: ['lunch', 'chicken', 'wrap', 'fresh'],
    allergens: ['gluten', 'eggs', 'dairy'],
    safetyNotes: 'Cook chicken to 165°F in the thickest part and avoid using utensils that touched raw chicken on the finished wrap.'
  },
  {
    id: 'chicken-soup',
    title: 'Deep-Flavored Chicken Noodle Soup',
    description: 'A clear, savory broth built from bone-in chicken and aromatics, finished with fresh vegetables, herbs, and just-tender noodles.',
    minutes: 95,
    category: 'lunch',
    servings: 6,
    ingredients: [
      '2 pounds bone-in chicken thighs',
      '8 cups low-sodium chicken broth',
      '3 carrots',
      '3 celery stalks',
      '1 large yellow onion',
      '2 garlic cloves',
      '2 sprigs fresh thyme',
      '1 bay leaf',
      '6 ounces wide egg noodles',
      '2 tablespoons chopped fresh parsley',
      '1 tablespoon fresh lemon juice'
    ],
    instructions: [
      'Combine the chicken, broth, half of the carrots, half of the celery, half of the onion, garlic, thyme, and bay leaf in a stockpot. Bring just to a boil over medium-high heat, then immediately reduce to low so the broth holds a gentle simmer.',
      'Simmer partially covered for 40 to 50 minutes. Skim foam from the surface as needed. The chicken is ready when the thickest part reaches at least 165°F.',
      'Transfer the chicken to a plate. Strain the broth through a fine-mesh sieve, discard the spent aromatics, and return the clear broth to the pot.',
      'Dice the remaining carrots, celery, and onion. Bring the broth back to a gentle simmer over medium heat, add the fresh vegetables, and cook 12 to 15 minutes until just tender.',
      'Add the egg noodles and simmer according to package timing, usually 5 to 8 minutes, stopping when they are just al dente.',
      'Remove the skin and bones from the rested chicken and shred the meat. Return it to the soup for 2 to 3 minutes, just long enough to heat through. Remove from the heat, stir in parsley and lemon juice, then season to taste.'
    ],
    tags: ['lunch', 'soup', 'chicken', 'comfort food', 'slow simmer'],
    allergens: ['gluten', 'eggs'],
    safetyNotes: 'Cook poultry to at least 165°F. Cool leftovers promptly and reheat to 165°F.'
  },
  {
    id: 'chicken-tacos',
    title: 'Skillet Lime Chicken Tacos',
    description: 'Lime-cumin chicken seared hard in a hot skillet, rested before slicing, and finished with crisp vegetables and warm tortillas.',
    minutes: 30,
    category: 'dinner',
    servings: 4,
    ingredients: [
      '1 1/4 pounds boneless skinless chicken breasts',
      '8 small corn tortillas',
      '1 lime',
      '2 garlic cloves, minced',
      '1 teaspoon ground cumin',
      '1 teaspoon smoked paprika',
      '1/2 teaspoon dried oregano',
      '1 tablespoon olive oil',
      '1/2 cup diced white onion',
      '1 cup shredded lettuce',
      '1 cup diced tomato',
      '1/4 cup chopped cilantro'
    ],
    instructions: [
      'Slice the chicken horizontally into thinner cutlets. Toss with the juice of half the lime, garlic, cumin, paprika, oregano, olive oil, and a pinch of salt. Marinate in the refrigerator for 15 minutes.',
      'Heat a heavy skillet over medium-high heat for 2 minutes. Add the chicken in a single layer and cook without moving for 3 to 4 minutes, until well browned.',
      'Flip and cook another 3 to 5 minutes, depending on thickness, until the center reaches 165°F. Transfer to a board and rest 5 minutes before slicing across the grain.',
      'Lower the skillet to medium and warm the tortillas 20 to 30 seconds per side, stacking them under a clean towel to stay soft.',
      'Fill each tortilla with sliced chicken, onion, lettuce, tomato, and cilantro. Finish with the remaining lime juice just before serving.'
    ],
    tags: ['dinner', 'mexican-inspired', 'chicken', 'quick', 'tacos'],
    allergens: [],
    safetyNotes: 'Cook chicken to 165°F in the thickest portion before resting and slicing.'
  },
  {
    id: 'garlic-pasta',
    title: 'Silky Garlic Parmesan Pasta',
    description: 'A glossy, emulsified garlic-Parmesan sauce built with butter and starchy pasta water instead of heavy cream.',
    minutes: 22,
    category: 'dinner',
    servings: 4,
    ingredients: [
      '12 ounces spaghetti or linguine',
      '4 tablespoons unsalted butter',
      '4 garlic cloves, finely grated',
      '1 cup finely grated Parmesan cheese',
      '1 teaspoon freshly cracked black pepper',
      '1 tablespoon chopped fresh parsley',
      '1 teaspoon fresh lemon juice'
    ],
    instructions: [
      'Bring a large pot of water to a rolling boil over high heat. Salt it lightly, add the pasta, and cook 1 to 2 minutes less than the package al-dente time. Reserve 1 1/2 cups pasta water before draining.',
      'While the pasta cooks, melt 2 tablespoons butter in a large skillet over medium-low heat. Add the garlic and cook 45 to 60 seconds, stirring constantly, until fragrant but not browned.',
      'Add 3/4 cup reserved pasta water and the remaining butter. Increase to medium heat and bring to a gentle simmer for about 30 seconds.',
      'Add the undercooked pasta and black pepper. Toss vigorously over medium heat for 1 to 2 minutes until the pasta finishes cooking and the liquid turns slightly glossy.',
      'Remove the skillet from the heat. Add Parmesan a handful at a time while tossing continuously for 1 to 2 minutes. Add more pasta water a tablespoon at a time until the sauce is smooth and clings to every strand.',
      'Finish with parsley and lemon juice. Serve immediately on warm plates; reheating this sauce aggressively can cause the cheese to separate.'
    ],
    tags: ['dinner', 'italian-inspired', 'pasta', 'quick', 'vegetarian', 'chef technique'],
    allergens: ['gluten', 'dairy']
  },
  {
    id: 'beef-stir-fry',
    title: 'High-Heat Beef & Broccoli',
    description: 'Thin flank steak, crisp broccoli, ginger, and garlic cooked quickly over high heat with a glossy savory sauce.',
    minutes: 35,
    category: 'dinner',
    servings: 4,
    ingredients: [
      '1 pound flank steak, sliced thinly against the grain',
      '1 pound broccoli florets',
      '3 tablespoons low-sodium soy sauce',
      '1 tablespoon oyster sauce',
      '1 tablespoon cornstarch',
      '1 teaspoon brown sugar',
      '1 teaspoon toasted sesame oil',
      '1 tablespoon grated fresh ginger',
      '2 garlic cloves, grated',
      '2 tablespoons neutral cooking oil',
      '3 cups cooked rice'
    ],
    instructions: [
      'Bring a saucepan of water to a boil over high heat. Blanch the broccoli for 2 to 3 minutes until bright green and barely tender, then drain immediately.',
      'Whisk soy sauce, oyster sauce, cornstarch, brown sugar, sesame oil, and 1/3 cup water. Toss the sliced beef with 2 tablespoons of this sauce and let it stand 10 minutes while the pan heats.',
      'Heat a wok or heavy skillet over high heat for 2 to 3 minutes, until very hot. Add 1 tablespoon oil and half the beef in a single layer. Sear 60 to 90 seconds without moving, then toss for another 30 to 60 seconds. Transfer to a plate and repeat with the remaining oil and beef.',
      'Keep the pan over high heat. Add ginger and garlic and stir-fry for 20 to 30 seconds. Add broccoli and toss for 1 minute.',
      'Whisk the remaining sauce again, pour it into the pan, and boil for 60 to 90 seconds until glossy. Return the beef and any juices; toss 30 to 60 seconds just to coat and finish cooking.',
      'Serve immediately over hot rice. For food-safety assurance, intact beef should reach 145°F followed by a 3-minute rest.'
    ],
    tags: ['dinner', 'asian-inspired', 'beef', 'quick', 'stir-fry'],
    allergens: ['soy', 'shellfish']
  },
  {
    id: 'sheet-pan-chicken',
    title: 'Crisp-Roasted Chicken Thighs & Vegetables',
    description: 'Golden chicken thighs with potatoes, carrots, onion, garlic, and pan juices roasted at high heat for crisp edges and tender meat.',
    minutes: 55,
    category: 'dinner',
    servings: 4,
    ingredients: [
      '2 pounds bone-in skin-on chicken thighs',
      '1 pound baby potatoes, halved',
      '3 carrots, cut into 1-inch pieces',
      '1 yellow onion, cut into wedges',
      '6 garlic cloves',
      '2 tablespoons olive oil',
      '1 teaspoon dried thyme',
      '1 lemon'
    ],
    instructions: [
      'Heat the oven to 425°F with a rack in the upper-middle position. Put a rimmed sheet pan in the oven for 5 minutes so the vegetables begin roasting on contact.',
      'Toss potatoes and carrots with 1 tablespoon olive oil, thyme, salt, and pepper. Carefully spread them over the hot pan and roast for 15 minutes.',
      'Pat the chicken very dry. Rub with the remaining olive oil and season well. Remove the pan, add the onion and garlic, turn the vegetables, and nestle the chicken thighs skin-side up among them.',
      'Roast at 425°F for 25 to 30 minutes more, until the skin is deeply golden, the vegetables are tender, and the chicken reaches at least 165°F. For especially tender thighs, 175 to 185°F is an excellent texture target.',
      'Rest the chicken on the pan for 5 minutes. Squeeze lemon over everything and toss the vegetables through the rendered chicken juices before serving.'
    ],
    tags: ['dinner', 'chicken', 'roasted', 'sheet pan'],
    allergens: [],
    safetyNotes: 'Chicken must reach at least 165°F in the thickest part without touching bone.'
  },
  {
    id: 'turkey-chili',
    title: 'Slow-Simmered Turkey Chili',
    description: 'Ground turkey, beans, tomatoes, and toasted spices simmered until thick, savory, and deeply integrated.',
    minutes: 65,
    category: 'dinner',
    servings: 6,
    ingredients: [
      '1 1/2 pounds ground turkey',
      '1 large yellow onion, diced',
      '1 red bell pepper, diced',
      '3 garlic cloves, minced',
      '2 tablespoons tomato paste',
      '2 tablespoons chili powder',
      '2 teaspoons ground cumin',
      '1 teaspoon smoked paprika',
      '1 28-ounce can crushed tomatoes',
      '1 15-ounce can kidney beans, drained',
      '1 15-ounce can black beans, drained',
      '2 cups low-sodium chicken broth',
      '1 tablespoon olive oil'
    ],
    instructions: [
      'Heat a Dutch oven over medium heat for 1 minute. Add olive oil, onion, and bell pepper; cook 5 to 6 minutes until softened and beginning to color.',
      'Add garlic, chili powder, cumin, and smoked paprika. Cook for 60 seconds, stirring constantly, to bloom the spices without burning them.',
      'Add tomato paste and cook over medium heat for 1 to 2 minutes until it darkens slightly.',
      'Increase to medium-high heat, add the turkey, and cook 6 to 8 minutes, breaking it into small pieces, until no pink remains and the meat reaches 165°F.',
      'Add crushed tomatoes, broth, kidney beans, and black beans. Bring to a boil over medium-high heat, then immediately reduce to low.',
      'Simmer uncovered for 30 to 40 minutes, stirring every 8 to 10 minutes, until thick enough to coat a spoon. Rest off heat 5 minutes before tasting and adjusting seasoning.'
    ],
    tags: ['dinner', 'comfort food', 'turkey', 'one-pot', 'chili'],
    allergens: [],
    safetyNotes: 'Ground poultry should reach 165°F.'
  },
  {
    id: 'baked-ziti',
    title: 'Three-Cheese Baked Ziti',
    description: 'Tender-but-structured pasta layered with marinara, ricotta, mozzarella, and Parmesan, baked until bubbling and browned.',
    minutes: 70,
    category: 'dinner',
    servings: 8,
    ingredients: [
      '1 pound ziti',
      '5 cups marinara sauce',
      '15 ounces whole-milk ricotta cheese',
      '12 ounces mozzarella cheese, shredded',
      '1 cup finely grated Parmesan cheese',
      '1 large egg',
      '2 tablespoons chopped fresh parsley',
      '1 garlic clove, finely grated'
    ],
    instructions: [
      'Heat the oven to 375°F. Bring a large pot of salted water to a rolling boil and cook the ziti 2 minutes less than the package al-dente time. Drain well; do not overcook because the pasta will continue cooking in the oven.',
      'Mix ricotta, half the mozzarella, half the Parmesan, the egg, parsley, garlic, a pinch of salt, and black pepper in a bowl.',
      'Spread 1 cup marinara in a 9-by-13-inch baking dish. Toss the hot pasta with 2 cups sauce, then fold in the ricotta mixture only a few times so distinct pockets of cheese remain.',
      'Transfer half the pasta to the dish, spoon over 1 cup sauce, then add the remaining pasta. Top with the last cup of sauce, remaining mozzarella, and remaining Parmesan.',
      'Cover loosely with foil and bake at 375°F for 20 minutes. Uncover and bake 10 to 15 minutes more, until vigorously bubbling at the edges, browned in spots, and the center reaches 165°F.',
      'Rest for 10 minutes before serving so the cheese sets enough to scoop cleanly.'
    ],
    tags: ['dinner', 'italian-american', 'pasta', 'comfort food', 'vegetarian'],
    allergens: ['gluten', 'dairy', 'eggs']
  },
  {
    id: 'salmon-rice-bowl',
    title: 'Soy-Lime Salmon Rice Bowl',
    description: 'Roasted salmon with glossy soy-lime glaze, steamed jasmine rice, cucumber, carrot, scallion, and a bright finish.',
    minutes: 40,
    category: 'dinner',
    servings: 4,
    ingredients: [
      '4 6-ounce salmon fillets',
      '1 1/2 cups jasmine rice',
      '1 cucumber, thinly sliced',
      '2 carrots, cut into matchsticks',
      '3 scallions, thinly sliced',
      '3 tablespoons low-sodium soy sauce',
      '1 tablespoon honey',
      '1 tablespoon fresh lime juice',
      '1 teaspoon grated fresh ginger',
      '1 teaspoon toasted sesame oil'
    ],
    instructions: [
      'Rinse the rice until the water runs mostly clear. Combine rice with 2 1/4 cups water in a saucepan, bring to a boil over medium-high heat, then cover and reduce to low. Cook 15 minutes, remove from heat, and rest covered 10 minutes.',
      'While the rice cooks, heat the oven to 425°F. Whisk soy sauce, honey, lime juice, ginger, and sesame oil.',
      'Pat salmon dry, place on a foil-lined sheet pan, and brush with half the glaze. Roast at 425°F for 8 to 12 minutes depending on thickness, brushing once more halfway through.',
      'Check the thickest part with an instant-read thermometer; for USDA food-safety guidance, fish should reach 145°F. Remove promptly so it stays moist.',
      'Fluff the rested rice. Divide among bowls and add cucumber, carrot, and scallions. Top with salmon and spoon over any clean reserved glaze that did not touch raw fish.'
    ],
    tags: ['dinner', 'seafood', 'rice bowl', 'salmon', 'quick'],
    allergens: ['fish', 'soy'],
    safetyNotes: 'Cook fish to 145°F for USDA food-safety guidance. Never reuse glaze that contacted raw fish unless it is boiled.'
  },
  {
    id: 'pot-roast',
    title: 'Red-Wine Style Classic Pot Roast',
    description: 'Chuck roast deeply browned, then slowly braised with aromatic vegetables until spoon-tender in a glossy, concentrated sauce.',
    minutes: 225,
    category: 'dinner',
    servings: 8,
    ingredients: [
      '4 pounds boneless beef chuck roast',
      '1 pound baby potatoes',
      '4 carrots, cut into large pieces',
      '2 yellow onions, cut into wedges',
      '4 garlic cloves',
      '2 tablespoons tomato paste',
      '2 cups beef broth',
      '1 cup dry red wine',
      '2 tablespoons Worcestershire sauce',
      '2 sprigs fresh thyme',
      '1 sprig fresh rosemary',
      '2 tablespoons olive oil'
    ],
    instructions: [
      'Heat the oven to 325°F. Pat the roast completely dry and season generously. Heat a Dutch oven over medium-high heat for 2 minutes, add olive oil, and sear the roast 4 to 5 minutes per broad side plus 1 to 2 minutes on the edges. Transfer to a plate.',
      'Reduce to medium heat. Add onions and carrots and cook 8 to 10 minutes, stirring occasionally, until lightly browned. Add garlic and tomato paste and cook 1 to 2 minutes.',
      'Add red wine, increase to medium-high, and simmer 3 to 4 minutes while scraping the browned bits from the bottom. Add broth, Worcestershire, thyme, and rosemary.',
      'Return the roast to the pot. The liquid should come roughly halfway up the meat. Cover tightly and braise at 325°F for 2 1/2 hours.',
      'Add the potatoes around the roast, cover again, and continue braising 45 to 60 minutes, until the meat yields easily to a fork. Although beef roasts are food-safe at 145°F with a 3-minute rest, chuck becomes properly braise-tender only after prolonged cooking.',
      'Transfer meat and vegetables to a platter and rest 15 minutes. Skim excess fat from the braising liquid and simmer it uncovered over medium-high heat for 5 to 10 minutes until lightly reduced. Spoon over the sliced or pulled roast.'
    ],
    tags: ['dinner', 'beef', 'comfort food', 'braised', 'slow cooked'],
    allergens: []
  },
  {
    id: 'pulled-pork',
    title: 'Low-and-Slow Pulled Pork',
    description: 'Pork shoulder seasoned overnight if time allows, slowly roasted until collagen melts, then shredded into its own reduced juices.',
    minutes: 390,
    category: 'dinner',
    servings: 10,
    ingredients: [
      '5 pounds boneless pork shoulder',
      '1 yellow onion, sliced',
      '2 tablespoons smoked paprika',
      '2 tablespoons brown sugar',
      '1 tablespoon garlic powder',
      '2 teaspoons ground cumin',
      '1 cup apple cider',
      '1/2 cup barbecue sauce'
    ],
    instructions: [
      'Mix paprika, brown sugar, garlic powder, cumin, salt, and black pepper. Rub the pork all over. For deeper seasoning, refrigerate uncovered or loosely covered for 8 to 24 hours; otherwise let it stand 30 minutes while the oven heats.',
      'Heat the oven to 300°F. Place sliced onion in a Dutch oven or deep roasting pan and set the pork on top. Pour the apple cider around, not over, the meat.',
      'Cover tightly and roast at 300°F for 4 hours. Uncover, baste with the juices, and continue roasting 1 to 2 hours more until deeply browned and very tender.',
      'Begin checking around the 5-hour mark. Pork is safe at 145°F with a 3-minute rest, but pulled pork needs much more collagen breakdown; a practical shredding target is about 195 to 203°F and the meat should offer almost no resistance to a fork.',
      'Transfer the pork to a board and rest 20 minutes. Meanwhile, skim excess fat from the pan juices and simmer them over medium-high heat for 5 to 8 minutes until concentrated.',
      'Shred the pork, discarding large pieces of fat, and toss with enough reduced juices and barbecue sauce to moisten without drowning the meat.'
    ],
    tags: ['dinner', 'pork', 'slow cooked', 'barbecue'],
    allergens: [],
    safetyNotes: 'Pork roasts are safe at 145°F with a 3-minute rest, but shoulder should cook far beyond that for proper pulled texture.'
  },
  {
    id: 'lentil-curry',
    title: 'Coconut Red Lentil Curry',
    description: 'Red lentils simmered with toasted curry spices, tomato, coconut milk, garlic, ginger, and lime until creamy but not heavy.',
    minutes: 45,
    category: 'dinner',
    servings: 6,
    ingredients: [
      '1 1/2 cups red lentils, rinsed',
      '1 13.5-ounce can coconut milk',
      '1 14-ounce can diced tomatoes',
      '1 large yellow onion, diced',
      '3 garlic cloves, minced',
      '1 tablespoon grated fresh ginger',
      '2 tablespoons curry powder',
      '1 teaspoon ground cumin',
      '3 cups vegetable broth',
      '1 lime',
      '2 tablespoons olive oil',
      '3 cups cooked basmati rice'
    ],
    instructions: [
      'Heat olive oil in a wide pot over medium heat. Add onion and cook 5 to 6 minutes until soft and lightly golden.',
      'Add garlic, ginger, curry powder, and cumin. Cook for 60 to 90 seconds, stirring constantly, until very fragrant; do not let the garlic or spices scorch.',
      'Add tomatoes and cook over medium heat for 3 minutes, stirring, until some of their liquid evaporates and the mixture looks slightly jammy.',
      'Stir in lentils, coconut milk, and broth. Increase to medium-high and bring just to a boil, then reduce to low.',
      'Simmer uncovered for 20 to 25 minutes, stirring every few minutes, until the lentils are tender and the curry is creamy. Add a splash of water if it becomes too thick before the lentils soften.',
      'Remove from the heat and rest 5 minutes. Stir in fresh lime juice and adjust seasoning. Serve over hot basmati rice.'
    ],
    tags: ['dinner', 'vegetarian', 'vegan', 'curry', 'lentils'],
    allergens: []
  },
  {
    id: 'cucumber-hummus-bites',
    title: 'Cucumber Hummus Bites',
    description: 'Chilled cucumber rounds with creamy hummus, smoked paprika, lemon, and fresh herbs for a crisp five-minute snack.',
    minutes: 8,
    category: 'snack',
    servings: 4,
    ingredients: [
      '1 English cucumber',
      '3/4 cup hummus',
      '1/2 teaspoon smoked paprika',
      '1 teaspoon fresh lemon juice',
      '1 tablespoon chopped fresh parsley'
    ],
    instructions: [
      'Chill the cucumber until cold, then slice into 1/2-inch rounds. Pat the cut surfaces dry so the hummus does not slide.',
      'Stir the hummus with lemon juice until smooth. Spoon or pipe about 1 teaspoon onto each cucumber round.',
      'Dust lightly with smoked paprika and parsley. Serve immediately, or refrigerate up to 30 minutes before serving so the cucumber stays crisp.'
    ],
    tags: ['snack', 'quick', 'vegetarian', 'no-cook'],
    allergens: ['sesame']
  },
  {
    id: 'apple-yogurt-crunch',
    title: 'Warm Cinnamon Apple Yogurt Crunch',
    description: 'Warm sautéed cinnamon apples over cold yogurt with crisp granola for contrast in temperature and texture.',
    minutes: 12,
    category: 'snack',
    servings: 2,
    ingredients: [
      '1 crisp apple, diced',
      '1 cup Greek yogurt',
      '1/2 cup granola',
      '1/2 teaspoon ground cinnamon',
      '1 teaspoon maple syrup',
      '1 teaspoon unsalted butter'
    ],
    instructions: [
      'Heat a small skillet over medium heat for 1 minute. Add butter and the diced apple; cook 3 to 4 minutes, stirring occasionally, until the edges begin to brown but the pieces still hold their shape.',
      'Add cinnamon and maple syrup and cook 30 to 60 seconds more, tossing constantly, until the apple is glossy. Remove from the heat and cool for 2 minutes.',
      'Divide cold yogurt between bowls. Spoon the warm apples over the yogurt and finish with granola immediately so it stays crisp.'
    ],
    tags: ['snack', 'quick', 'vegetarian', 'fruit'],
    allergens: ['dairy', 'gluten']
  },
  {
    id: 'chocolate-mug-cake',
    title: 'Fudgy Chocolate Mug Cake',
    description: 'A moist single-serving chocolate cake with a soft center, designed for a short microwave cook instead of a dry, rubbery finish.',
    minutes: 7,
    category: 'dessert',
    servings: 1,
    ingredients: [
      '1/4 cup all-purpose flour',
      '2 tablespoons unsweetened cocoa powder',
      '2 tablespoons sugar',
      '1/4 teaspoon baking powder',
      '1/4 cup milk',
      '2 tablespoons neutral oil',
      '1/4 teaspoon vanilla extract',
      '2 tablespoons chocolate chips'
    ],
    instructions: [
      'In a 12- to 14-ounce microwave-safe mug, whisk flour, cocoa, sugar, baking powder, and a small pinch of salt until evenly blended.',
      'Add milk, oil, and vanilla. Stir just until no dry pockets remain, then fold in the chocolate chips. Do not overmix.',
      'Microwave uncovered on HIGH for 70 seconds in a roughly 1000-watt microwave. Check the center; if visibly wet, continue in 10-second bursts, usually no more than 90 seconds total.',
      'The top should look set while the center remains soft. Rest 2 to 3 minutes before eating; the cake continues cooking from residual heat during the rest.'
    ],
    tags: ['dessert', 'quick', 'chocolate', 'vegetarian'],
    allergens: ['gluten', 'dairy']
  },
  {
    id: 'cinnamon-baked-apples',
    title: 'Cinnamon-Oat Baked Apples',
    description: 'Tender baked apples with a buttery cinnamon-oat center, basted once so the fruit stays glossy and moist.',
    minutes: 45,
    category: 'dessert',
    servings: 4,
    ingredients: [
      '4 firm baking apples',
      '1/2 cup rolled oats',
      '2 tablespoons brown sugar',
      '1 teaspoon ground cinnamon',
      '2 tablespoons unsalted butter, softened',
      '1/2 cup apple cider or apple juice',
      '1 teaspoon fresh lemon juice'
    ],
    instructions: [
      'Heat the oven to 400°F. Core the apples from the top, leaving the bottom intact so each apple forms a cup. Peel a narrow strip around the upper third of each apple and brush exposed flesh with lemon juice.',
      'Mix oats, brown sugar, cinnamon, butter, and a small pinch of salt. Pack the filling loosely into the apples.',
      'Stand the apples in a snug baking dish and pour the cider around them. Bake at 400°F for 15 minutes.',
      'Spoon the hot cider from the dish over the apples, then continue baking 13 to 20 minutes, until a thin knife slides into the flesh with little resistance but the apples still hold their shape.',
      'Rest 5 minutes before serving. Spoon the reduced cinnamon-cider juices over the top.'
    ],
    tags: ['dessert', 'fruit', 'vegetarian', 'baked'],
    allergens: ['dairy']
  },
  {
    id: 'berry-yogurt-parfait',
    title: 'Honey-Lemon Berry Yogurt Parfait',
    description: 'Cold creamy yogurt layered with lightly macerated berries and crisp granola, assembled at the last minute for maximum texture.',
    minutes: 15,
    category: 'dessert',
    servings: 4,
    ingredients: [
      '3 cups Greek yogurt',
      '2 cups mixed fresh berries',
      '1 cup granola',
      '2 tablespoons honey',
      '1 teaspoon fresh lemon juice',
      '1/2 teaspoon finely grated lemon zest'
    ],
    instructions: [
      'Toss the berries gently with honey, lemon juice, and lemon zest. Let stand at cool room temperature for 10 minutes so the berries release a little juice without becoming mushy.',
      'Keep the yogurt chilled until assembly. Spoon a layer of yogurt into each glass, followed by berries and a small spoonful of their juices.',
      'Repeat the yogurt and berry layers. Add granola only at the very end and serve immediately so it remains crisp.'
    ],
    tags: ['dessert', 'quick', 'fruit', 'vegetarian', 'no-cook'],
    allergens: ['dairy', 'gluten']
  }
];


export const RECIPES: Recipe[] = [
  ...CORE_RECIPES,
  ...BREAKFAST_RECIPES,
  ...LUNCH_RECIPES,
  ...DINNER_RECIPES_A,
  ...DINNER_RECIPES_B,
  ...SNACK_DESSERT_RECIPES
];
