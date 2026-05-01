from rembg import remove
from PIL import Image
import os

img = Image.open('logo_raw.png')

# Process with rembg
out = remove(img, post_process_mask=True)

# Convert to RGBA
out = out.convert("RGBA")

# Ensure the image is not completely black/transparent
extrema = out.getextrema()
print("RGBA extrema:", extrema)

# Find true bbox
bbox = out.getbbox()
if bbox:
    out = out.crop(bbox)

# Does it still have colors?
print("Size:", out.size)

out.save('test_rembg.png', "PNG")
