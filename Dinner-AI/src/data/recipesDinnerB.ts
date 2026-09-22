import { Recipe } from '@/src/types';

export const DINNER_RECIPES_B: Recipe[] = [
  {
    id:'mustard-herb-pork-tenderloin', title:'Mustard-Herb Pork Tenderloin', description:'Roasted pork tenderloin with Dijon, rosemary, garlic, and a glossy pan reduction.', minutes:45, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds pork tenderloin','2 tablespoons Dijon mustard','2 garlic cloves, grated','1 tablespoon chopped rosemary','1 tablespoon olive oil','1 cup chicken broth','1 tablespoon unsalted butter'],
    instructions:[
      'Heat the oven to 425°F. Pat pork dry and remove any silver skin. Rub with Dijon, garlic, rosemary, olive oil, salt, and pepper.',
      'Heat an oven-safe skillet over medium-high heat for 2 minutes. Sear pork 2 minutes per side until browned all around.',
      'Transfer skillet to the oven and roast 12 to 18 minutes, until the thickest part reaches at least 145°F.',
      'Move pork to a board and rest at least 5 minutes. Put the skillet over medium heat, add broth, and simmer 3 to 5 minutes while scraping the fond.',
      'Remove from heat, whisk in butter, slice pork across the grain, and spoon sauce over the slices.'
    ], tags:['dinner','pork','roast','pan sauce'], allergens:['dairy'], safetyNotes:'Pork tenderloin should reach at least 145°F and rest at least 3 minutes.'
  },
  {
    id:'oven-carnitas', title:'Crisp Oven Carnitas', description:'Pork shoulder braised until tender, then broiled hard for caramelized crispy edges.', minutes:240, category:'dinner', servings:8,
    ingredients:['4 pounds pork shoulder, cut into large chunks','1 orange, juiced','1 lime, juiced','1 yellow onion, quartered','5 garlic cloves','2 teaspoons ground cumin','2 teaspoons dried oregano','1 cup chicken broth'],
    instructions:[
      'Heat the oven to 325°F. Season pork with cumin, oregano, salt, and pepper and place in a Dutch oven with onion and garlic.',
      'Add orange juice, lime juice, and broth. Bring to a simmer on the stovetop, cover tightly, and transfer to the oven.',
      'Braise 2 1/2 to 3 hours, turning once, until the pork is very tender and easily pulls apart.',
      'Transfer pork to a sheet pan and shred. Skim excess fat from the braising liquid, then spoon about 1/2 cup over the meat.',
      'Broil on high 4 to 7 minutes, tossing once halfway through, until edges are deeply browned and crisp. Serve immediately.'
    ], tags:['dinner','pork','mexican-inspired','slow cooked','carnitas'], allergens:[]
  },
  {
    id:'shrimp-scampi', title:'Lemon-Garlic Shrimp Scampi', description:'Quick-seared shrimp in a glossy garlic, lemon, butter, and white-wine style sauce.', minutes:25, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds large shrimp, peeled and deveined','4 garlic cloves, thinly sliced','4 tablespoons unsalted butter','2 tablespoons olive oil','1/2 cup dry white wine or seafood broth','2 tablespoons fresh lemon juice','1/4 teaspoon red pepper flakes','2 tablespoons chopped parsley'],
    instructions:[
      'Pat shrimp very dry and season lightly. Heat olive oil in a wide skillet over medium-high heat.',
      'Add shrimp in one layer and cook 60 to 90 seconds per side until opaque and 145°F. Transfer immediately to a plate.',
      'Reduce heat to medium. Add 2 tablespoons butter, garlic, and pepper flakes; cook 30 to 45 seconds until fragrant.',
      'Add wine or broth and simmer 2 to 3 minutes until reduced by about half. Remove from heat and whisk in remaining butter and lemon juice.',
      'Return shrimp and juices for 30 seconds, then finish with parsley.'
    ], tags:['dinner','seafood','shrimp','quick','scampi'], allergens:['shellfish','dairy'], safetyNotes:'Shrimp and other seafood should reach 145°F.'
  },
  {
    id:'garlic-butter-shrimp-rice', title:'Garlic Butter Shrimp Rice Bowls', description:'Seared shrimp with garlic butter, lemon, scallion, and fluffy rice.', minutes:30, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds large shrimp, peeled and deveined','3 cups cooked jasmine rice','3 tablespoons unsalted butter','3 garlic cloves, minced','1 lemon','3 scallions, sliced','1 tablespoon olive oil'],
    instructions:[
      'Reheat rice until steaming hot and keep covered.',
      'Pat shrimp dry. Heat olive oil in a skillet over medium-high heat and cook shrimp 60 to 90 seconds per side until 145°F; transfer out.',
      'Reduce heat to medium-low, add butter and garlic, and cook 30 seconds until fragrant but not browned.',
      'Return shrimp and toss 30 seconds with lemon zest and half the lemon juice.',
      'Divide rice among bowls and top with shrimp, scallions, and remaining lemon juice.'
    ], tags:['dinner','shrimp','rice','quick'], allergens:['shellfish','dairy'], safetyNotes:'Seafood should reach 145°F.'
  },
  {
    id:'seared-scallops-lemon-butter', title:'Seared Scallops with Lemon Butter', description:'Dry-packed scallops with a deep golden crust and a bright butter pan sauce.', minutes:20, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds dry sea scallops','1 tablespoon neutral oil','3 tablespoons unsalted butter','1 tablespoon fresh lemon juice','1 tablespoon chopped chives'],
    instructions:[
      'Remove the side muscle from scallops and pat them extremely dry. Season just before cooking.',
      'Heat a heavy skillet over high heat for 2 to 3 minutes. Add oil and place scallops flat-side down with space between them.',
      'Sear without moving 90 seconds to 2 minutes until a dark crust forms. Flip and cook 60 to 90 seconds more, until the center reaches 145°F.',
      'Transfer scallops immediately. Reduce heat to medium-low, add butter, and swirl 30 seconds until foamy.',
      'Remove from heat, add lemon juice and chives, and spoon sauce around the scallops.'
    ], tags:['dinner','seafood','scallops','quick','chef technique'], allergens:['shellfish','dairy'], safetyNotes:'Seafood should reach 145°F.'
  },
  {
    id:'crispy-fish-tacos', title:'Crispy Fish Tacos with Lime Slaw', description:'Spiced white fish, crisp cabbage, crema, and lime in warm corn tortillas.', minutes:35, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds cod or mahi mahi','8 corn tortillas','3 cups shredded cabbage','1/3 cup sour cream','2 tablespoons fresh lime juice','1 teaspoon chili powder','1/2 teaspoon ground cumin','2 tablespoons neutral oil','1/4 cup chopped cilantro'],
    instructions:[
      'Toss cabbage with half the lime juice, a pinch of salt, and half the cilantro. Mix sour cream with remaining lime juice and 1 tablespoon water.',
      'Cut fish into thick strips and season with chili powder, cumin, salt, and pepper.',
      'Heat oil in a nonstick or cast-iron skillet over medium-high heat. Cook fish 2 to 4 minutes per side, depending on thickness, until browned and 145°F in the center.',
      'Warm tortillas in a dry skillet for 20 to 30 seconds per side.',
      'Fill tortillas with fish, slaw, lime crema, and remaining cilantro.'
    ], tags:['dinner','fish','tacos','seafood','quick'], allergens:['fish','dairy'], safetyNotes:'Fish should reach 145°F.'
  },
  {
    id:'cod-piccata', title:'Cod Piccata', description:'Flaky cod with lemon, capers, parsley, and a butter-emulsified pan sauce.', minutes:30, category:'dinner', servings:4,
    ingredients:['4 cod fillets, 6 ounces each','1/3 cup all-purpose flour','2 tablespoons olive oil','3 tablespoons unsalted butter','1/2 cup seafood or chicken broth','1/4 cup fresh lemon juice','2 tablespoons capers','2 tablespoons chopped parsley'],
    instructions:[
      'Pat cod dry, season, and dust lightly in flour.',
      'Heat olive oil and 1 tablespoon butter in a skillet over medium-high heat. Cook cod 3 to 5 minutes on the first side until golden.',
      'Flip carefully and cook 2 to 4 minutes more until the thickest part reaches 145°F. Transfer to a warm plate.',
      'Reduce heat to medium. Add broth, lemon, and capers; simmer 2 to 3 minutes until slightly reduced.',
      'Remove from heat, whisk in remaining butter, add parsley, and spoon sauce around the fish.'
    ], tags:['dinner','fish','cod','pan sauce','quick'], allergens:['fish','gluten','dairy'], safetyNotes:'Fish should reach 145°F.'
  },
  {
    id:'mushroom-risotto', title:'Mushroom Parmesan Risotto', description:'Creamy arborio rice with deeply browned mushrooms, Parmesan, and a flowing all’onda texture.', minutes:50, category:'dinner', servings:4,
    ingredients:['1 1/2 cups arborio rice','12 ounces cremini mushrooms, sliced','5 cups low-sodium vegetable broth','1 small shallot, minced','1/2 cup dry white wine','1 cup grated Parmesan cheese','3 tablespoons unsalted butter','1 tablespoon olive oil'],
    instructions:[
      'Warm broth in a saucepan and keep it at a bare simmer. In a wide pan, heat olive oil over medium-high and brown mushrooms 6 to 8 minutes; transfer out.',
      'Reduce heat to medium, add 1 tablespoon butter and shallot, and cook 2 minutes. Add rice and toast 2 minutes, stirring until edges look translucent.',
      'Add wine and cook until almost dry, about 2 minutes. Add hot broth one ladle at a time, stirring frequently and waiting until mostly absorbed before adding more.',
      'Continue 17 to 20 minutes until rice is tender with a slight bite and the mixture flows when the pan is shaken.',
      'Remove from heat and vigorously stir in Parmesan, remaining butter, and mushrooms. Rest 2 minutes, then loosen with broth if needed.'
    ], tags:['dinner','risotto','vegetarian','italian-inspired','mushrooms'], allergens:['dairy']
  },
  {
    id:'cacio-e-pepe', title:'Cacio e Pepe', description:'Spaghetti coated in a silky Pecorino and black-pepper emulsion with no cream.', minutes:25, category:'dinner', servings:4,
    ingredients:['12 ounces spaghetti','2 cups finely grated Pecorino Romano cheese','2 teaspoons freshly cracked black pepper'],
    instructions:[
      'Bring a wide pot of water to a boil and salt lightly because Pecorino is salty. Cook spaghetti 2 minutes less than package al-dente time; reserve 2 cups pasta water.',
      'Toast black pepper in a large dry skillet over medium heat for 30 to 45 seconds. Add 3/4 cup pasta water and simmer 30 seconds.',
      'Transfer undercooked pasta to the skillet and toss over medium heat for 1 to 2 minutes until nearly al dente.',
      'Remove the skillet from the heat and let stand 30 seconds. Add Pecorino gradually while tossing vigorously, adding small splashes of pasta water until glossy and creamy.',
      'Serve immediately; keep the pan off direct heat while adding cheese to prevent clumping.'
    ], tags:['dinner','pasta','italian','vegetarian','chef technique'], allergens:['gluten','dairy']
  },
  {
    id:'spaghetti-carbonara', title:'Silky Spaghetti Carbonara', description:'Egg, Pecorino, black pepper, and crisp pork emulsified with pasta water—no cream.', minutes:30, category:'dinner', servings:4,
    ingredients:['12 ounces spaghetti','6 ounces pancetta or guanciale, diced','3 large eggs','2 large egg yolks','1 1/2 cups finely grated Pecorino Romano cheese','1 1/2 teaspoons freshly cracked black pepper'],
    instructions:[
      'Bring a pot of water to a boil and salt lightly. Cook pasta 1 minute less than package al-dente time; reserve 1 1/2 cups pasta water.',
      'Meanwhile cook pancetta in a wide skillet over medium heat 6 to 8 minutes until crisp and fat renders. Turn off heat.',
      'Whisk eggs, yolks, Pecorino, and pepper into a thick paste.',
      'Add hot drained pasta to the pancetta skillet and toss 30 seconds. Let cool off heat for 30 to 45 seconds, then add egg mixture while tossing vigorously.',
      'Add hot pasta water a tablespoon at a time until the sauce becomes glossy and creamy. Return to very low heat only if needed, stirring constantly and never allowing the eggs to scramble.'
    ], tags:['dinner','pasta','italian','carbonara'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'basil-pesto-pasta', title:'Basil Pesto Pasta', description:'Bright basil pesto loosened with pasta water and tossed off heat to preserve its fresh flavor.', minutes:25, category:'dinner', servings:4,
    ingredients:['12 ounces pasta','2 cups packed fresh basil leaves','1/3 cup pine nuts or walnuts','1 garlic clove','3/4 cup grated Parmesan cheese','1/2 cup extra-virgin olive oil','1 tablespoon fresh lemon juice'],
    instructions:[
      'Bring salted water to a rolling boil and cook pasta until al dente according to package timing. Reserve 1 cup pasta water.',
      'Pulse basil, nuts, garlic, Parmesan, and a pinch of salt in a food processor until finely chopped.',
      'With the machine running, stream in olive oil just until emulsified. Stir in lemon juice.',
      'Drain pasta and let it cool for 30 seconds so extreme heat does not dull the basil.',
      'Toss pasta off heat with pesto and enough reserved pasta water to make a glossy sauce that clings to the noodles.'
    ], tags:['dinner','pasta','pesto','vegetarian','italian-inspired'], allergens:['gluten','dairy','tree nuts']
  },
  {
    id:'vegetable-lasagna', title:'Roasted Vegetable Lasagna', description:'Roasted zucchini, spinach, ricotta, mozzarella, and marinara layered with tender pasta.', minutes:110, category:'dinner', servings:8,
    ingredients:['12 lasagna noodles','2 zucchini, sliced','10 ounces baby spinach','15 ounces ricotta cheese','12 ounces mozzarella cheese, shredded','1 cup grated Parmesan cheese','1 large egg','5 cups marinara sauce','2 tablespoons olive oil'],
    instructions:[
      'Heat the oven to 425°F. Toss zucchini with olive oil and roast 15 to 18 minutes until browned and moisture has evaporated. Reduce oven to 375°F.',
      'Cook lasagna noodles 2 minutes less than package al-dente time, drain, and lay flat.',
      'Wilt spinach in a skillet over medium heat for 2 minutes, cool slightly, then squeeze very dry. Mix with ricotta, egg, half the Parmesan, salt, and pepper.',
      'Layer marinara, noodles, ricotta mixture, zucchini, and mozzarella in a 9-by-13-inch dish, repeating and finishing with sauce, mozzarella, and remaining Parmesan.',
      'Cover and bake 30 minutes, uncover and bake 15 to 20 minutes more until bubbling and 165°F in the center. Rest 15 minutes before cutting.'
    ], tags:['dinner','lasagna','vegetarian','italian-inspired'], allergens:['gluten','dairy','eggs'], safetyNotes:'Casseroles should reach 165°F.'
  },
  {
    id:'stovetop-mac-cheese', title:'Creamy Stovetop Mac & Cheese', description:'Sharp cheddar macaroni with a smooth roux-based sauce that stays creamy instead of greasy.', minutes:30, category:'dinner', servings:6,
    ingredients:['1 pound elbow macaroni','4 tablespoons unsalted butter','1/4 cup all-purpose flour','3 cups whole milk, warmed','12 ounces sharp cheddar cheese, grated','1 teaspoon Dijon mustard'],
    instructions:[
      'Boil macaroni in salted water 1 minute less than package al-dente time. Drain.',
      'Melt butter in a saucepan over medium heat. Whisk in flour and cook 1 to 2 minutes until foamy but not browned.',
      'Slowly whisk in warm milk. Bring to a gentle simmer and cook 4 to 6 minutes, whisking, until thick enough to coat a spoon.',
      'Remove from heat. Stir in Dijon, then add cheddar by handfuls, whisking until smooth before adding more.',
      'Fold in hot macaroni and return to low heat for 1 minute if needed. Serve immediately.'
    ], tags:['dinner','pasta','vegetarian','comfort food','mac and cheese'], allergens:['gluten','dairy']
  },
  {
    id:'eggplant-parmesan', title:'Crisp Eggplant Parmesan', description:'Breaded roasted-fried eggplant layered lightly with marinara, mozzarella, and Parmesan.', minutes:90, category:'dinner', servings:6,
    ingredients:['2 large eggplants, sliced 1/2 inch','1 cup all-purpose flour','3 large eggs','2 cups panko breadcrumbs','1 cup grated Parmesan cheese','4 cups marinara sauce','12 ounces mozzarella cheese, shredded','1/2 cup olive oil'],
    instructions:[
      'Salt eggplant slices lightly and place on racks for 30 minutes. Pat completely dry. Heat the oven to 400°F.',
      'Set up flour, beaten eggs, and panko mixed with half the Parmesan. Bread each slice.',
      'Heat a thin layer of olive oil in a skillet over medium-high heat. Cook eggplant in batches 2 to 3 minutes per side until golden, adding oil as needed. Drain on a rack.',
      'Layer a thin amount of marinara, eggplant, mozzarella, and Parmesan in a baking dish, repeating but avoiding excess sauce so the crust remains distinct.',
      'Bake at 400°F for 20 to 25 minutes until bubbling and browned. Rest 10 minutes before serving.'
    ], tags:['dinner','vegetarian','eggplant','italian-american'], allergens:['gluten','eggs','dairy']
  },
  {
    id:'black-bean-tacos', title:'Crispy Black Bean Tacos', description:'Spiced smashed black beans in crisp corn tortillas with avocado-lime slaw.', minutes:30, category:'dinner', servings:4,
    ingredients:['2 15-ounce cans black beans, drained','8 corn tortillas','1 teaspoon ground cumin','1/2 teaspoon smoked paprika','2 cups shredded cabbage','1 avocado','1 lime','1/2 cup shredded Monterey Jack cheese','1 tablespoon olive oil'],
    instructions:[
      'Heat the oven to 425°F. Mash black beans with cumin, paprika, half the lime juice, 2 tablespoons water, and a pinch of salt, leaving some beans whole.',
      'Warm tortillas 20 seconds per side so they are flexible. Fill one half with bean mixture and cheese, fold, and brush lightly with olive oil.',
      'Arrange on a sheet pan and bake 8 minutes, flip, then bake 5 to 7 minutes more until crisp and browned.',
      'Toss cabbage with remaining lime juice and a pinch of salt.',
      'Serve tacos immediately with slaw and sliced avocado.'
    ], tags:['dinner','vegetarian','beans','tacos','quick'], allergens:['dairy']
  },
  {
    id:'chickpea-tomato-stew', title:'Spiced Chickpea Tomato Stew', description:'Chickpeas simmered with caramelized onion, tomato, cumin, paprika, and lemon.', minutes:40, category:'dinner', servings:4,
    ingredients:['2 15-ounce cans chickpeas, drained','1 yellow onion, diced','3 garlic cloves, minced','1 28-ounce can crushed tomatoes','1 teaspoon ground cumin','1 teaspoon smoked paprika','2 cups vegetable broth','3 cups baby spinach','2 tablespoons olive oil','1 lemon'],
    instructions:[
      'Heat olive oil in a pot over medium heat. Cook onion 7 to 9 minutes until soft and golden.',
      'Add garlic, cumin, and paprika and cook 60 seconds.',
      'Add chickpeas, tomatoes, and broth. Bring to a boil, reduce to medium-low, and simmer uncovered 20 minutes until slightly thickened.',
      'Stir in spinach and cook 2 minutes until wilted.',
      'Remove from heat, add fresh lemon juice, and rest 5 minutes before serving.'
    ], tags:['dinner','vegan','vegetarian','chickpeas','stew'], allergens:[]
  },
  {
    id:'vegetable-fried-rice', title:'High-Heat Vegetable Fried Rice', description:'Cold rice, egg, peas, carrots, scallions, and soy cooked quickly in a hot wok.', minutes:25, category:'dinner', servings:4,
    ingredients:['4 cups cold cooked rice','3 large eggs','1 cup frozen peas and carrots, thawed','4 scallions, sliced','3 tablespoons low-sodium soy sauce','1 teaspoon sesame oil','2 tablespoons neutral oil'],
    instructions:[
      'Break cold rice into individual grains before starting. Beat eggs with a pinch of salt.',
      'Heat a wok or large skillet over high heat for 2 minutes. Add 1 teaspoon oil and scramble eggs rapidly for 30 to 45 seconds; transfer out.',
      'Add remaining oil and rice. Stir-fry 3 to 4 minutes, letting some rice contact the pan long enough to toast.',
      'Add peas and carrots and cook 2 minutes. Return eggs and add soy sauce, sesame oil, and scallions.',
      'Toss over high heat 1 minute until everything is steaming hot and evenly seasoned.'
    ], tags:['dinner','vegetarian','fried rice','quick','asian-inspired'], allergens:['eggs','soy','sesame']
  }
];
