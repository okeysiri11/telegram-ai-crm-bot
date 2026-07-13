# Marketing Automation Engine v1 — media watermark, optimization, hashtag generation.

from __future__ import annotations

import re
import shutil
import uuid
from pathlib import Path
from typing import Any

MEDIA_ROOT = Path(__file__).resolve().parent.parent / "storage" / "marketing_automation"
WATERMARK_TEXT = "AUTO"

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".webp"})


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "", value.strip())
    return cleaned or "tag"


def generate_hashtags(
    *,
    channel: str,
    make: str | None = None,
    model: str | None = None,
    year: int | None = None,
    extra: list[str] | None = None,
    limit: int = 12,
) -> list[str]:
    tags: list[str] = ["#cars", "#forsale", "#auto"]

    channel_defaults = {
        "telegram": ["#telegramcars"],
        "instagram": ["#carsofinstagram", "#instacars", "#autodealer"],
        "facebook": ["#marketplace", "#autosale"],
        "tiktok": ["#tiktokcars", "#fyp", "#carsoftiktok"],
    }
    tags.extend(channel_defaults.get(channel, []))

    if make:
        tags.append(f"#{_slug(make)}")
    if model:
        tags.append(f"#{_slug(model)}")
    if year:
        tags.append(f"#{year}")

    if extra:
        for tag in extra:
            normalized = tag if tag.startswith("#") else f"#{_slug(tag)}"
            tags.append(normalized)

    seen: set[str] = set()
    unique: list[str] = []
    for tag in tags:
        lowered = tag.lower()
        if lowered not in seen:
            seen.add(lowered)
            unique.append(tag)
    return unique[:limit]


def _try_import_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont

        return Image, ImageDraw, ImageFont
    except ImportError:
        return None, None, None


def optimize_image(
    source_path: Path,
    output_path: Path,
    *,
    max_width: int = 1920,
    quality: int = 85,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    original_size = source_path.stat().st_size

    Image, _, _ = _try_import_pillow()
    if Image is None or source_path.suffix.lower() not in IMAGE_EXTENSIONS:
        shutil.copy2(source_path, output_path)
        processed_size = output_path.stat().st_size
        return {
            "optimized": False,
            "watermark_applied": False,
            "original_size_bytes": original_size,
            "processed_size_bytes": processed_size,
            "note": "pillow_unavailable_or_non_image",
        }

    try:
        with Image.open(source_path) as img:
            img = img.convert("RGB")
            width, height = img.size
            if width > max_width:
                ratio = max_width / width
                img = img.resize((max_width, int(height * ratio)))

            save_kwargs: dict[str, Any] = {"optimize": True}
            if output_path.suffix.lower() in {".jpg", ".jpeg"}:
                save_kwargs["quality"] = quality
            img.save(output_path, **save_kwargs)
            final_size = (img.size[0], img.size[1])
    except Exception:
        shutil.copy2(source_path, output_path)
        processed_size = output_path.stat().st_size
        return {
            "optimized": False,
            "watermark_applied": False,
            "original_size_bytes": original_size,
            "processed_size_bytes": processed_size,
            "note": "image_decode_failed",
        }

    processed_size = output_path.stat().st_size
    return {
        "optimized": True,
        "watermark_applied": False,
        "original_size_bytes": original_size,
        "processed_size_bytes": processed_size,
        "width": final_size[0],
        "height": final_size[1],
    }


def apply_watermark(
    source_path: Path,
    output_path: Path,
    *,
    text: str = WATERMARK_TEXT,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    original_size = source_path.stat().st_size

    Image, ImageDraw, ImageFont = _try_import_pillow()
    if Image is None or source_path.suffix.lower() not in IMAGE_EXTENSIONS:
        shutil.copy2(source_path, output_path)
        return {
            "optimized": False,
            "watermark_applied": False,
            "original_size_bytes": original_size,
            "processed_size_bytes": output_path.stat().st_size,
            "note": "pillow_unavailable_or_non_image",
        }

    try:
        with Image.open(source_path) as img:
            img = img.convert("RGBA")
            overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)
            font = ImageFont.load_default()
            margin = 16
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = img.size[0] - text_width - margin
            y = img.size[1] - text_height - margin
            draw.rectangle(
                (x - 6, y - 4, x + text_width + 6, y + text_height + 4),
                fill=(0, 0, 0, 120),
            )
            draw.text((x, y), text, fill=(255, 255, 255, 220), font=font)
            combined = Image.alpha_composite(img, overlay).convert("RGB")
            combined.save(output_path, quality=90, optimize=True)
    except Exception:
        shutil.copy2(source_path, output_path)
        return {
            "optimized": False,
            "watermark_applied": False,
            "original_size_bytes": original_size,
            "processed_size_bytes": output_path.stat().st_size,
            "note": "image_decode_failed",
        }

    return {
        "optimized": True,
        "watermark_applied": True,
        "original_size_bytes": original_size,
        "processed_size_bytes": output_path.stat().st_size,
    }


def process_media(
    source_relative_path: str,
    *,
    watermark_enabled: bool = True,
    optimize_enabled: bool = True,
    watermark_text: str = WATERMARK_TEXT,
) -> tuple[str, dict[str, Any]]:
    """Return processed relative path and metadata."""
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    source_path = MEDIA_ROOT / source_relative_path
    if not source_path.exists():
        raise FileNotFoundError(f"Media not found: {source_relative_path}")

    batch_id = uuid.uuid4()
    output_relative = f"processed/{batch_id}{source_path.suffix.lower() or '.jpg'}"
    output_path = MEDIA_ROOT / output_relative

    meta: dict[str, Any] = {}
    working_source = source_path

    if optimize_enabled:
        temp_relative = f"processed/{batch_id}_opt{source_path.suffix.lower() or '.jpg'}"
        temp_path = MEDIA_ROOT / temp_relative
        meta.update(optimize_image(working_source, temp_path))
        working_source = temp_path

    if watermark_enabled:
        meta.update(apply_watermark(working_source, output_path, text=watermark_text))
    elif working_source != source_path:
        shutil.copy2(working_source, output_path)
        meta.setdefault("processed_size_bytes", output_path.stat().st_size)
    else:
        shutil.copy2(source_path, output_path)
        meta = {
            "optimized": False,
            "watermark_applied": False,
            "original_size_bytes": source_path.stat().st_size,
            "processed_size_bytes": output_path.stat().st_size,
        }

    if working_source != source_path and working_source.exists():
        working_source.unlink(missing_ok=True)

    return output_relative, meta
