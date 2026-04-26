import sqlite3

# script used mainly for devo of website.
conn = sqlite3.connect("user_recipes.db")
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        title TEXT,
        score FLOAT,
        category TEXT,
        matched TEXT,
        missing TEXT
    )
""")


"""
for the creation of "user_recipes"
rows = [
    ("Marinated Flank Steak Recipe", "black pepper, chili powder, cinnamon, cumin, garlic, oregano, paprika, salt"),
    ("French Chicken Stew", "black pepper, chili powder, cinnamon, cumin, garlic, ginger, paprika, salt"),
    ("My Favorite Cheese Cake", "black pepper, chili powder, cumin, garlic, ginger, oregano, paprika, salt"),
    ("Pork rub", "black pepper, chili powder, cumin, garlic, ginger, oregano, paprika, salt")
]

for the creation of "all_recipes"
rows = [
    ("Marinated Flank Steak Recipe", "black pepper, chili powder, cinnamon, cumin, garlic, oregano, paprika, salt", "1 1/2 pound flank steak, 1/2 c. finely minced green onions (scallions), 1/2 c. dry red wine, 1/4 c. soy sauce, 3 tbsp. salad oil, 3 teaspoon sesame seeds, 2 teaspoon packed brown sugar, 1/4 teaspoon grnd black pepper, 1/4 teaspoon grnd ginger, 1 clove garlic, chopped", "Remove tenderloin from steak., Score meat., Combine remaining ingredients and pour over meat., Let marinate 24 hrs., Preheat grill., Broil or possibly grill., Slice thinly on an angle against the grain.", "/data/images/MarinatedFlankSteak.jpg"),
    ("French Chicken Stew", "black pepper, chili powder, cinnamon, cumin, garlic, ginger, paprika, salt", "1 tablespoon rosemary, 1 teaspoon thyme, 3 bay leaves, 1 teaspoon smoked paprika, 1 teaspoon pepper, 1/4 cup red wine, 3 cups chicken broth, 2 cups button mushrooms sliced, 2 cups mushroom mix, oyster, shiitake, baby bella, sliced, 2 medium carrots sliced diagonally, 1 onion medium, chopped, 1 red potato medium, cut in 1-inch pieces, 1 cup frozen green beans 1-inch pieces, 1/2 can black olives pitted ripe, halved, 1 handful grape tomatoes halved, 8 chicken thighs with bones and skin. 2-3 lbs, 2 stalks celery, 3 cups water", "combine all ingredients in slow cooker (6 quarts). bury chicken in vegetables. don't put herbs directly on chicken (because skin is removed later), add enough broth and water to cover most of ingredients. liquid level rises a good amount during cooking, so careful with filling the slow cooker too much., turn slow cooker on low for 6-7 hours or high 3-4 hours. Note: in my newer Crock-Pot this was enough time, but in my parents' older Crock-Pot 7 hours on low was not enough (don't know how long would be good. we left the veggies a little tough)., pull out all chicken., skim off fat from top with spoon, pull off skin and remove bones from chicken. shred and return to soup.", "/data/images/FrenchChickenStew.jpg"),
    ("My Favorite Cheese Cake", "black pepper, chili powder, cumin, garlic, ginger, oregano, paprika, salt", "1 1/4 c. graham cracker crumbs, 1/4 c. sugar, 1/3 c. melted margarine, 2 (8 oz.) pkg. cream cheese, softened, 1 (14 oz.) can Eagle Brand milk, 3 eggs, 1/4 c. lemon juice, 1 (8 oz.) carton sour cream", "To make the apple juice ice cubes, pour the apple juice into two ice trays and freeze until the sangria is ready to serve., Combine the water, mint leaves, sugar, and cinnamon in a small saucepan, and bring to a boil over medium heat. Reduce the heat and simmer for several minutes. Remove from the heat and allow to cool. Once the mixture has cooled to room temperature, remove and discard the mint and cinnamon sticks., Transfer the remaining mixture to a large serving bowl., Add the grape juice, peaches, pears, and the orange and lemon slices to the serving bowl. Mix well, and refrigerate overnight. Immediately before serving, mix in the sparkling apple cider and the apple juice ice cubes., Garnish with fresh mint leaves, if desired.", "/data/images/MyFavoriteCheesecake.jpg"),
    ("Pork rub", "black pepper, chili powder, cumin, garlic, ginger, oregano, paprika, salt", "2 tablespoons sweet paprika, 2 teaspoons ground cumin, 2 teaspoons fresh ground pepper, 2 teaspoons cocoa powder, 1 tablespoon muscovado sugar, 1 teaspoon salt", "Mix up all the ingredients., Rub on each side of the pork before either grilling or barbequeing., The rub can be stored in an air tight container., Meat can be marinated in the rub to add a more intense flavour, if doing this add the salt at the last stage., When barbequeing sprinkle some of the rub over the hot coals for a smokey flavour.", "/data/images/PorkRub.jpg"),
    ("Pretzel Salad Or Dessert", "salt (if unsalted pretzels)", "2 c. crushed small thin pretzels (sticks), 3/4 c. margarine", "Mix and press in baking pan thats approximately 13 x 9-inch., Bake 8 minutes at 400\u00b0., Let cool to desired temp.", "data/images/PretzelSaladDessert.jpg")
]
"""

rows = [
    ("Marinated Flank Steak Recipe", .833, "Dinner", "black pepper, chili powder, cinnamon, cumin, garlic, oregano, paprika, salt", "red pepper flakes, saffron"),
    ("French Chicken Stew", .801, "Dinner", "black pepper, chili powder, cinnamon, cumin, garlic, ginger, paprika, salt", "red pepper flakes, saffron"),
    ("My Favorite Cheese Cake", .784, "Snack/Dessert", "black pepper, chili powder, cumin, garlic, ginger, oregano, paprika, salt", "red pepper flakes, saffron"),
    ("Pork rub", .741, "Other/General", "black pepper, chili powder, cumin, garlic, ginger, oregano, paprika, salt", "red pepper flakes, saffron")
]

cursor.executemany("INSERT INTO recipes (title, score, category, matched, missing) VALUES (?, ?, ?, ?, ?)", rows)

conn.commit()
conn.close()