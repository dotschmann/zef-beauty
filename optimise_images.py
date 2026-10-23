from pathlib import Path

from PIL import Image, ImageOps

IMAGE_DIRECTORY = Path(__file__).resolve().parent / "images"
MAX_SIZE = (1920, 1920)
QUALITY = 85

for source in sorted(IMAGE_DIRECTORY.glob("*.png")):
    # Keep the logo unchanged.
    if source.name == "zef-beauty-logo.png":
        continue

    destination = source.with_suffix(".webp")

    # Avoid overwriting an existing WebP.
    if destination.exists():
        print(f"Skipped existing file: {destination.name}")
        continue

    with Image.open(source) as original:
        colour_profile = original.info.get("icc_profile")
        image = ImageOps.exif_transpose(original)

        # Preserve transparency when present.
        has_transparency = (
            "A" in image.getbands()
            or "transparency" in image.info
        )
        image = image.convert("RGBA" if has_transparency else "RGB")

        # Preserve proportions without enlarging smaller photos.
        image.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)

        options = {
            "format": "WEBP",
            "quality": QUALITY,
            "method": 6,
        }

        if colour_profile:
            options["icc_profile"] = colour_profile

        image.save(destination, **options)

    original_kb = source.stat().st_size / 1024
    converted_kb = destination.stat().st_size / 1024
    reduction = (1 - converted_kb / original_kb) * 100

    print(
        f"{destination.name}: "
        f"{original_kb:.0f} KB -> {converted_kb:.0f} KB "
        f"({reduction:.0f}% smaller)"
    )