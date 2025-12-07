from PIL import Image
import numpy as np

IMG_W = 128
IMG_H = 128

# Read simulation output
pixels = np.loadtxt("out_pixels.txt", dtype=int)

pixels = pixels[:(IMG_H-2)*(IMG_W-2)]


pixels = np.clip(pixels, 0, 255).astype(np.uint8)

# Reshape to image
pixels = pixels.reshape((IMG_H-2, IMG_W-2))

img = Image.fromarray(pixels)
img.save("convolved_image.png")

print("Convolved image saved as convolved_image.png")
