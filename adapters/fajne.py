"""FAJNE JEDLO (Tower) — weekly menu is published only as an image
(uploads/.../JEDLIS-TOWER-<MMDD>_<MMDD>.jpg). Returns ImageMenu so the runner
sends it to the vision model."""
import re

from core.common import ImageMenu, StaleMenuError

NAME = "FAJNE JEDLO"
URL = "https://fajnejedlo.sk/menu-tyzdnove-tower/"

IMG_RE = re.compile(
    r'https://fajnejedlo\.sk/wp-content/uploads/\d{4}/\d{2}/JEDLIS-TOWER-(\d{4})_(\d{4})\.jpe?g',
    re.I,
)


def scrape(ctx):
    html = ctx.fetch(URL).text
    matches = list(IMG_RE.finditer(html))
    if not matches:
        raise ValueError("JEDLIS-TOWER menu image not found")

    today_mmdd = ctx.target_date.strftime("%m%d")

    def covers_today(m):
        # filename tokens are DDMM (0706 = 6 July); reorder to MMDD to compare
        return _dm(m.group(1)) <= today_mmdd <= _dm(m.group(2))

    current = next((m for m in matches if covers_today(m)), None)
    if current is None:
        rng = f"{matches[0].group(1)}–{matches[0].group(2)}"
        raise StaleMenuError(f"menu image covers {rng} (DDMM), not today")

    img = ctx.fetch(current.group(0), headers={"Referer": URL}).content
    return ImageMenu(NAME, img, "image/jpeg", current.group(0))


def _dm(token: str) -> str:
    """Site encodes DDMM (0706 = 6 July) — reorder to MMDD for comparison."""
    return token[2:4] + token[0:2]
