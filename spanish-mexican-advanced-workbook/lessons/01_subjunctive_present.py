import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from workbook_engine import run_exercises, choose_translation

translation_exercises = [
    {
        "question": "Translate: 'I want you to try the mole poblano.'",
        "answer": ["Quiero que pruebes el mole poblano", "Quiero que pruebes el mole poblano."],
        "hint": "Use querer que + subjunctive",
        "explanation": "'Querer que' triggers the subjunctive because you desire an action from someone else. 'Pruebes' is the present subjunctive of 'probar'. Mole poblano is a quintessential Mexican dish from Puebla.",
        "context": "Volitional verb: querer que"
    },
    {
        "question": "Translate: 'The chef demands that we use fresh chiles from Oaxaca.'",
        "answer": ["El chef exige que usemos chiles frescos de Oaxaca", "El chef exige que usemos chiles frescos de Oaxaca."],
        "hint": "Exigir que + subjunctive; 'usemos' from 'usar'",
        "explanation": "'Exigir que' (to demand that) is a strong volitional verb requiring the subjunctive. 'Usemos' is the present subjunctive of 'usar' for nosotros. Oaxaca is famous for its chiles, especially chile pasilla and chile chilcostle.",
        "context": "Volitional verb: exigir que"
    },
    {
        "question": "Translate: 'I suggest that you (formal) visit San Miguel de Allende.'",
        "answer": ["Sugiero que visite San Miguel de Allende", "Sugiero que usted visite San Miguel de Allende", "Sugiero que visite San Miguel de Allende."],
        "hint": "Sugerir que + subjunctive; 'visite' from 'visitar' for usted",
        "explanation": "'Sugerir que' triggers subjunctive. Note the stem change e→ie in 'sugiero' but the subjunctive 'visite' is regular. San Miguel de Allende is a UNESCO World Heritage city in Guanajuato popular with both Mexican and international visitors.",
        "context": "Volitional verb: sugerir que"
    },
    {
        "question": "Translate: 'The doctor recommends that I drink herbal tea for my stomach.'",
        "answer": ["El médico recomienda que yo tome té de hierbas para el estómago", "El doctor recomienda que yo tome té de hierbas para el estómago", "El médico recomienda que yo tome té de hierbas para mi estómago", "El doctor recomienda que yo tome té de hierbas para mi estómago"],
        "hint": "Recomendar que + subjunctive; 'tome' from 'tomar'",
        "explanation": "'Recomendar que' requires subjunctive. In Mexican Spanish, 'té de hierbas' (herbal tea) is a common home remedy, and 'tome' is the subjunctive of 'tomar' — the preferred verb for consuming beverages in Mexico (over 'beber').",
        "context": "Volitional verb: recomendar que"
    },
    {
        "question": "Translate: 'I hope that the parade in Zacatecas is spectacular.'",
        "answer": ["Espero que el desfile en Zacatecas sea espectacular", "Espero que la paradadesfile en Zacatecas sea espectacular", "Espero que el desfile en Zacatecas sea espectacular."],
        "hint": "Esperar que + subjunctive; 'sea' from 'ser'",
        "explanation": "'Esperar que' (to hope that) is an emotion verb that triggers subjunctive because it expresses desire/expectation about something uncertain. 'Sea' is the subjunctive of 'ser'. Zacatecas hosts a famous annual fair (Feria Nacional de Zacatecas).",
        "context": "Emotion verb: esperar que"
    },
    {
        "question": "Translate: 'It bothers me that they always arrive late to the posada.'",
        "answer": ["Me molesta que siempre lleguen tarde a la posada", "Me molesta que siempre lleguen tarde a la posada."],
        "hint": "Molestar que + subjunctive; 'lleguen' from 'llegar'",
        "explanation": "'Molestar que' expresses annoyance — an emotional reaction triggering subjunctive. 'Lleguen' is the subjunctive of 'llegar'. A 'posada' is a traditional Mexican Christmas celebration reenacting Mary and Joseph's search for lodging.",
        "context": "Emotion verb: molestar que"
    },
    {
        "question": "Translate: 'I'm glad that you like the tamales from the market.'",
        "answer": ["Me alegra que te gusten los tamales del mercado", "Me alegra que te gusten los tamales del mercado."],
        "hint": "Alegrar que + subjunctive; 'gusten' from 'gustar'",
        "explanation": "'Alegrar que' (to make glad that) expresses happiness about someone else's situation, triggering subjunctive. 'Gusten' is plural subjunctive of 'gustar' because 'los tamales' is plural. Mexican tamales vary by region — Oaxacan, Yucatecan, and DF-style are all different.",
        "context": "Emotion verb: alegrar que"
    },
    {
        "question": "Translate: 'I fear that the rainy season will damage the avocado crop.'",
        "answer": ["Temo que la temporada de lluvias dañe la cosecha de aguacate", "Temo que la temporada de lluvias dañe la cosecha de aguacates", "Temo que la temporada de lluvias dañe la cosecha de aguacate."],
        "hint": "Temer que + subjunctive; 'dañe' from 'dañar'",
        "explanation": "'Temer que' (to fear that) triggers subjunctive because it expresses doubt or emotional concern. 'Dañe' is the subjunctive of 'dañar'. Mexico is the world's largest avocado producer, especially Michoacán, making this a culturally relevant example.",
        "context": "Emotion verb: temer que"
    },
    {
        "question": "Translate: 'I doubt that the chilaquiles here are better than my grandmother's.'",
        "answer": ["Dudo que los chilaquiles de aquí sean mejores que los de mi abuela", "Dudo que los chilaquiles de aquí sean mejores que los de mi abuela."],
        "hint": "Dudar que + subjunctive; 'sean' from 'ser'",
        "explanation": "'Dudar que' (to doubt that) is a classic subjunctive trigger expressing uncertainty. 'Sean' is the subjunctive of 'ser'. Chilaquiles — tortilla chips simmered in salsa — are a beloved Mexican breakfast dish, and every Mexican family claims their recipe is the best.",
        "context": "Doubt/certainty: dudar que"
    },
    {
        "question": "Translate: 'I don't believe that the metro is faster than the pesero.'",
        "answer": ["No creo que el metro sea más rápido que el pesero", "No creo que el metro sea más rápido que el pesero."],
        "hint": "No creer que + subjunctive; 'sea' from 'ser'",
        "explanation": "'No creer que' (to not believe that) triggers subjunctive because negating belief creates doubt. Note: 'creer que' in the affirmative takes indicative. 'Pesero' or 'microbús' is Mexican Spanish for the small buses common in Mexico City — 'colectivo' is Argentine usage.",
        "context": "Doubt/certainty: no creer que"
    },
    {
        "question": "Translate: 'It's possible that the mercado is closed for Independence Day.'",
        "answer": ["Es posible que el mercado esté cerrado por el Día de la Independencia", "Es posible que el mercado esté cerrado por el Día de la Independencia."],
        "hint": "Es posible que + subjunctive; 'esté' from 'estar'",
        "explanation": "'Es posible que' triggers subjunctive because it expresses possibility/doubt. 'Esté' is subjunctive of 'estar'. Mexico's Independence Day (September 16) is one of the most important national holidays — markets and businesses often close for the 'grito' celebrations.",
        "context": "Doubt/certainty: es posible que"
    },
    {
        "question": "Translate: 'Perhaps the tlacuache is hiding in the rooftop garden.'",
        "answer": ["Quizás el tlacuache se esconda en el jardín de la azotea", "Quizá el tlacuache se esconda en el jardín de la azotea", "Quizás el tlacuache se esconda en el jardín de la azotea."],
        "hint": "Quizás/quizá + subjunctive; 'se esconda' from 'esconderse'",
        "explanation": "'Quizás' or 'quizá' (perhaps) triggers subjunctive when referring to future or uncertain events. 'Se esconda' is the subjunctive of 'esconderse'. A 'tlacuache' (opossum) is a Nahuatl-derived word used throughout Mexico. 'Azotea' is the rooftop common in Mexican homes.",
        "context": "Doubt/certainty: quizás"
    },
    {
        "question": "Translate: 'It's necessary that we reserve a table at the cantina.'",
        "answer": ["Es necesario que reservemos una mesa en la cantina", "Es necesario que reservemos una mesa en la cantina."],
        "hint": "Es necesario que + subjunctive; 'reservemos' from 'reservar'",
        "explanation": "'Es necesario que' is an impersonal expression requiring subjunctive. 'Reservemos' is the nosotros subjunctive of 'reservar'. In Mexico, a 'cantina' is a traditional bar — not just any restaurant — often with a machismo heritage, though many are now modernized.",
        "context": "Impersonal expression: es necesario que"
    },
    {
        "question": "Translate: 'It's important that you (informal) learn to make salsa verde.'",
        "answer": ["Es importante que aprendas a hacer salsa verde", "Es importante que aprendas a hacer salsa verde."],
        "hint": "Es importante que + subjunctive; 'aprendas' from 'aprender'",
        "explanation": "'Es importante que' triggers subjunctive. 'Aprendas' is the subjunctive of 'aprender'. Salsa verde — made with tomatillos, serrano chiles, and cilantro — is a staple of Mexican cuisine, far more common in daily life than salsa roja.",
        "context": "Impersonal expression: es importante que"
    },
    {
        "question": "Translate: 'It's better that we take the pesero instead of the taxi.'",
        "answer": ["Es mejor que tomemos el pesero en vez del taxi", "Es mejor que tomemos el pesero en lugar del taxi", "Es mejor que tomemos el pesero en vez del taxi."],
        "hint": "Es mejor que + subjunctive; 'tomemos' from 'tomar'",
        "explanation": "'Es mejor que' triggers subjunctive. 'Tomemos' is the nosotros subjunctive of 'tomar' — the preferred verb for transportation in Mexico. 'En vez de' and 'en lugar de' both mean 'instead of'. 'Pesero' is uniquely Mexican Spanish for a small bus.",
        "context": "Impersonal expression: es mejor que"
    },
    {
        "question": "Translate: 'I ask that you (formal) sign the document before the notario.'",
        "answer": ["Le pido que firme el documento ante el notario", "Le pido que usted firme el documento ante el notario", "Le pido que firme el documento ante el notario."],
        "hint": "Pedir que + subjunctive; 'firme' from 'firmar' for usted",
        "explanation": "'Pedir que' (to ask/request that) triggers subjunctive. 'Firme' is the usted subjunctive of 'firmar'. The 'notario público' in Mexico holds a much more powerful legal role than in English-speaking countries — they are lawyers appointed by the state.",
        "context": "Volitional verb: pedir que"
    },
    {
        "question": "Translate: 'I beg that you (formal) help me find the mercado.'",
        "answer": ["Le ruego que me ayude a encontrar el mercado", "Le ruego que me ayude a encontrar el mercado.", "Ruego que usted me ayude a encontrar el mercado"],
        "hint": "Rogar que + subjunctive; 'ayude' from 'ayudar'",
        "explanation": "'Rogar que' (to beg/plead that) is a strong volitional verb triggering subjunctive. 'Ayude' is the usted subjunctive of 'ayudar'. 'Mercado' in Mexico refers to the traditional covered markets found in every neighborhood — not a supermarket.",
        "context": "Volitional verb: rogar que"
    },
    {
        "question": "Translate: 'The boss orders that we deliver the report before cinco de mayo.'",
        "answer": ["El jefe manda que entreguemos el informe antes del cinco de mayo", "El jefe ordena que entreguemos el informe antes del cinco de mayo"],
        "hint": "Mandar que / ordenar que + subjunctive; 'entreguemos' from 'entregar'",
        "explanation": "'Mandar que' and 'ordenar que' both mean 'to order that' and require subjunctive. 'Entreguemos' is the nosotros subjunctive. Cinco de mayo commemorates the Battle of Puebla (1862) — far more significant in Puebla than in the US.",
        "context": "Volitional verb: mandar que / ordenar que"
    },
    {
        "question": "Translate: 'They prohibit that we park near the zócalo.'",
        "answer": ["Prohíben que nos estacionemos cerca del zócalo", "Prohíben que aparquemos cerca del zócalo", "Prohíben que nos estacionemos cerca del zócalo."],
        "hint": "Prohibir que + subjunctive; 'estacionemos' from 'estacionarse'",
        "explanation": "'Prohibir que' (to prohibit that) triggers subjunctive. In Mexican Spanish, 'estacionarse' is used for parking a car (not 'aparcar', which is more Peninsular). The 'zócalo' is the main plaza in any Mexican city.",
        "context": "Volitional verb: prohibir que"
    },
    {
        "question": "Translate: 'My mother insists that I come home early for Las Posadas.'",
        "answer": ["Mi mamá insiste en que yo llegue temprano a casa para Las Posadas", "Mi mamá insiste en que llegue temprano a casa para Las Posadas"],
        "hint": "Insistir en que + subjunctive; 'llegue' from 'llegar'",
        "explanation": "'Insistir en que' (note the preposition 'en') triggers subjunctive when there's a subject change. 'Llegue' is the subjunctive of 'llegar'. Las Posadas (Dec 16-24) are the nine nights before Christmas, reenacting Mary and Joseph seeking shelter — a deeply Mexican tradition.",
        "context": "Volitional verb: insistir en que"
    },
    {
        "question": "Translate: 'I advise that you (informal) try the tacos al pastor at El Huequito.'",
        "answer": ["Te aconsejo que pruebes los tacos al pastor en El Huequito", "Aconsejo que pruebes los tacos al pastor en El Huequito"],
        "hint": "Aconsejar que + subjunctive; 'pruebes' from 'probar'",
        "explanation": "'Aconsejar que' (to advise that) triggers subjunctive. 'Pruebes' is the subjunctive of 'probar' (with stem change o→ue). Tacos al pastor — spit-roasted pork with pineapple — are iconic CDMX street food. El Huequito is a legendary taquería near the Zócalo.",
        "context": "Volitional verb: aconsejar que"
    },
    {
        "question": "Translate: 'It surprises me that she speaks Nahuatl so well.'",
        "answer": ["Me sorprende que ella hable náhuatl tan bien", "Me sorprende que hable náhuatl tan bien"],
        "hint": "Sorprender que + subjunctive; 'hable' from 'hablar'",
        "explanation": "'Sorprender que' (to surprise that) is an emotion verb triggering subjunctive. 'Hable' is the subjunctive of 'hablar'. Nahuatl is the most widely spoken indigenous language in Mexico, with over a million speakers, especially in Veracruz, Puebla, and Guerrero.",
        "context": "Emotion verb: sorprender que"
    },
    {
        "question": "Translate: 'I like that you (informal) prepare horchata for the fiesta.'",
        "answer": ["Me gusta que prepares horchata para la fiesta", "Me gusta que prepares horchata para la fiesta."],
        "hint": "Gustar que + subjunctive; 'prepares' from 'preparar'",
        "explanation": "'Gustar que' (to like/please that) triggers subjunctive because it expresses an emotional reaction to someone else's action. 'Prepares' is the subjunctive of 'preparar'. Horchata — rice water with cinnamon — is one of the three classic aguas frescas (along with jamaica and tamarindo) found at every Mexican fiesta.",
        "context": "Emotion verb: gustar que"
    },
    {
        "question": "Translate: 'It scares me that the earthquakes are so frequent in CDMX.'",
        "answer": ["Me da miedo que los sismos sean tan frecuentes en la CDMX", "Me da miedo que los terremotos sean tan frecuentes en la CDMX", "Me da miedo que los sismos sean tan frecuentes en CDMX"],
        "hint": "Dar miedo que + subjunctive; 'sean' from 'ser'",
        "explanation": "'Dar miedo que' (to frighten that) triggers subjunctive. 'Sean' is the subjunctive of 'ser'. In Mexican Spanish, 'sismo' is preferred over 'terremoto' for earthquakes. CDMX sits on a dry lakebed, making it seismically vulnerable — the 1985 and 2017 quakes are seared in national memory.",
        "context": "Emotion verb: dar miedo que"
    },
    {
        "question": "Translate: 'It matters to me that they respect our traditions on Día de Reyes.'",
        "answer": ["Me importa que respeten nuestras tradiciones el Día de Reyes", "Me importa que respeten nuestras tradiciones en el Día de Reyes"],
        "hint": "Importar que + subjunctive; 'respeten' from 'respetar'",
        "explanation": "'Importar que' (to matter that) triggers subjunctive because it expresses an emotional stance. 'Respeten' is the subjunctive of 'respetar'. Día de Reyes (Jan 6) is when Mexican children traditionally receive gifts from the Three Wise Men — the rosca de reyes is shared with hot chocolate.",
        "context": "Emotion verb: importar que"
    },
    {
        "question": "Translate: 'It fascinates me that they make cochinita pibil underground in Mérida.'",
        "answer": ["Me fascina que hagan cochinita pibil bajo tierra en Mérida", "Me fascina que preparen cochinita pibil bajo tierra en Mérida"],
        "hint": "Fascinar que + subjunctive; 'hagan' from 'hacer'",
        "explanation": "'Fascinar que' (to fascinate that) triggers subjunctive. 'Hagan' is the subjunctive of 'hacer'. Traditional cochinita pibil is wrapped in banana leaves and cooked in an underground pit (píib) — a Yucatecan Maya technique. Mérida is the culinary capital of the Yucatán.",
        "context": "Emotion verb: fascinar que"
    },
    {
        "question": "Translate: 'It annoys me that the chilaquiles at this fondita are always cold.'",
        "answer": ["Me fastidia que los chilaquiles de esta fondita siempre estén fríos", "Me fastidia que los chilaquiles de esta fondita siempre estén fríos."],
        "hint": "Fastidiar que + subjunctive; 'estén' from 'estar'",
        "explanation": "'Fastidiar que' (to annoy/irritate that) triggers subjunctive. 'Estén' is the subjunctive of 'estar'. A 'fondita' is a small, inexpensive Mexican eatery — the diminutive of 'fonda'. Chilaquiles should be served hot and freshly made; cold chilaquiles are a culinary sin in Mexico.",
        "context": "Emotion verb: fastidiar que"
    },
    {
        "question": "Translate: 'I'm not sure that the pulque is from Hidalgo.'",
        "answer": ["No estoy seguro de que el pulque sea de Hidalgo", "No estoy seguro de que el pulque sea de Hidalgo."],
        "hint": "No estar seguro de que + subjunctive; 'sea' from 'ser'",
        "explanation": "'No estar seguro de que' (to not be sure that) triggers subjunctive because it expresses doubt. 'Sea' is the subjunctive of 'ser'. Pulque — fermented agave sap — is a pre-Columbian drink from central Mexico, especially Hidalgo and Tlaxcala, now enjoying a renaissance in CDMX pulquerías.",
        "context": "Doubt: no estar seguro que"
    },
    {
        "question": "Translate: 'It's probable that the tamales sell out before noon.'",
        "answer": ["Es probable que los tamales se agoten antes del mediodía", "Es probable que los tamales se acaben antes del mediodía"],
        "hint": "Es probable que + subjunctive; 'se agoten' from 'agotarse'",
        "explanation": "'Es probable que' triggers subjunctive because it expresses probability/doubt. 'Se agoten' is the subjunctive of 'agotarse' (to sell out/run out). In Mexico, tamales from a good puesto disappear fast — especially on weekends. 'Se acaben' is also valid.",
        "context": "Doubt: es probable que"
    },
    {
        "question": "Translate: 'Perhaps the elote stand is on this corner.'",
        "answer": ["Puede que el puesto de elote esté en esta esquina", "Puede que el puesto de elotes esté en esta esquina", "Tal vez el puesto de elote esté en esta esquina"],
        "hint": "Puede que / tal vez + subjunctive; 'esté' from 'estar'",
        "explanation": "'Puede que' and 'tal vez' both trigger subjunctive for uncertain situations. 'Esté' is the subjunctive of 'estar'. 'Elote' (corn on the cob) is sold at street stands with mayonnaise, chile, lime, and cheese — a beloved CDMX snack. 'Esquina' means corner.",
        "context": "Doubt: puede que / tal vez"
    },
    {
        "question": "Translate: 'Could it be that the esquites vendor went home already?'",
        "answer": ["Acaso el vendedor de esquites ya se haya ido a casa", "Acaso la señora de los esquites ya se haya ido"],
        "hint": "Acaso + subjunctive; 'se haya ido' from 'irse'",
        "explanation": "'Acaso' in questions means 'could it be that' and triggers subjunctive. 'Se haya ido' is the present perfect subjunctive of 'irse'. Esquites are corn kernels served in a cup with chile, lime, and mayo — the cup version of elote. Street vendors (usually women) set up in the evenings.",
        "context": "Doubt: acaso"
    },
    {
        "question": "Translate: 'It's strange that there's no atole at the posada this year.'",
        "answer": ["Es raro que no haya atole en la posada este año", "Es raro que no haya atole en la posada este año."],
        "hint": "Es raro que + subjunctive; 'haya' from 'haber'",
        "explanation": "'Es raro que' (it's strange that) triggers subjunctive as an impersonal expression of doubt/surprise. 'Haya' is the subjunctive of 'haber'. Atole — a hot corn-based drink — is essential at Las Posadas and Día de los Muertos; its absence would be truly rare.",
        "context": "Impersonal expression: es raro que"
    },
    {
        "question": "Translate: 'It's curious that Guadalajara has so many murals.'",
        "answer": ["Es curioso que Guadalajara tenga tantos murales", "Es curioso que Guadalajara tenga tantos murales."],
        "hint": "Es curioso que + subjunctive; 'tenga' from 'tener'",
        "explanation": "'Es curioso que' (it's curious that) triggers subjunctive. 'Tenga' is the subjunctive of 'tener'. Guadalajara, Mexico's second city, is a hub of muralism — José Clemente Orozco's works in the Hospicio Cabañas are UNESCO-listed. It also has a vibrant modern street art scene.",
        "context": "Impersonal expression: es curioso que"
    },
    {
        "question": "Translate: 'It's a shame that the museum is closed on Mondays.'",
        "answer": ["Es una lástima que el museo esté cerrado los lunes", "Es una lástima que el museo esté cerrado los lunes."],
        "hint": "Es una lástima que + subjunctive; 'esté' from 'estar'",
        "explanation": "'Es una lástima que' (it's a shame/pity that) triggers subjunctive. 'Esté' is the subjunctive of 'estar'. Most Mexican museums, including the famous Museo Nacional de Antropología in CDMX, close on Mondays — a source of disappointment for many tourists.",
        "context": "Impersonal expression: es una lástima que"
    },
    {
        "question": "Translate: 'It's necessary that we wake up early for the tianguis.'",
        "answer": ["Es necesario que nos levantemos temprano para el tianguis", "Es necesario que nos levantemos temprano para el tianguis."],
        "hint": "Es necesario que + subjunctive; 'nos levantemos' from 'levantarse'",
        "explanation": "'Es necesario que' triggers subjunctive. 'Nos levantemos' is the nosotros subjunctive of 'levantarse'. A 'tianguis' is a traditional open-air market held on specific days — from Nahuatl 'tianquiztli'. The Jamaica Market tianguis in CDMX is one of the largest.",
        "context": "Impersonal expression: es necesario que"
    },
    {
        "question": "Translate: 'It's advisable that you (informal) drink jamaica water to stay hydrated.'",
        "answer": ["Conviene que tomes agua de jamaica para mantenerte hidratado", "Conviene que tomes agua de jamaica para mantenerte hidratada", "Conviene que bebas agua de jamaica para mantenerte hidratado"],
        "hint": "Conviene que + subjunctive; 'tomes' from 'tomar'",
        "explanation": "'Conviene que' (it's advisable that) triggers subjunctive. 'Tomes' is the subjunctive of 'tomar'. 'Agua de jamaica' (hibiscus water) is one of Mexico's three classic aguas frescas — refreshing, tart, and naturally ruby-red. 'Tomar' is the Mexican verb for drinking.",
        "context": "Impersonal expression: conviene que"
    },
    {
        "question": "Translate: 'It's urgent that we leave before the traffic gets bad in Monterrey.'",
        "answer": ["Es urgente que salgamos antes de que el tráfico empeore en Monterrey", "Es urgente que nos vayamos antes de que el tráfico empeore en Monterrey"],
        "hint": "Es urgente que + subjunctive; 'salgamos' from 'salir'",
        "explanation": "'Es urgente que' triggers subjunctive. 'Salgamos' is the nosotros subjunctive of 'salir' (irregular: salgo, sales, sale, salimos, salen → salga, salgas, salga, salgamos, salgan). Note the second subjunctive 'empeore' in 'antes de que el tráfico empeore' — 'antes de que' also triggers subjunctive. Monterrey's traffic is notoriously bad.",
        "context": "Impersonal expression: es urgente que"
    },
    {
        "question": "Translate: 'Let him come in!' (using Que + subjunctive as a command)",
        "answer": ["Que pase", "Que entre", "¡Que pase!", "¡Que entre!"],
        "hint": "Que + subjunctive for third-person commands",
        "explanation": "'Que + subjunctive' is used for indirect/ third-person commands in Spanish. 'Que pase' or 'que entre' both mean 'let him/her come in.' This is extremely common in Mexican homes and offices. 'Pase' is from 'pasar' and 'entre' from 'entrar'.",
        "context": "Negative/indirect commands: Que + subjunctive"
    },
    {
        "question": "Translate: 'Let her leave right now!' (using Que + subjunctive)",
        "answer": ["Que se vaya ahora mismo", "¡Que se vaya ahora mismo!", "Que se vaya en este momento"],
        "hint": "Que + subjunctive; 'se vaya' from 'irse'",
        "explanation": "'Que se vaya' uses the subjunctive of 'irse' (to leave) as a third-person command. This construction is common when giving orders about someone who isn't present or when someone else is the authority. '¡Que se vaya!' is emphatic and direct.",
        "context": "Negative/indirect commands: Que + subjunctive"
    },
    {
        "question": "Translate: 'Let the doctor see the patient first.' (using Que + subjunctive)",
        "answer": ["Que el doctor vea al paciente primero", "Que el doctor pase al paciente primero", "Que el médico vea al paciente primero"],
        "hint": "Que + subjunctive; 'vea' from 'ver'",
        "explanation": "'Que el doctor vea' uses the subjunctive of 'ver' (veo, ves, ve, vemos, ven → vea, veas, vea, veamos, vean). This indirect command structure is used in hospitals and clinics across Mexico. 'Pase al paciente' (let the patient through) is also very natural.",
        "context": "Negative/indirect commands: Que + subjunctive"
    },
    {
        "question": "Translate: 'Let them eat first since they haven't had chilaquiles all morning.'",
        "answer": ["Que coman primero, porque no han probado chilaquiles en toda la mañana", "Que coman primero que no han probado chilaquiles en toda la mañana"],
        "hint": "Que + subjunctive for third-person commands",
        "explanation": "'Que coman' uses the subjunctive of 'comer' as a third-person command. This is the natural way to say 'let them eat' in Mexican Spanish. Chilaquiles are a quintessential Mexican breakfast — tortilla chips in green or red salsa — and skipping them would be unusual.",
        "context": "Negative/indirect commands: Que + subjunctive"
    },
    {
        "question": "Translate: 'I'm looking for a cantina that serves good mezcal.'",
        "answer": ["Busco una cantina que sirva buen mezcal", "Busco una cantina que tenga buen mezcal"],
        "hint": "Indefinite antecedent + subjunctive; 'sirva' from 'servir'",
        "explanation": "When the antecedent (cantina) is indefinite/unknown, the relative clause takes subjunctive: 'que sirva' (not 'que sirve'). 'Sirva' is the subjunctive of 'servir' (e→i stem change). Mezcal — Oaxaca's iconic spirit — is increasingly available in CDMX cantinas.",
        "context": "Indefinite antecedent: subjunctive in relative clauses"
    },
    {
        "question": "Translate: 'Is there a taquería around here that sells tacos de canasta?'",
        "answer": ["¿Hay alguna taquería por aquí que venda tacos de canasta?", "¿Hay alguna taquería cerca que venda tacos de canasta?"],
        "hint": "Indefinite antecedent + subjunctive; 'venda' from 'vender'",
        "explanation": "The question '¿hay alguna... que?' establishes an indefinite antecedent, triggering subjunctive 'venda'. Tacos de canasta (basket tacos) are a CDMX street specialty — steamed tacos kept warm in a cloth-lined basket, sold by cyclists throughout the city.",
        "context": "Indefinite antecedent: subjunctive in relative clauses"
    },
    {
        "question": "Translate: 'I need a market that has fresh chiles for the mole.'",
        "answer": ["Necesito un mercado que tenga chiles frescos para el mole", "Necesito un mercado que tenga chiles frescos para el mole."],
        "hint": "Indefinite antecedent + subjunctive; 'tenga' from 'tener'",
        "explanation": "When the market is not yet identified/specific, subjunctive 'tenga' is used. If you knew the market, you'd say 'tiene' (indicative). Mole requires dried chiles (ancho, pasilla, mulato) — finding fresh ones requires the right market, like Mercado de la Merced in CDMX.",
        "context": "Indefinite antecedent: subjunctive in relative clauses"
    },
    {
        "question": "Translate: 'I want a café de olla that has a lot of cinnamon.'",
        "answer": ["Quiero un café de olla que tenga mucha canela", "Quiero un café de olla que tenga mucha canela."],
        "hint": "Indefinite antecedent + subjunctive; 'tenga' from 'tener'",
        "explanation": "Since you're describing an ideal/unidentified café de olla, subjunctive 'tenga' is required. Café de olla is traditionally brewed with cinnamon sticks (canela) and piloncillo in a clay pot — the canela should be generous for authentic flavor.",
        "context": "Indefinite antecedent: subjunctive in relative clauses"
    },
    {
        "question": "Translate: 'It's necessary that everyone bring tequila to the fiesta.'",
        "answer": ["Es necesario que todos traigan tequila a la fiesta", "Es necesario que todos lleven tequila a la fiesta"],
        "hint": "Es necesario que + subjunctive; 'traigan' from 'traer'",
        "explanation": "'Es necesario que' + subjunctive 'traigan' (from 'traer', to bring). In Mexican Spanish, 'traer' means to bring toward the speaker, while 'llevar' means to take away. Tequila — from Jalisco — is Mexico's most famous spirit, and no fiesta is complete without it.",
        "context": "Impersonal expression: es necesario que"
    },
    {
        "question": "Translate: 'I insist that you (formal) try the cochinita pibil in Mérida.'",
        "answer": ["Insisto en que usted pruebe la cochinita pibil en Mérida", "Insisto en que pruebe la cochinita pibil en Mérida"],
        "hint": "Insistir en que + subjunctive; 'pruebe' from 'probar'",
        "explanation": "'Insistir en que' (note 'en') triggers subjunctive with a subject change. 'Pruebe' is the usted subjunctive of 'probar' (o→ue). Cochinita pibil — slow-roasted pork in achiote and citrus, wrapped in banana leaves — is the defining dish of Yucatecan cuisine.",
        "context": "Volitional verb: insistir en que"
    },
    {
        "question": "Translate: 'The teacher orders that the students arrive on time for the Guelaguetza rehearsal.'",
        "answer": ["La maestra ordena que los estudiantes lleguen a tiempo para el ensayo de la Guelaguetza", "El maestro ordena que los estudiantes lleguen a tiempo para el ensayo de la Guelaguetza"],
        "hint": "Ordenar que + subjunctive; 'lleguen' from 'llegar'",
        "explanation": "'Ordenar que' (to order/command that) triggers subjunctive. 'Lleguen' is the subjunctive of 'llegar'. The Guelaguetza is Oaxaca's biggest annual festival — a celebration of indigenous dance and culture requiring extensive rehearsal by community groups.",
        "context": "Volitional verb: ordenar que"
    },
    {
        "question": "Translate: 'I'm delighted that you (informal) like the elote from the stand.'",
        "answer": ["Me encanta que te guste el elote del puesto", "Me encanta que te guste el elote del carrito"],
        "hint": "Encantar que + subjunctive; 'guste' from 'gustar'",
        "explanation": "'Encantar que' (to delight that) triggers subjunctive. 'Guste' is the subjunctive of 'gustar'. 'Elote' refers to corn on the cob sold at street stands or carritos (carts), slathered in mayo, chile, lime, and queso — a quintessential Mexican street snack.",
        "context": "Emotion verb: encantar que"
    },
    {
        "question": "Translate: 'Perhaps the metro won't be so crowded during the holidays.'",
        "answer": ["Tal vez el metro no esté tan lleno durante las fiestas", "Acaso el metro no esté tan lleno durante las fiestas", "Puede que el metro no esté tan lleno durante las fiestas"],
        "hint": "Tal vez / puede que + subjunctive; 'esté' from 'estar'",
        "explanation": "'Tal vez' and 'puede que' trigger subjunctive for uncertain future events. 'Esté' is the subjunctive of 'estar'. The CDMX metro — one of the world's busiest — carries millions daily; it might be less crowded during holiday periods like Semana Santa or Navidad.",
        "context": "Doubt: tal vez / puede que"
    },
    {
        "question": "Translate: 'It's strange that there's no line at the tamale stand today.'",
        "answer": ["Es raro que no haya fila en el puesto de tamales hoy", "Es raro que no haya cola en el puesto de tamales hoy"],
        "hint": "Es raro que + subjunctive; 'haya' from 'haber'",
        "explanation": "'Es raro que' triggers subjunctive. 'Haya' is the subjunctive of 'haber'. In Mexican Spanish, 'fila' is more common than 'cola' for a line/queue. Tamales are such a popular breakfast that a stall without a line is genuinely rare — especially during the holiday season.",
        "context": "Impersonal expression: es raro que"
    },
    {
        "question": "Translate: 'It's curious that Oaxaca has so many different moles.'",
        "answer": ["Es curioso que Oaxaca tenga tantos moles diferentes", "Es curioso que Oaxaca tenga tantos tipos de mole diferentes"],
        "hint": "Es curioso que + subjunctive; 'tenga' from 'tener'",
        "explanation": "'Es curioso que' triggers subjunctive. 'Tenga' is the subjunctive of 'tener'. Oaxaca is called 'the land of seven moles' — mole negro, coloradito, amarillo, verde, chichilo, manchamantel, and rojo — each a complex sauce requiring dozens of ingredients and days to prepare.",
        "context": "Impersonal expression: es curioso que"
    },
    {
        "question": "Translate: 'It's a pity that the 5 de mayo parade was canceled.'",
        "answer": ["Es una lástima que el desfile del 5 de mayo haya sido cancelado", "Es una lástima que hayan cancelado el desfile del 5 de mayo"],
        "hint": "Es una lástima que + present perfect subjunctive",
        "explanation": "'Es una lástima que' triggers subjunctive. 'Haya sido cancelado' uses the present perfect subjunctive of 'ser' for a completed past action. The 5 de mayo parade in Puebla commemorates the 1862 victory over France — a major local celebration, though far less important in most of Mexico than Independence Day.",
        "context": "Impersonal expression: es una lástima que"
    },
    {
        "question": "Translate: 'Let them start the posada already!' (using Que + subjunctive)",
        "answer": ["Que ya empiecen la posada", "¡Que ya empiecen la posada!", "Que ya comiencen la posada"],
        "hint": "Que + subjunctive for third-person commands; 'empiecen' from 'empezar'",
        "explanation": "'Que + subjunctive' expresses an indirect command. 'Empiecen' is the subjunctive of 'empezar' (e→ie). Las Posadas involve candlelit processions, piñatas, and ponche — '¡Que ya empiecen!' captures the eager impatience of children waiting for the festivities to begin.",
        "context": "Negative/indirect commands: Que + subjunctive"
    },
    {
        "question": "Translate: 'We're looking for a restaurant that prepares authentic chilaquiles verdes.'",
        "answer": ["Buscamos un restaurante que prepare chilaquiles verdes auténticos", "Buscamos un restaurante que haga chilaquiles verdes auténticos"],
        "hint": "Indefinite antecedent + subjunctive; 'prepare' from 'preparar'",
        "explanation": "Since the restaurant is not yet identified, subjunctive 'prepare' is required. If you said 'que prepara,' it would imply you already know which restaurant it is. Chilaquiles verdes — fried tortilla strips in tomatillo salsa — are a beloved Mexican breakfast, and authenticity matters.",
        "context": "Indefinite antecedent: subjunctive in relative clauses"
    },
    {
        "question": "Translate: 'There isn't anyone here who knows how to make atole de chocolate.'",
        "answer": ["No hay nadie aquí que sepa hacer atole de chocolate", "No hay nadie aquí que sepa preparar atole de chocolate"],
        "hint": "Indefinite antecedent (negative) + subjunctive; 'sepa' from 'saber'",
        "explanation": "Negative antecedents ('no hay nadie que') always trigger subjunctive. 'Sepa' is the subjunctive of 'saber'. Atole de chocolate (champurrado) is a thick, warm corn-and-chocolate drink traditional at Las Posadas and Día de los Muertos — knowing how to make it is a cherished skill.",
        "context": "Indefinite antecedent: subjunctive in relative clauses"
    },
    {
        "question": "Translate: 'I beg you (informal) to not leave without trying the esquites.'",
        "answer": ["Te ruego que no te vayas sin probar los esquites", "Te ruego que no te vayas sin probar los esquites."],
        "hint": "Rogar que + subjunctive; 'te vayas' from 'irse'",
        "explanation": "'Rogar que' triggers subjunctive. 'Te vayas' is the subjunctive of 'irse'. 'Esquites' — corn kernels in a cup with chile, lime, mayo, and cheese — are the cup version of elote, sold at evening stands across Mexico, especially in CDMX.",
        "context": "Volitional verb: rogar que"
    },
    {
        "question": "Translate: 'The government prohibits that we fish in the lake near Pátzcuaro.'",
        "answer": ["El gobierno prohíbe que pesquemos en el lago cerca de Pátzcuaro", "Prohíben que pesquemos en el lago cerca de Pátzcuaro"],
        "hint": "Prohibir que + subjunctive; 'pesquemos' from 'pescar'",
        "explanation": "'Prohibir que' triggers subjunctive. 'Pesquemos' is the nosotros subjunctive of 'pescar' (note: pesco, pescas → pesque, pesques, pesque, pesquemos, pesquen — the u is added to preserve the /k/ sound). Pátzcuaro's lake in Michoacán is famous for its butterfly-net fishing tradition.",
        "context": "Volitional verb: prohibir que"
    },
    {
        "question": "Translate: 'It frightens me that the volcano Popocatépetl might erupt again.'",
        "answer": ["Me da miedo que el volcán Popocatépetl entre en erupción otra vez", "Me da miedo que el Popocatépetl vuelva a entrar en erupción"],
        "hint": "Dar miedo que + subjunctive; 'entre' from 'entrar'",
        "explanation": "'Dar miedo que' triggers subjunctive. 'Entre' is the subjunctive of 'entrar'. Popocatépetl (the Smoking Mountain) is an active volcano visible from CDMX and Puebla — its eruptions regularly affect daily life for millions, making this a very real Mexican fear.",
        "context": "Emotion verb: dar miedo que"
    },
    {
        "question": "Translate: 'It bothers me that there's no good mezcal in this cantina.'",
        "answer": ["Me molesta que no haya buen mezcal en esta cantina", "Me fastidia que no haya buen mezcal en esta cantina"],
        "hint": "Molestar que + subjunctive; 'haya' from 'haber'",
        "explanation": "'Molestar que' (or 'fastidiar que') triggers subjunctive. 'Haya' is the subjunctive of 'haber'. A cantina without good mezcal is a genuine disappointment — mezcal has exploded in popularity in CDMX cantinas, and any self-respecting one should stock espadín from Oaxaca at minimum.",
        "context": "Emotion verb: molestar que"
    },
    {
        "question": "Translate: 'It's urgent that she sign the contract before the notario público.'",
        "answer": ["Es urgente que ella firme el contrato ante el notario público", "Es urgente que firme el contrato ante el notario público"],
        "hint": "Es urgente que + subjunctive; 'firme' from 'firmar'",
        "explanation": "'Es urgente que' triggers subjunctive. 'Firme' is the subjunctive of 'firmar'. The 'notario público' in Mexico is a powerful legal figure — a state-appointed lawyer who authenticates documents, unlike notaries in English-speaking countries who merely witness signatures.",
        "context": "Impersonal expression: es urgente que"
    },
    {
        "question": "Translate: 'It's advisable that we arrive early to the Día de Reyes celebration.'",
        "answer": ["Conviene que lleguemos temprano a la celebración del Día de Reyes", "Conviene que lleguemos temprano a la celebración de Día de Reyes"],
        "hint": "Conviene que + subjunctive; 'lleguemos' from 'llegar'",
        "explanation": "'Conviene que' triggers subjunctive. 'Lleguemos' is the nosotros subjunctive of 'llegar' (llego, llegas → llegue, llegues, llegue, lleguemos, lleguen — note the u). Día de Reyes (Jan 6) celebrations center around the rosca de reyes — arriving early ensures you get a slice without the hidden baby Jesus figurine.",
        "context": "Impersonal expression: conviene que"
    },
    {
        "question": "Translate: 'I'm not sure that the metrobus goes to the neighborhood of Coyoacán.'",
        "answer": ["No estoy seguro de que el metrobús vaya a la colonia Coyoacán", "No estoy seguro de que el metrobús pase por Coyoacán"],
        "hint": "No estar seguro de que + subjunctive; 'vaya' from 'ir'",
        "explanation": "'No estar seguro de que' triggers subjunctive. 'Vaya' is the subjunctive of 'ir' (completely irregular). The Metrobús is CDMX's BRT system along key corridors — though to reach Coyoacán, you'd likely need the Metro (Line 3, Coyoacán station) or a pesero.",
        "context": "Doubt: no estar seguro que"
    },
]

multiple_choice = [
    (
        "I want you (informal) to eat enchiladas with me.",
        [
            "Quiero que tú comes enchiladas conmigo.",
            "Quiero que comas enchiladas conmigo.",
            "Quiero que vas a comer enchiladas conmigo.",
            "Quiero que comerías enchiladas conmigo."
        ],
        2,
        "'Querer que' requires the subjunctive, not the indicative. 'Comas' is the subjunctive of 'comer'. Indicative 'comes' is incorrect after 'que' with a different subject."
    ),
    (
        "It bothers me that he speaks Spanish with an accent.",
        [
            "Me molesta que él habla español con acento.",
            "Me molesta que él hable español con acento.",
            "Me molesta que él hablara español con acento.",
            "Me molesta que él ha hablado español con acento."
        ],
        2,
        "'Molestar que' expresses emotion and triggers present subjunctive. 'Hable' (subjunctive) is correct; 'habla' (indicative) is wrong after an emotion trigger."
    ),
    (
        "I doubt that the churros from this stand are fresh.",
        [
            "Dudo que los churros de este puesto son frescos.",
            "Dudo que los churros de este puesto eran frescos.",
            "Dudo que los churros de este puesto sean frescos.",
            "Dudo que los churros de este puesto serán frescos."
        ],
        3,
        "'Dudar que' triggers subjunctive: 'sean' (present subjunctive of 'ser') is correct. 'Son' is indicative and cannot follow 'dudar que'. Mexican street puestos (stands) are where you find the best churros."
    ),
    (
        "It's important that we try the cochinita pibil in Mérida.",
        [
            "Es importante que probamos la cochinita pibil en Mérida.",
            "Es importante que probáramos la cochinita pibil en Mérida.",
            "Es importante que probemos la cochinita pibil en Mérida.",
            "Es importante que vamos a probar la cochinita pibil en Mérida."
        ],
        3,
        "'Es importante que' requires present subjunctive: 'probemos' (nosotros subjunctive of 'probar'). 'Probamos' is indicative. Cochinita pibil is Yucatecan — a must-try in Mérida."
    ),
    (
        "Which is the correct Mexican Spanish for: 'Perhaps it will rain during the Guelaguetza.'",
        [
            "Quizás llueve durante la Guelaguetza.",
            "Quizás lloverá durante la Guelaguetza.",
            "Quizás llueva durante la Guelaguetza.",
            "Quizás lloviendo durante la Guelaguetza."
        ],
        3,
        "'Quizás' + future/uncertain event requires subjunctive. 'Llueva' (subjunctive) is correct. 'Llueve' is indicative. The Guelaguetza is Oaxaca's famous indigenous cultural festival each July."
    ),
    (
        "The professor insists that the students read Sor Juana Inés de la Cruz.",
        [
            "La profesora insiste en que los estudiantes lean a Sor Juana Inés de la Cruz.",
            "La profesora insiste que los estudiantes leen a Sor Juana Inés de la Cruz.",
            "La profesora insiste que los estudiantes lean a Sor Juana Inés de la Cruz.",
            "La profesora insiste en que los estudiantes leen a Sor Juana Inés de la Cruz."
        ],
        1,
        "'Insistir en que' (with 'en') is the correct preposition. When different subjects, subjunctive 'lean' is used. Sor Juana Inés de la Cruz is Mexico's most celebrated colonial-era writer — a nun, poet, and intellectual."
    ),
    (
        "I'm happy that you (informal) got the scholarship at UNAM.",
        [
            "Me alegro de que tú consigues la beca en la UNAM.",
            "Me alegro de que tú conseguiste la beca en la UNAM.",
            "Me alegro de que tú consigas la beca en la UNAM.",
            "Me alegro que tú consigas la beca en la UNAM."
        ],
        3,
        "'Alegrarse de que' requires subjunctive and the preposition 'de'. Since this is a present-tense emotional reaction about a current state, present subjunctive 'consigas' is appropriate. UNAM is Mexico's largest and most prestigious university."
    ),
    (
        "It's better that you (informal) not drink the water from the tap in Monterrey.",
        [
            "Es mejor que no bebes el agua del grifo en Monterrey.",
            "Es mejor que no tomes el agua de la llave en Monterrey.",
            "Es mejor que no bebas el agua del grifo en Monterrey.",
            "Es mejor no tomas el agua de la llave en Monterrey."
        ],
        2,
        "'Es mejor que' + subjunctive: 'tomes' is correct. Mexican Spanish uses 'tomar' for drinking and 'llave' (not 'grifo') for faucet/tap. The infinitive construction 'es mejor no tomar' is also valid, but after 'que' we need subjunctive."
    ),
    (
        "I don't think that the mariachi band plays at the plaza tonight.",
        [
            "No creo que la banda de mariachi toca en la plaza esta noche.",
            "No creo que la banda de mariachi toque en la plaza esta noche.",
            "No creo que la banda de mariachi tocará en la plaza esta noche.",
            "No creo que la banda de mariachi jugaba en la plaza esta noche."
        ],
        2,
        "'No creer que' triggers subjunctive: 'toque' is correct. Note that 'tocar' means 'to play (an instrument)' — 'jugar' is for sports. 'Plaza' in Mexico refers to the central town square (zócalo)."
    ),
    (
        "They demand that we respect the Day of the Dead traditions.",
        [
            "Exigen que respetamos las tradiciones del Día de los Muertos.",
            "Exigen que respetáramos las tradiciones del Día de los Muertos.",
            "Exigen que respetemos las tradiciones del Día de los Muertos.",
            "Exigen que vamos a respetar las tradiciones del Día de los Muertos."
        ],
        3,
        "'Exigir que' triggers present subjunctive: 'respetemos' (nosotros subjunctive). 'Respetamos' is indicative. Día de los Muertos (Nov 1-2) is one of Mexico's most sacred traditions, honoring deceased loved ones with ofrendas."
    ),
    (
        "I beg that you (formal) help me carry the esquites.",
        [
            "Le ruego que me ayudas a cargar los esquites.",
            "Le ruego que me ayude a cargar los esquites.",
            "Le ruego que me ayudará a cargar los esquites.",
            "Le ruego que me ayudaba a cargar los esquites."
        ],
        2,
        "'Rogar que' (to beg that) triggers subjunctive: 'ayude' (subjunctive of 'ayudar'). 'Ayudas' is indicative. 'Cargar' is Mexican Spanish for carrying things; esquites are corn kernels in a cup sold at street stands."
    ),
    (
        "The boss orders that we finish the project before cinco de mayo.",
        [
            "El jefe manda que terminamos el proyecto antes del cinco de mayo.",
            "El jefe manda que termináramos el proyecto antes del cinco de mayo.",
            "El jefe manda que terminemos el proyecto antes del cinco de mayo.",
            "El jefe manda que vamos a terminar el proyecto antes del cinco de mayo."
        ],
        3,
        "'Mandar que' (to order that) triggers present subjunctive: 'terminemos' (nosotros subjunctive). 'Terminamos' is indicative. Cinco de mayo commemorates the Battle of Puebla (1862) — a date far more significant in Puebla than in the US."
    ),
    (
        "They prohibit that we park near the zócalo.",
        [
            "Prohíben que nos estacionamos cerca del zócalo.",
            "Prohíben que nos estacionemos cerca del zócalo.",
            "Prohíben que estacionaremos cerca del zócalo.",
            "Prohíben que nos estacionábamos cerca del zócalo."
        ],
        2,
        "'Prohibir que' triggers subjunctive: 'nos estacionemos'. 'Estacionarse' is Mexican Spanish for parking; 'aparcar' is Peninsular. The 'zócalo' is the central plaza found in every Mexican town."
    ),
    (
        "My mother insists that I come home early for Las Posadas.",
        [
            "Mi mamá insiste que llego temprano a casa para Las Posadas.",
            "Mi mamá insiste en que llegue temprano a casa para Las Posadas.",
            "Mi mamá insiste que llegue temprano a casa para Las Posadas.",
            "Mi mamá insiste en que llego temprano a casa para Las Posadas."
        ],
        2,
        "'Insistir en que' requires the preposition 'en' and subjunctive 'llegue' when there's a subject change. Without 'en', the construction is incorrect. Las Posadas (Dec 16-24) are nine nights of processions before Christmas."
    ),
    (
        "I advise that you (informal) try the tacos al pastor.",
        [
            "Te aconsejo que pruebes los tacos al pastor.",
            "Te aconsejo que pruebas los tacos al pastor.",
            "Te aconsejo que probarás los tacos al pastor.",
            "Te aconsejo que probabas los tacos al pastor."
        ],
        1,
        "'Aconsejar que' triggers subjunctive: 'pruebes' (from 'probar', o→ue stem change). 'Pruebas' is indicative. Tacos al pastor — spit-roasted pork with pineapple — are Mexico City's most iconic street food."
    ),
    (
        "It surprises me that she speaks Nahuatl so well.",
        [
            "Me sorprende que ella habla náhuatl tan bien.",
            "Me sorprende que ella hablara náhuatl tan bien.",
            "Me sorprende que ella hable náhuatl tan bien.",
            "Me sorprende que ella ha hablado náhuatl tan bien."
        ],
        3,
        "'Sorprender que' (to surprise that) is an emotion verb requiring subjunctive: 'hable'. 'Habla' is indicative and wrong here. Nahuatl has over a million speakers in Mexico, especially in Veracruz, Puebla, and Guerrero."
    ),
    (
        "I like that you (informal) prepare horchata for the fiesta.",
        [
            "Me gusta que preparas horchata para la fiesta.",
            "Me gusta que prepararás horchata para la fiesta.",
            "Me gusta que preparar horchata para la fiesta.",
            "Me gusta que prepares horchata para la fiesta."
        ],
        4,
        "'Gustar que' triggers subjunctive because it expresses an emotional reaction to someone else's action. 'Prepares' (subjunctive) is correct; 'preparas' (indicative) is wrong. Horchata is rice water with cinnamon — a classic Mexican agua fresca."
    ),
    (
        "It scares me that the earthquakes are so frequent in CDMX.",
        [
            "Me da miedo que los sismos son tan frecuentes en la CDMX.",
            "Me da miedo que los sismos eran tan frecuentes en la CDMX.",
            "Me da miedo que los sismos sean tan frecuentes en la CDMX.",
            "Me da miedo que los sismos serán tan frecuentes en la CDMX."
        ],
        3,
        "'Dar miedo que' triggers subjunctive: 'sean' (from 'ser'). 'Son' is indicative. In Mexican Spanish, 'sismo' is preferred over 'terremoto'. CDMX sits on a lakebed, making it especially vulnerable to seismic activity."
    ),
    (
        "It matters to me that they respect our traditions on Día de Reyes.",
        [
            "Me importa que respeten nuestras tradiciones el Día de Reyes.",
            "Me importa que respetan nuestras tradiciones el Día de Reyes.",
            "Me importa que respetaron nuestras tradiciones el Día de Reyes.",
            "Me importa que van a respetar nuestras tradiciones el Día de Reyes."
        ],
        1,
        "'Importar que' triggers subjunctive: 'respeten'. 'Respetan' is indicative and wrong. Día de Reyes (Jan 6) is when Mexican children receive gifts from the Three Wise Men — the rosca de reyes is shared that day."
    ),
    (
        "It fascinates me that they make cochinita pibil underground in Mérida.",
        [
            "Me fascina que hacen cochinita pibil bajo tierra en Mérida.",
            "Me fascina que hagan cochinita pibil bajo tierra en Mérida.",
            "Me fascina que harían cochinita pibil bajo tierra en Mérida.",
            "Me fascina que hicieron cochinita pibil bajo tierra en Mérida."
        ],
        2,
        "'Fascinar que' triggers subjunctive: 'hagan' (from 'hacer'). 'Hacen' is indicative. Traditional cochinita pibil is wrapped in banana leaves and cooked in an underground pit (píib) — a Yucatecan Maya technique."
    ),
    (
        "It annoys me that the chilaquiles are always cold at this fondita.",
        [
            "Me fastidia que los chilaquiles siempre están fríos en esta fondita.",
            "Me fastidia que los chilaquiles siempre eran fríos en esta fondita.",
            "Me fastidia que los chilaquiles siempre estén fríos en esta fondita.",
            "Me fastidia que los chilaquiles siempre estarán fríos en esta fondita."
        ],
        3,
        "'Fastidiar que' (to annoy/irritate) triggers subjunctive: 'estén'. 'Están' is indicative. A 'fondita' is a small, inexpensive eatery — the diminutive of 'fonda'. Cold chilaquiles are a culinary sin in Mexico."
    ),
    (
        "I'm not sure that the pulque is from Hidalgo.",
        [
            "No estoy seguro de que el pulque es de Hidalgo.",
            "No estoy seguro de que el pulque sea de Hidalgo.",
            "No estoy seguro que el pulque sea de Hidalgo.",
            "No estoy seguro de que el pulque fuera de Hidalgo."
        ],
        2,
        "'No estar seguro de que' triggers subjunctive: 'sea'. 'Es' is indicative and wrong. Note the required 'de'. Pulque is a pre-Columbian fermented agave drink, especially from Hidalgo and Tlaxcala."
    ),
    (
        "It's probable that the tamales sell out before noon.",
        [
            "Es probable que los tamales se agotan antes del mediodía.",
            "Es probable que los tamales se agotarán antes del mediodía.",
            "Es probable que los tamales se agoten antes del mediodía.",
            "Es probable que los tamales se agotaron antes del mediodía."
        ],
        3,
        "'Es probable que' triggers subjunctive: 'se agoten' (from 'agotarse'). 'Se agotan' is indicative. In Mexico, good tamales from a puesto sell out fast — especially on weekends."
    ),
    (
        "Perhaps the elote stand is on this corner.",
        [
            "Tal vez el puesto de elote está en esta esquina.",
            "Tal vez el puesto de elote esté en esta esquina.",
            "Tal vez el puesto de elote estaba en esta esquina.",
            "Tal vez el puesto de elote estará en esta esquina."
        ],
        2,
        "'Tal vez' + subjunctive for uncertain present/future: 'esté'. When 'tal vez' expresses real doubt about a present situation, subjunctive is preferred. 'Está' (indicative) would suggest higher certainty. Elote stands are ubiquitous evening vendors in CDMX."
    ),
    (
        "It's strange that there's no atole at the posada this year.",
        [
            "Es raro que no hay atole en la posada este año.",
            "Es raro que no había atole en la posada este año.",
            "Es raro que no haya atole en la posada este año.",
            "Es raro que no habrá atole en la posada este año."
        ],
        3,
        "'Es raro que' triggers subjunctive: 'haya' (from 'haber'). 'Hay' is indicative. Atole — a hot corn-based drink — is essential at Las Posadas; its absence would be genuinely strange."
    ),
    (
        "It's curious that Guadalajara has so many murals.",
        [
            "Es curioso que Guadalajara tiene tantos murales.",
            "Es curioso que Guadalajara tenga tantos murales.",
            "Es curioso que Guadalajara tenía tantos murales.",
            "Es curioso que Guadalajara tendrá tantos murales."
        ],
        2,
        "'Es curioso que' triggers subjunctive: 'tenga'. 'Tiene' is indicative. Guadalajara is a hub of Mexican muralism — Orozco's works in the Hospicio Cabañas are UNESCO-listed."
    ),
    (
        "It's a shame that the museum is closed on Mondays.",
        [
            "Es una lástima que el museo está cerrado los lunes.",
            "Es una lástima que el museo estaba cerrado los lunes.",
            "Es una lástima que el museo esté cerrado los lunes.",
            "Es una lástima que el museo será cerrado los lunes."
        ],
        3,
        "'Es una lástima que' triggers subjunctive: 'esté'. 'Está' is indicative. Most Mexican museums close on Mondays — a consistent source of tourist disappointment."
    ),
    (
        "It's urgent that we leave before the traffic gets bad in Monterrey.",
        [
            "Es urgente que salimos antes de que el tráfico empeore en Monterrey.",
            "Es urgente que salgamos antes de que el tráfico empeora en Monterrey.",
            "Es urgente que salgamos antes de que el tráfico empeore en Monterrey.",
            "Es urgente que salgamos antes de que el tráfico empeoraba en Monterrey."
        ],
        3,
        "'Es urgente que' triggers subjunctive 'salgamos'. Note also 'antes de que' triggers subjunctive 'empeore'. Both clauses need subjunctive. 'Salimos' and 'empeora' are indicative and wrong. Monterrey's traffic is notoriously bad."
    ),
    (
        "Which is the correct way to say 'Let him come in!' in Mexican Spanish?",
        [
            "Que entra.",
            "Que entre.",
            "Que entrará.",
            "Que entraba."
        ],
        2,
        "'Que + subjunctive' is used for third-person commands: 'que entre' (subjunctive of 'entrar'). 'Entra' is indicative and incorrect. This is the natural way Mexicans say 'let him/her come in' at a door."
    ),
    (
        "Let her leave right now!",
        [
            "Que se va ahora mismo.",
            "Que se fue ahora mismo.",
            "Que se vaya ahora mismo.",
            "Que se irá ahora mismo."
        ],
        3,
        "'Que + subjunctive' for indirect commands: 'que se vaya' (subjunctive of 'irse'). 'Se va' is indicative. This emphatic structure is very common in Mexican Spanish for orders about third persons."
    ),
    (
        "I'm looking for a cantina that serves good mezcal.",
        [
            "Busco una cantina que sirve buen mezcal.",
            "Busco una cantina que servirá buen mezcal.",
            "Busco una cantina que sirva buen mezcal.",
            "Busco una cantina que serviría buen mezcal."
        ],
        3,
        "Indefinite antecedent triggers subjunctive in relative clauses: 'que sirva' (subjunctive). 'Que sirve' (indicative) implies you already know which cantina. Mezcal — Oaxaca's iconic spirit — is increasingly popular in CDMX cantinas."
    ),
    (
        "Is there a taquería around here that sells tacos de canasta?",
        [
            "¿Hay alguna taquería por aquí que vende tacos de canasta?",
            "¿Hay alguna taquería por aquí que vendía tacos de canasta?",
            "¿Hay alguna taquería por aquí que venda tacos de canasta?",
            "¿Hay alguna taquería por aquí que venderá tacos de canasta?"
        ],
        3,
        "'Alguna... que' establishes an indefinite antecedent, triggering subjunctive 'venda'. 'Vende' (indicative) would imply you already know the taquería exists. Tacos de canasta are steamed tacos sold from baskets by cyclists throughout CDMX."
    ),
    (
        "There isn't anyone here who knows how to make atole de chocolate.",
        [
            "No hay nadie aquí que sabe hacer atole de chocolate.",
            "No hay nadie aquí que supo hacer atole de chocolate.",
            "No hay nadie aquí que sepa hacer atole de chocolate.",
            "No hay nadie aquí que sabrá hacer atole de chocolate."
        ],
        3,
        "Negative antecedent ('no hay nadie que') always triggers subjunctive: 'sepa' (from 'saber'). 'Sabe' is indicative and wrong here. Atole de chocolate (champurrado) is a traditional warm corn-and-chocolate drink."
    ),
    (
        "Which construction correctly expresses 'It's advisable that we arrive early to the tianguis'?",
        [
            "Conviene que llegamos temprano al tianguis.",
            "Conviene que lleguemos temprano al tianguis.",
            "Conviene que llegáramos temprano al tianguis.",
            "Conviene que llegaremos temprano al tianguis."
        ],
        2,
        "'Conviene que' triggers present subjunctive: 'lleguemos'. 'Llegamos' is indicative. A 'tianguis' is a traditional open-air market (from Nahuatl 'tianquiztli') held on specific days in Mexican neighborhoods."
    ),
    (
        "Could it be that the esquites vendor went home already?",
        [
            "Acaso el vendedor de esquites ya se fue a casa.",
            "Acaso el vendedor de esquites ya se haya ido a casa.",
            "Acaso el vendedor de esquites ya se iba a casa.",
            "Acaso el vendedor de esquites ya irá a casa."
        ],
        2,
        "'Acaso' in questions means 'could it be that' and triggers subjunctive: 'se haya ido' (present perfect subjunctive). 'Se fue' is preterite indicative. Esquites are corn kernels in a cup — a beloved evening street snack in CDMX."
    ),
    (
        "It's necessary that everyone bring tequila to the fiesta.",
        [
            "Es necesario que todos traen tequila a la fiesta.",
            "Es necesario que todos trajeron tequila a la fiesta.",
            "Es necesario que todos traigan tequila a la fiesta.",
            "Es necesario que todos traerán tequila a la fiesta."
        ],
        3,
        "'Es necesario que' triggers subjunctive: 'traigan' (from 'traer'). 'Traen' is indicative. In Mexican Spanish, 'traer' means to bring toward the speaker. Tequila — from Jalisco — is essential at any Mexican fiesta."
    ),
    (
        "Which verb form completes: 'Es una lástima que el desfile del 5 de mayo ____ cancelado'?",
        [
            "está",
            "estuvo",
            "esté",
            "estará"
        ],
        3,
        "'Es una lástima que' triggers subjunctive: 'esté' (from 'estar'). 'Está' is indicative. The 5 de mayo parade in Puebla commemorates the 1862 Battle of Puebla — a major local celebration."
    ),
    (
        "It's urgent that she sign the contract before the notario público.",
        [
            "Es urgente que ella firma el contrato ante el notario público.",
            "Es urgente que ella firme el contrato ante el notario público.",
            "Es urgente que ella firmará el contrato ante el notario público.",
            "Es urgente que ella firmaba el contrato ante el notario público."
        ],
        2,
        "'Es urgente que' triggers subjunctive: 'firme' (from 'firmar'). 'Firma' is indicative. The 'notario público' in Mexico is a state-appointed lawyer with far more authority than notaries in English-speaking countries."
    ),
    (
        "I'm not sure that the metrobus goes to the neighborhood of Coyoacán.",
        [
            "No estoy seguro de que el metrobús va a la colonia Coyoacán.",
            "No estoy seguro de que el metrobús vaya a la colonia Coyoacán.",
            "No estoy seguro que el metrobús vaya a la colonia Coyoacán.",
            "No estoy seguro de que el metrobús iba a la colonia Coyoacán."
        ],
        2,
        "'No estar seguro de que' triggers subjunctive: 'vaya' (from 'ir', completely irregular). Note the required 'de'. 'Va' is indicative. Coyoacán is a charming colonial neighborhood (colonia) in southern CDMX — Frida Kahlo's neighborhood."
    ),
    (
        "It's advisable that we arrive early to the Día de Reyes celebration.",
        [
            "Conviene que llegamos temprano a la celebración del Día de Reyes.",
            "Conviene que lleguemos temprano a la celebración del Día de Reyes.",
            "Conviene que llegáramos temprano a la celebración del Día de Reyes.",
            "Conviene que llegaremos temprano a la celebración del Día de Reyes."
        ],
        2,
        "'Conviene que' triggers present subjunctive: 'lleguemos' (from 'llegar'). Note the spelling change: lleg- → llegu- in subjunctive. 'Llegamos' is indicative. Día de Reyes (Jan 6) is when Mexicans share the rosca de reyes."
    ),
]

if __name__ == "__main__":
    run_exercises(translation_exercises, title="Lesson 1: Present Subjunctive in Mexican Spanish — Translation Exercises")
    choose_translation(multiple_choice, title="Lesson 1: Present Subjunctive in Mexican Spanish — Multiple Choice")