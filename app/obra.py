"""Ilustraciones de obra para el índice público y datos demo."""

from __future__ import annotations


SCENES: dict[str, tuple[str, str, str]] = {
    "albanileria": ("#b54a2a", "#d27a4a", "Muro de tabique"),
    "plomeria": ("#3d5a73", "#7ea0b8", "Tubería de cobre"),
    "electricidad": ("#c9a227", "#ead37a", "Tablero y conduit"),
    "carpinteria": ("#8a5a2b", "#c48a4e", "Entarimado"),
    "herreria": ("#4a4a4a", "#8d8d8d", "Reja de patio"),
    "pintura": ("#6d7a3a", "#c4c07a", "Muro recién pintado"),
    "pisos_azulejos": ("#6a5340", "#cbb79a", "Piso de barro"),
    "vidrieria_canceleria": ("#4d6d8a", "#b7c9d6", "Cancel de aluminio"),
    "tablaroca": ("#9a8f7a", "#e4dcc8", "Muro de tablaroca"),
    "impermeabilizacion": ("#5a4638", "#b08968", "Azotea sellada"),
}


def obra_svg(
    title: str,
    trade: str,
    zone: str,
    *,
    variant: int = 0,
) -> bytes:
    accent, wash, caption = SCENES.get(trade, ("#b54a2a", "#d27a4a", "Obra"))
    shift = (variant % 5) * 18
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 480" role="img" aria-label="{title} en {zone}">
  <rect width="640" height="480" fill="#f4ead6"/>
  <g stroke="#1e2433" stroke-width="1" fill="none" opacity="0.18">
    <path d="M0 40 H640 M0 80 H640 M0 120 H640 M0 160 H640 M0 200 H640 M0 240 H640 M0 280 H640 M0 320 H640 M0 360 H640 M0 400 H640 M0 440 H640"/>
    <path d="M40 0 V480 M80 0 V480 M120 0 V480 M160 0 V480 M200 0 V480 M240 0 V480 M280 0 V480 M320 0 V480 M360 0 V480 M400 0 V480 M440 0 V480 M480 0 V480 M520 0 V480 M560 0 V480 M600 0 V480"/>
  </g>
  <rect x="{48 + shift}" y="56" width="360" height="280" fill="{wash}" stroke="#1e2433" stroke-width="3"/>
  <rect x="{72 + shift}" y="80" width="312" height="232" fill="{accent}" stroke="#1e2433" stroke-width="2"/>
  <path d="M{88 + shift} 300 H{360 + shift} M{88 + shift} 252 H{360 + shift} M{88 + shift} 204 H{360 + shift} M{88 + shift} 156 H{360 + shift}" stroke="#1e2433" stroke-width="2" opacity="0.45"/>
  <rect x="{400 - shift}" y="188" width="168" height="148" fill="#f7f0e4" stroke="#1e2433" stroke-width="3"/>
  <path d="M{420 - shift} 220 h128 M{420 - shift} 252 h128 M{420 - shift} 284 h90" stroke="#1e2433" stroke-width="6" stroke-linecap="square"/>
  <rect x="24" y="372" width="592" height="84" fill="#1e2433"/>
  <text x="40" y="408" fill="#f4ead6" font-family="Archivo, Liberation Sans Narrow, sans-serif" font-size="22" font-weight="800" text-transform="uppercase">{title[:42]}</text>
  <text x="40" y="436" fill="#ead37a" font-family="Atkinson Hyperlegible Next, Liberation Sans, sans-serif" font-size="16">{caption} · zona {zone}</text>
</svg>
""".encode("utf-8")
