from __future__ import annotations

import json
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
PNG = ROOT / "wps_export_final" / "幻灯片1.png"
PPTX = ROOT / "see_e2f_rdb_wps_reproduction_final.pptx"
AUDIT_DIR = ROOT / "audits"
CROP_DIR = AUDIT_DIR / "crops"
CONTACT = AUDIT_DIR / "wps_render_contact_sheet.png"
STRUCTURE = AUDIT_DIR / "pptx_structure_audit.json"
VISUAL = AUDIT_DIR / "wps_visual_audit.json"

PPT_W, PPT_H = 1600, 900


def crop_box(coords, sx, sy):
    x, y, w, h = coords
    return (round(x * sx), round(y * sy), round((x + w) * sx), round((y + h) * sy))


def main():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    CROP_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.open(PNG).convert("RGB")
    sx, sy = img.width / PPT_W, img.height / PPT_H

    regions = {
        "01_full_figure": (0, 0, 1600, 900),
        "02_left_initialization": (10, 5, 445, 820),
        "03_left_steps_4_5_red_group": (15, 430, 435, 330),
        "04_middle_population_controller": (470, 55, 480, 260),
        "05_middle_offspring_generator": (970, 55, 280, 395),
        "06_middle_eval_archive_front": (680, 335, 460, 490),
        "07_right_final_output": (1280, 10, 305, 810),
        "08_pareto_front_chart": (1300, 375, 285, 300),
        "09_bottom_legends": (0, 835, 1600, 65),
    }
    crops = []
    for name, box in regions.items():
        out = CROP_DIR / f"{name}.png"
        crop = img.crop(crop_box(box, sx, sy))
        crop.save(out)
        crops.append({"name": name, "path": str(out), "size": crop.size})

    thumbs = []
    for item in crops:
        crop = Image.open(item["path"]).convert("RGB")
        crop.thumbnail((520, 260))
        thumbs.append((item["name"], crop.copy()))
    pad = 18
    label_h = 28
    cols = 2
    cell_w = 560
    cell_h = 320
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell_w + pad, rows * cell_h + pad), "white")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except OSError:
        font = ImageFont.load_default()
    for idx, (name, crop) in enumerate(thumbs):
        col, row = idx % cols, idx // cols
        x = pad + col * cell_w
        y = pad + row * cell_h
        draw.text((x, y), name, fill=(12, 31, 58), font=font)
        sheet.paste(crop, (x, y + label_h))
        draw.rectangle((x, y + label_h, x + crop.width, y + label_h + crop.height), outline=(190, 190, 190), width=1)
    sheet.save(CONTACT)

    with zipfile.ZipFile(PPTX) as zf:
        names = zf.namelist()
        structure = {
            "pptx": str(PPTX),
            "slide_count": sum(1 for n in names if n.startswith("ppt/slides/slide") and n.endswith(".xml")),
            "embedded_media_count": sum(1 for n in names if n.startswith("ppt/media/")),
            "contains_editable_slide_xml": any(n == "ppt/slides/slide1.xml" for n in names),
            "media_files": [n for n in names if n.startswith("ppt/media/")],
        }
    STRUCTURE.write_text(json.dumps(structure, ensure_ascii=False, indent=2), encoding="utf-8")

    visual = {
        "wps_png": str(PNG),
        "image_size": img.size,
        "expected_aspect": "16:9",
        "crop_count": len(crops),
        "contact_sheet": str(CONTACT),
        "crops": crops,
        "manual_visual_review": {
            "text_overflow": "not observed in WPS export",
            "legend_clipping": "not observed after final pass",
            "arrow_label_collision": "not observed after final pass",
            "delivery_status": "PASS with stated L3-ish editable-shape boundary",
        },
    }
    VISUAL.write_text(json.dumps(visual, ensure_ascii=False, indent=2), encoding="utf-8")
    print(CONTACT)
    print(STRUCTURE)
    print(VISUAL)


if __name__ == "__main__":
    main()
