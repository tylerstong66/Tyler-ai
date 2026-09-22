import { Recipe } from '@/src/types';

export const SNACK_DESSERT_RECIPES: Recipe[] = [
  {
    id:'classic-guacamole', title:'Classic Guacamole', description:'Creamy avocado with lime, onion, cilantro, and jalapeño balanced for freshness and texture.', minutes:10, category:'snack', servings:4,
    ingredients:['3 ripe avocados','1/4 cup finely diced white onion','1 jalapeño, minced','2 tablespoons chopped cilantro','2 tablespoons fresh lime juice','1 small tomato, seeded and diced'],
    instructions:[
      'Mash avocados with lime juice and 1/2 teaspoon salt until mostly smooth but still slightly chunky.',
      'Fold in onion, jalapeño, and cilantro without overmixing.',
      'Fold in tomato last so it keeps its shape.',
      'Taste and adjust lime and salt. Serve immediately, or press plastic wrap directly onto the surface and refrigerate up to 2 hours.'
    ], tags:['snack','dip','avocado','vegan','quick'], allergens:[]
  },
  {
    id:'restaurant-salsa', title:'Roasted Tomato Salsa', description:'Charred tomatoes, onion, jalapeño, garlic, lime, and cilantro blended to a restaurant-style texture.', minutes:25, category:'snack', servings:6,
    ingredients:['6 Roma tomatoes, halved','1/2 white onion','1 jalapeño','2 garlic cloves','1 tablespoon neutral oil','2 tablespoons fresh lime juice','1/4 cup cilantro'],
    instructions:[
      'Heat the broiler on high with a rack 5 to 6 inches from the element. Toss tomatoes, onion, jalapeño, and garlic with oil.',
      'Broil 6 to 10 minutes, turning once, until blistered and blackened in spots.',
      'Cool 5 minutes, then pulse with lime juice, cilantro, and salt until finely chopped but not completely smooth.',
      'Rest 10 minutes before serving so the flavors settle.'
    ], tags:['snack','salsa','vegan','mexican-inspired'], allergens:[]
  },
  {
    id:'crispy-roasted-chickpeas', title:'Crispy Roasted Chickpeas', description:'Dry-roasted chickpeas with smoked paprika and cumin, crisp enough for snacking.', minutes:45, category:'snack', servings:4,
    ingredients:['2 15-ounce cans chickpeas, drained','1 tablespoon olive oil','1 teaspoon smoked paprika','1/2 teaspoon ground cumin'],
    instructions:[
      'Heat the oven to 425°F. Pat chickpeas very dry with towels and remove loose skins.',
      'Roast chickpeas dry on a sheet pan for 10 minutes.',
      'Toss hot chickpeas with olive oil, paprika, cumin, and salt.',
      'Return to the oven for 20 to 25 minutes, shaking every 8 minutes, until crisp and deeply golden.',
      'Cool on the pan for 10 minutes; they crisp further as steam escapes.'
    ], tags:['snack','chickpeas','vegan','roasted'], allergens:[]
  },
  {
    id:'deviled-eggs', title:'Classic Deviled Eggs', description:'Silky yolk filling with Dijon, mayonnaise, vinegar, and paprika.', minutes:30, category:'snack', servings:6,
    ingredients:['6 large eggs','3 tablespoons mayonnaise','1 teaspoon Dijon mustard','1 teaspoon white wine vinegar','1/4 teaspoon smoked paprika'],
    instructions:[
      'Place eggs in a saucepan, cover by 1 inch with water, and bring to a boil. Cover, remove from heat, and stand 10 minutes.',
      'Transfer eggs to ice water for 5 minutes, then peel and halve lengthwise.',
      'Mash yolks with mayonnaise, Dijon, vinegar, salt, and pepper until completely smooth.',
      'Pipe or spoon filling into whites and dust with paprika. Keep chilled until serving.'
    ], tags:['snack','eggs','party','quick'], allergens:['eggs']
  },
  {
    id:'three-cheese-quesadilla', title:'Crisp Three-Cheese Quesadilla', description:'A thin, evenly melted cheese layer inside a crisp golden tortilla.', minutes:15, category:'snack', servings:2,
    ingredients:['2 large flour tortillas','1/2 cup shredded cheddar cheese','1/2 cup shredded Monterey Jack cheese','1/4 cup grated Parmesan cheese','1 teaspoon neutral oil'],
    instructions:[
      'Heat a large skillet over medium heat for 1 minute and brush lightly with oil.',
      'Lay in one tortilla and scatter cheeses evenly, leaving a 1/2-inch border. Top with the second tortilla.',
      'Cook 2 to 3 minutes until underside is golden and cheese begins melting.',
      'Flip carefully and cook 2 minutes more until crisp and fully melted. Rest 1 minute before cutting into wedges.'
    ], tags:['snack','quesadilla','vegetarian','quick'], allergens:['gluten','dairy']
  },
  {
    id:'caprese-skewers', title:'Caprese Skewers', description:'Tomato, mozzarella, basil, olive oil, and balsamic arranged into bright one-bite snacks.', minutes:15, category:'snack', servings:6,
    ingredients:['1 pint cherry tomatoes','8 ounces small mozzarella balls','24 basil leaves','1 tablespoon extra-virgin olive oil','1 tablespoon balsamic glaze'],
    instructions:[
      'Drain mozzarella and pat both cheese and tomatoes dry.',
      'Thread tomato, basil, and mozzarella onto small skewers, repeating once if space allows.',
      'Drizzle lightly with olive oil and balsamic glaze just before serving.',
      'Finish with flaky salt and black pepper and serve cool, not ice-cold.'
    ], tags:['snack','vegetarian','no-cook','italian-inspired'], allergens:['dairy']
  },
  {
    id:'stovetop-popcorn', title:'Perfect Stovetop Popcorn', description:'Evenly popped kernels finished with browned butter and fine salt.', minutes:12, category:'snack', servings:4,
    ingredients:['1/2 cup popcorn kernels','3 tablespoons neutral oil','2 tablespoons unsalted butter'],
    instructions:[
      'Add oil and 3 popcorn kernels to a heavy pot, cover, and heat over medium-high until the test kernels pop.',
      'Remove from heat, add remaining kernels in an even layer, cover, and wait 30 seconds.',
      'Return to medium-high heat and shake the pot every 10 to 15 seconds. When popping slows to about 2 seconds between pops, immediately remove from heat.',
      'Melt butter in a small pan over medium heat for 2 to 3 minutes until nutty and lightly browned, then drizzle over popcorn and season.'
    ], tags:['snack','popcorn','quick','vegetarian'], allergens:['dairy']
  },
  {
    id:'parmesan-zucchini-fries', title:'Parmesan Zucchini Fries', description:'Oven-crisp zucchini spears with panko and Parmesan.', minutes:35, category:'snack', servings:4,
    ingredients:['2 medium zucchini','1/2 cup all-purpose flour','2 large eggs','1 cup panko breadcrumbs','1/2 cup grated Parmesan cheese'],
    instructions:[
      'Heat the oven to 425°F and place a wire rack over a sheet pan.',
      'Cut zucchini into thick spears and pat dry. Dredge in flour, then beaten egg, then panko mixed with Parmesan.',
      'Arrange on the rack with space between pieces and spray or brush lightly with oil.',
      'Bake 18 to 22 minutes, turning once, until crisp and golden. Serve immediately.'
    ], tags:['snack','zucchini','vegetarian','baked'], allergens:['gluten','eggs','dairy']
  },

  {
    id:'brown-butter-chocolate-chip-cookies', title:'Brown Butter Chocolate Chip Cookies', description:'Chewy cookies with nutty browned butter, crisp edges, soft centers, and dark chocolate.', minutes:55, category:'dessert', servings:12,
    ingredients:['1 cup unsalted butter','1 cup packed brown sugar','1/2 cup sugar','2 large eggs','2 teaspoons vanilla extract','2 1/4 cups all-purpose flour','1 teaspoon baking soda','2 cups semisweet chocolate chips'],
    instructions:[
      'Melt butter in a saucepan over medium heat. Continue cooking 4 to 6 minutes, swirling often, until milk solids turn amber and smell nutty. Pour into a bowl and cool 15 minutes.',
      'Heat the oven to 350°F. Whisk browned butter with both sugars, then whisk in eggs and vanilla.',
      'Fold in flour, baking soda, and 3/4 teaspoon salt just until combined; fold in chocolate chips. Chill dough 20 minutes.',
      'Scoop 2-tablespoon portions onto parchment-lined pans 2 inches apart. Bake 10 to 13 minutes until edges are golden but centers still look slightly soft.',
      'Cool on the pan 5 minutes before transferring to a rack.'
    ], tags:['dessert','cookies','chocolate','baking'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'fudgy-brownies', title:'Fudgy Chocolate Brownies', description:'Dense, glossy-topped brownies with a moist center and deep cocoa flavor.', minutes:50, category:'dessert', servings:16,
    ingredients:['10 tablespoons unsalted butter','1 1/4 cups sugar','3/4 cup unsweetened cocoa powder','2 large eggs','1 teaspoon vanilla extract','3/4 cup all-purpose flour','1/2 cup chopped dark chocolate'],
    instructions:[
      'Heat the oven to 350°F. Line an 8-inch square pan with parchment.',
      'Melt butter over low heat. Remove from heat and whisk in sugar, cocoa, and 1/2 teaspoon salt until smooth. Cool 3 minutes.',
      'Whisk in eggs one at a time, then vanilla. Fold in flour just until no dry streaks remain, then fold in chocolate.',
      'Spread evenly and bake 22 to 28 minutes until edges are set and a toothpick from the center has moist crumbs but no raw batter.',
      'Cool at least 30 minutes before cutting for the fudgiest texture.'
    ], tags:['dessert','brownies','chocolate','baking'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'apple-crisp', title:'Brown Sugar Apple Crisp', description:'Tender cinnamon apples under a deeply browned oat-butter crumble.', minutes:65, category:'dessert', servings:8,
    ingredients:['6 apples, peeled and sliced','1 tablespoon fresh lemon juice','1 teaspoon ground cinnamon','1/2 cup brown sugar','1 cup rolled oats','3/4 cup all-purpose flour','6 tablespoons cold unsalted butter, cubed'],
    instructions:[
      'Heat the oven to 375°F. Toss apples with lemon juice, cinnamon, 2 tablespoons brown sugar, and a pinch of salt. Spread in a baking dish.',
      'Mix oats, flour, remaining brown sugar, and a pinch of salt. Rub in cold butter until uneven clumps form.',
      'Scatter topping over apples without packing it down.',
      'Bake 40 to 50 minutes until fruit bubbles around the edges and topping is deeply golden.',
      'Rest 15 minutes before serving so the juices thicken slightly.'
    ], tags:['dessert','apple','fruit','baking'], allergens:['gluten','dairy']
  },
  {
    id:'banana-bread', title:'Caramelized Banana Bread', description:'Moist banana bread with browned edges, warm spice, and concentrated banana flavor.', minutes:80, category:'dessert', servings:10,
    ingredients:['3 very ripe bananas, mashed','1/2 cup unsalted butter, melted','3/4 cup brown sugar','2 large eggs','1 teaspoon vanilla extract','1 3/4 cups all-purpose flour','1 teaspoon baking soda','1/2 teaspoon ground cinnamon'],
    instructions:[
      'Heat the oven to 350°F. Grease and line a 9-by-5-inch loaf pan.',
      'Whisk mashed banana, melted butter, brown sugar, eggs, and vanilla until smooth.',
      'Whisk flour, baking soda, cinnamon, and 1/2 teaspoon salt separately. Fold dry into wet only until no dry flour remains.',
      'Transfer to the pan and bake 50 to 60 minutes until deeply golden and a skewer in the center comes out with a few moist crumbs.',
      'Cool in the pan 15 minutes, then move to a rack and cool at least 30 minutes before slicing.'
    ], tags:['dessert','banana','quick bread','baking'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'blueberry-muffins', title:'Bakery-Style Blueberry Muffins', description:'High-domed muffins with juicy berries, lemon, and a crisp sugar top.', minutes:35, category:'dessert', servings:12,
    ingredients:['2 cups all-purpose flour','3/4 cup sugar','2 teaspoons baking powder','2 large eggs','3/4 cup milk','1/2 cup unsalted butter, melted','1 teaspoon vanilla extract','1 1/2 cups blueberries','1 teaspoon lemon zest'],
    instructions:[
      'Heat the oven to 400°F and line a 12-cup muffin pan.',
      'Whisk flour, sugar, baking powder, and 1/2 teaspoon salt. Whisk eggs, milk, melted butter, vanilla, and zest separately.',
      'Fold wet into dry just until mostly combined, then gently fold in blueberries. Do not overmix.',
      'Divide batter nearly to the tops of the cups. Bake 18 to 22 minutes until golden and the tops spring back when lightly pressed.',
      'Cool in the pan 5 minutes before transferring to a rack.'
    ], tags:['dessert','muffins','blueberry','baking'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'vanilla-cupcakes', title:'Vanilla Bean Cupcakes', description:'Tender vanilla cupcakes with a fine crumb and smooth buttercream.', minutes:50, category:'dessert', servings:12,
    ingredients:['1 1/2 cups all-purpose flour','1 1/2 teaspoons baking powder','1 cup sugar','1/2 cup unsalted butter, softened','2 large eggs','2 teaspoons vanilla extract','1/2 cup whole milk','2 cups vanilla buttercream'],
    instructions:[
      'Heat the oven to 350°F and line a 12-cup muffin pan.',
      'Beat softened butter and sugar on medium speed for 3 minutes until pale and fluffy. Beat in eggs one at a time, then vanilla.',
      'Whisk flour, baking powder, and 1/2 teaspoon salt. Add dry ingredients in three additions alternating with milk, mixing on low only until smooth.',
      'Fill cups about two-thirds full and bake 17 to 20 minutes until tops spring back and a tester comes out clean.',
      'Cool 5 minutes in the pan, then completely on a rack before frosting.'
    ], tags:['dessert','cupcakes','vanilla','baking'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'lemon-bars', title:'Bright Lemon Bars', description:'Buttery shortbread under a sharp, silky lemon custard with a clean slice.', minutes:70, category:'dessert', servings:16,
    ingredients:['1 1/2 cups all-purpose flour','1/2 cup powdered sugar','3/4 cup unsalted butter, cold and cubed','4 large eggs','1 1/2 cups sugar','2/3 cup fresh lemon juice','1 tablespoon lemon zest','1/4 cup all-purpose flour'],
    instructions:[
      'Heat the oven to 350°F. Line a 9-inch square pan with parchment.',
      'Combine 1 1/2 cups flour and powdered sugar; cut in cold butter until crumbly. Press firmly into the pan and bake 18 to 22 minutes until pale golden.',
      'Whisk eggs, sugar, lemon juice, zest, and remaining 1/4 cup flour until smooth.',
      'Pour filling over the hot crust and bake 20 to 25 minutes until edges are set and the center has only a slight wobble.',
      'Cool completely, then refrigerate at least 2 hours before cutting and dusting with powdered sugar.'
    ], tags:['dessert','lemon','bars','baking'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'espresso-tiramisu-cups', title:'Espresso Tiramisu Cups', description:'Mascarpone cream layered with espresso-soaked ladyfingers and cocoa.', minutes:30, category:'dessert', servings:6,
    ingredients:['8 ounces mascarpone cheese','1 cup heavy cream','1/3 cup sugar','1 teaspoon vanilla extract','1 cup strong espresso, cooled','18 ladyfingers','2 tablespoons unsweetened cocoa powder'],
    instructions:[
      'Beat heavy cream and sugar to medium peaks, 2 to 4 minutes. Fold in mascarpone and vanilla gently until smooth.',
      'Dip each ladyfinger in cooled espresso for about 1 second per side; do not soak until mushy.',
      'Layer broken ladyfingers and mascarpone cream in six glasses, repeating once.',
      'Cover and refrigerate at least 4 hours so the layers set and flavors meld.',
      'Dust with cocoa immediately before serving.'
    ], tags:['dessert','tiramisu','coffee','no-bake'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'vanilla-panna-cotta', title:'Vanilla Panna Cotta', description:'Silky vanilla cream set just firmly enough to hold its shape.', minutes:20, category:'dessert', servings:6,
    ingredients:['2 cups heavy cream','1 cup whole milk','1/2 cup sugar','2 1/4 teaspoons unflavored gelatin','1 teaspoon vanilla extract'],
    instructions:[
      'Sprinkle gelatin over 1/4 cup cold milk and let bloom 5 minutes.',
      'Heat cream, remaining milk, sugar, and a pinch of salt over medium heat until steaming and about 180°F; do not boil hard.',
      'Remove from heat and whisk in bloomed gelatin until completely dissolved, then add vanilla.',
      'Divide among six ramekins and cool 20 minutes at room temperature.',
      'Refrigerate at least 4 hours, until softly set.'
    ], tags:['dessert','panna cotta','no-bake','vanilla'], allergens:['dairy']
  },
  {
    id:'creme-brulee', title:'Vanilla Crème Brûlée', description:'Silky baked custard beneath a thin, glassy caramelized sugar crust.', minutes:70, category:'dessert', servings:6,
    ingredients:['2 cups heavy cream','5 large egg yolks','1/2 cup sugar','1 teaspoon vanilla extract','6 teaspoons sugar for topping'],
    instructions:[
      'Heat the oven to 325°F. Heat cream over medium-low until steaming, about 180°F, then remove from heat.',
      'Whisk yolks with 1/2 cup sugar until smooth. Slowly whisk in hot cream in a thin stream, then add vanilla.',
      'Strain custard into six ramekins. Set ramekins in a roasting pan and add hot water halfway up their sides.',
      'Bake 30 to 40 minutes until edges are set but centers still tremble slightly. Remove from water, cool, then refrigerate at least 4 hours.',
      'Sprinkle each with 1 teaspoon sugar and caramelize with a torch until amber. Rest 2 minutes for the crust to harden.'
    ], tags:['dessert','custard','french-inspired','vanilla'], allergens:['dairy','eggs']
  },
  {
    id:'bread-pudding', title:'Vanilla-Cinnamon Bread Pudding', description:'Custardy brioche with caramelized edges and a soft vanilla center.', minutes:75, category:'dessert', servings:8,
    ingredients:['10 cups cubed brioche','4 large eggs','3 cups whole milk','3/4 cup sugar','2 teaspoons vanilla extract','1 teaspoon ground cinnamon','4 tablespoons unsalted butter'],
    instructions:[
      'Heat the oven to 350°F and butter a 9-by-13-inch baking dish.',
      'Spread brioche cubes in the dish. Whisk eggs, milk, sugar, vanilla, cinnamon, and a pinch of salt until fully blended.',
      'Pour custard over bread and press gently. Rest 20 minutes so the bread absorbs the liquid.',
      'Dot with butter and bake 40 to 50 minutes until browned, puffed, and the center reaches 160°F.',
      'Rest 10 minutes before serving.'
    ], tags:['dessert','bread pudding','comfort food','baking'], allergens:['gluten','dairy','eggs']
  },
  {
    id:'peach-cobbler', title:'Golden Peach Cobbler', description:'Juicy peaches beneath a tender biscuit-like topping baked until deeply golden.', minutes:65, category:'dessert', servings:8,
    ingredients:['6 cups sliced peaches','3/4 cup sugar','1 tablespoon fresh lemon juice','1 tablespoon cornstarch','1 1/2 cups all-purpose flour','2 teaspoons baking powder','6 tablespoons cold unsalted butter','3/4 cup whole milk'],
    instructions:[
      'Heat the oven to 375°F. Toss peaches with half the sugar, lemon juice, cornstarch, and a pinch of salt. Spread in a baking dish.',
      'Whisk flour, remaining sugar, baking powder, and 1/2 teaspoon salt. Cut in cold butter until pea-size pieces remain.',
      'Stir in milk just until a shaggy dough forms. Drop spoonfuls over the fruit, leaving small gaps for steam.',
      'Bake 40 to 50 minutes until topping is deep golden and fruit is bubbling vigorously around the edges.',
      'Rest 15 minutes before serving.'
    ], tags:['dessert','peach','cobbler','fruit','baking'], allergens:['gluten','dairy']
  }
];
