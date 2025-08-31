from typing import List, Dict, Optional
from .base import LayoutStrategy


class MosaicLayoutStrategy(LayoutStrategy):
    """Mosaic layout: non-cropping, pattern-aware blocks (incl. narrow + two wide)."""

    @property
    def name(self) -> str:
        return "mosaic"

    @property
    def description(self) -> str:
        return "Mosaic grid without cropping; detects portrait + two landscape blocks"

    def select_hero_image(self, photos: List[Dict]) -> Optional[Dict]:
        if not photos:
            return None
        # Prefer strong, non-portrait, non-panoramic hero
        best = None
        best_score = -10**9
        for p in photos:
            md = p.get("metadata", {})
            dims = md.get("dimensions", {})
            hints = md.get("layout_hints", {})
            score = 0
            if not hints.get("is_portrait", False):
                score += 3
            if not hints.get("is_panoramic", False):
                score += 1
            w = dims.get("width", 0)
            if w > 3000:
                score += 2
            elif w > 2000:
                score += 1
            if score > best_score:
                best = p
                best_score = score
        return best or photos[0]

    def arrange_grid_photos(self, photos: List[Dict], max_per_grid: int = 9) -> List[List[Dict]]:
        # Not used for mosaic; return a single list for compatibility
        return [photos]

    def _ar(self, photo: Dict) -> float:
        md = photo.get("metadata", {})
        dims = md.get("dimensions", {})
        w = max(1, dims.get("width", 1))
        h = max(1, dims.get("height", 1))
        return float(w) / float(h)

    def _is_portrait(self, photo: Dict) -> bool:
        return self._ar(photo) < 0.9

    def _is_landscape(self, photo: Dict) -> bool:
        return self._ar(photo) > 1.2

    def _is_pano(self, photo: Dict) -> bool:
        return self._ar(photo) > 2.5 or photo.get("metadata", {}).get("layout_hints", {}).get("is_panoramic", False)

    def _build_blocks(self, photos: List[Dict]) -> List[Dict]:
        blocks = []
        i = 0
        n = len(photos)
        while i < n:
            p = photos[i]

            # Panoramic: its own full-width block
            if self._is_pano(p):
                blocks.append({"type": "full", "photos": [p]})
                i += 1
                continue

            # Portrait + two landscapes pattern
            if self._is_portrait(p) and i + 2 < n and self._is_landscape(photos[i + 1]) and self._is_landscape(photos[i + 2]):
                blocks.append({
                    "type": "narrow_two_wide",
                    "photos": [p, photos[i + 1], photos[i + 2]],
                })
                i += 3
                continue

            # Two portraits side-by-side
            if i + 1 < n and self._is_portrait(p) and self._is_portrait(photos[i + 1]):
                blocks.append({"type": "row2", "photos": [p, photos[i + 1]]})
                i += 2
                continue

            # Three regular images in a row
            if i + 2 < n:
                blocks.append({"type": "row3", "photos": [p, photos[i + 1], photos[i + 2]]})
                i += 3
                continue

            # Fallbacks for last 1-2 images
            if i + 1 < n:
                blocks.append({"type": "row2", "photos": [p, photos[i + 1]]})
                i += 2
            else:
                blocks.append({"type": "single", "photos": [p]})
                i += 1

        return blocks

    def generate_gallery_html(self, photos: List[Dict], title: str) -> str:
        if not photos:
            return ""

        # Hero first (non-cropping, just full-width image)
        hero = self.select_hero_image(photos)
        remaining = [p for p in photos if p is not hero]

        parts = []
        if hero:
            parts.append(
                f"""<div class=\"gallery\">\n    <div class=\"gallery-item full\">\n        {self._img(hero, title, loading="eager")}\n    </div>\n</div>"""
            )

        if remaining:
            blocks = self._build_blocks(remaining)
            html = ["<div class=\"gallery layout-strat-mosaic\">"]
            for blk in blocks:
                t = blk["type"]
                ph = blk["photos"]
                if t == "full":
                    html.append("    <div class=\"mosaic-block full\">")
                    html.append(f"        <div class=\"gallery-item\">{self._img(ph[0], title)}</div>")
                    html.append("    </div>")
                elif t == "narrow_two_wide":
                    html.append("    <div class=\"mosaic-block narrow-two-wide\">")
                    html.append("        <div class=\"col-left\">")
                    html.append(f"            <div class=\"gallery-item\">{self._img(ph[0], title)}</div>")
                    html.append("        </div>")
                    html.append("        <div class=\"col-right\">")
                    html.append(f"            <div class=\"gallery-item\">{self._img(ph[1], title)}</div>")
                    html.append(f"            <div class=\"gallery-item\">{self._img(ph[2], title)}</div>")
                    html.append("        </div>")
                    html.append("    </div>")
                elif t == "row3":
                    html.append("    <div class=\"mosaic-block row-3\">")
                    for p3 in ph:
                        html.append(f"        <div class=\"gallery-item\">{self._img(p3, title)}</div>")
                    html.append("    </div>")
                elif t == "row2":
                    html.append("    <div class=\"mosaic-block row-2\">")
                    for p2 in ph:
                        html.append(f"        <div class=\"gallery-item\">{self._img(p2, title)}</div>")
                    html.append("    </div>")
                else:  # single
                    html.append("    <div class=\"mosaic-block single\">")
                    html.append(f"        <div class=\"gallery-item\">{self._img(ph[0], title)}</div>")
                    html.append("    </div>")
            html.append("</div>")
            parts.append("\n".join(html))

        return "\n\n".join(parts)

    def _img(self, photo: Dict, alt_text: str, loading: str = "lazy", use_webp: bool = True) -> str:
        urls = photo.get("urls", {})
        md = photo.get("metadata", {})
        dims = md.get("dimensions", {})
        width = dims.get("width", 800)
        height = dims.get("height", 600)

        # Non-cropping: do not force container heights; let images size naturally.
        if use_webp and isinstance(next(iter(urls.values()), {}), dict):
            webp_srcset = []
            jpeg_srcset = []
            for size, fmt in urls.items():
                if isinstance(fmt, dict):
                    wv = int(str(size).replace("w", ""))
                    if "webp" in fmt:
                        webp_srcset.append(f"{fmt['webp']} {wv}w")
                    if "jpeg" in fmt:
                        jpeg_srcset.append(f"{fmt['jpeg']} {wv}w")
            fallback = ""
            for pref in ["1000w", "1500w", "2000w"]:
                if pref in urls and isinstance(urls[pref], dict) and "jpeg" in urls[pref]:
                    fallback = urls[pref]["jpeg"]
                    break
            if not fallback and urls:
                for fmt in urls.values():
                    if isinstance(fmt, dict) and "jpeg" in fmt:
                        fallback = fmt["jpeg"]
                        break
            return (
                f"<picture>\n"
                f"    <source type=\"image/webp\" srcset=\"{', '.join(webp_srcset)}\">\n"
                f"    <img src=\"{fallback}\" srcset=\"{', '.join(jpeg_srcset)}\" alt=\"{alt_text}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\">\n"
                f"</picture>"
            )
        else:
            srcset = []
            for size, url in urls.items():
                if isinstance(url, str):
                    wv = int(str(size).replace("w", ""))
                    srcset.append(f"{url} {wv}w")
            fallback = urls.get("1000w", "") or (next(iter(urls.values())) if urls else "")
            return (
                f"<img src=\"{fallback}\" srcset=\"{', '.join(srcset)}\" alt=\"{alt_text}\" width=\"{width}\" height=\"{height}\" loading=\"{loading}\">"
            )
