# filename: snake_game.py

import random

# Set the initial position of the snake
snake_x = 100
snake_y = 100

# Set the direction of the snake
direction = "right"

# Create a list of food items
food_items = []

# Create the snake
snake = []
for i in range(50):
    snake.append(random.randint(100, 200))
snake.append(random.randint(100, 200))

# Create the food items
for i in range(10):
    food_items.append(random.randint(100, 200))

# Keep track of the score
score = 0

# Keep track of the time
time = 0

# Run the game loop
while True:
    # Move the snake
    if direction == "right":
        snake_x += 1
    elif direction == "left":
        snake_x -= 1
    elif direction == "up":
        snake_y -= 1
    elif direction == "down":
        snake_y += 1

    # Check if the snake has hit itself or the walls
    if snake_x < 0 or snake_x > 200:
        direction = "left"
    elif snake_y < 0 or snake_y > 200:
        direction = "up"
    elif snake_x in [food_item for food_item in food_items]:
        food_items.remove(food_item)
        score += 1
        if score == 10:
            direction = "left"
        elif score == 20:
            direction = "right"
    else:
        snake.pop()

    # Add a new food item to the list
    food_items.append(random.randint(100, 200))

    # Check if the snake has eaten all the food
    if len(food_items) == 10:
        break

    # Update the time
    time += 0.01

    # Render the game
    print("Score:", score)
    print("Time:", time)
    print("Snake coordinates:", snake_x, snake_y)
    print("Food coordinates:", [food_item for food_item in food_items])

    # Check if the snake has won
    if snake_x == 200 and snake_y == 200:
        print("You win!")
        break