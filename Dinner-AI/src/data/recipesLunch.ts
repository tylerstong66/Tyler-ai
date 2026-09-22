import { Recipe } from '@/src/types';

export const LUNCH_RECIPES: Recipe[] = [
  {
    id:'chicken-caesar-salad', title:'Chicken Caesar Salad', description:'Juicy chicken breast, crisp romaine, Parmesan, garlicky croutons, and a bright Caesar-style dressing.', minutes:35, category:'lunch', servings:4,
    ingredients:['1 pound boneless skinless chicken breasts','2 romaine hearts','1 cup sourdough cubes','1/2 cup grated Parmesan cheese','1/3 cup mayonnaise','1 tablespoon fresh lemon juice','1 teaspoon Dijon mustard','1 small garlic clove, grated','1 teaspoon Worcestershire sauce','1 tablespoon olive oil'],
    instructions:[
      'Heat the oven to 400°F. Toss sourdough cubes with 1 teaspoon olive oil and a pinch of salt; bake 8 to 10 minutes, turning once, until crisp and golden.',
      'Pat chicken dry, season, and heat the remaining olive oil in a skillet over medium-high heat. Cook chicken 4 to 6 minutes per side, depending on thickness, until the center reaches 165°F. Rest 5 minutes before slicing.',
      'Whisk mayonnaise, lemon juice, Dijon, garlic, Worcestershire, 2 tablespoons Parmesan, and 1 to 2 tablespoons water until pourable.',
      'Toss chopped romaine with enough dressing to lightly coat. Add croutons and most of the remaining Parmesan.',
      'Top with sliced chicken and finish with the remaining Parmesan and black pepper.'
    ], tags:['lunch','salad','chicken','caesar'], allergens:['eggs','dairy','gluten','fish'], safetyNotes:'Cook chicken to 165°F in the thickest part.'
  },
  {
    id:'tomato-soup-grilled-cheese', title:'Roasted Tomato Soup & Grilled Cheese', description:'Silky roasted tomato soup paired with a deeply golden cheddar grilled cheese.', minutes:50, category:'lunch', servings:4,
    ingredients:['2 pounds ripe tomatoes, halved','1 yellow onion, sliced','4 garlic cloves','2 cups vegetable broth','1/2 cup heavy cream','8 slices sourdough bread','8 slices sharp cheddar cheese','4 tablespoons unsalted butter','2 tablespoons olive oil'],
    instructions:[
      'Heat the oven to 425°F. Toss tomatoes, onion, and garlic with olive oil, salt, and pepper; roast 30 to 35 minutes until edges caramelize.',
      'Transfer roasted vegetables and juices to a pot with broth. Simmer over medium heat 8 minutes, then blend until completely smooth. Stir in cream and keep hot over low heat without boiling hard.',
      'Butter one side of each bread slice. Build four sandwiches with cheddar, keeping buttered sides out.',
      'Cook sandwiches in a skillet over medium-low heat 3 to 4 minutes per side, pressing gently, until bread is deep golden and cheese is fully melted.',
      'Taste the soup for seasoning and serve immediately with the hot sandwiches.'
    ], tags:['lunch','soup','sandwich','vegetarian','comfort food'], allergens:['gluten','dairy']
  },
  {
    id:'turkey-avocado-club', title:'Turkey Avocado Club', description:'Toasted multigrain bread layered with turkey, bacon, avocado, tomato, lettuce, and lemon-Dijon mayo.', minutes:20, category:'lunch', servings:2,
    ingredients:['6 slices multigrain bread','8 ounces sliced cooked turkey','4 slices bacon','1 avocado','1 tomato, sliced','4 leaves romaine lettuce','3 tablespoons mayonnaise','1 teaspoon Dijon mustard','1 teaspoon fresh lemon juice'],
    instructions:[
      'Cook bacon in a skillet over medium heat for 6 to 8 minutes, turning as needed, until crisp. Drain on paper towels.',
      'Toast bread until golden and crisp.',
      'Mix mayonnaise, Dijon, and lemon juice. Mash avocado lightly with a pinch of salt.',
      'Spread two toast slices with avocado, two with lemon-Dijon mayo, and leave two plain for the middle layer.',
      'Build each club with lettuce, tomato, turkey, bacon, and the middle toast layer; secure and cut into triangles.'
    ], tags:['lunch','sandwich','turkey','club'], allergens:['gluten','eggs']
  },
  {
    id:'tuna-melt', title:'Open-Faced Tuna Melt', description:'Bright tuna salad under bubbling cheddar on crisp sourdough.', minutes:20, category:'lunch', servings:4,
    ingredients:['2 5-ounce cans tuna, drained','1/3 cup mayonnaise','2 celery stalks, finely diced','2 tablespoons diced red onion','1 tablespoon fresh lemon juice','1 teaspoon Dijon mustard','4 slices sourdough bread','1 cup shredded sharp cheddar cheese'],
    instructions:[
      'Heat the broiler on high with a rack 6 inches from the element. Toast sourdough until lightly crisp, 1 to 2 minutes per side.',
      'Mix tuna, mayonnaise, celery, onion, lemon, Dijon, and black pepper, breaking the tuna into chunky flakes rather than a paste.',
      'Divide tuna mixture over toast and top evenly with cheddar.',
      'Broil 2 to 4 minutes, watching continuously, until cheese is melted, bubbling, and browned in spots.',
      'Rest 1 minute before serving so the cheese sets slightly.'
    ], tags:['lunch','tuna','sandwich','quick'], allergens:['fish','eggs','dairy','gluten']
  },
  {
    id:'mediterranean-grain-bowl', title:'Mediterranean Grain Bowl', description:'Herbed quinoa, roasted vegetables, chickpeas, cucumber, feta, and lemon-tahini dressing.', minutes:40, category:'lunch', servings:4,
    ingredients:['1 cup quinoa','1 15-ounce can chickpeas, drained','1 zucchini, diced','1 red bell pepper, diced','1 cucumber, diced','1/2 cup crumbled feta cheese','1/4 cup tahini','2 tablespoons fresh lemon juice','2 tablespoons olive oil','1 tablespoon chopped parsley'],
    instructions:[
      'Heat the oven to 425°F. Toss chickpeas, zucchini, and bell pepper with olive oil, salt, and pepper; roast 20 to 25 minutes, stirring once.',
      'Rinse quinoa. Combine with 2 cups water and a pinch of salt, bring to a boil, cover, reduce to low, and cook 15 minutes. Remove from heat and rest covered 5 minutes, then fluff.',
      'Whisk tahini, lemon juice, 3 tablespoons warm water, and a pinch of salt until smooth and pourable.',
      'Stir parsley into warm quinoa.',
      'Build bowls with quinoa, roasted vegetables, cucumber, feta, and tahini dressing.'
    ], tags:['lunch','grain bowl','vegetarian','mediterranean-inspired'], allergens:['sesame','dairy']
  },
  {
    id:'caprese-panini', title:'Caprese Pesto Panini', description:'Fresh mozzarella, tomato, basil pesto, and balsamic pressed until crisp and molten.', minutes:18, category:'lunch', servings:2,
    ingredients:['4 slices ciabatta bread','6 ounces fresh mozzarella, sliced','1 large tomato, sliced','3 tablespoons basil pesto','1 teaspoon balsamic glaze','1 tablespoon olive oil'],
    instructions:[
      'Pat mozzarella and tomato slices dry so the sandwich stays crisp.',
      'Spread pesto on the inside of the bread. Layer mozzarella and tomato, season lightly, and drizzle with balsamic glaze.',
      'Brush the outside of bread with olive oil.',
      'Cook in a panini press at medium-high heat for 4 to 6 minutes, or in a skillet over medium heat for 3 to 4 minutes per side under a weighted pan, until bread is crisp and cheese is fully melted.',
      'Rest 1 minute, then slice and serve.'
    ], tags:['lunch','panini','vegetarian','italian-inspired'], allergens:['gluten','dairy','tree nuts']
  },
  {
    id:'chicken-pesto-sandwich', title:'Chicken Pesto Mozzarella Sandwich', description:'Seared chicken, basil pesto, tomato, and mozzarella on toasted ciabatta.', minutes:30, category:'lunch', servings:4,
    ingredients:['1 pound boneless skinless chicken breasts','4 ciabatta rolls','1/3 cup basil pesto','8 ounces fresh mozzarella, sliced','1 tomato, sliced','1 tablespoon olive oil'],
    instructions:[
      'Slice chicken breasts horizontally into thin cutlets. Season with salt and pepper.',
      'Heat olive oil in a skillet over medium-high heat. Cook chicken 3 to 4 minutes per side until browned and 165°F in the center. Rest 5 minutes.',
      'Heat the broiler on high. Split ciabatta rolls and toast cut sides for 1 to 2 minutes.',
      'Spread pesto on rolls, add chicken, tomato, and mozzarella, then broil open-faced 1 to 2 minutes until cheese softens and begins to bubble.',
      'Close sandwiches and serve immediately.'
    ], tags:['lunch','sandwich','chicken','pesto'], allergens:['gluten','dairy','tree nuts'], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'lentil-vegetable-soup', title:'French Lentil Vegetable Soup', description:'Earthy lentils simmered with caramelized aromatics, tomatoes, thyme, and greens.', minutes:55, category:'lunch', servings:6,
    ingredients:['1 1/2 cups green lentils','1 yellow onion, diced','2 carrots, diced','2 celery stalks, diced','3 garlic cloves, minced','1 14-ounce can diced tomatoes','6 cups vegetable broth','1 teaspoon dried thyme','3 cups chopped kale','2 tablespoons olive oil'],
    instructions:[
      'Heat olive oil in a Dutch oven over medium heat. Cook onion, carrots, and celery 8 to 10 minutes until softened and lightly browned.',
      'Add garlic and thyme and cook 60 seconds.',
      'Add lentils, tomatoes, and broth. Bring to a boil over medium-high heat, then reduce to low and simmer partially covered 30 to 35 minutes until lentils are tender but intact.',
      'Add kale and simmer 5 minutes until tender.',
      'Rest off heat 5 minutes, then season with salt, pepper, and a splash of vinegar or lemon if desired.'
    ], tags:['lunch','soup','lentils','vegan','vegetarian'], allergens:[]
  },
  {
    id:'classic-minestrone', title:'Classic Minestrone', description:'Tomato-rich vegetable soup with beans, pasta, and Parmesan.', minutes:50, category:'lunch', servings:6,
    ingredients:['1 yellow onion, diced','2 carrots, diced','2 celery stalks, diced','1 zucchini, diced','2 garlic cloves, minced','1 28-ounce can crushed tomatoes','1 15-ounce can cannellini beans, drained','6 cups vegetable broth','1 cup small pasta','2 cups baby spinach','1/2 cup grated Parmesan cheese','2 tablespoons olive oil'],
    instructions:[
      'Heat olive oil in a large pot over medium heat. Cook onion, carrots, and celery 8 minutes until soft and lightly golden.',
      'Add zucchini and garlic; cook 2 minutes.',
      'Add tomatoes, beans, and broth. Bring to a boil, then reduce to a lively simmer for 15 minutes.',
      'Add pasta and cook according to package timing, usually 7 to 10 minutes, until just al dente.',
      'Stir in spinach for 1 minute until wilted. Remove from heat, rest 3 minutes, and serve with Parmesan.'
    ], tags:['lunch','soup','vegetarian','italian-inspired'], allergens:['gluten','dairy']
  },
  {
    id:'cobb-salad', title:'Classic Cobb Salad', description:'Chicken, bacon, egg, avocado, tomato, blue cheese, and greens with red-wine vinaigrette.', minutes:35, category:'lunch', servings:4,
    ingredients:['1 pound boneless skinless chicken breasts','6 slices bacon','4 large eggs','8 cups chopped romaine','1 avocado, diced','1 cup cherry tomatoes, halved','1/2 cup crumbled blue cheese','3 tablespoons red wine vinegar','1 teaspoon Dijon mustard','5 tablespoons olive oil'],
    instructions:[
      'Place eggs in a saucepan, cover with water by 1 inch, bring to a boil, then cover, remove from heat, and stand 10 minutes. Transfer to ice water for 5 minutes before peeling.',
      'Cook bacon in a skillet over medium heat 6 to 8 minutes until crisp. Drain.',
      'Season chicken and cook in a lightly oiled skillet over medium-high heat 4 to 6 minutes per side until 165°F. Rest 5 minutes, then slice.',
      'Whisk vinegar, Dijon, olive oil, salt, and pepper until emulsified.',
      'Arrange romaine with chicken, bacon, quartered eggs, avocado, tomatoes, and blue cheese. Dress just before serving.'
    ], tags:['lunch','salad','chicken','cobb'], allergens:['eggs','dairy'], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'southwest-burrito-bowl', title:'Southwest Chicken Burrito Bowl', description:'Cumin-lime chicken, black beans, corn, rice, salsa, and avocado with charred edges and fresh contrast.', minutes:40, category:'lunch', servings:4,
    ingredients:['1 pound boneless skinless chicken thighs','2 cups cooked rice','1 15-ounce can black beans, drained','1 cup corn kernels','1 avocado, diced','1 cup salsa','1 lime','1 teaspoon ground cumin','1 teaspoon smoked paprika','1 tablespoon olive oil'],
    instructions:[
      'Toss chicken with olive oil, cumin, paprika, lime zest, salt, and pepper. Heat a skillet over medium-high heat for 2 minutes.',
      'Cook chicken 5 to 7 minutes per side until browned and the center reaches 165°F. Rest 5 minutes, then slice.',
      'In the same skillet, cook corn over medium-high heat 3 to 4 minutes until lightly charred. Warm black beans over low heat with 2 tablespoons water.',
      'Reheat rice until steaming hot.',
      'Divide rice, beans, corn, chicken, avocado, and salsa among bowls. Finish with fresh lime juice.'
    ], tags:['lunch','bowl','chicken','southwest-inspired'], allergens:[], safetyNotes:'Cook chicken to 165°F.'
  },
  {
    id:'roast-beef-horseradish-sandwich', title:'Roast Beef & Horseradish Sandwich', description:'Thin roast beef, peppery arugula, caramelized onion, and horseradish cream on toasted rye.', minutes:30, category:'lunch', servings:4,
    ingredients:['12 ounces sliced cooked roast beef','8 slices rye bread','1 large yellow onion, thinly sliced','2 cups arugula','1/3 cup sour cream','1 tablespoon prepared horseradish','1 teaspoon Dijon mustard','1 tablespoon unsalted butter'],
    instructions:[
      'Melt butter in a skillet over medium heat. Add onion and a pinch of salt; cook 15 to 18 minutes, stirring every few minutes, until deep golden and soft.',
      'Mix sour cream, horseradish, and Dijon.',
      'Toast rye bread until crisp at the edges.',
      'Warm roast beef briefly in the skillet over low heat for 30 to 60 seconds, just enough to remove the chill without overcooking it.',
      'Build sandwiches with horseradish cream, roast beef, caramelized onion, and arugula.'
    ], tags:['lunch','sandwich','beef'], allergens:['gluten','dairy']
  },
  {
    id:'chickpea-salad-pita', title:'Herbed Chickpea Salad Pita', description:'Creamy smashed chickpeas with herbs, lemon, cucumber, and greens tucked into warm pita.', minutes:15, category:'lunch', servings:4,
    ingredients:['2 15-ounce cans chickpeas, drained','1/3 cup Greek yogurt','1 tablespoon mayonnaise','2 tablespoons fresh lemon juice','1 celery stalk, finely diced','1/4 cup chopped parsley','1 cucumber, diced','4 pita breads','2 cups mixed greens'],
    instructions:[
      'Mash about two-thirds of the chickpeas with a fork, leaving the rest whole for texture.',
      'Fold in Greek yogurt, mayonnaise, lemon juice, celery, parsley, 1/2 teaspoon salt, and black pepper.',
      'Warm pita in a 350°F oven for 3 to 5 minutes or in a dry skillet for 20 seconds per side.',
      'Fill each pita with greens, cucumber, and chickpea salad.',
      'Serve immediately or chill the chickpea mixture up to 24 hours before assembly.'
    ], tags:['lunch','vegetarian','chickpeas','pita'], allergens:['gluten','dairy','eggs']
  }
];
