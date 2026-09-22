import { Recipe } from '@/src/types';

export const DINNER_RECIPES_A: Recipe[] = [
  {
    id:'herb-roast-chicken', title:'Herb-Roasted Whole Chicken', description:'Crisp-skinned roast chicken with lemon, garlic, thyme, and concentrated pan juices.', minutes:105, category:'dinner', servings:6,
    ingredients:['1 whole chicken, 4 to 5 pounds','1 lemon, halved','1 head garlic, halved crosswise','6 sprigs fresh thyme','2 tablespoons unsalted butter, softened','1 tablespoon olive oil'],
    instructions:[
      'Heat the oven to 425°F. Pat the chicken completely dry, including the cavity. Season generously inside and out with salt and pepper.',
      'Stuff the cavity loosely with lemon, garlic, and thyme. Rub the skin with butter and olive oil; tuck wing tips underneath and tie the legs loosely.',
      'Roast breast-side up for 20 minutes at 425°F, then reduce the oven to 375°F without opening the door.',
      'Continue roasting 45 to 60 minutes, rotating the pan once, until the thickest breast and innermost thigh both reach at least 165°F without the thermometer touching bone.',
      'Transfer to a board and rest 15 minutes before carving. Spoon the defatted pan juices over the meat.'
    ], tags:['dinner','chicken','roast','classic'], allergens:['dairy'], safetyNotes:'All poultry must reach at least 165°F.'
  },
  {
    id:'chicken-piccata', title:'Chicken Piccata', description:'Thin chicken cutlets with a bright lemon-caper pan sauce finished with butter.', minutes:30, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds boneless skinless chicken breasts','1/2 cup all-purpose flour','2 tablespoons olive oil','3 tablespoons unsalted butter','1/2 cup chicken broth','1/3 cup fresh lemon juice','3 tablespoons capers, drained','2 tablespoons chopped parsley'],
    instructions:[
      'Slice chicken into thin cutlets and pound to about 1/2 inch. Season and dredge lightly in flour, shaking off excess.',
      'Heat olive oil and 1 tablespoon butter in a skillet over medium-high heat. Sear chicken 3 to 4 minutes per side until golden and 165°F in the center. Transfer to a plate.',
      'Reduce heat to medium. Add broth and scrape up browned bits; simmer 2 minutes.',
      'Add lemon juice and capers and simmer 1 minute. Remove from heat and whisk in remaining cold butter until glossy.',
      'Return chicken and accumulated juices for 30 seconds, then finish with parsley.'
    ], tags:['dinner','chicken','italian-american','quick','pan sauce'], allergens:['gluten','dairy'], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'chicken-marsala', title:'Chicken Marsala', description:'Golden chicken cutlets with deeply browned mushrooms and a reduced Marsala pan sauce.', minutes:40, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds boneless skinless chicken breasts','8 ounces cremini mushrooms, sliced','1/2 cup all-purpose flour','3/4 cup dry Marsala wine','3/4 cup chicken broth','2 tablespoons olive oil','3 tablespoons unsalted butter','1 tablespoon chopped parsley'],
    instructions:[
      'Cut chicken into 1/2-inch cutlets, season, and dredge lightly in flour.',
      'Heat olive oil and 1 tablespoon butter in a wide skillet over medium-high heat. Cook chicken 3 to 4 minutes per side until 165°F. Transfer to a plate.',
      'Add mushrooms and cook over medium-high heat 5 to 7 minutes until their moisture evaporates and edges brown.',
      'Add Marsala and boil 2 to 3 minutes until reduced by about half. Add broth and simmer 3 to 4 minutes until lightly thickened.',
      'Remove from heat, whisk in remaining butter, return chicken for 1 minute, and finish with parsley.'
    ], tags:['dinner','chicken','italian-american','mushrooms','pan sauce'], allergens:['gluten','dairy'], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'chicken-parmesan', title:'Crisp Chicken Parmesan', description:'Crunchy breaded chicken with tomato sauce, mozzarella, and Parmesan, broiled just until bubbling.', minutes:55, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds boneless skinless chicken breasts','1/2 cup all-purpose flour','2 large eggs','1 1/2 cups panko breadcrumbs','1/2 cup grated Parmesan cheese','2 cups marinara sauce','8 ounces mozzarella cheese, sliced','1/3 cup olive oil'],
    instructions:[
      'Heat the oven to 425°F. Slice chicken into 1/2-inch cutlets. Set up flour, beaten eggs, and panko mixed with half the Parmesan.',
      'Coat chicken in flour, then egg, then panko. Heat olive oil in a skillet over medium-high heat and fry in batches 2 to 3 minutes per side until deep golden.',
      'Transfer to a rack set over a sheet pan and bake 6 to 10 minutes until chicken reaches 165°F.',
      'Spoon a modest amount of hot marinara over each cutlet, add mozzarella and remaining Parmesan, then broil 1 to 3 minutes until cheese bubbles and browns.',
      'Rest 3 minutes before serving so the crust remains crisp.'
    ], tags:['dinner','chicken','italian-american','breaded'], allergens:['gluten','eggs','dairy'], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'butter-chicken', title:'Butter Chicken', description:'Spiced yogurt-marinated chicken simmered briefly in a silky tomato-butter sauce.', minutes:60, category:'dinner', servings:6,
    ingredients:['2 pounds boneless skinless chicken thighs','1/2 cup plain yogurt','1 tablespoon lemon juice','2 teaspoons garam masala','1 teaspoon ground cumin','1 teaspoon turmeric','1 yellow onion, diced','3 garlic cloves, minced','1 tablespoon grated ginger','1 15-ounce can tomato sauce','1 cup heavy cream','3 tablespoons unsalted butter'],
    instructions:[
      'Toss chicken with yogurt, lemon, half the garam masala, cumin, turmeric, and salt. Marinate refrigerated at least 30 minutes.',
      'Heat the broiler on high. Spread chicken on a foil-lined pan and broil 6 to 8 minutes per side until browned and at least 165°F. Rest 5 minutes, then cut into pieces.',
      'Melt 1 tablespoon butter in a saucepan over medium heat. Cook onion 6 to 8 minutes until golden; add garlic and ginger for 1 minute.',
      'Add tomato sauce and remaining garam masala; simmer 10 minutes over medium-low heat. Stir in cream and remaining butter and simmer gently 3 minutes.',
      'Add chicken and juices and simmer 3 to 5 minutes only, just to marry the flavors without drying the meat.'
    ], tags:['dinner','chicken','indian-inspired','curry'], allergens:['dairy'], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'chicken-teriyaki', title:'Glazed Chicken Teriyaki', description:'Caramelized chicken thighs lacquered with a reduced soy-ginger glaze.', minutes:35, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds boneless skinless chicken thighs','1/3 cup low-sodium soy sauce','3 tablespoons brown sugar','2 tablespoons rice vinegar','1 tablespoon grated ginger','2 garlic cloves, grated','1 teaspoon sesame oil','1 tablespoon neutral oil','3 cups cooked rice'],
    instructions:[
      'Whisk soy sauce, brown sugar, vinegar, ginger, garlic, sesame oil, and 1/3 cup water.',
      'Heat neutral oil in a skillet over medium-high heat. Add chicken smooth-side down and sear 5 to 6 minutes until browned.',
      'Flip and cook 4 to 6 minutes more until the center reaches 165°F. Transfer chicken to a plate.',
      'Pour sauce into the skillet and boil over medium-high heat for 3 to 5 minutes until glossy and reduced enough to coat a spoon.',
      'Return chicken for 1 minute, turning to glaze. Rest 3 minutes, slice, and serve over rice.'
    ], tags:['dinner','chicken','japanese-inspired','rice'], allergens:['soy','sesame'], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'chicken-fajitas', title:'Sizzling Chicken Fajitas', description:'High-heat seared chicken with charred peppers and onions, lime, and warm tortillas.', minutes:35, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds boneless skinless chicken breasts','2 bell peppers, sliced','1 large onion, sliced','8 flour tortillas','1 lime','1 teaspoon ground cumin','1 teaspoon chili powder','1/2 teaspoon smoked paprika','2 tablespoons neutral oil'],
    instructions:[
      'Slice chicken into 1/2-inch strips. Toss with cumin, chili powder, paprika, half the lime juice, 1 tablespoon oil, and salt.',
      'Heat a cast-iron skillet over high heat for 2 to 3 minutes. Cook chicken in a single layer for 3 minutes without moving, then toss and cook 2 to 4 minutes more until 165°F. Transfer to a plate.',
      'Add remaining oil, peppers, and onion. Cook over high heat 5 to 7 minutes, tossing occasionally, until charred at the edges but still slightly crisp.',
      'Return chicken and juices for 1 minute and finish with remaining lime juice.',
      'Warm tortillas 20 seconds per side in a dry skillet and serve immediately.'
    ], tags:['dinner','chicken','tex-mex','quick'], allergens:['gluten'], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'chicken-fried-rice', title:'Wok-Style Chicken Fried Rice', description:'Day-old rice, seared chicken, egg, scallion, and vegetables cooked fast over high heat.', minutes:30, category:'dinner', servings:4,
    ingredients:['1 pound boneless skinless chicken thighs, diced','4 cups cold cooked rice','2 large eggs','1 cup frozen peas and carrots, thawed','4 scallions, sliced','3 tablespoons low-sodium soy sauce','1 teaspoon sesame oil','2 tablespoons neutral oil'],
    instructions:[
      'Break cold rice apart with your fingers so there are no large clumps. Beat eggs with a pinch of salt.',
      'Heat a wok or large skillet over high heat for 2 minutes. Add 1 tablespoon oil and chicken; stir-fry 4 to 6 minutes until browned and 165°F. Transfer out.',
      'Add a teaspoon oil, pour in eggs, and stir rapidly 30 to 45 seconds until barely set. Transfer with chicken.',
      'Add remaining oil and rice. Cook over high heat 3 to 4 minutes, tossing and pressing rice against the pan so some grains toast.',
      'Add vegetables, chicken, eggs, soy sauce, sesame oil, and scallions. Toss 1 to 2 minutes until steaming hot.'
    ], tags:['dinner','chicken','fried rice','asian-inspired','quick'], allergens:['eggs','soy','sesame'], safetyNotes:'Cook chicken to 165°F and reheat rice until steaming hot.'
  },
  {
    id:'steak-au-poivre', title:'Steak au Poivre', description:'Pepper-crusted steaks with a cognac-style cream pan sauce.', minutes:35, category:'dinner', servings:4,
    ingredients:['4 beef strip steaks, 8 ounces each','2 tablespoons coarsely cracked black peppercorns','1 tablespoon neutral oil','2 tablespoons unsalted butter','1/3 cup brandy or cognac','3/4 cup beef broth','1/2 cup heavy cream'],
    instructions:[
      'Pat steaks dry and season with salt. Press cracked pepper firmly onto both sides. Let stand at room temperature 20 minutes while the pan heats.',
      'Heat a heavy skillet over medium-high heat for 2 to 3 minutes. Add oil and sear steaks 3 to 5 minutes per side, depending on thickness, until at least 145°F for USDA minimum safety. Rest at least 3 minutes.',
      'Reduce heat to medium and carefully add brandy away from flame. Simmer 1 minute, scraping the fond.',
      'Add broth and simmer 3 to 4 minutes until reduced by half. Add cream and simmer 2 to 3 minutes until lightly thickened.',
      'Remove from heat and swirl in butter. Spoon sauce around, not over, the steak crust.'
    ], tags:['dinner','beef','french-inspired','steak','pan sauce'], allergens:['dairy'], safetyNotes:'Whole beef steaks should reach at least 145°F and rest at least 3 minutes.'
  },
  {
    id:'cast-iron-sirloin', title:'Cast-Iron Garlic Butter Sirloin', description:'Hard-seared sirloin basted with foaming butter, garlic, and herbs.', minutes:30, category:'dinner', servings:4,
    ingredients:['2 sirloin steaks, 12 ounces each','1 tablespoon neutral oil','3 tablespoons unsalted butter','3 garlic cloves, smashed','3 sprigs fresh thyme'],
    instructions:[
      'Pat steaks very dry and season generously. Let stand 20 minutes. Heat a cast-iron skillet over medium-high to high heat until very hot, about 3 minutes.',
      'Add oil and steaks. Sear without moving 2 to 3 minutes, then flip and sear 2 minutes.',
      'Reduce heat to medium. Add butter, garlic, and thyme; when butter foams, tilt the pan and baste steaks continuously for 1 to 3 minutes.',
      'Check the center with an instant-read thermometer. For USDA minimum safety, cook whole beef steaks to at least 145°F.',
      'Rest on a board at least 3 minutes before slicing across the grain.'
    ], tags:['dinner','beef','steak','cast iron','quick'], allergens:['dairy'], safetyNotes:'Whole beef steaks should reach at least 145°F and rest at least 3 minutes.'
  },
  {
    id:'ground-beef-tacos', title:'Spiced Ground Beef Tacos', description:'Browned beef with toasted spices, tomato, and crisp fresh toppings.', minutes:30, category:'dinner', servings:4,
    ingredients:['1 pound ground beef','8 corn tortillas','1/2 yellow onion, diced','2 garlic cloves, minced','1 tablespoon chili powder','1 teaspoon ground cumin','1 tablespoon tomato paste','1/2 cup salsa','1 cup shredded lettuce','1 cup diced tomato'],
    instructions:[
      'Heat a skillet over medium-high heat. Add ground beef and cook 5 to 7 minutes, breaking into small crumbles, until browned and the center of the meat reaches 160°F.',
      'Push beef to one side, add onion, and cook 3 minutes. Add garlic, chili powder, and cumin for 30 seconds.',
      'Stir in tomato paste and cook 1 minute, then add salsa and 1/4 cup water. Simmer 3 to 4 minutes until the mixture is juicy but not watery.',
      'Warm tortillas in a dry skillet over medium-high heat for 20 to 30 seconds per side.',
      'Fill tortillas with beef, lettuce, and tomato.'
    ], tags:['dinner','beef','tacos','tex-mex','quick'], allergens:[], safetyNotes:'Ground beef should reach 160°F.'
  },
  {
    id:'smash-burgers', title:'Crisp-Edged Smash Burgers', description:'Thin beef patties smashed on a ripping-hot griddle for maximum browned crust.', minutes:25, category:'dinner', servings:4,
    ingredients:['1 1/2 pounds 80/20 ground beef','4 burger buns','4 slices American or cheddar cheese','1 small onion, thinly sliced','8 pickle slices','2 tablespoons mayonnaise','1 tablespoon yellow mustard'],
    instructions:[
      'Divide beef into eight loose 3-ounce balls; do not pack tightly. Heat a cast-iron griddle or skillet over high heat for 3 to 4 minutes.',
      'Place four balls on the dry hot surface and immediately smash each very thin with a sturdy spatula. Season and cook 90 seconds to 2 minutes until the edges are dark and lacy.',
      'Scrape firmly underneath, flip, top with cheese, and cook 60 to 90 seconds more. Repeat. Ground beef should reach 160°F.',
      'Toast buns cut-side down on the griddle for 30 to 60 seconds.',
      'Stack two patties per bun with onion, pickles, mayonnaise, and mustard.'
    ], tags:['dinner','beef','burger','griddle','quick'], allergens:['gluten','dairy','eggs'], safetyNotes:'Ground beef should reach 160°F.'
  },
  {
    id:'meatballs-marinara', title:'Tender Meatballs in Marinara', description:'Beef-and-pork meatballs browned first, then gently finished in tomato sauce.', minutes:60, category:'dinner', servings:6,
    ingredients:['1 pound ground beef','1 pound ground pork','1 cup fresh breadcrumbs','1/2 cup milk','1 large egg','1/2 cup grated Parmesan cheese','2 garlic cloves, grated','2 tablespoons chopped parsley','4 cups marinara sauce','2 tablespoons olive oil'],
    instructions:[
      'Heat the oven to 400°F. Soak breadcrumbs in milk for 5 minutes.',
      'Gently combine beef, pork, soaked crumbs, egg, Parmesan, garlic, parsley, 1 teaspoon salt, and pepper. Form into 1 1/2-inch balls without compacting.',
      'Heat olive oil in a wide oven-safe skillet over medium-high heat. Brown meatballs 2 to 3 minutes on several sides, about 8 minutes total.',
      'Add marinara and bring to a gentle simmer. Transfer to the oven for 12 to 18 minutes until meatballs reach 160°F.',
      'Rest in the sauce 5 minutes before serving.'
    ], tags:['dinner','beef','pork','italian-american','meatballs'], allergens:['gluten','dairy','eggs'], safetyNotes:'Ground beef and pork mixtures should reach 160°F.'
  },
  {
    id:'classic-beef-stew', title:'Classic Beef Stew', description:'Deeply browned beef chuck slowly braised with wine, broth, carrots, and potatoes.', minutes:180, category:'dinner', servings:8,
    ingredients:['3 pounds beef chuck, cut into 1 1/2-inch cubes','1 yellow onion, diced','3 carrots, cut into chunks','1 pound Yukon Gold potatoes, cut into chunks','3 garlic cloves, minced','2 tablespoons tomato paste','1 cup dry red wine','4 cups beef broth','2 tablespoons all-purpose flour','2 tablespoons olive oil','2 sprigs thyme'],
    instructions:[
      'Heat the oven to 325°F. Pat beef very dry, season, and dust lightly with flour.',
      'Heat oil in a Dutch oven over medium-high heat. Brown beef in batches 3 to 4 minutes per side; do not crowd. Transfer to a plate.',
      'Reduce heat to medium. Cook onion and carrots 6 minutes. Add garlic and tomato paste for 1 minute. Add wine and boil 3 minutes, scraping browned bits.',
      'Return beef, add broth and thyme, cover, and braise at 325°F for 1 1/2 hours.',
      'Add potatoes, cover, and braise 45 to 60 minutes more until beef is fork-tender. Rest 10 minutes before serving.'
    ], tags:['dinner','beef','stew','braised','comfort food'], allergens:['gluten']
  },
  {
    id:'shepherds-pie', title:'Beef Shepherd’s Pie', description:'Rich ground beef and vegetables under a browned blanket of buttery mashed potatoes.', minutes:75, category:'dinner', servings:6,
    ingredients:['1 1/2 pounds ground beef','2 pounds Yukon Gold potatoes','1 yellow onion, diced','2 carrots, diced','1 cup frozen peas','2 tablespoons tomato paste','1 tablespoon Worcestershire sauce','1 cup beef broth','4 tablespoons unsalted butter','1/2 cup milk'],
    instructions:[
      'Heat the oven to 400°F. Boil potatoes in salted water 15 to 20 minutes until completely tender. Drain, steam-dry 2 minutes, then mash with butter and warm milk.',
      'Meanwhile brown beef in a skillet over medium-high heat 6 to 8 minutes until 160°F. Drain excess fat.',
      'Add onion and carrots and cook 6 minutes. Stir in tomato paste for 1 minute, then Worcestershire and broth. Simmer 5 minutes until thick; stir in peas.',
      'Transfer filling to a baking dish and spread potatoes evenly over top, roughing the surface with a fork.',
      'Bake 20 to 25 minutes until bubbling and 165°F in the center; broil 1 to 2 minutes for deeper browning. Rest 10 minutes.'
    ], tags:['dinner','beef','comfort food','casserole'], allergens:['dairy'], safetyNotes:'Ground beef should reach 160°F; casseroles should reach 165°F.'
  },
  {
    id:'beef-stroganoff', title:'Beef Stroganoff', description:'Seared beef and browned mushrooms in a tangy sour-cream pan sauce over egg noodles.', minutes:40, category:'dinner', servings:4,
    ingredients:['1 1/4 pounds sirloin steak, sliced thinly','8 ounces cremini mushrooms, sliced','1 small onion, sliced','8 ounces egg noodles','1 1/2 cups beef broth','1 tablespoon Dijon mustard','2 teaspoons Worcestershire sauce','1/2 cup sour cream','2 tablespoons unsalted butter','1 tablespoon neutral oil'],
    instructions:[
      'Bring salted water to a boil and cook egg noodles according to package timing until al dente. Drain.',
      'Heat oil in a skillet over high heat. Sear beef in two batches for 60 to 90 seconds per side; cook to at least 145°F for USDA minimum safety, then rest 3 minutes off heat.',
      'Reduce to medium-high. Add butter and mushrooms; cook 5 to 7 minutes until browned. Add onion and cook 3 minutes.',
      'Add broth, Dijon, and Worcestershire; simmer 4 to 5 minutes until reduced by about one-third.',
      'Remove from heat before stirring in sour cream so it does not split. Return beef and juices for 30 seconds and serve over noodles.'
    ], tags:['dinner','beef','noodles','comfort food'], allergens:['gluten','dairy','eggs'], safetyNotes:'Whole beef cuts should reach at least 145°F and rest at least 3 minutes.'
  },
  {
    id:'pork-chops-apple-pan-sauce', title:'Pork Chops with Apple Pan Sauce', description:'Hard-seared pork chops with caramelized apples, thyme, and a cider-butter reduction.', minutes:40, category:'dinner', servings:4,
    ingredients:['4 bone-in pork chops, about 1 inch thick','2 crisp apples, sliced','1 shallot, sliced','1 cup apple cider','1 teaspoon Dijon mustard','2 sprigs fresh thyme','2 tablespoons unsalted butter','1 tablespoon neutral oil'],
    instructions:[
      'Pat chops dry and season. Heat a heavy skillet over medium-high heat for 2 minutes, add oil, and sear chops 3 to 5 minutes per side until browned.',
      'Reduce heat to medium and continue cooking as needed until the center reaches at least 145°F. Transfer to a plate and rest at least 3 minutes.',
      'Add apples and shallot to the skillet and cook 4 to 5 minutes until lightly caramelized.',
      'Add cider, Dijon, and thyme; simmer 4 to 6 minutes until reduced by about half.',
      'Remove from heat, swirl in butter, and spoon apples and sauce around the rested chops.'
    ], tags:['dinner','pork','apple','pan sauce'], allergens:['dairy'], safetyNotes:'Pork chops should reach at least 145°F and rest at least 3 minutes.'
  }
];
