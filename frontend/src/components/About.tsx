import { api } from "../api";
import { type Lang } from "../i18n";
import { Ajolota } from "./Ajolota";

/** Structured the way Millennial Lotería's about page moves: a full-bleed
 *  banner, then short explainer blocks that alternate with photographs rather
 *  than long prose. Ours carries a founder story, because this deck has one. */

const img = (name: string) => `${api.base}/assets/web/event/${name}.jpg`;

export function About({ lang }: { lang: Lang }) {
  const es = lang === "es";

  return (
    <section className="about">
      <figure className="about-banner">
        <img src={img("group-holding-cards")} alt={es
          ? "Un salón lleno de gente sosteniendo las cartas de la Lotería Climática"
          : "A room full of people holding up Climate Lotería cards"} />
      </figure>

      <div className="hero tight">
        <h1>{es ? "La historia" : "The story"}</h1>
        <p className="lede">
          {es
            ? "Esto empezó con un mazo de lotería en la mesa de mis abuelitos, y terminó en un salón lleno de gente levantando cartas sobre el clima."
            : "This started with a lotería deck on my grandparents' table, and ended up in a room full of people holding climate cards in the air."}
        </p>
      </div>

      <div className="about-block">
        <div>
          <h2>{es ? "¿Qué es la lotería?" : "What is lotería?"}</h2>
          <p>
            {es
              ? "Lotería es el juego que todos conocemos: alguien canta las cartas, los demás marcan su tabla con frijolitos, y el primero que la llena grita ¡Lotería! Lleva generaciones en nuestras casas, en las fiestas, en la sobremesa."
              : "Lotería is the game everybody already knows: somebody calls the cards, everyone else marks their board with beans, and the first to fill one shouts ¡Lotería! It has been in our houses for generations — at parties, at the table after dinner."}
          </p>
          <p>
            {es
              ? "Nosotros le cambiamos las cartas. Cada una trae un mito climático como la gente de verdad lo dice, la verdad con evidencia, y algo concreto que puedes hacer esta semana."
              : "We swapped the cards. Each one carries a climate myth the way people actually say it, the truth with evidence behind it, and one concrete thing you can do this week."}
          </p>
        </div>
        <figure>
          <img src={img("cards-on-easel")} alt={es ? "Cartas sobre una mesa" : "Cards displayed on a table"} />
        </figure>
      </div>

      <div className="about-block flip">
        <div>
          <h2>{es ? "El Valle" : "The Valley"}</h2>
          <p>
            {es
              ? "Soy del sur de Texas, del Río Grande Valley: esa franja donde el español y el inglés caen en la misma frase y donde nadie necesita que le expliquen el clima en abstracto. En el Valle el clima es el aire acondicionado que no alcanza, el recibo de la luz en agosto, la tormenta que inunda la calle de siempre, el tío que trabaja afuera todo el día."
              : "I'm from South Texas — the Rio Grande Valley, that stretch where Spanish and English land in the same sentence and nobody needs climate explained to them in the abstract. In the Valley, climate is the AC that can't keep up, the August electric bill, the storm that floods the same street every time, the tío who works outside all day."}
          </p>
          <p>
            {es
              ? "También es donde aprendí que la información que de verdad te mueve no llega en un reporte. Llega de tu mamá, de tu comadre, del grupo de WhatsApp de la familia. Por eso este proyecto vive donde vive."
              : "It's also where I learned that the information that actually moves you doesn't arrive in a report. It arrives from your mom, your comadre, the family WhatsApp group. That is why this project lives where it lives."}
          </p>
        </div>
        <figure>
          <img src={img("jp-speaking")} alt="Juan Pablo Alvarado" />
        </figure>
      </div>

      <div className="about-block">
        <div>
          <h2>{es ? "Las primeras doce cartas" : "The first twelve cards"}</h2>
          <p>
            {es
              ? "En GreenLatinos, y junto con Intersectional Environmentalist, creé las primeras doce cartas de la Lotería Climática. Las imprimimos, las pegamos en las paredes, las pusimos en caballetes y las llevamos a eventos donde la gente las levantó y se tomó fotos con ellas."
              : "At GreenLatinos, alongside Intersectional Environmentalist, I created the first twelve Climate Lotería cards. We printed them, taped them to walls, set them on easels, and took them to events where people picked them up and took pictures with them."}
          </p>
          <p>
            {es
              ? "En 2025, GreenLatinos y Resource Media probaron ese mensaje con 1,797 adultos latinos usando Grow Progress. El estudio midió qué marcos de valores mueven de verdad a nuestra gente: la salud, la familia y la fe funcionan; señalar villanos genéricos no. Ese dato enmarca cada carta nueva de este sitio."
              : "In 2025, GreenLatinos and Resource Media tested that messaging with 1,797 Latino adults using Grow Progress. The study measured which value frames actually move our people: health, family and faith work; naming generic villains does not. That data frames every new card on this site."}
          </p>
        </div>
        <figure>
          <img src={img("cards-in-window")} alt={es ? "Cartas pegadas en una ventana" : "Cards taped in a window"} />
        </figure>
      </div>

      <div className="about-block flip">
        <div>
          <h2>{es ? "Por qué una fábrica y no un folleto" : "Why a factory, not a pamphlet"}</h2>
          <p>
            {es
              ? "Doce cartas se hacen en meses. La desinformación cambia en días. Por eso este sitio no es un folleto: la gente pregunta, el sistema escucha lo que ninguna carta contesta, y fabrica la que falta — con evidencia citada, enmarcada por el estudio, y siempre revisada por una persona antes de publicarse."
              : "Twelve cards take months to make. Disinformation changes in days. So this site is not a pamphlet: people ask, the system notices what no card answers, and it manufactures the missing one — with cited evidence, framed by the study, and always reviewed by a person before it publishes."}
          </p>
          <p>
            {es
              ? "El mazo ampliado, el sistema de agentes y esta aplicación son un proyecto independiente, hecho como trabajo final de MGT 409 en Yale SOM."
              : "The expanded deck, the agent system and this application are an independent project, built as the final project for MGT 409 at Yale SOM."}
          </p>
        </div>
        <figure>
          <img src={img("card-on-pole")} alt={es ? "Una carta pegada en un poste" : "A card taped to a pole"} />
        </figure>
      </div>


      <div className="mascot-block">
        <div className="mascot-art">
          <Ajolota size={210} pose="waving" />
        </div>
        <div>
          <span className="tag">{es ? "La mascota" : "The mascot"}</span>
          <h2>{es ? "\u00bfPor qu\u00e9 una ajolota?" : "Why an axolotl?"}</h2>
          <p>
            {es
              ? "El ajolote es de aqu\u00ed. Vive \u2014apenas\u2014 en los canales de Xochimilco, lo que queda del sistema de chinampas que los mexicas construyeron sobre el lago. Su nombre viene del n\u00e1huatl: X\u00f3lotl, el dios que se convirti\u00f3 en ajolote para escapar del sacrificio. Es de las pocas criaturas que seguimos nombrando con la palabra que ya ten\u00eda antes de que llegara el espa\u00f1ol."
              : "The axolotl is from here. It lives \u2014 barely \u2014 in the canals of Xochimilco, what is left of the chinampa system the Mexica built out over the lake. Its name comes from Nahuatl: X\u00f3lotl, the god who turned himself into an axolotl to escape sacrifice. It is one of the few creatures we still call by the word it had before Spanish arrived."}
          </p>
          <p>
            {es
              ? "Tambi\u00e9n es un animal que regenera lo que pierde: una pata, parte del coraz\u00f3n, parte del cerebro. Y est\u00e1 en peligro cr\u00edtico en estado salvaje, por la contaminaci\u00f3n del agua, las especies invasoras y una ciudad que no dej\u00f3 de crecer. Esas dos cosas al mismo tiempo \u2014poder sanar y estar a punto de desaparecer\u2014 son exactamente la conversaci\u00f3n clim\u00e1tica que tenemos en nuestras familias."
              : "It is also an animal that regrows what it loses: a leg, part of its heart, part of its brain. And it is critically endangered in the wild, from water pollution, invasive species and a city that kept growing. Those two facts at once \u2014 able to heal, and nearly gone \u2014 are exactly the climate conversation we are having in our families."}
          </p>
          <p>
            {es
              ? "Por eso la Comadre Ajolota es quien contesta aqu\u00ed. No es una mascota bonita pegada encima del proyecto: es mexicana, es del agua, aguanta, y est\u00e1 en riesgo. Si alguien va a explicarte el clima en la mesa de tu casa, que sea alguien de los nuestros."
              : "That is why Comadre Ajolota is the one who answers here. She is not a cute mascot stuck on top of the project: she is Mexican, she is of the water, she endures, and she is at risk. If somebody is going to explain the climate at your kitchen table, let it be one of ours."}
          </p>
        </div>
      </div>

      <section className="credits">
        <div className="credits-head">
          <h2>{es ? "Cr\u00e9ditos" : "Credits"}</h2>
          <p className="credits-name">Juan Pablo Alvarado</p>
          <p className="credits-role">
            MBA, Yale School of Management
            <span className="sep">·</span>
            {es ? "Ex Program Manager, GreenLatinos" : "Former Program Manager, GreenLatinos"}
          </p>
        </div>
        <div className="credits-grid">
          <div className="credit-item">
            <span className="credit-k">{es ? "Las cartas 1\u201312" : "Cards 1\u201312"}</span>
            <p>{es
              ? "Creadas por Juan Pablo Alvarado en GreenLatinos, junto con Intersectional Environmentalist. Se muestran con cr\u00e9dito y con su arte original."
              : "Created by Juan Pablo Alvarado at GreenLatinos, with Intersectional Environmentalist. Shown with attribution and their original artwork."}</p>
          </div>
          <div className="credit-item">
            <span className="credit-k">{es ? "Las cartas 13\u201354" : "Cards 13\u201354"}</span>
            <p>{es
              ? "Fabricadas por el sistema de agentes de este sitio, con evidencia citada y revisi\u00f3n humana. No llevan ninguna marca de GreenLatinos."
              : "Manufactured by this site's agent system, with cited evidence and human review. They carry no GreenLatinos mark."}</p>
          </div>
          <div className="credit-item">
            <span className="credit-k">{es ? "Datos de mensajes" : "Message data"}</span>
            <p>{es
              ? "GreenLatinos y Resource Media, prueba con Grow Progress (2025): 1,797 adultos latinos."
              : "GreenLatinos and Resource Media, Grow Progress message test (2025): 1,797 Latino adults."}</p>
          </div>
          <div className="credit-item">
            <span className="credit-k">{es ? "Evidencia" : "Evidence"}</span>
            <p>{es
              ? "CAAD, Friends of the Earth, Climate Power En Acci\u00f3n, y las fuentes p\u00fablicas citadas en cada carta."
              : "CAAD, Friends of the Earth, Climate Power En Acci\u00f3n, and the public sources cited on each card."}</p>
          </div>
          <div className="credit-item">
            <span className="credit-k">{es ? "Fotos" : "Photography"}</span>
            <p>{es ? "Del equipo de la campa\u00f1a, del evento donde se usaron las cartas."
                   : "By the campaign team, from the event where the cards were used."}</p>
          </div>
          <div className="credit-item">
            <span className="credit-k">{es ? "La ajolota" : "The axolotl"}</span>
            <p>{es ? "Dibujada para este proyecto, en el mismo lenguaje visual que las cartas."
                   : "Drawn for this project, in the same visual language as the cards."}</p>
          </div>
        </div>
        <p className="source-note">
          {es ? "Sin afiliaci\u00f3n ni respaldo de" : "Not affiliated with or endorsed by"}{" "}
          GreenLatinos, CAAD, Friends of the Earth, Climate Power, Resource Media.
        </p>
      </section>
    </section>
  );
}
