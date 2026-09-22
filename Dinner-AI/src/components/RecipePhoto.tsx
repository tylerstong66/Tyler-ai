import React, { useState } from 'react';
import { Image, LayoutChangeEvent, StyleSheet, View, ViewStyle } from 'react-native';

const RECIPE_IDS = ["veggie-omelet","banana-oatmeal","chicken-salad-wrap","chicken-soup","chicken-tacos","garlic-pasta","beef-stir-fry","sheet-pan-chicken","turkey-chili","baked-ziti","salmon-rice-bowl","pot-roast","pulled-pork","lentil-curry","cucumber-hummus-bites","apple-yogurt-crunch","chocolate-mug-cake","cinnamon-baked-apples","berry-yogurt-parfait","soft-scrambled-eggs","buttermilk-pancakes","crispy-waffles","custardy-french-toast","breakfast-burritos","shakshuka","avocado-poached-egg-toast","crispy-breakfast-potatoes","spinach-mushroom-frittata","huevos-rancheros","sausage-egg-breakfast-sandwich","blueberry-lemon-yogurt-bowl","savory-breakfast-quiche","apple-cinnamon-overnight-oats","chicken-caesar-salad","tomato-soup-grilled-cheese","turkey-avocado-club","tuna-melt","mediterranean-grain-bowl","caprese-panini","chicken-pesto-sandwich","lentil-vegetable-soup","classic-minestrone","cobb-salad","southwest-burrito-bowl","roast-beef-horseradish-sandwich","chickpea-salad-pita","herb-roast-chicken","chicken-piccata","chicken-marsala","chicken-parmesan","butter-chicken","chicken-teriyaki","chicken-fajitas","chicken-fried-rice","steak-au-poivre","cast-iron-sirloin","ground-beef-tacos","smash-burgers","meatballs-marinara","classic-beef-stew","shepherds-pie","beef-stroganoff","pork-chops-apple-pan-sauce","mustard-herb-pork-tenderloin","oven-carnitas","shrimp-scampi","garlic-butter-shrimp-rice","seared-scallops-lemon-butter","crispy-fish-tacos","cod-piccata","mushroom-risotto","cacio-e-pepe","spaghetti-carbonara","basil-pesto-pasta","vegetable-lasagna","stovetop-mac-cheese","eggplant-parmesan","black-bean-tacos","chickpea-tomato-stew","vegetable-fried-rice","classic-guacamole","restaurant-salsa","crispy-roasted-chickpeas","deviled-eggs","three-cheese-quesadilla","caprese-skewers","stovetop-popcorn","parmesan-zucchini-fries","brown-butter-chocolate-chip-cookies","fudgy-brownies","apple-crisp","banana-bread","blueberry-muffins","vanilla-cupcakes","lemon-bars","espresso-tiramisu-cups","vanilla-panna-cotta","creme-brulee","bread-pudding","peach-cobbler"];
const ATLAS = require('../../assets/recipe-atlas.jpg');

export function RecipePhoto({
  recipeId,
  height,
  style
}: {
  recipeId: string;
  height: number;
  style?: ViewStyle;
}) {
  const [width, setWidth] = useState(0);
  const index = RECIPE_IDS.indexOf(recipeId);

  if (index < 0) return null;

  const row = Math.floor(index / 10);
  const col = index % 10;

  function onLayout(event: LayoutChangeEvent) {
    const nextWidth = event.nativeEvent.layout.width;
    if (Math.abs(nextWidth - width) > 1) setWidth(nextWidth);
  }

  return (
    <View style={[styles.crop, { height }, style]} onLayout={onLayout}>
      {width > 0 ? (
        <Image
          source={ATLAS}
          resizeMode="stretch"
          style={{
            position: 'absolute',
            width: width * 10,
            height: width * 10,
            left: -col * width,
            top: -row * width
          }}
        />
      ) : null}
    </View>
  );
}

export function hasRecipePhoto(recipeId: string) {
  return RECIPE_IDS.includes(recipeId);
}

const styles = StyleSheet.create({
  crop: {
    width: '100%',
    overflow: 'hidden',
    backgroundColor: '#E8EFEA'
  }
});
