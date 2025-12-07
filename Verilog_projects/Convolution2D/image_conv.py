from PIL import Image
import numpy as np

img = Image.open("test_image.png").convert("L")  
img = img.resize((128, 128))                     

pixels = np.array(img).flatten()  


with open("image_data.txt", "w") as f: 
    for p in pixels:
        f.write(f"{p}\n")

print("Pixel data saved to image_data.txt")
