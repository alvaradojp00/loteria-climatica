/** Every string the interface shows, in both languages.
 *  Spanish is the first-class version, not a toggle afterthought. */

export type Lang = "en" | "es";

type Dict = Record<string, { es: string; en: string }>;

export const CATEGORY: Dict = {
  community: { es: "comunidad", en: "community" },
  energy: { es: "energía", en: "energy" },
  food: { es: "comida", en: "food" },
  health: { es: "salud", en: "health" },
  justice: { es: "justicia", en: "justice" },
  land: { es: "tierra", en: "land" },
  waste: { es: "basura", en: "waste" },
  water: { es: "agua", en: "water" },
  general: { es: "general", en: "general" },
};

export const S: Dict = {
  // nav
  nav_home: { es: "Inicio", en: "Home" },
  nav_deck: { es: "La Lotería", en: "The Deck" },
  nav_ayuda: { es: "Pregúntale", en: "Ask" },
  nav_boletin: { es: "El Boletín", en: "The Brief" },
  nav_jugar: { es: "Jugar", en: "Play" },
  nav_recursos: { es: "Recursos", en: "Resources" },
  nav_about: { es: "La Historia", en: "The Story" },
  nav_taller: { es: "El Taller", en: "The Workshop" },

  // deck
  deck_lede: {
    es: "Un juego de lotería sobre el clima y la desinformación que llega a nuestras familias. Cada carta trae el mito como se dice, la verdad con evidencia, y algo concreto que puedes hacer.",
    en: "A lotería deck about climate change and the disinformation that reaches our families. Every card carries the myth as people say it, an evidence-backed truth, and one concrete thing you can do.",
  },
  all: { es: "Todas", en: "All" },
  card: { es: "carta", en: "card" },
  myth: { es: "Mito", en: "Myth" },
  truth: { es: "Verdad", en: "Truth" },
  action: { es: "Qué puedes hacer", en: "What you can do" },
  evidence: { es: "Evidencia", en: "Evidence" },
  close: { es: "Cerrar", en: "Close" },
  original_note: {
    es: "Carta original de la campaña, con su arte impreso.",
    en: "Original campaign card, shown with its printed artwork.",
  },
  generated_note: {
    es: "Carta hecha por el sistema a partir de un reclamo que la gente estaba preguntando.",
    en: "Card manufactured by the system from a claim people were actually asking about.",
  },
  pending: { es: "pendiente de revisión", en: "pending review" },
  download_card: { es: "Descargar", en: "Download" },

  // ask (comadre + contra)
  ask_title: { es: "Pregúntale a La Comadre", en: "Ask La Comadre" },
  ask_lede: {
    es: "Pega el mensaje que te reenviaron o escribe tu duda. Te decimos qué dice la evidencia, con qué técnica está armado, y te damos una respuesta lista para mandar.",
    en: "Paste the forward you received or just ask. We tell you what the evidence says, name the technique behind it, and hand you a reply you can send.",
  },
  ask_placeholder: {
    es: "Pega el mensaje aquí, o pregunta lo que quieras…",
    en: "Paste the message here, or just ask…",
  },
  send: { es: "Enviar", en: "Send" },
  thinking: { es: "Pensando…", en: "Thinking…" },
  use_example: { es: "Ver un ejemplo", en: "See an example" },
  reply_ready: { es: "Respuesta lista para mandar", en: "Ready to send" },
  say_this: { es: "Dile esto", en: "Say this" },
  one_move: { es: "Un paso esta semana", en: "One move this week" },
  copy: { es: "Copiar", en: "Copy" },
  copied: { es: "Copiado ✓", en: "Copied ✓" },
  technique: { es: "Técnica usada", en: "Technique used" },
  how_to_spot: { es: "Cómo reconocerla", en: "How to spot it" },
  safety_notice: { es: "Aviso de seguridad", en: "Safety notice" },
  hidden_text: {
    es: "Este mensaje traía texto escondido dirigido a sistemas de IA, invisible para quien lo lee en el teléfono. Lo tratamos como evidencia, no como instrucción.",
    en: "This message carried hidden text aimed at AI systems, invisible to a person reading it on a phone. We treated it as evidence, not instruction.",
  },
  enter_sends: { es: "Enter envía · Shift+Enter salto de línea", en: "Enter sends · Shift+Enter newline" },

  // brief
  brief_lede: {
    es: "Cada dos semanas: qué está circulando, con qué técnica está armado, y una frase que puedes decir en la mesa antes de que te llegue.",
    en: "Every two weeks: what is circulating, the technique behind it, and one line you can say at the table before it reaches you.",
  },
  say_first: { es: "Qué decir antes", en: "What to say first" },
  covered_by: { es: "Ya hay carta", en: "Covered by card" },
  no_card_yet: { es: "Ninguna carta cubre esto todavía.", en: "No card covers this yet." },
  read_further: { es: "Para leer más", en: "Read further" },
  no_brief: { es: "Todavía no hay boletín generado.", en: "No brief has been generated yet." },

  // play
  play_title: { es: "Juega y comparte", en: "Play and share" },
  play_lede: {
    es: "Descarga el mazo, imprime las tablas, y juega lotería con tu gente. Así es como la conversación empieza sin que nadie se sienta regañado.",
    en: "Download the deck, print the boards, and play lotería with your people. That is how the conversation starts without anyone feeling lectured.",
  },
  generate_boards: { es: "Generar 6 tablas", en: "Generate 6 boards" },
  new_boards: { es: "Otras 6 tablas", en: "Six more boards" },
  print_boards: { es: "Imprimir tablas", en: "Print the boards" },
  print_deck: { es: "Imprimir el mazo", en: "Print the deck" },
  download_deck: { es: "Descargar presentación", en: "Download slide deck" },
  choose_language: { es: "¿En qué idioma?", en: "Which language?" },
  deck_blurb: {
    es: "Una diapositiva por carta: el frente, el mito y la verdad, y el texto completo. Incluye la historia del proyecto.",
    en: "One slide per card: the front, the myth and truth face, and the full text. Includes the project story.",
  },
  in_spanish: { es: "En español", en: "In Spanish" },
  in_english: { es: "En inglés", en: "In English" },
  as_pdf: { es: "PDF", en: "PDF" },
  as_pptx: { es: "PowerPoint", en: "PowerPoint" },
  board: { es: "Tabla", en: "Board" },
  call_order: { es: "Orden para cantar", en: "Caller's order" },
  seed_note: {
    es: "Cada juego de tablas tiene un número. Con el mismo número salen las mismas tablas, para que puedas reimprimir el mismo set.",
    en: "Every set of boards has a number. The same number regenerates the same boards, so you can reprint the same set.",
  },
  how_to_play: { es: "Cómo se juega", en: "How to play" },
  caller_title: { es: "Que cante la Ajolota", en: "Let Ajolota call the game" },
  caller_lede: {
    es: "¿Nadie quiere cantar? Ella lo hace. Saca las cartas una por una, lee el mito y la verdad, y le da una pregunta a la mesa para que la plática siga.",
    en: "Nobody wants to be the caller? She'll do it. She pulls the cards one by one, reads the myth and the truth, and hands the table a question to keep the conversation going.",
  },
  start_calling: { es: "Empezar a cantar", en: "Start calling" },
  how_to_play_body: {
    es: "Una persona canta las cartas en orden. Los demás marcan con frijolitos, monedas o piedritas. El que llena su tabla grita ¡Lotería! Lee en voz alta el mito y la verdad de cada carta que cantes: ahí está el juego de verdad.",
    en: "One person calls the cards in order. Everyone else marks their board with beans, coins or pebbles. First to fill a board shouts ¡Lotería! Read the myth and the truth aloud as you call each card — that is where the real game is.",
  },

  // admin
  admin_title: { es: "El Taller de Cartas", en: "El Taller de Cartas" },
  admin_sub: {
    es: "Área de operación. Aquí se ven los huecos, se fabrican cartas y se aprueban.",
    en: "Operator area. The gap queue, the factory, and approvals.",
  },
  password: { es: "Contraseña", en: "Password" },
  enter: { es: "Entrar", en: "Enter" },
  wrong_password: { es: "Contraseña incorrecta.", en: "Wrong password." },
  sign_out: { es: "Salir", en: "Sign out" },

  // misc
  backend_down: {
    es: "No encuentro el servidor. Córrelo con: uvicorn main:app --port 8010",
    en: "Backend not reachable. Start it with: uvicorn main:app --port 8010",
  },
};

export function t(key: string, lang: Lang): string {
  const entry = S[key] ?? CATEGORY[key];
  return entry ? entry[lang] : key;
}

export function category(name: string, lang: Lang): string {
  return CATEGORY[name] ? CATEGORY[name][lang] : name;
}
