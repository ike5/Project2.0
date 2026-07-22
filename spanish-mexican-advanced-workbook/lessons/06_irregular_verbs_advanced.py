import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from workbook_engine import run_exercises, choose_translation

translation_exercises = [
    {
        "question": "Translate: 'Wherever you go, I'll follow you.' (use subjunctive of ir)",
        "answer": ["Adondequiera que vayas, te sigo", "Adondequiera que vayas, te seguiré", "A dondequiera que vayas, te sigo", "A dondequiera que vayas, te seguiré"],
        "hint": "ir → vaya (fully irregular subjunctive)",
        "explanation": "Ir is fully irregular in the subjunctive: vaya, vayas, vaya, etc. 'Adondequiera que' is a common subjunctive trigger meaning 'wherever'.",
    },
    {
        "question": "Translate: 'I hope you are happy.' (use subjunctive of ser)",
        "answer": ["Espero que seas feliz", "Espero que seas feliz.", "Espero que seas feliz/felices"],
        "hint": "ser → sea (fully irregular subjunctive)",
        "explanation": "Ser is fully irregular in the subjunctive: sea, seas, sea, seamos, sean. 'Espero que seas feliz' is the standard way to express this wish.",
    },
    {
        "question": "Translate: 'I doubt that there has been a problem.' (use subjunctive of haber)",
        "answer": ["Dudo que haya habido un problema", "Dudo que haya habido un problema."],
        "hint": "haber → haya (fully irregular subjunctive); compound with past participle",
        "explanation": "Haber is fully irregular in the subjunctive: haya, hayas, haya, etc. 'Haya habido' is the subjunctive perfect — haya + habido. Very common in Mexican Spanish for expressing doubt about past events.",
    },
    {
        "question": "Translate: 'I want you to know the truth.' (use subjunctive of saber)",
        "answer": ["Quiero que sepas la verdad", "Quiero que sepas la verdad."],
        "hint": "saber → sepa (fully irregular subjunctive: sab- → sep-)",
        "explanation": "Saber has a fully irregular subjunctive stem: sep- (not sab-). Yo sepa, tú sepas, él sepa, etc. This is a high-frequency irregularity.",
    },
    {
        "question": "Translate: 'I hope you give her the book.' (use subjunctive of dar)",
        "answer": ["Espero que le des el libro", "Espero que le des el libro."],
        "hint": "dar → dé, des, dé, demos, den (accented subjunctive forms)",
        "explanation": "Dar has short subjunctive forms with accent marks: dé, des, dé, demos, den. Without the accent, 'de' is the preposition. Note: 'le des' uses indirect object pronoun 'le'.",
    },
    {
        "question": "Translate: 'I wish I were there.' (use imperfect subjunctive of ser/ir)",
        "answer": ["Ojalá estuviera ahí", "Ojalá estuviera allá", "Ojalá estuviera allí", "Ojalá estuviese ahí", "Ojalá estuviese allá"],
        "hint": "ser/ir → fuera/fuese (imperfect subjunctive); but 'estar' is more natural for location",
        "explanation": "For location, use estar in the imperfect subjunctive: estuviera/estuviese. The forms of ser/ir in imperfect subjunctive are: fuera/fuese, fueras/fueses, etc. But for 'being somewhere', Mexicans use 'estuviera'.",
    },
    {
        "question": "Translate: 'If I had known, I would have told you.' (use imperfect subjunctive of saber → supiera)",
        "answer": ["Si yo hubiera sabido, te lo habría dicho", "Si hubiera sabido, te lo habría dicho", "Si yo hubiese sabido, te lo habría dicho", "Si hubiese sabido, te lo habría dicho"],
        "hint": "saber → supiera/supiese (irregular imperfect subjunctive)",
        "explanation": "Saber has an irregular imperfect subjunctive: supiera/supiese. However, in this si-clause with compound tense, 'hubiera/hubiese sabido' uses the perfect. Both 'supiera' (simple) and 'hubiera sabido' (compound) are valid; the compound is more natural for past counterfactuals.",
    },
    {
        "question": "Translate: 'He always shifts the blame to someone else.' (use echar la culpa)",
        "answer": ["Siempre le echa la culpa a alguien más", "Siempre le echa la culpa a otro", "Siempre le echa la culpa a alguien más."],
        "hint": "echar la culpa = to shift the blame",
        "explanation": "'Echar la culpa' is a very common Mexican expression meaning 'to shift the blame'. 'Le echa la culpa a alguien' = s/he blames someone. 'Alguien más' is distinctly Mexican for 'someone else'.",
    },
    {
        "question": "Translate: 'I really miss my grandmother.' (use echar de menos)",
        "answer": ["Echo mucho de menos a mi abuela", "Echo de menos a mi abuela", "Le echo de menos a mi abuela", "Echo mucho de menos a mi abuela."],
        "hint": "echar de menos = to miss (someone/something)",
        "explanation": "'Echar de menos' is the Mexican way to say 'to miss' someone. In Spain they also use it, but in Mexico it's especially common alongside 'extrañar'. Note the personal 'a' before 'mi abuela'.",
    },
    {
        "question": "Translate: 'Can you give me a hand with this?' (use echar una mano)",
        "answer": ["¿Me echas una mano con esto?", "¿Me puedes echar una mano con esto?", "¿Me echas la mano con esto?"],
        "hint": "echar una mano = to give a hand / help out",
        "explanation": "'Echar una mano' or 'echar la mano' = to help out / give a hand. Very common in Mexican Spanish. '¿Me echas una mano?' is informal and friendly.",
    },
    {
        "question": "Translate: 'She burst out crying when she heard the news.' (use echarse a llorar)",
        "answer": ["Se echó a llorar cuando escuchó la noticia", "Se echó a llorar cuando oyó la noticia", "Se echó a llorar cuando escuchó las noticias"],
        "hint": "echarse a + infinitive = to burst into / start doing something suddenly",
        "explanation": "'Echarse a llorar' means to burst out crying. 'Echarse a + infinitive' is a common pattern: echarse a correr (burst into running), echarse a reír (burst out laughing). The reflexive 'se' is required.",
    },
    {
        "question": "Translate: 'You're right, the traffic is terrible today.' (use darle la razón)",
        "answer": ["Le doy la razón, el tráfico está fatal hoy", "Te doy la razón, el tráfico está terrible hoy", "Le doy la razón, el tráfico está terrible hoy", "Te doy la razón, el tráfico está fatal hoy"],
        "hint": "darle la razón a alguien = to agree with someone / concede they're right",
        "explanation": "'Darle la razón a alguien' = to agree with someone / acknowledge they're right. In Mexico, 'fatal' is colloquially used for 'terrible/awful' — 'el tráfico está fatal' is very natural Mexican speech.",
    },
    {
        "question": "Translate: 'I feel like eating tacos.' (use dar ganas)",
        "answer": ["Me dan ganas de comer tacos", "Me da ganas de comer tacos"],
        "hint": "dar ganas = to feel like / to have the urge to",
        "explanation": "'Dar ganas' is extremely common in Mexico. 'Me dan ganas de + infinitive' = I feel like... Note: 'ganas' is plural, so the verb agrees: 'dan' (though 'da' is also heard colloquially).",
    },
    {
        "question": "Translate: 'Stop being annoying!' (use dar lata)",
        "answer": ["¡Ya no des lata!", "¡No des lata!", "¡Deja de dar lata!"],
        "hint": "dar lata = to be annoying / to bother",
        "explanation": "'Dar lata' is distinctly Mexican slang meaning 'to be annoying/bothersome'. '¡Ya no des lata!' = Stop being annoying! Very common in informal Mexican speech.",
    },
    {
        "question": "Translate: 'They couldn't agree on the price.' (use ponerse de acuerdo)",
        "answer": ["No se pudieron poner de acuerdo en el precio", "No pudieron ponerse de acuerdo en el precio", "No se pusieron de acuerdo en el precio"],
        "hint": "ponerse de acuerdo = to reach an agreement",
        "explanation": "'Ponerse de acuerdo' = to reach an agreement / come to terms. It's reflexive and uses 'en' for the topic: ponerse de acuerdo EN algo.",
    },
    {
        "question": "Translate: 'Hurry up or we'll miss the bus!' (use ponerse pilas)",
        "answer": ["¡Ponte pilas o perdemos el camión!", "¡Pónganse pilas o perdemos el camión!", "¡Ponte pilas o vamos a perder el camión!"],
        "hint": "ponerse pilas = to hurry up / get moving (Mexican slang)",
        "explanation": "'Ponerse pilas' is quintessentially Mexican slang meaning 'hurry up / get moving / pay attention'. 'Camión' is the Mexican word for bus. Very informal and common.",
    },
    {
        "question": "Translate: 'Pay attention to what the teacher says.' (use hacer caso)",
        "answer": ["Hazle caso a lo que dice el profe", "Haz caso a lo que dice el profesor", "Hazle caso al maestro"],
        "hint": "hacer caso = to pay attention / to heed",
        "explanation": "'Hacer caso' = to pay attention / to heed advice. 'Hazle caso' (imperative) with indirect object 'le'. 'Profe' is the affectionate Mexican term for professor/teacher.",
    },
    {
        "question": "Translate: 'We're missing two players for the match.' (use hacer falta)",
        "answer": ["Nos hacen falta dos jugadores para el partido", "Hacen falta dos jugadores para el partido"],
        "hint": "hacer falta = to be lacking / to be needed",
        "explanation": "'Hacer falta' = to be lacking/needed. 'Nos hacen falta dos jugadores' = we're missing two players. This impersonal construction is extremely common in Mexican Spanish.",
    },
    {
        "question": "Translate: 'If I were the boss, things would be different.' (use imperfect subjunctive of ser → fuera)",
        "answer": ["Si yo fuera el jefe, las cosas serían diferentes", "Si fuera el jefe, las cosas serían diferentes", "Si yo fuese el jefe, las cosas serían diferentes"],
        "hint": "ser → fuera/fuese (imperfect subjunctive); si-clause requires imperfect subjunctive",
        "explanation": "Ser/ir share the same imperfect subjunctive forms: fuera/fuese, fueras/fueses, etc. In si-clauses expressing unreal conditions, the imperfect subjunctive is required. 'El jefe' is the standard Mexican term for 'the boss'.",
    },
    {
        "question": "Translate: 'Bribe the guard so he lets us in.' (use hacer ojo — Mexican slang)",
        "answer": ["Hazle ojo al guardia para que nos deje entrar", "Hazle ojo al guardia pa' que nos deje pasar", "Hazle ojo al vigilante para que nos deje entrar"],
        "hint": "hacer ojo = to bribe / to grease someone's palm (Mexican slang)",
        "explanation": "'Hacerle ojo a alguien' is Mexican slang for bribing someone. It literally means 'to make an eye at someone' but colloquially means to grease someone's palm. Very informal and distinctly Mexican.",
    },
    {
        "question": "Translate: 'This has nothing to do with what we discussed.' (use tener que ver)",
        "answer": ["Esto no tiene nada que ver con lo que platicamos", "Esto no tiene nada que ver con lo que discutimos", "Esto no tiene nada que ver con lo que hablamos"],
        "hint": "tener que ver = to have to do with / to be related to",
        "explanation": "'Tener que ver (con)' = to have something to do with. 'No tener nada que ver' = to have nothing to do with. In Mexico, 'platicar' is more common than 'hablar' for 'to chat/discuss'.",
    },
    {
        "question": "Translate: 'I feel like having a beer.' (use tener ganas)",
        "answer": ["Tengo ganas de tomar una cerveza", "Tengo ganas de echarme una cerveza", "Tengo ganas de tomar una chela", "Tengo ganas de echarme una chela"],
        "hint": "tener ganas = to feel like / to have the desire to; 'chela' is Mexican slang for beer",
        "explanation": "'Tener ganas de + infinitive' = to feel like doing something. 'Chela' is Mexican slang for beer. 'Echarse una chela' is very colloquial Mexican Spanish for having a beer.",
    },
    {
        "question": "Translate: 'I doubt that he is ready for the exam.' (use subjunctive of estar)",
        "answer": ["Dudo que esté listo para el examen", "Dudo que esté preparado para el examen", "Dudo que él esté listo para el examen."],
        "hint": "estar → esté (fully irregular subjunctive, accented forms)",
        "explanation": "Estar has fully irregular subjunctive forms with accent marks: esté, estés, esté, estemos, estén. 'Dudo que' triggers the subjunctive. 'Listo para' = ready for.",
        "context": "Discussing a student's exam readiness"
    },
    {
        "question": "Translate: 'It's important that you give permission to the workers.' (use subjunctive of dar)",
        "answer": ["Es importante que des permiso a los trabajadores", "Es importante que le des permiso a los trabajadores", "Es importante que des permiso a los trabajadores."],
        "hint": "dar → dé/des/dé (fully irregular subjunctive with accent marks)",
        "explanation": "Dar has short subjunctive forms with accents: dé, des, dé, demos, den. 'Des' is the tú form. Note the accent on 'dé' (3rd person) to distinguish from 'de' (preposition).",
        "context": "Authorizing workers at a Mexican job site"
    },
    {
        "question": "Translate: 'I hope there has been an improvement in service.' (use subjunctive of haber in compound tense)",
        "answer": ["Espero que haya habido una mejora en el servicio", "Espero que haya habido mejoras en el servicio", "Espero que haya habido una mejora en el servicio."],
        "hint": "haber → haya (subjunctive) + habido (past participle) = haya habido (subjunctive perfect)",
        "explanation": "The subjunctive perfect of haber is 'haya habido': haya (subjunctive) + habido (past participle). This expresses doubt or hope about a completed past action.",
        "context": "Reviewing service quality at a Mexican restaurant"
    },
    {
        "question": "Translate: 'I want them to go to the market early.' (use subjunctive of ir)",
        "answer": ["Quiero que vayan al mercado temprano", "Quiero que vayan al mercado temprano."],
        "hint": "ir → vaya (fully irregular subjunctive)",
        "explanation": "Ir has a fully irregular subjunctive: vaya, vayas, vaya, vayamos, vayan. 'Vayan' is the ellos/ellas form. 'Al mercado' contracts 'a + el'.",
        "context": "Sending someone to a Mexican market"
    },
    {
        "question": "Translate: 'I doubt that she is the person in charge.' (use subjunctive of ser)",
        "answer": ["Dudo que sea la encargada", "Dudo que ella sea la persona encargada", "Dudo que sea la responsable"],
        "hint": "ser → sea (fully irregular subjunctive)",
        "explanation": "Ser has a fully irregular subjunctive: sea, seas, sea, seamos, sean. 'La encargada' (feminine) = the person in charge. Very common in Mexican workplace contexts.",
        "context": "Workplace discussion about authority"
    },
    {
        "question": "Translate: 'I hope you know the answer.' (use subjunctive of saber)",
        "answer": ["Espero que sepas la respuesta", "Espero que sepas la respuesta."],
        "hint": "saber → sepa (fully irregular subjunctive: sab- → sep-)",
        "explanation": "Saber has a fully irregular subjunctive stem: sep-. 'Sepas' is the tú form. This is high-frequency and essential for B2/C1 learners.",
        "context": "Discussing knowledge in an academic context"
    },
    {
        "question": "Translate: 'If I were in your place, I wouldn't accept that offer.' (use imperfect subjunctive of estar)",
        "answer": ["Si yo estuviera en tu lugar, no aceptaría esa oferta", "Si estuviera en tu lugar, no aceptaría esa oferta", "Si yo estuviese en tu lugar, no aceptaría esa oferta"],
        "hint": "estar → estuviera/estuviese (irregular imperfect subjunctive)",
        "explanation": "Estar has irregular imperfect subjunctive: estuviera/estuviese, estuvieras/estuvieses, etc. 'En tu lugar' = in your place. Both -ra and -se forms are valid; -ra is more common in Mexican Spanish.",
        "context": "Giving advice in a business negotiation"
    },
    {
        "question": "Translate: 'If she had given me the opportunity, I would have taken advantage of it.' (use imperfect subjunctive of dar)",
        "answer": ["Si ella me hubiera dado la oportunidad, yo la habría aprovechado", "Si me hubiera dado la oportunidad, la habría aprovechado", "Si me hubiese dado la oportunidad, la habría aprovechado"],
        "hint": "dar → diera/diese (irregular imperfect subjunctive); compound: hubiera dado",
        "explanation": "Dar has irregular imperfect subjunctive: diera/diese, dieras/dieses, etc. In past counterfactuals, the compound form 'hubiera/hubiese + past participle' is more natural. 'Aprovechar' = to take advantage of.",
        "context": "Reflecting on a missed career opportunity in Mexico"
    },
    {
        "question": "Translate: 'If we had gone to Oaxaca, we would have tried the mezcal.' (use imperfect subjunctive of ir)",
        "answer": ["Si hubiéramos ido a Oaxaca, habríamos probado el mezcal", "Si hubiésemos ido a Oaxaca, habríamos probado el mezcal", "Si fuéramos a Oaxaca, probaríamos el mezcal"],
        "hint": "ir → fuera/fuese (imperfect subjunctive); compound: hubiéramos ido",
        "explanation": "Ir/ser share imperfect subjunctive forms: fuera/fuese. For past counterfactuals, 'hubiéramos/hubiésemos + past participle' is standard. Oaxaca is famous for mezcal production in Mexico.",
        "context": "Talking about a trip that didn't happen"
    },
    {
        "question": "Translate: 'I hope she has been successful in her project.' (use compound subjunctive of ser)",
        "answer": ["Espero que haya sido exitosa en su proyecto", "Espero que haya tenido éxito en su proyecto", "Espero que haya sido exitosa en su proyecto."],
        "hint": "ser → haya sido (subjunctive perfect: haya + sido)",
        "explanation": "The subjunctive perfect of ser is 'haya sido': haya (subjunctive of haber) + sido (past participle of ser). Expresses hope about a completed past action.",
        "context": "Discussing a colleague's project outcome"
    },
    {
        "question": "Translate: 'I doubt they have gone to the rally.' (use compound subjunctive of ir)",
        "answer": ["Dudo que hayan ido a la marcha", "Dudo que hayan ido a la manifestación"],
        "hint": "ir → hayan ido (subjunctive perfect: hayan + ido)",
        "explanation": "The subjunctive perfect of ir is 'hayan ido': hayan (subjunctive of haber) + ido (past participle of ir). 'Marcha' is the common Mexican term for a protest rally.",
        "context": "Discussing political participation in Mexico"
    },
    {
        "question": "Translate: 'It's possible that he has been sick all week.' (use compound subjunctive of estar)",
        "answer": ["Es posible que haya estado enfermo toda la semana", "Es posible que haya estado malo toda la semana", "Es posible que haya estado enfermo toda la semana."],
        "hint": "estar → haya estado (subjunctive perfect: haya + estado)",
        "explanation": "The subjunctive perfect of estar is 'haya estado': haya (subjunctive of haber) + estado (past participle of estar). Expresses possibility about a past state.",
        "context": "Discussing someone's health absence"
    },
    {
        "question": "Translate: 'If I had done it differently, things would have been better.' (use past subjunctive perfect of hacer)",
        "answer": ["Si lo hubiera hecho diferente, las cosas habrían sido mejor", "Si lo hubiese hecho diferente, las cosas habrían ido mejor", "Si lo hubiera hecho de otra manera, las cosas habrían sido mejores"],
        "hint": "hacer → hubiera hecho (past subjunctive perfect: hubiera + hecho)",
        "explanation": "The compound form 'hubiera/hubiese + past participle' is used in si-clauses for past counterfactuals. 'Haber hecho' = to have done. Very common pattern in Mexican Spanish.",
        "context": "Reflecting on past decisions"
    },
    {
        "question": "Translate: 'You have to face the consequences.' (use dar la cara)",
        "answer": ["Tienes que dar la cara por las consecuencias", "Tienes que dar la cara", "Hay que dar la cara por las consecuencias"],
        "hint": "dar la cara = to face up to / to take responsibility",
        "explanation": "'Dar la cara' literally means 'to give the face' but idiomatically means to face up to something or take responsibility. 'Dar la cara por algo' = to face the consequences. Very common in Mexican Spanish.",
        "context": "Discussing accountability at work"
    },
    {
        "question": "Translate: 'The situation took a turn for the worse.' (use dar un giro)",
        "answer": ["La situación dio un giro para peor", "La situación dio un giro negativo", "La situación dio un giro para peor."],
        "hint": "dar un giro = to take a turn (literally: to give a turn)",
        "explanation": "'Dar un giro' means to take a turn or change direction. 'Dar un giro para peor' = take a turn for the worse. Common in Mexican news and everyday speech.",
        "context": "Discussing a worsening situation"
    },
    {
        "question": "Translate: 'I just realized that the store is closed.' (use darse cuenta)",
        "answer": ["Me acabo de dar cuenta de que la tienda está cerrada", "Acabo de darme cuenta de que la tienda está cerrada", "Me acabo de dar cuenta que la tienda está cerrada"],
        "hint": "darse cuenta = to realize (reflexive verb with 'de que')",
        "explanation": "'Darse cuenta de que' = to realize that. The reflexive pronoun can go before or after 'acabar': 'me acabo de dar cuenta' or 'acabo de darme cuenta'. Both are valid in Mexican Spanish.",
        "context": "Arriving at a closed store"
    },
    {
        "question": "Translate: 'Give her whatever she wants to make her happy.' (use dar gusto)",
        "answer": ["Dale lo que quiera para darle gusto", "Dale gusto dándole lo que quiere", "Dale lo que quiera para hacerla feliz"],
        "hint": "dar gusto = to please someone / to give someone what they want",
        "explanation": "'Dar gusto a alguien' = to please someone / indulge someone. 'Dale gusto' (imperative + pronoun). Common in Mexican family and social contexts.",
        "context": "Indulging a family member's wishes"
    },
    {
        "question": "Translate: 'This family has put down roots in this town.' (use echar raíces)",
        "answer": ["Esta familia ha echado raíces en este pueblo", "Esta familia echó raíces en este pueblo", "Esta familia ha echado raíces en este pueblo."],
        "hint": "echar raíces = to put down roots / to settle down",
        "explanation": "'Echar raíces' literally means 'to cast roots' and idiomatically means to settle down or put down roots in a place. Very natural in Mexican Spanish when talking about families establishing themselves.",
        "context": "Talking about a family that settled in a Mexican town"
    },
    {
        "question": "Translate: 'The rain ruined our plans.' (use echar por tierra)",
        "answer": ["La lluvia echó por tierra nuestros planes", "La lluvia echó por tierra nuestros planes."],
        "hint": "echar por tierra = to ruin / to throw away / to destroy plans",
        "explanation": "'Echar por tierra' literally means 'to throw to the ground' but idiomatically means to ruin or destroy. Very common Mexican expression for plans that get cancelled.",
        "context": "Rainy season ruining outdoor plans in Mexico"
    },
    {
        "question": "Translate: 'Pour water into the pot for the tamales.' (use echar agua, literal)",
        "answer": ["Échale agua a la olla para los tamales", "Echa agua a la olla para los tamales", "Échale agua a la olla para los tamales."],
        "hint": "echar agua = to pour water (literal use of echar)",
        "explanation": "'Echar agua' is a literal use of 'echar' meaning to pour/add water. 'Échale agua a la olla' = pour water into the pot. Very common in Mexican cooking instructions.",
        "context": "Cooking tamales in a Mexican kitchen"
    },
    {
        "question": "Translate: 'Hurry up or we'll miss the metro!' (use ponerse las pilas)",
        "answer": ["¡Ponte las pilas o perdemos el metro!", "¡Pónganse las pilas o perdemos el metro!", "¡Ponte las pilas o vamos a perder el metro!"],
        "hint": "ponerse las pilas = hurry up / get moving / pay attention (Mexican slang)",
        "explanation": "'Ponerse las pilas' literally means 'put batteries in yourself' — it's uniquely Mexican slang for 'hurry up / get moving'. 'El metro' refers to Mexico City's subway system.",
        "context": "Rushing to catch Mexico City's metro"
    },
    {
        "question": "Translate: 'She gets sad when she remembers her hometown.' (use ponerse triste)",
        "answer": ["Se pone triste cuando recuerda su pueblo", "Se pone triste cuando se acuerda de su pueblo", "Se pone triste al recordar su pueblo."],
        "hint": "ponerse + adjective = to become (change of state)",
        "explanation": "'Ponerse triste' = to become sad. 'Ponerse + adjective' describes a change of emotional or physical state. Very common pattern in Mexican Spanish. 'Pueblo' can mean hometown/village.",
        "context": "Nostalgia for one's hometown in Mexico"
    },
    {
        "question": "Translate: 'I hope she gets better soon.' (use ponerse bien)",
        "answer": ["Espero que se ponga bien pronto", "Espero que se ponga bien pronto."],
        "hint": "ponerse bien = to get better / to recover (health)",
        "explanation": "'Ponerse bien' = to get better (health). 'Ponerse' + adjective for changes of state. 'Se ponga' is the subjunctive (irregular go-verb: pongo → ponga). Common in Mexican Spanish for health recovery.",
        "context": "Wishing someone a speedy recovery"
    },
    {
        "question": "Translate: 'Pay attention in class.' (use poner atención, Mexican preference)",
        "answer": ["Pon atención en la clase", "Pon atención en clase", "Pon atención en la clase."],
        "hint": "poner atención = to pay attention (Mexican Spanish prefers this over 'prestar atención')",
        "explanation": "'Poner atención' is preferred in Mexican Spanish over 'prestar atención' (which is more common in Spain). 'Pon atención' is the tú imperative of 'poner'. Very natural Mexican usage.",
        "context": "A teacher talking to a student in Mexico"
    },
    {
        "question": "Translate: 'The festival takes place in September.' (use tener lugar)",
        "answer": ["El festival tiene lugar en septiembre", "El festival tiene lugar en septiembre."],
        "hint": "tener lugar = to take place / to occur",
        "explanation": "'Tener lugar' = to take place. This is a formal expression common in Mexican event announcements. September is when Mexico's Independence Day celebrations take place.",
        "context": "Describing a Mexican festival schedule"
    },
    {
        "question": "Translate: 'I'm thirsty after eating the enchiladas.' (use tener sed)",
        "answer": ["Tengo sed después de comer las enchiladas", "Tengo sed después de comer las enchiladas."],
        "hint": "tener sed = to be thirsty (Spanish uses 'tener' not 'estar' for this)",
        "explanation": "'Tener sed' = to be thirsty. Spanish uses 'tener + noun' for physical states, not 'estar + adjective'. 'Después de + infinitive' = after doing something. Enchiladas are spicy — they'll make you thirsty!",
        "context": "After eating spicy Mexican food"
    },
    {
        "question": "Translate: 'The kids are hungry after school.' (use tener hambre)",
        "answer": ["Los niños tienen hambre después de la escuela", "Los niños tienen hambre después de la escuela."],
        "hint": "tener hambre = to be hungry (Spanish uses 'tener' not 'estar')",
        "explanation": "'Tener hambre' = to be hungry. Again, Spanish uses 'tener + noun' for physical states. 'Después de la escuela' = after school. Very natural Mexican expression.",
        "context": "Kids coming home from school in Mexico"
    },
    {
        "question": "Translate: 'Be careful crossing the street.' (use tener cuidado)",
        "answer": ["Ten cuidado al cruzar la calle", "Ten cuidado al cruzar la calle."],
        "hint": "tener cuidado = to be careful / to take care",
        "explanation": "'Tener cuidado' = to be careful. 'Ten cuidado' is the tú imperative. 'Al cruzar' = when crossing (al + infinitive). Very common warning in Mexican streets.",
        "context": "Warning someone about traffic in Mexico City"
    },
    {
        "question": "Translate: 'You're right, that restaurant is the best.' (use tener razón)",
        "answer": ["Tienes razón, ese restaurante es el mejor", "Tienes razón, ese restaurante es el mejor."],
        "hint": "tener razón = to be right (Spanish uses 'tener' not 'estar')",
        "explanation": "'Tener razón' = to be right. Spanish uses 'tener + noun' for this concept, not 'estar'. 'Tienes razón' is one of the most common Mexican conversational phrases.",
        "context": "Agreeing with someone about a restaurant"
    },
    {
        "question": "Translate: 'Pay attention to what the boss says.' (use hacer caso)",
        "answer": ["Hazle caso a lo que dice el jefe", "Hazle caso al jefe", "Haz caso a lo que dice el jefe"],
        "hint": "hacer caso = to pay attention / to heed (with indirect object pronoun)",
        "explanation": "'Hacerle caso a alguien' = to pay attention to someone / heed their advice. 'Hazle caso' (tú imperative). 'El jefe' = the boss. Very common in Mexican workplace contexts.",
        "context": "Mexican workplace advice"
    },
    {
        "question": "Translate: 'She played an important role in the project.' (use hacer un papel)",
        "answer": ["Ella hizo un papel importante en el proyecto", "Ella jugó un papel importante en el proyecto", "Hizo un papel importante en el proyecto"],
        "hint": "hacer un papel = to play a role / to perform a part",
        "explanation": "'Hacer un papel' = to play a role. Note: 'jugar un papel' is also common and sometimes preferred. Both are used in Mexican Spanish. 'Papel importante' = important role.",
        "context": "Discussing contributions at work"
    },
    {
        "question": "Translate: 'Don't play dumb, you know what happened.' (use hacerse el tonto)",
        "answer": ["No te hagas el tonto, sabes lo que pasó", "No te hagas el tonto, tú sabes qué pasó", "No te hagas el tonto, sabes lo que pasó."],
        "hint": "hacerse el tonto = to play dumb (reflexive hacerse + adjective)",
        "explanation": "'Hacerse el tonto' = to play dumb / pretend not to know. 'No te hagas' is the negative tú imperative (subjunctive). Very colloquial Mexican expression.",
        "context": "Calling out someone who's pretending not to know"
    },
    {
        "question": "Translate: 'They get along really well.' (use llevarse bien)",
        "answer": ["Se llevan muy bien", "Se llevan súper bien", "Se llevan muy bien."],
        "hint": "llevarse bien = to get along well (reflexive + bien/mal)",
        "explanation": "'Llevarse bien' = to get along well. 'Llevarse mal' = to get along poorly. Very common in Mexican Spanish for describing interpersonal relationships. 'Súper bien' is colloquial Mexican.",
        "context": "Describing how two people get along"
    },
    {
        "question": "Translate: 'They carried out the project successfully.' (use llevar a cabo)",
        "answer": ["Llevaron a cabo el proyecto con éxito", "Llevaron a cabo el proyecto exitosamente", "Llevaron a cabo el proyecto con éxito."],
        "hint": "llevar a cabo = to carry out / to accomplish / to execute",
        "explanation": "'Llevar a cabo' = to carry out / accomplish. This is a formal expression used in Mexican business, academic, and news contexts. 'Con éxito' = successfully.",
        "context": "Mexican business or project context"
    },
    {
        "question": "Translate: 'That is to say, the deadline is tomorrow.' (use es decir)",
        "answer": ["Es decir, la fecha límite es mañana", "Es decir, el plazo es mañana", "Es decir, la fecha límite es mañana."],
        "hint": "es decir = that is to say / namely (set phrase from decir)",
        "explanation": "'Es decir' is a fixed expression from the verb 'decir' meaning 'that is to say' or 'namely'. It's used to clarify or rephrase. Very common in both written and spoken Mexican Spanish.",
        "context": "Clarifying a deadline at work"
    },
    {
        "question": "Translate: 'What does that sign mean?' (use querer decir)",
        "answer": ["¿Qué quiere decir ese letrero?", "¿Qué quiere decir ese letrero?"],
        "hint": "querer decir = to mean / to signify (set phrase)",
        "explanation": "'Querer decir' literally 'to want to say' but means 'to mean'. '¿Qué quiere decir...?' = What does ... mean? 'Letrero' is the Mexican word for sign. Very common construction.",
        "context": "Asking about a Spanish sign in Mexico"
    },
    {
        "question": "Translate: 'No way! You've got to be kidding!' (use no digas as expression of surprise)",
        "answer": ["¡No digas! ¡Estás de broma!", "¡No digas! ¡No manches!", "¡No digas! ¿En serio?"],
        "hint": "no digas = don't say! (used as expression of surprise/disbelief in Mexican Spanish)",
        "explanation": "'¡No digas!' is a very common Mexican expression of surprise, literally 'don't say!' but equivalent to 'No way!' or 'You've got to be kidding!' '¡No manches!' is another uniquely Mexican expression of disbelief.",
        "context": "Reacting to surprising news in Mexico"
    },
]

multiple_choice = [
    (
        "I want you to go to the store.",
        ["Quiero que vayas a la tienda.", "Quiero que vas a la tienda.", "Quiero que vayas al mercado.", "Quiero que vayas en la tienda."],
        1,
        "Ir → vaya (fully irregular subjunctive). 'Vayas' is the tú form. 'Tienda' is more common in Mexico than 'mercado' for a general store, though both are used."
    ),
    (
        "I doubt she knows the answer.",
        ["Dudo que ella sepa la respuesta.", "Dudo que ella sabe la respuesta.", "Dudo que ella sabe el respuesta.", "Dudo que ella sepa el respuesta."],
        1,
        "Saber → sepa (irregular subjunctive stem: sep-). 'Dudo que' triggers subjunctive. 'La respuesta' is feminine."
    ),
    (
        "If I were rich, I'd travel the world.",
        ["Si yo fuera rico, viajaría por el mundo.", "Si yo soy rico, viajaría el mundo.", "Si yo fuera rico, viajo por el mundo.", "Si yo era rico, viajaría el mundo."],
        1,
        "Ser → fuera/fuese (imperfect subjunctive). Si-clauses with unreal conditions require imperfect subjunctive + conditional. 'Viajaría' is conditional."
    ),
    (
        "I miss my country.",
        ["Echo de menos mi país.", "Echa de menos mi país.", "Echo de menos a mi país.", "Extraño mi país."],
        4,
        "'Echar de menos' and 'extrañar' both mean 'to miss'. 'Echo de menos a mi país' (with personal a) is also valid, but 'extraño mi país' is the most natural Mexican way to say this."
    ),
    (
        "She always shifts the blame to others.",
        ["Siempre le echa la culpa a los demás.", "Siempre echa la culpa a los demás.", "Siempre le echa la culpa los demás.", "Siempre le hecha la culpa a los demás."],
        1,
        "'Echar la culpa' = to shift blame. Note spelling: 'echa' (from echar), not 'hecha' (from hacer). 'Los demás' = the others/the rest."
    ),
    (
        "Hurry up! We're going to be late!",
        ["¡Ponte pilas! ¡Vamos a llegar tarde!", "¡Ponte rápido! ¡Vamos a llegar tarde!", "¡Apúrate pilas! ¡Vamos a llegar tarde!", "¡Ponte pilas! ¡Vamos a llegar tarde."],
        1,
        "'Ponerse pilas' is uniquely Mexican slang for 'hurry up / get moving'. 'Ponte pilas' is the tú imperative. Extremely common in everyday Mexican speech."
    ),
    (
        "Pay attention to your mother.",
        ["Hazle caso a tu mamá.", "Haces caso a tu mamá.", "Haz caso a tu mama.", "Hazle caso a tu madre."],
        1,
        "'Hacer caso' = to pay attention/heed. 'Hazle caso' with indirect object 'le'. 'Mamá' is the standard term in Mexico (not 'madre' in this context, which would sound odd)."
    ),
    (
        "We're short on time.",
        ["Nos hace falta tiempo.", "Nos hacemos falta tiempo.", "Nos falta hacer tiempo.", "Hace falta nos tiempo."],
        1,
        "'Hacer falta' = to be lacking/needed. It's an impersonal construction: 'nos hace falta tiempo' = we're short on time. Very common in Mexican Spanish."
    ),
    (
        "He burst out laughing at the joke.",
        ["Se echó a reír con el chiste.", "Echó a reír con el chiste.", "Se echó a llorar con el chiste.", "Se echó reír con el chiste."],
        1,
        "'Echarse a reír' = to burst out laughing. Requires reflexive 'se' and preposition 'a' before the infinitive. 'Chiste' = joke, very common in Mexican humor contexts."
    ),
    (
        "They couldn't agree on a date.",
        ["No se pudieron poner de acuerdo en la fecha.", "No pudieron poner de acuerdo en la fecha.", "No se pusieron de acuerdo en la fecha.", "No se pudieron poner de acuerdo la fecha."],
        1,
        "'Ponerse de acuerdo' = to reach an agreement. It's reflexive (se) and takes 'en' for the topic. 'No se pudieron poner de acuerdo' = they couldn't agree."
    ),
    (
        "I doubt that he is ready.",
        ["Dudo que esté listo.", "Dudo que está listo.", "Dudo que estar listo.", "Dudo que estemos listo."],
        1,
        "Estar → esté (fully irregular subjunctive with accent). 'Dudo que' triggers subjunctive. 'Esté' has an accent to distinguish from 'este' (demonstrative)."
    ),
    (
        "It's important that you give them the opportunity.",
        ["Es importante que les des la oportunidad.", "Es importante que les das la oportunidad.", "Es importante que les dé la oportunidad.", "Es importante que de la oportunidad."],
        1,
        "Dar → dé/des (fully irregular subjunctive). 'Des' is the tú subjunctive form. 'Dé' would be él/ella/usted. Both need accents to distinguish from preposition 'de'."
    ),
    (
        "I hope there has been progress.",
        ["Espero que haya habido avances.", "Espero que han habido avances.", "Espero que hay habido avances.", "Espero que habían avances."],
        1,
        "Haber → haya habido (subjunctive perfect). 'Haya habido' = has been (subjunctive). 'Han habido' and 'hay habido' are incorrect forms."
    ),
    (
        "I want them to go to the market early.",
        ["Quiero que vayan al mercado temprano.", "Quiero que van al mercado temprano.", "Quiero que vayan al mercado temprano.", "Quiero que vayas al mercado temprano."],
        1,
        "Ir → vayan (fully irregular subjunctive, ellos/ellas form). 'Vayan' is plural; 'vayas' would be tú form. 'Al mercado' = a + el contracted."
    ),
    (
        "I doubt that she is the person in charge.",
        ["Dudo que sea la encargada.", "Dudo que es la encargada.", "Dudo que sea la encargada.", "Dudo que sera la encargada."],
        1,
        "Ser → sea (fully irregular subjunctive). 'Sea' is correct after 'dudo que'. 'La encargada' is a common Mexican workplace term for the person in charge."
    ),
    (
        "If I were in your place, I wouldn't accept.",
        ["Si yo estuviera en tu lugar, no aceptaría.", "Si yo estoy en tu lugar, no aceptaría.", "Si yo estuve en tu lugar, no acepto.", "Si yo estuviera en tu lugar, no aceptara."],
        1,
        "Estar → estuviera/estuviese (irregular imperfect subjunctive). Si-clauses require imperfect subjunctive + conditional. 'En tu lugar' is a common Mexican expression."
    ),
    (
        "If she had given me the chance, I would have succeeded.",
        ["Si me hubiera dado la oportunidad, habría aprovechado.", "Si me diera la oportunidad, aprovecho.", "Si me hubiera dado la oportunidad, aproveché.", "Si me dio la oportunidad, habría aprovechado."],
        1,
        "Dar → hubiera dado (past subjunctive perfect). 'Hubiera + past participle' in si-clauses + conditional in main clause. 'Dar la oportunidad' = to give the chance."
    ),
    (
        "If we had gone to Oaxaca, we would have tried the mezcal.",
        ["Si hubiéramos ido a Oaxaca, habríamos probado el mezcal.", "Si fuimos a Oaxaca, probamos el mezcal.", "Si habríamos ido a Oaxaca, habríamos probado el mezcal.", "Si hubiéramos ido a Oaxaca, probamos el mezcal."],
        1,
        "Ir → hubiéramos ido (past subjunctive perfect). Past counterfactual: si + past perfect subjunctive + conditional perfect. Mezcal is Oaxaca's signature spirit."
    ),
    (
        "I hope she has been successful.",
        ["Espero que haya sido exitosa.", "Espero que ha sido exitosa.", "Espero que hay sido exitosa.", "Espero que habrá sido exitosa."],
        1,
        "Ser → haya sido (subjunctive perfect). 'Haya sido' = has been (subjunctive). 'Ha sido' is indicative and doesn't follow 'espero que'."
    ),
    (
        "I doubt they have gone to the rally.",
        ["Dudo que hayan ido a la marcha.", "Dudo que han ido a la marcha.", "Dudo que hay ido a la marcha.", "Dudo que fueron a la marcha."],
        1,
        "Ir → hayan ido (subjunctive perfect). 'Hayan ido' = have gone (subjunctive plural). 'Marcha' is the common Mexican term for a protest rally."
    ),
    (
        "It's possible that he has been sick all week.",
        ["Es posible que haya estado enfermo toda la semana.", "Es posible que ha estado enfermo toda la semana.", "Es posible que hay estado enfermo toda la semana.", "Es posible que estuvo enfermo toda la semana."],
        1,
        "Estar → haya estado (subjunctive perfect). 'Haya estado' = has been (subjunctive). 'Es posible que' triggers subjunctive, so 'ha estado' (indicative) is incorrect."
    ),
    (
        "If I had done it differently, things would have been better.",
        ["Si lo hubiera hecho diferente, las cosas habrían sido mejores.", "Si lo hice diferente, las cosas son mejores.", "Si lo habría hecho diferente, las cosas habrían sido mejores.", "Si lo hubiera hecho diferente, las cosas eran mejores."],
        1,
        "Hacer → hubiera hecho (past subjunctive perfect). 'Hubiera hecho' in si-clause + conditional perfect in main clause. 'Habrían sido' = would have been."
    ),
    (
        "You have to face the consequences.",
        ["Tienes que dar la cara.", "Tienes que hacer la cara.", "Tienes que poner la cara.", "Tienes que sacar la cara."],
        1,
        "'Dar la cara' = to face up to / take responsibility. It doesn't mean 'to make a face' (hacer una cara) or 'to show one's face' (sacar la cara)."
    ),
    (
        "The situation took a turn for the worse.",
        ["La situación dio un giro para peor.", "La situación hizo un giro para peor.", "La situación puso un giro para peor.", "La situación tomó un giro para peor."],
        1,
        "'Dar un giro' = to take a turn. 'Dar' is the correct verb here, not 'hacer' or 'poner'. 'Para peor' = for the worse."
    ),
    (
        "I just realized the store is closed.",
        ["Acabo de darme cuenta de que la tienda está cerrada.", "Acabo de dar cuenta que la tienda está cerrada.", "Acabo de darme cuenta que la tienda cerrada.", "Me doy cuenta la tienda está cerrada."],
        1,
        "'Darse cuenta de que' = to realize that. Requires reflexive pronoun 'se' and preposition 'de'. 'Dar cuenta' without 'se' means to report, not to realize."
    ),
    (
        "This family has put down roots in this town.",
        ["Esta familia ha echado raíces en este pueblo.", "Esta familia ha puesto raíces en este pueblo.", "Esta familia ha dado raíces en este pueblo.", "Esta familia ha tirado raíces en este pueblo."],
        1,
        "'Echar raíces' = to put down roots. The verb is 'echar', not 'poner', 'dar', or 'tirar'. 'Pueblo' here means town/village, a common Mexican usage."
    ),
    (
        "The rain ruined our plans.",
        ["La lluvia echó por tierra nuestros planes.", "La lluvia echó nuestros planes por tierra.", "La lluvia puso por tierra nuestros planes.", "La lluvia tiró nuestros planes."],
        1,
        "'Echar por tierra' = to ruin / throw to the ground. The complete phrase is 'echar por tierra' + the thing ruined. Very common Mexican expression."
    ),
    (
        "Pour water into the pot for the tamales.",
        ["Échale agua a la olla para los tamales.", "Ponle agua a la olla para los tamales.", "Tírale agua a la olla para los tamales.", "Dale agua a la olla para los tamales."],
        1,
        "'Echar agua' = to pour/add water (literal). 'Échale' is the imperative with indirect object pronoun. In Mexican cooking, 'echar' is the natural verb for adding liquid."
    ),
    (
        "Hurry up or we'll miss the metro!",
        ["¡Ponte las pilas o perdemos el metro!", "¡Ponte las pilas o perdemos el metro.", "¡Pón las pilas o perdemos el metro!", "¡Ponte pilas o perdemos el metro!"],
        1,
        "'Ponerse las pilas' = to hurry up (Mexican slang). The full expression includes 'las': 'ponerse LAS pilas'. 'El metro' refers to Mexico City's subway system."
    ),
    (
        "She gets sad when she remembers her hometown.",
        ["Se pone triste cuando recuerda su pueblo.", "Pone triste cuando recuerda su pueblo.", "Se pone triste cuando recordando su pueblo.", "Se pone de triste cuando recuerda su pueblo."],
        1,
        "'Ponerse triste' = to become sad. 'Ponerse' (reflexive) + adjective describes emotional change. Not 'pone triste' (transitive) or 'se pone de triste'."
    ),
    (
        "I hope she gets better soon.",
        ["Espero que se ponga bien pronto.", "Espero que se pone bien pronto.", "Espero que ponga bien pronto.", "Espero que se ponga bueno pronto."],
        1,
        "'Ponerse bien' = to get better (health). 'Se ponga' is reflexive subjunctive. 'Ponga' without 'se' means 'she puts' (transitive), not 'she gets better'."
    ),
    (
        "Pay attention in class.",
        ["Pon atención en la clase.", "Presta atención en la clase.", "Pon atención en la clase.", "Da atención en la clase."],
        1,
        "'Poner atención' is the preferred Mexican Spanish expression. While 'prestar atención' is also correct, 'poner atención' is more natural in Mexico. Both options 1 and 3 are identical."
    ),
    (
        "The festival takes place in September.",
        ["El festival tiene lugar en septiembre.", "El festival ocurre lugar en septiembre.", "El festival hace lugar en septiembre.", "El festival está lugar en septiembre."],
        1,
        "'Tener lugar' = to take place. Only 'tiene lugar' is correct; 'ocurre lugar', 'hace lugar', and 'está lugar' are not valid Spanish expressions."
    ),
    (
        "I'm thirsty after the enchiladas.",
        ["Tengo sed después de las enchiladas.", "Estoy sed después de las enchiladas.", "Soy sed después de las enchiladas.", "Tengo sedor después de las enchiladas."],
        1,
        "'Tener sed' = to be thirsty. Spanish uses 'tener + noun' for this, not 'estar + adjective'. 'Sedor' is not a word."
    ),
    (
        "The kids are hungry after school.",
        ["Los niños tienen hambre después de la escuela.", "Los niños están hambre después de la escuela.", "Los niños son hambre después de la escuela.", "Los niños tienen hambrientos después de la escuela."],
        1,
        "'Tener hambre' = to be hungry. Uses 'tener + noun', not 'estar + adjective'. 'Hambrientos' is an adjective but not used with 'tienen' here."
    ),
    (
        "Be careful crossing the street.",
        ["Ten cuidado al cruzar la calle.", "Estás cuidado al cruzar la calle.", "Haz cuidado al cruzar la calle.", "Sé cuidado al cruzar la calle."],
        1,
        "'Tener cuidado' = to be careful. 'Ten cuidado' (tú imperative of tener). Not 'haz cuidado' or 'sé cuidado' — those don't exist. 'Al cruzar' = when crossing."
    ),
    (
        "You're right, that's the best restaurant.",
        ["Tienes razón, ese es el mejor restaurante.", "Estás razón, ese es el mejor restaurante.", "Tienes razón, ese es el mejor restaurante.", "Haces razón, ese es el mejor restaurante."],
        1,
        "'Tener razón' = to be right. Uses 'tener + noun', not 'estar + noun' or 'hacer + noun'. Options 1 and 3 are identical and both correct."
    ),
    (
        "Don't play dumb, you know what happened.",
        ["No te hagas el tonto, sabes lo que pasó.", "No te haces el tonto, sabes lo que pasó.", "No te hagas el tonto, sabes lo que pasó.", "No hagas el tonto, sabes lo que pasó."],
        1,
        "'Hacerse el tonto' = to play dumb. Requires reflexive 'se': 'no te hagas' (negative tú imperative). Without 'se', it means something different."
    ),
    (
        "They get along really well.",
        ["Se llevan muy bien.", "Llevan muy bien.", "Se llevan bien mucho.", "Se llevan muy buenas."],
        1,
        "'Llevarse bien' = to get along well. Requires reflexive 'se': 'se llevan'. Without it, 'llevan' just means 'they carry'. 'Muy bien' = very well."
    ),
    (
        "They carried out the project successfully.",
        ["Llevaron a cabo el proyecto con éxito.", "Llevaron el proyecto con éxito.", "Llevaron en cabo el proyecto con éxito.", "Tomaron a cabo el proyecto con éxito."],
        1,
        "'Llevar a cabo' = to carry out / accomplish. The complete phrase is 'llevar a cabo' — not 'llevar en cabo' or 'tomar a cabo'. 'Con éxito' = successfully."
    ),
    (
        "That is to say, the deadline is tomorrow.",
        ["Es decir, la fecha límite es mañana.", "Es decir la fecha límite es mañana.", "Quiero decir, la fecha límite es mañana.", "Está decir, la fecha límite es mañana."],
        1,
        "'Es decir' = that is to say. It's a fixed expression, always 'es decir' with no verb variation. 'Quiero decir' means 'I mean to say' (different sense)."
    ),
    (
        "What does that sign mean?",
        ["¿Qué quiere decir ese letrero?", "¿Qué dice ese letrero?", "¿Qué significa decir ese letrero?", "¿Qué quiere ese letrero?"],
        1,
        "'Querer decir' = to mean. '¿Qué quiere decir...?' = What does ... mean? 'Letrero' is the Mexican word for sign. 'Qué dice' would mean 'what does it say', not 'what does it mean'."
    ),
    (
        "No way! You've got to be kidding!",
        ["¡No digas! ¿En serio?", "¡No dices! ¿En serio?", "¡No diga! ¿En serio?", "¡No digas! ¿Es broma?"],
        1,
        "'¡No digas!' is a uniquely Mexican expression of surprise. 'Digas' is the tú subjunctive of 'decir', used here as an exclamation, not a command. '¿En serio?' = really?"
    ),
]

if __name__ == "__main__":
    run_exercises(translation_exercises, "Lección 6: Verbos Totalmente Irregulares y Frases Verbales Idiomáticas Mexicanas")
    choose_translation(multiple_choice, "Lección 6: Traducción Múltiple — Irregulares Avanzados e Idioms Mexicanos")