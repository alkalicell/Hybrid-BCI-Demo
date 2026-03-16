import sys
from pathlib import Path
import pygame
import pygame.locals

path = Path()

# List of image paths

def demo_4_imgs(image_paths):

    # Initialize pygame
    pygame.init()

    # Set the width and height of the window
    WIDTH, HEIGHT = 770, 580

    # Create a window and a surface
    pygame.display.set_caption("AI Picture Demo")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))

    # Load the images using pygame
    images = [pygame.image.load(path) for path in image_paths]

    # Get the size of the images
    image_sizes = [image.get_size() for image in images]

    # Calculate the positions to center the images on the screen
    positions = [(WIDTH - w) // 2 for w, h in image_sizes]

    # Create a font object.
    font = pygame.font.Font(None, 50)
    # Render the text "AI Picture Rendering...".
    text_surface = font.render("You have made a amazing drawing", True, (0, 0, 0))

    # Calculate the position to center the text in the rectangle.
    text_x = WIDTH / 2 - text_surface.get_width() // 2
    text_y = HEIGHT / 2 - text_surface.get_height() // 2

    # Blit the text surface to the screen.
    screen.fill((255, 255, 255))
    screen.blit(text_surface, (text_x, text_y))
    pygame.display.update()
    pygame.time.delay(5000)

    # Display the images one by one with a fade effect
    for i in range(0,5):
        screen.fill((0, 0, 0))
        first_picture = pygame.Surface(image_sizes[i])
        first_picture.blit(images[i], (0, 0))
        screen.blit(first_picture, (positions[i], 0))
        pygame.display.update()
        pygame.time.delay(3000)

        if i == 0:
            screen.fill((255, 255, 255))
            text_surface = font.render("But is it a little dull? Let us help you!", True, (0, 0, 0))
            # Blit the text surface to the screen.
            text_x = WIDTH / 2 - text_surface.get_width() // 2
            text_y = HEIGHT / 2 - text_surface.get_height() // 2
            screen.blit(text_surface, (text_x, text_y))
            pygame.display.update()
            pygame.time.delay(3000)
            screen.blit(first_picture, (positions[i], 0))
            pygame.display.update()
            pygame.time.delay(1500)



        if i <4:
            second_picture = pygame.Surface(image_sizes[i+1])
            second_picture.blit(images[i+1], (0, 0))
            second_picture.set_alpha(0)
            for alpha in range(0, 255, 5):
                # Set the alpha value of the surface
                second_picture.set_alpha(alpha)
                screen.blit(second_picture, (positions[i+1], 0))
                # Update the display
                pygame.display.update()
                # Delay to create the fade effect
                pygame.time.delay(50)

    text_surface = font.render("Which one is your favorite? Share with us!", True, (0, 0, 0))
    # Blit the text surface to the screen.
    text_x = WIDTH / 2 - text_surface.get_width() // 2
    text_y = HEIGHT / 2 - text_surface.get_height() // 2

    for alpha in range(0, 255, 5):
        # Set the alpha value of the surface
        picture = pygame.Surface(image_sizes[4])
        picture.fill((255, 255, 255))
        picture.set_alpha(alpha)
        text_surface.set_alpha(alpha)
        screen.blit(picture, (positions[4], 0))
        screen.blit(text_surface, (text_x, text_y))
        # Update the display
        pygame.display.update()
        # Delay to create the fade effect
        pygame.time.delay(10)
    # Display the last four images side by side until the space key is pressed
    pygame.display.update()
    pygame.time.delay(5000)
    screen.fill((255, 255, 255))

    for i in range(1, 5):
        # Scale the image to 1/4 of the screen size
        scaled_image = pygame.transform.scale(images[i], (WIDTH // 2 - 15, HEIGHT // 2 - 15))

        # Calculate the position of the image
        if i == 1:
            pos = (10, 10)  # Top left corner
        elif i == 2:
            pos = (WIDTH // 2 + 5, 10)  # Top right corner
        elif i == 3:
            pos = (10, HEIGHT // 2 + 5)  # Bottom left corner
        else:
            pos = (WIDTH // 2 + 5, HEIGHT // 2 + 5)  # Bottom right corner

        # Blit the image onto the screen
        screen.blit(scaled_image, pos)

    pygame.display.update()

    # Wait for the space key to be pressed
    while True:
        for event in pygame.event.get():
            if event.type == pygame.locals.KEYDOWN and event.key == pygame.locals.K_SPACE:
                pygame.quit()
                sys.exit()

if __name__ == '__main__':
    sample_PATH = [path / 'sample_data' / 'sample_outimg.png',
                   path / 'sample_data' / 'sample_outai_1.jpg',
                   path / 'sample_data' / 'sample_outai_2.jpg',
                   path / 'sample_data' / 'sample_outai_3.jpg',
                   path / 'sample_data' / 'sample_outai_4.jpg']
    demo_4_imgs(sample_PATH)