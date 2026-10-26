"""The committed sample.

A two-week slice of the kind of material the monitoring adapters return, so
El Boletin renders immediately from a fresh clone with no network and no
credentials -- which is what the teaching staff will run.

These are paraphrased composites of narratives the partner organisations
document circulating in Spanish-language channels. They are written here as
sample input, not quoted from any individual's post, and no account handles or
personal details appear. Timestamps are generated relative to today so the
brief always has a plausible window.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from models import SignalRecord

# (days_ago, platform, claim, reach, url)
SAMPLE: list[tuple[int, str, str, int, str]] = [
    (1, "WhatsApp", "Están instalando paneles solares en el barrio y cuando llegue el frío se va a ir la luz como pasó en Texas. No firmen nada.", 0, ""),
    (1, "Facebook", "El gobierno quiere quitarte la estufa de gas. Primero el carro, ahora la cocina. Así empieza el control.", 4200, "https://example.org/post/a1"),
    (2, "TikTok", "Las turbinas de viento en el mar están matando ballenas, por eso aparecen muertas en la playa.", 18800, "https://example.org/post/a2"),
    (2, "WhatsApp", "Las estelas que dejan los aviones son químicos para modificar el clima. Por eso llueve cuando no debe.", 0, ""),
    (3, "YouTube", "Los científicos dicen que hay crisis porque les pagan por decirlo. Es un negocio de miles de millones.", 9100, "https://example.org/post/a3"),
    (4, "Facebook", "China contamina diez veces más que nosotros. Lo que hagamos aquí no cambia nada, solo nos empobrece.", 6700, "https://example.org/post/a4"),
    (4, "WhatsApp", "El recibo de la luz subió por las renovables. Antes con el gas pagábamos menos.", 0, ""),
    (5, "X", "Hizo un frío histórico este invierno. ¿Dónde está el calentamiento global que tanto anuncian?", 23400, "https://example.org/post/a5"),
    (6, "Facebook", "Los carros eléctricos contaminan más que los de gasolina por la minería del litio. Es puro marketing.", 5100, "https://example.org/post/a6"),
    (7, "WhatsApp", "Si pides ayuda de FEMA después del huracán te preguntan el estatus migratorio y te reportan.", 0, ""),
    (8, "TikTok", "El calor de ahora es igual que siempre. Nuestros abuelos trabajaban en el campo sin aire acondicionado y no pasaba nada.", 31200, "https://example.org/post/a7"),
    (9, "Facebook", "Las reglas nuevas de descanso por calor para los trabajadores del campo solo van a hacer que los despidan.", 3300, "https://example.org/post/a8"),
    (10, "WhatsApp", "Cuidar el clima significa que ya no vas a poder comer la comida de tu cultura. Quieren quitarnos hasta eso.", 0, ""),
    (11, "X", "Los incendios los provocan pirómanos, no el cambio climático. Lo dicen para asustar.", 14900, "https://example.org/post/a9"),
    (12, "Facebook", "Con la captura de carbono podemos seguir usando petróleo sin problema. Ya está resuelto.", 2600, "https://example.org/post/a10"),
    (13, "WhatsApp", "El agua de la llave es segura en todos lados. Lo del plomo fue solo en Flint y ya se arregló.", 0, ""),
]


def collect(days: int = 14, limit: int = 60) -> list[SignalRecord]:
    now = datetime.now(timezone.utc)
    out = []
    for ago, platform, claim, reach, url in SAMPLE:
        if ago > days:
            continue
        out.append(SignalRecord(
            source="fixture",
            platform=platform,
            language="es",
            captured_at=(now - timedelta(days=ago, hours=ago * 2 % 11)).isoformat(),
            claim_text=claim,
            url=url,
            reach_estimate=reach or None,
        ))
    return out[:limit]
