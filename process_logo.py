from rembg import remove
from PIL import Image
import numpy as np

# Load the original logo (the one with the dark brick background)
img = Image.open('images/brand-mark.png').convert("RGBA")

# ---------------------------------------------------------
# Step 1: Remove the Gemini sparkle watermark.
# It sits in the bottom-right corner — paint it out with
# the surrounding dark color before we do background removal
# so rembg doesn't accidentally keep it.
# ---------------------------------------------------------
w, h = img.size
# Erase bottom-right ~80x80 px region (sparkle area)
erase_region = (w - 90, h - 90, w, h)
from PIL import ImageDraw
draw = ImageDraw.Draw(img)
# Sample the color just to the left of the sparkle to fill naturally
fill_color = (40, 50, 60, 255)  # approximate dark slate color
draw.rectangle(erase_region, fill=fill_color)

# ---------------------------------------------------------
# Step 2: Use rembg AI to remove the brick wall background
# ---------------------------------------------------------
print("Running background removal (this may take a moment)...")
out = remove(img, post_process_mask=True)
out = out.convert("RGBA")

# ---------------------------------------------------------
# Step 3: Tight-crop to the logo badge (remove empty space)
# ---------------------------------------------------------
bbox = out.getbbox()
if bbox:
    # Add a small 10px padding all around
    pad = 10
    bbox = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(out.width,  bbox[2] + pad),
        min(out.height, bbox[3] + pad),
    )
    out = out.crop(bbox)

print(f"Final logo size: {out.size}")

# Save as PNG (with transparency) into the images folder
out.save('images/brand-mark.png', "PNG")
print("Saved: images/brand-mark.png")
