"""The claim queue El Taller works through.

In production these arrive from the gap detector: what people actually asked La
Comadre and could not be answered, plus what El Boletin saw being pushed. This
file is the seeded equivalent, so the deck can be built before the ledger has
real traffic in it. Each entry is a narrative the partner organisations
document circulating in Spanish-language channels.

Keys are stable: a key already present in the deck is skipped, so the batch is
safe to re-run.
"""

from __future__ import annotations

# 42 claims. With the 12 extracted originals this makes a full 54-card deck.
# 42 claims. With the 12 extracted originals this makes a full 54-card deck.
QUEUE: list[tuple[str, str]] = [
    # --- first wave (cards 13-20) -------------------------------------------
    ("tax-hoax", "El cambio climático es un invento de los políticos para cobrarnos más impuestos."),
    ("ev-dirtier", "Los carros eléctricos contaminan más que los de gasolina por las baterías."),
    ("cold-snap", "Si todavía hace tanto frío en invierno, el calentamiento global no puede ser real."),
    ("wind-whales", "Las turbinas de viento en el mar están matando a las ballenas."),
    ("gas-stove", "Cocinar con gas natural es seguro y limpio, no afecta la salud de la familia."),
    ("china-blame", "China contamina muchísimo más, así que lo que hagamos aquí no cambia nada."),
    ("bills-up", "Las energías renovables son las que están subiendo el recibo de la luz."),

    # --- heat, health and the body ------------------------------------------
    ("ac-luxury", "El aire acondicionado es un lujo; nuestros abuelos aguantaban el calor sin quejarse."),
    ("farmworker-rules", "Las reglas de descanso por calor para los trabajadores del campo solo quitan trabajo."),
    ("heat-deaths", "Casi nadie se muere por el calor; eso lo exageran para asustarnos."),
    ("pregnancy-heat", "El calor extremo no le hace nada a una mujer embarazada ni al bebé."),
    ("asthma-kids", "El asma de los niños es por genética, no por el aire que respiran en el barrio."),
    ("smoke-ok", "El humo de los incendios solo molesta un rato, no es peligroso de verdad."),

    # --- weather and disaster ------------------------------------------------
    ("hurricanes-always", "Los huracanes siempre han existido; no tienen nada que ver con el clima."),
    ("floods-normal", "Las inundaciones son normales, nada más la gente construyó donde no debía."),
    ("drought-cycle", "La sequía es un ciclo natural, siempre ha pasado y siempre va a pasar."),
    ("fema-status", "Si pides ayuda después de un desastre te van a preguntar por tu estatus migratorio."),
    ("chemtrails", "Las estelas de los aviones son químicos que rocían para controlar el clima."),

    # --- air, water and land -------------------------------------------------
    ("warehouse-diesel", "Las bodegas y los camiones de diésel traen trabajo, el aire no se ve afectado."),
    ("refinery-neighbor", "Vivir cerca de una refinería no es más peligroso que vivir en cualquier otro lado."),
    ("lead-pipes", "El agua de la llave es segura en todos lados; lo del plomo fue solo en Flint."),
    ("pesticides-safe", "Los pesticidas que usan en el campo ya están aprobados, así que son seguros."),
    ("fracking-safe", "El fracking no contamina el agua de los pozos de las comunidades."),
    ("urban-heat", "Los árboles en la ciudad son adorno; no cambian la temperatura del barrio."),

    # --- energy, technology and its trade-offs -------------------------------
    ("heat-pump-cold", "Las bombas de calor no sirven en lugares donde de verdad hace frío."),
    ("nuclear-answer", "La energía nuclear es la solución perfecta y sin riesgos para el clima."),
    ("hydro-clean", "Las represas son energía totalmente limpia y no le hacen daño a nadie."),
    ("biofuel-clean", "Los biocombustibles son limpios porque vienen de plantas."),
    ("carbon-capture", "Con la captura de carbono podemos seguir quemando petróleo sin problema."),
    ("grid-blackouts", "Mientras más renovables pongan, más apagones vamos a tener."),

    # --- money, work and the household ---------------------------------------
    ("rebates-scam", "Los reembolsos del gobierno para la casa son un truco, al final sales perdiendo."),
    ("solar-scam", "Todos los que venden paneles solares son estafadores."),
    ("renter-stuck", "Si rentas no puedes hacer nada por el consumo de energía de tu casa."),
    ("green-jobs-fake", "Los trabajos verdes son mal pagados y no duran."),
    ("union-clean", "La energía limpia va a acabar con los trabajos de sindicato."),
    ("community-solar", "La energía solar solo es para los que son dueños de su casa."),

    # --- food, culture and the home ------------------------------------------
    ("meat-culture", "Cuidar el clima significa que ya no puedes comer la comida de tu cultura."),
    ("milpa-old", "Las formas de sembrar de nuestros abuelos ya no sirven para el clima de hoy."),

    # --- politics, power and trust -------------------------------------------
    ("scientists-paid", "Los científicos dicen eso porque les pagan por asustarnos."),
    ("climate-communism", "Lo del clima es una excusa para quitarnos la libertad y lo que tenemos."),
    ("vote-pointless", "Votar no cambia nada en temas de contaminación ni de energía."),
    ("migration-climate", "La gente que migra no tiene nada que ver con sequías ni con el clima."),
]

# Held for the next cycle. These are real narratives, but a deck is a deck:
# 54 cards is the form, so these wait for the gap detector to argue for
# them against what people are actually asking.
DEFERRED: list[tuple[str, str]] = [
    ("climate-anxiety", "Preocuparse por el clima es cosa de jóvenes dramáticos, no un problema real."),
    ("insurance-climate", "Las aseguradoras suben el precio por avaricia, no por el riesgo climático."),
    ("microplastics", "Los microplásticos no llegan a la comida, eso es exageración."),
    ("ocean-fish", "Los océanos son tan grandes que lo que hacemos no afecta la pesca."),
    ("hydrogen-hype", "El hidrógeno va a resolver todo y por eso no hace falta cambiar nada ahora."),
    ("mining-minerals", "Las baterías son limpias; la minería de litio no afecta a ninguna comunidad."),
    ("storage-impossible", "La energía solar no sirve porque no se puede guardar para la noche."),
    ("transit-waste", "El transporte público es un desperdicio de dinero en nuestras ciudades."),
    ("food-waste", "Tirar comida no tiene nada que ver con el cambio climático."),
    ("compost-dirty", "La composta solo atrae plagas y huele mal, no sirve de nada."),
    ("fast-fashion", "La ropa barata no tiene nada que ver con la contaminación."),
    ("offsets-greenwash", "Si una empresa compra bonos de carbono ya está resolviendo su contaminación."),
]
