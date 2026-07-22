import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))
from workbook_engine import run_exercises, choose_translation

translation_exercises = [
    {
        "question": "Translate: 'I hope you sleep well tonight.' (use subjunctive of dormir)",
        "answer": ["Espero que duermas bien esta noche", "Espero que duermas bien esta noche."],
        "hint": "dormir → duerma (o→ue stem change in subjunctive)",
        "explanation": "Dormir is a stem-changing verb (o→ue) in the subjunctive: yo duerma, tú duermas, etc. In Mexico, 'Espero que duermas bien' is the natural way to wish someone a good night.",
        "context": "Talking to a friend before bedtime"
    },
    {
        "question": "Translate: 'It's important that you feel better soon.' (use subjunctive of sentir)",
        "answer": ["Es importante que sientas mejor pronto", "Es importante que te sientas mejor pronto", "Es importante que sientas mejor pronto.", "Es importante que te sientas mejor pronto."],
        "hint": "sentir → sienta (e→ie stem change in subjunctive)",
        "explanation": "Sentir changes e→ie in the subjunctive. 'Sentirse' (to feel) is reflexive — Mexicans commonly say 'Es importante que te sientas mejor'.",
    },
    {
        "question": "Translate: 'I ask that you request the documents on time.' (use subjunctive of pedir)",
        "answer": ["Pido que pidas los documentos a tiempo", "Pido que pidas los documentos a tiempo."],
        "hint": "pedir → pida (e→i stem change in subjunctive)",
        "explanation": "Pedir is an e→i stem-changing verb in the subjunctive: yo pida, tú pidas, él pida, etc. The stem change carries through all subjunctive forms.",
    },
    {
        "question": "Translate: 'Maybe we can go to Guadalajara next weekend.' (use subjunctive of poder)",
        "answer": ["Quizás podamos ir a Guadalajara el próximo fin de semana", "A lo mejor podamos ir a Guadalajara el próximo fin de semana", "Quizás podamos ir a Guadalajara el próximo fin de semana."],
        "hint": "poder → pueda (o→ue stem change in subjunctive)",
        "explanation": "Poder changes o→ue in the subjunctive. 'Quizás' or 'a lo mejor' both trigger the subjunctive in Mexican Spanish when expressing doubt or possibility.",
    },
    {
        "question": "Translate: 'The tailor needs to darn this sweater.' (use subjunctive of zurcir for spelling change c→z)",
        "answer": ["El sastre necesita que zurza este suéter", "El sastre necesita zurcir este suéter"],
        "hint": "zurcir → zurza (c→z spelling change to preserve sound)",
        "explanation": "Verbs ending in -cir change c→z in the subjunctive first person: zurcir→zurza, to preserve the /s/ sound before 'a'. In Mexico, 'zurcir' is commonly used for mending clothes.",
    },
    {
        "question": "Translate: 'I hope you protect your family.' (use subjunctive of proteger for spelling change g→j)",
        "answer": ["Espero que protejas a tu familia", "Espero que protejas a tu familia."],
        "hint": "proteger → proteja (g→j spelling change to preserve /x/ sound)",
        "explanation": "Proteger changes g→j in the subjunctive to preserve the /x/ (hard g) sound before 'a': proteja, protejas, etc. The personal 'a' is required before 'tu familia'.",
    },
    {
        "question": "Translate: 'It's necessary that you distinguish right from wrong.' (use subjunctive of distinguir for spelling change gu→g)",
        "answer": ["Es necesario que distingas el bien del mal", "Es necesario que distingas entre el bien y el mal", "Es necesario que distingas el bien del mal."],
        "hint": "distinguir → distinga (gu→g spelling change)",
        "explanation": "Distinguir drops the 'u' in the subjunctive: distinguir→distinga, distingas, etc. The 'u' in 'gu' is only needed before 'e/i' to maintain the /g/ sound; before 'a' it's unnecessary.",
    },
    {
        "question": "Translate: 'I want you to have enough money.' (use subjunctive of tener, a go-verb)",
        "answer": ["Quiero que tengas suficiente dinero", "Quiero que tengas suficiente dinero."],
        "hint": "tener → tenga (go-verb: yo tengo → subj. tenga)",
        "explanation": "Go-verbs form their subjunctive from the yo form minus -o plus subjunctive endings. Tener (tengo) → tenga, tengas, etc. 'Suficiente dinero' is natural Mexican usage.",
    },
    {
        "question": "Translate: 'Tell him to come here right now.' (use subjunctive of decir and venir)",
        "answer": ["Dile que venga aquí ahorita", "Dile que venga aquí ahorita."],
        "hint": "decir→diga, venir→venga (both go-verbs)",
        "explanation": "Both decir and venir are go-verbs: decir (digo) → diga; venir (vengo) → venga. 'Ahorita' is quintessentially Mexican and can mean 'right now' or 'in a bit' depending on context and tone.",
    },
    {
        "question": "Translate: 'I hope he does the homework.' (use subjunctive of hacer)",
        "answer": ["Espero que haga la tarea", "Espero que haga la tarea."],
        "hint": "hacer → haga (go-verb: yo hago → subj. haga)",
        "explanation": "Hacer is a go-verb: yo hago → subj. haga, hagas, etc. 'La tarea' is the standard Mexican term for homework.",
    },
    {
        "question": "Translate: 'It's good that you bring the sauce.' (use subjunctive of traer)",
        "answer": ["Es bueno que traigas la salsa", "Es bueno que traigas la salsa."],
        "hint": "traer → traiga (go-verb with irregular yo form)",
        "explanation": "Traer has an irregular go-verb form: yo traigo → subj. traiga, traigas, etc. In Mexico, 'salsa' is ubiquitous — every meal comes with salsa.",
    },
    {
        "question": "Translate: 'Maybe they destroy the old building.' (use subjunctive of destruir, y-change verb)",
        "answer": ["Quizás destruyan el edificio viejo", "A lo mejor destruyan el edificio viejo", "Quizás destruyan el edificio viejo."],
        "hint": "destruir → destruya (i→y change in subjunctive)",
        "explanation": "Verbs ending in -uir change i→y in all subjunctive forms: destruir → destruya, destruyas, destruya, etc. This applies to influir, huir, concluir, and others.",
    },
    {
        "question": "Translate: 'I hope she leaves early tomorrow.' (use subjunctive of salir, a go-verb)",
        "answer": ["Espero que salga temprano mañana", "Espero que salga temprano mañana."],
        "hint": "salir → salga (go-verb: yo salgo → subj. salga)",
        "explanation": "Salir is a go-verb: yo salgo → subj. salga, salgas, etc. 'Salir temprano' is very common in Mexican workplace culture.",
    },
    {
        "question": "Translate: 'We want you to put the bags here.' (use subjunctive of poner, a go-verb)",
        "answer": ["Queremos que pongas las bolsas aquí", "Queremos que pongas las bolsas aquí."],
        "hint": "poner → ponga (go-verb: yo pongo → subj. ponga)",
        "explanation": "Poner is a go-verb: yo pongo → subj. ponga, pongas, etc. 'Bolsas' is used for bags in Mexican Spanish.",
    },
    {
        "question": "Translate: 'Maybe he influences the decision.' (use subjunctive of influir, a y-change verb)",
        "answer": ["Quizás influya en la decisión", "A lo mejor influya en la decisión", "Quizás influya en la decisión."],
        "hint": "influir → influya (i→y change in subjunctive)",
        "explanation": "Influir changes i→y in the subjunctive: influya, influyas, etc. Note the preposition 'en' after influir: influir EN algo.",
    },
    {
        "question": "Translate: 'Run away from there!' (use subjunctive of huir as a command, y-change verb)",
        "answer": ["¡Huye de ahí!", "¡Huye de ahí!", "Huye de ahí"],
        "hint": "huir → huya (i→y change); imperative tú: huye",
        "explanation": "Huir changes i→y. The tú imperative is 'huye'. In Mexican Spanish, '¡Huye de ahí!' is a vivid, common way to say 'Get out of there!' Note: subjunctive would be 'huya' but the affirmative tú command is 'huye'.",
    },
    {
        "question": "Translate: 'I hope you think about it before deciding.' (use subjunctive of pensar)",
        "answer": ["Espero que pienses en eso antes de decidir", "Espero que pienses en eso antes de decidir."],
        "hint": "pensar → piense (e→ie stem change in subjunctive)",
        "explanation": "Pensar changes e→ie in the subjunctive: yo piense, tú pienses, etc. 'Pensar en algo' means to think about something.",
        "context": "Giving advice to a friend at a market"
    },
    {
        "question": "Translate: 'It's important that she wants to study medicine.' (use subjunctive of querer)",
        "answer": ["Es importante que quiera estudiar medicina", "Es importante que quiera estudiar medicina."],
        "hint": "querer → quiera (e→ie stem change in subjunctive)",
        "explanation": "Querer changes e→ie in the subjunctive: yo quiera, tú quieras, etc. In Mexico, 'estudiar medicina' is a common aspiration.",
        "context": "Discussing a family member's career plans"
    },
    {
        "question": "Translate: 'Maybe the baby sleeps through the night.' (use subjunctive of dormir)",
        "answer": ["Quizás el bebé duerma toda la noche", "A lo mejor el bebé duerma toda la noche", "Quizás el bebé duerma toda la noche."],
        "hint": "dormir → duerma (o→ue stem change in subjunctive)",
        "explanation": "Dormir changes o→ue in the subjunctive: yo duerma, tú duermas, etc. 'Toda la noche' means 'all night'. 'Quizás' triggers subjunctive.",
        "context": "New parents hoping for rest"
    },
    {
        "question": "Translate: 'I doubt that anyone dies from this illness.' (use subjunctive of morir)",
        "answer": ["Dudo que alguien muera de esta enfermedad", "Dudo que alguien muera de esta enfermedad."],
        "hint": "morir → muera (o→ue stem change in subjunctive)",
        "explanation": "Morir changes o→ue in the subjunctive: yo muera, tú mueras, etc. 'Muera de' means 'dies from'. Used to express doubt about a fatal outcome.",
        "context": "Discussing health concerns with a doctor"
    },
    {
        "question": "Translate: 'I suggest that you try the enchiladas.' (use subjunctive of sugerir)",
        "answer": ["Sugiero que pruebes las enchiladas", "Te sugiero que pruebes las enchiladas", "Sugiero que pruebes las enchiladas."],
        "hint": "sugerir → sugiera (e→ie stem change in subjunctive)",
        "explanation": "Sugerir changes e→ie in the subjunctive: yo sugiera, tú sugieras, etc. Enchiladas are a classic Mexican dish. 'Probar' (to try/taste) is more natural than 'intentar' for food.",
        "context": "Recommending food at a Mexican restaurant"
    },
    {
        "question": "Translate: 'I prefer that you choose the red one.' (use subjunctive of preferir)",
        "answer": ["Prefiero que elijas el rojo", "Prefiero que escojas el rojo", "Prefiero que elijas el rojo."],
        "hint": "preferir → prefiera (e→ie stem change in subjunctive); also elegir → elija (e→i)",
        "explanation": "Preferir changes e→ie in the subjunctive: yo prefiera, tú prefieras, etc. 'Elegir' in the subjunctive also changes: elija, elijas. Both stem changes appear in this sentence.",
        "context": "Shopping at a mercado in Mexico"
    },
    {
        "question": "Translate: 'I hope you have fun at the posada.' (use subjunctive of divertirse)",
        "answer": ["Espero que te diviertas en la posada", "Espero que te diviertas en la posada."],
        "hint": "divertirse → se divierta (e→ie stem change, reflexive pronouns shift)",
        "explanation": "Divertirse changes e→ie in subjunctive and requires reflexive pronouns: tú te diviertas. Las posadas are traditional Mexican Christmas celebrations with processions and piñatas.",
        "context": "Wishing a friend fun at a holiday celebration"
    },
    {
        "question": "Translate: 'I feel sorry that he feels bad about it.' (use subjunctive of sentir)",
        "answer": ["Siento que él se sienta mal por eso", "Siento que se sienta mal por eso", "Siento que él se sienta mal por eso."],
        "hint": "sentir → sienta (e→ie stem change in subjunctive)",
        "explanation": "Sentir changes e→ie in the subjunctive: yo sienta, tú sientas, etc. As a reflexive verb 'sentirse', pronouns shift: él se sienta. 'Siento que...' expresses regret.",
        "context": "Empathizing with a coworker"
    },
    {
        "question": "Translate: 'I don't want you to lie to me about what happened.' (use subjunctive of mentir)",
        "answer": ["No quiero que me mientas sobre lo que pasó", "No quiero que me mientas sobre lo que pasó."],
        "hint": "mentir → mienta (e→ie stem change in subjunctive)",
        "explanation": "Mentir changes e→ie in the subjunctive: yo mienta, tú mientas, etc. 'Mentir sobre algo' = to lie about something. A common Mexican expression for 'don't lie to me' is 'no me mientas'.",
        "context": "Confronting someone at work"
    },
    {
        "question": "Translate: 'It's important that the water boils before adding the nopales.' (use subjunctive of hervir)",
        "answer": ["Es importante que el agua hierva antes de agregar los nopales", "Es importante que hierva el agua antes de poner los nopales", "Es importante que el agua hierva antes de agregar los nopales."],
        "hint": "hervir → hierva (e→ie stem change in subjunctive)",
        "explanation": "Hervir changes e→ie in the subjunctive: yo hierva, tú hiervas, etc. Nopales (cactus paddles) are a traditional Mexican food that must be boiled before eating to remove the slime.",
        "context": "Preparing traditional Mexican food"
    },
    {
        "question": "Translate: 'I want you to choose the best candidate.' (use subjunctive of elegir)",
        "answer": ["Quiero que elijas al mejor candidato", "Quiero que elijas al mejor candidato."],
        "hint": "elegir → elija (e→i stem change in subjunctive)",
        "explanation": "Elegir changes e→i in the subjunctive: yo elija, tú elijas, etc. Note the personal 'a' before 'mejor candidato' because it refers to a person.",
        "context": "Discussing elections or hiring"
    },
    {
        "question": "Translate: 'I hope you get tickets for the concert.' (use subjunctive of conseguir)",
        "answer": ["Espero que consigas boletos para el concierto", "Espero que consigas boletos para el concierto."],
        "hint": "conseguir → consiga (e→i stem change in subjunctive)",
        "explanation": "Conseguir changes e→i in the subjunctive: yo consiga, tú consigas, etc. 'Boletos' is the Mexican Spanish word for tickets (not 'entradas').",
        "context": "Trying to get concert tickets in Mexico City"
    },
    {
        "question": "Translate: 'I want you to take out the trash.' (use subjunctive of sacar for spelling change c→qu)",
        "answer": ["Quiero que saques la basura", "Quiero que saques la basura."],
        "hint": "sacar → saque (c→qu spelling change to preserve /k/ sound)",
        "explanation": "Sacar changes c→qu in the subjunctive to preserve the /k/ sound: yo saque, tú saques, etc. Without the qu, 'saque' would sound different. 'La basura' = trash/garbage.",
        "context": "Household chores"
    },
    {
        "question": "Translate: 'It's necessary that you look for the receipt at the supermarket.' (use subjunctive of buscar for spelling change c→qu)",
        "answer": ["Es necesario que busques el ticket en el supermercado", "Es necesario que busques el ticket en el supermercado."],
        "hint": "buscar → busque (c→qu spelling change to preserve /k/ sound)",
        "explanation": "Buscar changes c→qu in the subjunctive: yo busque, tú busques, etc. In Mexico, 'ticket' or 'nota' is used for receipt (not 'recibo' for store receipts). 'Supermercado' or 'super' for short.",
        "context": "Shopping at a Mexican supermarket"
    },
    {
        "question": "Translate: 'I hope she crosses the street safely.' (use subjunctive of cruzar for spelling change z→c)",
        "answer": ["Espero que cruce la calle con cuidado", "Espero que cruce la calle con cuidado."],
        "hint": "cruzar → cruce (z→c spelling change to preserve /s/ sound)",
        "explanation": "Cruzar changes z→c in the subjunctive: yo cruce, tú cruces, etc. In Mexican Spanish, 'cruzar la calle' = to cross the street. 'Con cuidado' = carefully/safely.",
        "context": "Navigating busy Mexico City streets"
    },
    {
        "question": "Translate: 'I want you to raise your voice so they can hear you.' (use subjunctive of alzar for spelling change z→c and oír)",
        "answer": ["Quiero que alces la voz para que te oigan", "Quiero que levantes la voz para que te oigan", "Quiero que alces la voz para que te escuchen"],
        "hint": "alzar → alce (z→c spelling change); also oír → oiga (go-verb)",
        "explanation": "Alzar changes z→c in the subjunctive: yo alce, tú alces, etc. Note: 'levantar la voz' is more common than 'alzar la voz' in everyday Mexican Spanish, but both are valid. 'Oigan' is the subjunctive of oír.",
        "context": "Speaking up at a noisy mercado"
    },
    {
        "question": "Translate: 'It's important that she organizes the posada.' (use subjunctive of organizar for spelling change z→c)",
        "answer": ["Es importante que organice la posada", "Es importante que organice la posada."],
        "hint": "organizar → organice (z→c spelling change to preserve /s/ sound)",
        "explanation": "Organizar changes z→c in the subjunctive: yo organice, tú organices, etc. A 'posada' is a traditional Mexican Christmas celebration reenacting Mary and Joseph seeking lodging.",
        "context": "Planning holiday celebrations"
    },
    {
        "question": "Translate: 'I hope you start the project on time.' (use subjunctive of empezar for spelling change z→c)",
        "answer": ["Espero que empieces el proyecto a tiempo", "Espero que empieces el proyecto a tiempo."],
        "hint": "empezar → empiece (z→c spelling change, plus e→ie stem change)",
        "explanation": "Empezar has BOTH a stem change (e→ie) and a spelling change (z→c) in the subjunctive: yo empiece, tú empieces, etc. 'A tiempo' = on time. Very common in Mexican workplace contexts.",
        "context": "Workplace project planning"
    },
    {
        "question": "Translate: 'It's necessary that you pay the rent.' (use subjunctive of pagar for spelling change g→gu)",
        "answer": ["Es necesario que pagues la renta", "Es necesario que pagues la renta."],
        "hint": "pagar → pague (g→gu spelling change to preserve /g/ sound)",
        "explanation": "Pagar changes g→gu in the subjunctive: yo pague, tú pagues, etc. The 'u' preserves the hard /g/ sound before 'a'. In Mexico, 'renta' is the common word for rent (not 'alquiler').",
        "context": "Paying monthly rent in Mexico"
    },
    {
        "question": "Translate: 'I want you to arrive early to the office.' (use subjunctive of llegar for spelling change g→gu)",
        "answer": ["Quiero que llegues temprano a la oficina", "Quiero que llegues temprano a la oficina."],
        "hint": "llegar → llegue (g→gu spelling change to preserve /g/ sound)",
        "explanation": "Llegar changes g→gu in the subjunctive: yo llegue, tú llegues, etc. 'Llegar a' = arrive at. 'Temprano' = early. 'Oficina' = office.",
        "context": "Commuting to work in Mexico"
    },
    {
        "question": "Translate: 'I hope you play the guitar at the serenata.' (use subjunctive of tocar for spelling change c→qu)",
        "answer": ["Espero que toques la guitarra en la serenata", "Espero que toques la guitarra en la serenata."],
        "hint": "tocar → toque (c→qu spelling change to preserve /k/ sound)",
        "explanation": "Tocar changes c→qu in the subjunctive: yo toque, tú toques, etc. A 'serenata' or 'música de serenata' is a traditional Mexican serenade, often with guitar.",
        "context": "Mexican musical traditions"
    },
    {
        "question": "Translate: 'It's important that you practice your Spanish.' (use subjunctive of practicar for spelling change c→qu)",
        "answer": ["Es importante que practiques tu español", "Es importante que practiques tu español."],
        "hint": "practicar → practique (c→qu spelling change to preserve /k/ sound)",
        "explanation": "Practicar changes c→qu in the subjunctive: yo practique, tú practiques, etc. A very practical verb for language learners in Mexico.",
        "context": "Language learning in Mexico"
    },
    {
        "question": "Translate: 'I want you to come closer to the stage.' (use subjunctive of acercar for spelling change c→qu)",
        "answer": ["Quiero que te acerques al escenario", "Quiero que te acerques al escenario."],
        "hint": "acercar → acerque (c→qu spelling change to preserve /k/ sound)",
        "explanation": "Acercar changes c→qu in the subjunctive: yo acerque, tú acerques, etc. 'Acercarse a' = to approach/come closer to. 'Escenario' = stage. Reflexive form is common: acercarse.",
        "context": "At a concert or festival in Mexico"
    },
    {
        "question": "Translate: 'I hope she doesn't stumble on the cobblestones.' (use subjunctive of tropezar for spelling change z→c and stem change e→ie)",
        "answer": ["Espero que no tropiece con las piedras del empedrado", "Espero que no tropiece en el empedrado", "Espero que no tropiece con el empedrado."],
        "hint": "tropezar → tropiece (z→c spelling change AND e→ie stem change)",
        "explanation": "Tropezar has BOTH a stem change (e→ie) and a spelling change (z→c) in the subjunctive: yo tropiece, tú tropieces, etc. 'Empedrado' = cobblestone street, common in Mexican colonial towns.",
        "context": "Walking in a Mexican colonial town"
    },
    {
        "question": "Translate: 'I want you to hear what I'm saying.' (use subjunctive of oír, a go-verb)",
        "answer": ["Quiero que oigas lo que estoy diciendo", "Quiero que me oigas", "Quiero que oigas lo que te digo"],
        "hint": "oír → oiga (go-verb with irregular yo form: oigo)",
        "explanation": "Oír is a go-verb: yo oigo → subj. oiga, oigas, etc. 'Oír lo que estoy diciendo' = hear what I'm saying. 'Oigas' is the tú subjunctive form.",
        "context": "Having a conversation in a noisy place"
    },
    {
        "question": "Translate: 'I doubt that he falls for that trick.' (use subjunctive of caer, a go-verb)",
        "answer": ["Dudo que caiga en esa trampa", "Dudo que se caiga en esa trampa", "Dudo que caiga en esa trampa."],
        "hint": "caer → caiga (go-verb: yo caigo → subj. caiga)",
        "explanation": "Caer is a go-verb: yo caigo → subj. caiga, caigas, etc. 'Caer en una trampa' = to fall for a trick. In Mexican slang, 'caer' is also used in 'caer gordo' (to dislike someone).",
        "context": "Discussing someone being gullible"
    },
    {
        "question": "Translate: 'It's necessary that you bring your INE.' (use subjunctive of traer, a go-verb)",
        "answer": ["Es necesario que traigas tu INE", "Es necesario que traigas tu INE."],
        "hint": "traer → traiga (go-verb: yo traigo → subj. traiga)",
        "explanation": "Traer is a go-verb: yo traigo → subj. traiga, traigas, etc. 'INE' (Instituto Nacional Electoral) is the Mexican national ID card — essential for many transactions in Mexico.",
        "context": "Showing identification at a Mexican government office"
    },
    {
        "question": "Translate: 'I hope it's worth the effort.' (use subjunctive of valer, a go-verb)",
        "answer": ["Espero que valga la pena", "Espero que valga la pena."],
        "hint": "valer → valga (go-verb: yo valgo → subj. valga)",
        "explanation": "Valer is a go-verb: yo valgo → subj. valga, valgas, etc. 'Valer la pena' = to be worth it. This is one of the most common expressions with 'valer' in Mexican Spanish.",
        "context": "Considering whether to pursue something"
    },
    {
        "question": "Translate: 'I want her to leave right now.' (use subjunctive of salir, a go-verb)",
        "answer": ["Quiero que ella salga ahorita", "Quiero que salga ahorita", "Quiero que ella salga ahorita."],
        "hint": "salir → salga (go-verb: yo salgo → subj. salga)",
        "explanation": "Salir is a go-verb: yo salgo → subj. salga, salgas, etc. 'Ahorita' is quintessentially Mexican — it can mean 'right now' or 'in a bit' depending on context and tone.",
        "context": "Telling someone to leave promptly"
    },
    {
        "question": "Translate: 'It's important that you put the tamales on the table.' (use subjunctive of poner, a go-verb)",
        "answer": ["Es importante que pongas los tamales en la mesa", "Es importante que pongas los tamales en la mesa."],
        "hint": "poner → ponga (go-verb: yo pongo → subj. ponga)",
        "explanation": "Poner is a go-verb: yo pongo → subj. ponga, pongas, etc. Tamales are a quintessential Mexican food, especially during holidays and celebrations.",
        "context": "Setting up for a Mexican meal"
    },
    {
        "question": "Translate: 'I hope you come to the posada.' (use subjunctive of venir, a go-verb)",
        "answer": ["Espero que vengas a la posada", "Espero que vengas a la posada."],
        "hint": "venir → venga (go-verb: yo vengo → subj. venga)",
        "explanation": "Venir is a go-verb: yo vengo → subj. venga, vengas, etc. 'Venir a' = to come to. Las posadas are traditional Mexican Christmas celebrations.",
        "context": "Inviting someone to a holiday celebration"
    },
    {
        "question": "Translate: 'I want you to contribute to the community project.' (use subjunctive of contribuir, a y-change verb)",
        "answer": ["Quiero que contribuyas al proyecto comunitario", "Quiero que contribuyas al proyecto de la comunidad"],
        "hint": "contribuir → contribuya (i→y change in subjunctive)",
        "explanation": "Contribuir changes i→y in the subjunctive: yo contribuya, tú contribuyas, etc. Note the preposition 'a' after contribuir: contribuir A algo. Community projects are important in Mexican culture.",
        "context": "Community involvement in a Mexican neighborhood"
    },
    {
        "question": "Translate: 'I doubt they attribute the success to luck.' (use subjunctive of atribuir, a y-change verb)",
        "answer": ["Dudo que atribuyan el éxito a la suerte", "Dudo que le atribuyan el éxito a la suerte"],
        "hint": "atribuir → atribuya (i→y change in subjunctive)",
        "explanation": "Atribuir changes i→y in the subjunctive: yo atribuya, tú atribuyas, etc. 'Atribuir algo a algo' = to attribute something to something. 'El éxito' is masculine despite ending in -o.",
        "context": "Discussing business success in Mexico"
    },
    {
        "question": "Translate: 'It's necessary that you substitute the corn flour.' (use subjunctive of sustituir, a y-change verb)",
        "answer": ["Es necesario que sustituyas la harina de maíz", "Es necesario que sustituyas la masa de maíz"],
        "hint": "sustituir → sustituya (i→y change in subjunctive)",
        "explanation": "Sustituir changes i→y in the subjunctive: yo sustituya, tú sustituyas, etc. 'Harina de maíz' = corn flour (masa harina), essential for making tortillas and other Mexican dishes.",
        "context": "Cooking Mexican food with substitutions"
    },
    {
        "question": "Translate: 'I hope the storm doesn't destroy the milpa.' (use subjunctive of destruir, a y-change verb)",
        "answer": ["Espero que la tormenta no destruya la milpa", "Espero que no destruya la milpa la tormenta"],
        "hint": "destruir → destruya (i→y change in subjunctive)",
        "explanation": "Destruir changes i→y in the subjunctive: yo destruya, tú destruyas, etc. A 'milpa' is a traditional Mesoamerican crop-growing system (corn, beans, squash) — deeply Mexican.",
        "context": "Concern for crops during storm season in rural Mexico"
    },
    {
        "question": "Translate: 'I want you to flee from that dangerous neighborhood.' (use subjunctive of huir, a y-change verb)",
        "answer": ["Quiero que huyas de esa colonia peligrosa", "Quiero que huyas de ese barrio peligroso"],
        "hint": "huir → huya (i→y change in subjunctive)",
        "explanation": "Huir changes i→y in the subjunctive: yo huya, tú huyas, etc. 'Colonia' is the Mexican Spanish term for neighborhood (not 'barrio' in most of Mexico). 'Huir de' = to flee from.",
        "context": "Discussing safety in a Mexican neighborhood"
    },
    {
        "question": "Translate: 'I hope she concludes the investigation.' (use subjunctive of concluir, a y-change verb)",
        "answer": ["Espero que concluya la investigación", "Espero que concluya la investigación."],
        "hint": "concluir → concluya (i→y change in subjunctive)",
        "explanation": "Concluir changes i→y in the subjunctive: yo concluya, tú concluyas, etc. 'Concluir' = to conclude/finish. 'La investigación' = the investigation.",
        "context": "Academic or journalistic work in Mexico"
    },
    {
        "question": "Translate: 'I hope you choose the green chile and pay with cash.' (use subjunctives of elegir and pagar)",
        "answer": ["Espero que elijas el chile verde y pagues en efectivo", "Espero que escojas el chile verde y pagues en efectivo"],
        "hint": "elegir → elijas (e→i); pagar → pagues (g→gu spelling change)",
        "explanation": "This sentence combines two different types of irregularity: elegir's stem change (e→i) and pagar's spelling change (g→gu). 'Chile verde' is a staple of Mexican cuisine. 'En efectivo' = in cash.",
        "context": "Shopping at a Mexican market"
    },
    {
        "question": "Translate: 'It's necessary that you bring the sauce and put it on the table.' (use subjunctives of traer and poner, both go-verbs)",
        "answer": ["Es necesario que traigas la salsa y la pongas en la mesa", "Es necesario que traigas la salsa y la pongas en la mesa."],
        "hint": "traer → traigas (go-verb); poner → pongas (go-verb)",
        "explanation": "Both traer and poner are go-verbs: traigo→traigas, pongo→pongas. 'La salsa' in Mexico always refers to a spicy sauce — every table needs one.",
        "context": "Setting the table for a Mexican meal"
    },
    {
        "question": "Translate: 'I want you to sleep well and have fun at the fiesta.' (use subjunctives of dormir and divertirse)",
        "answer": ["Quiero que duermas bien y te diviertas en la fiesta", "Quiero que duermas bien y te diviertas en la fiesta."],
        "hint": "dormir → duermas (o→ue); divertirse → te diviertas (e→ie, reflexive)",
        "explanation": "This combines two different stem-changing verbs: dormir (o→ue) and divertirse (e→ie with reflexive). 'Fiesta' in Mexico can mean any celebration — birthday, saint's day, national holiday.",
        "context": "Wishing someone well at a Mexican celebration"
    },
    {
        "question": "Translate: 'I suggest you look for the documents and take out the copies.' (use subjunctives of buscar and sacar, both with spelling changes)",
        "answer": ["Te sugiero que busques los documentos y saques las copias", "Sugiero que busques los documentos y saques las copias"],
        "hint": "buscar → busques (c→qu); sacar → saques (c→qu)",
        "explanation": "Both buscar and sacar have c→qu spelling changes in the subjunctive. 'Sacar copias' = to make copies. In Mexico, 'copias' is commonly used for photocopies at a 'papelería' or copy shop.",
        "context": "Office work in Mexico"
    },
    {
        "question": "Translate: 'I doubt that he comes and brings the mole.' (use subjunctives of venir and traer, both go-verbs)",
        "answer": ["Dudo que venga y traiga el mole", "Dudo que él venga y traiga el mole"],
        "hint": "venir → venga (go-verb); traer → traiga (go-verb)",
        "explanation": "Both venir and traer are go-verbs: vengo→venga, traigo→traiga. 'Mole' is a quintessential Mexican dish — a complex sauce often served at celebrations.",
        "context": "Discussing who's bringing food to a gathering"
    },
    {
        "question": "Translate: 'It's important that you start the car and arrive on time.' (use subjunctives of empezar and llegar, both with spelling changes)",
        "answer": ["Es importante que arranques el carro y llegues a tiempo", "Es importante que enciendas el carro y llegues a tiempo", "Es importante que empieces el carro y llegues a tiempo"],
        "hint": "empezar → empieces (z→c AND e→ie); llegar → llegues (g→gu)",
        "explanation": "Empezar has both a spelling change (z→c) and stem change (e→ie); llegar has g→gu. Note: in Mexico, 'arrancar' is more common than 'empezar' for starting a car, and 'carro' is the Mexican word for car.",
        "context": "Driving in Mexican traffic"
    },
    {
        "question": "Translate: 'I hope you flee and don't get hurt.' (use subjunctives of huir and morir)",
        "answer": ["Espero que huyas y no te mueras", "Espero que huyas y no mueras"],
        "hint": "huir → huyas (i→y); morir → mueras (o→ue)",
        "explanation": "Huir has i→y change and morir has o→ue change. 'Morirse' (reflexive) is colloquial for 'to get hurt/die' in Mexican Spanish. 'No te mueras' = don't die/get hurt.",
        "context": "Warning someone about danger"
    },
    {
        "question": "Translate: 'I want you to contribute and conclude the report before leaving.' (use subjunctives of contribuir, concluir, and salir)",
        "answer": ["Quiero que contribuyas y concluyas el informe antes de salir", "Quiero que contribuyas y concluyas el reporte antes de salir"],
        "hint": "contribuir → contribuyas (i→y); concluir → concluyas (i→y); salir → salgas (go-verb)",
        "explanation": "This sentence combines y-change verbs (contribuir, concluir) with a go-verb (salir). 'Informe' or 'reporte' = report. 'Antes de + infinitive' = before doing something.",
        "context": "Workplace collaboration in Mexico"
    },
]

multiple_choice = [
    (
        "I hope you sleep well.",
        ["Espero que duermas bien.", "Espero que dormas bien.", "Espero que dormieras bien.", "Espero que durmas bien."],
        1,
        "Dormir → duerma (o→ue). 'Dormas' is not a valid form; 'durmas' would be Portuguese."
    ),
    (
        "It's necessary that he request the documents.",
        ["Es necesario que pida los documentos.", "Es necesario que peda los documentos.", "Es necesario que pidea los documentos.", "Es necesario que pide los documentos."],
        1,
        "Pedir → pida (e→i stem change in subjunctive). 'Pida' is the correct subjunctive form."
    ),
    (
        "I want you to protect the environment.",
        ["Quiero que protejas el medio ambiente.", "Quiero que proteges el medio ambiente.", "Quiero que protejas el medioambiente.", "Quiero que proteja el medio ambiente."],
        1,
        "Proteger → proteja, protejas (g→j). The tú subjunctive is 'protejas', not 'proteges' (that's indicative)."
    ),
    (
        "The seamstress needs to darn the shirt.",
        ["La costurera necesita zurcir la camisa.", "La costurera necesita zurza la camisa.", "La costurera necesita zurcer la camisa.", "La costurera necesita zarcir la camisa."],
        1,
        "Zurcir changes c→z only in subjunctive forms (zurza, zurzas). In the infinitive after 'necesita', the infinitive zurcir is used unchanged."
    ),
    (
        "I hope he comes here right now.",
        ["Espero que venga aquí ahorita.", "Espero que viene aquí ahorita.", "Espero que ven aquí ahorita.", "Espero que venga aquí ahora mismo."],
        1,
        "Venir → venga (go-verb). 'Ahorita' is very Mexican — it can mean 'right now' or 'in a little while'. 'Ahora mismo' is also valid but 'ahorita' is more distinctly Mexican."
    ),
    (
        "Tell her to tell the truth.",
        ["Dile que diga la verdad.", "Dile que dice la verdad.", "Dile que decir la verdad.", "Dile que dije la verdad."],
        1,
        "Decir → diga (go-verb). The subjunctive 'diga' is needed after 'que' in an indirect command."
    ),
    (
        "Maybe they destroy the building.",
        ["Quizás destruyan el edificio.", "Quizás destruyen el edificio.", "Quizás destruyeron el edificio.", "Quizás destruyen el edificio."],
        1,
        "Destruir → destruya (i→y change). 'Quizás' triggers the subjunctive, so 'destruyan' is correct."
    ),
    (
        "It's important that you distinguish fact from opinion.",
        ["Es importante que distingas el hecho de la opinión.", "Es importante que distinguas el hecho de la opinión.", "Es importante que distingues el hecho de la opinión.", "Es importante que distinga el hecho de la opinión."],
        1,
        "Distinguir → distinga, distingas (gu→g). The tú subjunctive is 'distingas', not 'distinguas' (which isn't a valid form)."
    ),
    (
        "I want you to bring the mole.",
        ["Quiero que traigas el mole.", "Quiero que traes el mole.", "Quiero que traiga el mole.", "Quiero que trajer el mole."],
        1,
        "Traer → traiga, traigas (go-verb). Mole is a quintessential Mexican dish — using it in context reinforces Mexican vocabulary."
    ),
    (
        "I hope you think about it.",
        ["Espero que pienses en eso.", "Espero que pensas en eso.", "Espero que piensas en eso.", "Espero que penséis en eso."],
        1,
        "Pensar → piense (e→ie stem change). 'Pienses' is the tú subjunctive; 'pensas' and 'piensas' are not subjunctive forms."
    ),
    (
        "It's important that she wants to study.",
        ["Es importante que quiera estudiar.", "Es importante que quiere estudiar.", "Es importante que querer estudiar.", "Es importante que quierar estudiar."],
        1,
        "Querer → quiera (e→ie). 'Quiera' is the correct subjunctive form; 'quiere' is indicative and 'quierar' doesn't exist."
    ),
    (
        "I doubt that anyone dies from this.",
        ["Dudo que alguien muera de esto.", "Dudo que alguien muere de esto.", "Dudo que alguien mora de esto.", "Dudo que alguien more de esto."],
        1,
        "Morir → muera (o→ue stem change in subjunctive). 'Dudo que' triggers the subjunctive."
    ),
    (
        "I suggest that you try the enchiladas.",
        ["Te sugiero que pruebes las enchiladas.", "Te sugiero que pruebas las enchiladas.", "Te sugiero que probas las enchiladas.", "Te sugiero que probéis las enchiladas."],
        1,
        "Sugerir → sugiera (e→ie stem change). The tú subjunctive is 'sugieras', but here it's used with 'pruebes' (probar→pruebe, o→ue). Enchiladas are quintessentially Mexican."
    ),
    (
        "I prefer that you choose the red one.",
        ["Prefiero que elijas el rojo.", "Prefiero que eliges el rojo.", "Prefiero que elegas el rojo.", "Prefiero que eligas el rojo."],
        1,
        "Elegir → elija (e→i stem change in subjunctive). 'Elijas' is correct; 'elegas' doesn't exist and 'eliges' is indicative."
    ),
    (
        "I hope you have fun at the posada.",
        ["Espero que te diviertas en la posada.", "Espero que te divertes en la posada.", "Espero que diviertas en la posada.", "Espero que te divertís en la posada."],
        1,
        "Divertirse → se divierta (e→ie, reflexive). 'Te diviertas' is the correct tú reflexive subjunctive."
    ),
    (
        "I don't want you to lie to me.",
        ["No quiero que me mientas.", "No quiero que me mentas.", "No quiero que me mientes.", "No quiero que me mentís."],
        1,
        "Mentir → mienta (e→ie stem change in subjunctive). 'Mientas' is correct; 'mentas' is not a valid form."
    ),
    (
        "It's important that the water boils before adding nopales.",
        ["Es importante que el agua hierva antes de agregar los nopales.", "Es importante que el agua herva antes de agregar los nopales.", "Es importante que el agua hierbe antes de agregar los nopales.", "Es importante que el agua hirva antes de agregar los nopales."],
        1,
        "Hervir → hierva (e→ie stem change). 'Hierva' is the correct subjunctive; 'herva' and 'hirva' are not valid forms. Nopales are a traditional Mexican food."
    ),
    (
        "I want you to choose the best candidate.",
        ["Quiero que elijas al mejor candidato.", "Quiero que eliges al mejor candidato.", "Quiero que elegas al mejor candidato.", "Quiero que elegís al mejor candidato."],
        1,
        "Elegir → elija (e→i stem change). 'Elijas' is the tú subjunctive. The personal 'a' is used before 'mejor candidato'."
    ),
    (
        "I hope you get tickets for the concert.",
        ["Espero que consigas boletos para el concierto.", "Espero que consigues boletos para el concierto.", "Espero que consiges boletos para el concierto.", "Espero que conseguas boletos para el concierto."],
        1,
        "Conseguir → consiga (e→i stem change). 'Consigas' is the tú subjunctive; 'conseguas' and 'consiges' don't exist. 'Boletos' is the Mexican word for tickets."
    ),
    (
        "I want you to take out the trash.",
        ["Quiero que saques la basura.", "Quiero que sacas la basura.", "Quiero que saque la basura.", "Quiero que sacar la basura."],
        1,
        "Sacar → saque (c→qu spelling change). 'Saques' preserves the /k/ sound. 'Saques' is tú subjunctive; 'saque' would be él/ella/usted."
    ),
    (
        "It's necessary that you look for the receipt.",
        ["Es necesario que busques el ticket.", "Es necesario que buscas el ticket.", "Es necesario que buscar el ticket.", "Es necesario que busques el recibo."],
        1,
        "Buscar → busque (c→qu spelling change). 'Busques' is the tú subjunctive. 'Ticket' is common in Mexico for receipt; 'recibo' is used for formal receipts."
    ),
    (
        "I hope she crosses the street carefully.",
        ["Espero que cruce la calle con cuidado.", "Espero que cruze la calle con cuidado.", "Espero que cruzas la calle con cuidado.", "Espero que cruza la calle con cuidado."],
        1,
        "Cruzar → cruce (z→c spelling change). 'Cruce' is the él/ella subjunctive; 'cruze' is not a valid Spanish spelling."
    ),
    (
        "I want you to raise your voice.",
        ["Quiero que alces la voz.", "Quiero que alzas la voz.", "Quiero que alze la voz.", "Quiero que alcen la voz."],
        1,
        "Alzar → alce (z→c spelling change). 'Alces' is the tú subjunctive. 'Alzar la voz' = to raise one's voice."
    ),
    (
        "It's important that she organizes the posada.",
        ["Es importante que organice la posada.", "Es importante que organiza la posada.", "Es importante que organizar la posada.", "Es importante que organize la posada."],
        1,
        "Organizar → organice (z→c spelling change). 'Organice' preserves the /s/ sound; 'organize' is not valid Spanish."
    ),
    (
        "I hope you start the project on time.",
        ["Espero que empieces el proyecto a tiempo.", "Espero que empieces el proyecto a tiempo.", "Espero que empezar el proyecto a tiempo.", "Espero que empiezas el proyecto a tiempo."],
        1,
        "Empezar → empiece (z→c AND e→ie). 'Empieces' is the tú subjunctive with both changes applied."
    ),
    (
        "It's necessary that you pay the rent.",
        ["Es necesario que pagues la renta.", "Es necesario que pagas la renta.", "Es necesario que page la renta.", "Es necesario que pagar la renta."],
        1,
        "Pagar → pague (g→gu spelling change). 'Pagues' preserves the hard /g/ sound. 'Renta' is the Mexican word for rent."
    ),
    (
        "I want you to arrive early to the office.",
        ["Quiero que llegues temprano a la oficina.", "Quiero que llegas temprano a la oficina.", "Quiero que llegemos temprano a la oficina.", "Quiero que llegemos temprano a la oficina."],
        1,
        "Llegar → llegue (g→gu spelling change). 'Llegues' is the tú subjunctive; 'llegas' is indicative. The 'u' preserves the /g/ sound."
    ),
    (
        "I hope you play the guitar.",
        ["Espero que toques la guitarra.", "Espero que tocas la guitarra.", "Espero que toque la guitarra.", "Espero que tocar la guitarra."],
        1,
        "Tocar → toque (c→qu spelling change). 'Toques' is the tú subjunctive; 'toque' would be él/ella/usted. 'Tocar' means to play (an instrument)."
    ),
    (
        "I doubt that he hears what we're saying.",
        ["Dudo que oiga lo que estamos diciendo.", "Dudo que oye lo que estamos diciendo.", "Dudo que oiga lo que decimos.", "Dudo que oigo lo que estamos diciendo."],
        1,
        "Oír → oiga (go-verb). 'Oiga' is the él subjunctive; 'oye' is the indicative tú form."
    ),
    (
        "Maybe he falls for the trick.",
        ["Quizás caiga en la trampa.", "Quizás cae en la trampa.", "Quizás caiga en la trampa.", "Quizás caye en la trampa."],
        1,
        "Caer → caiga (go-verb). 'Caiga' is the correct subjunctive; 'caye' is not a valid form. 'Caer en la trampa' = to fall for a trick."
    ),
    (
        "It's necessary that you bring your INE.",
        ["Es necesario que traigas tu INE.", "Es necesario que traes tu INE.", "Es necesario que traigan tu INE.", "Es necesario que trayas tu INE."],
        1,
        "Traer → traiga (go-verb). 'Traigas' is the tú subjunctive; 'trayas' doesn't exist. INE is the Mexican national ID."
    ),
    (
        "I hope it's worth the effort.",
        ["Espero que valga la pena.", "Espero que vale la pena.", "Espero que valga la penas.", "Espero que valgo la pena."],
        1,
        "Valer → valga (go-verb). 'Valga' is the correct subjunctive. 'Valer la pena' = to be worth it, a very common Mexican expression."
    ),
    (
        "I want her to leave right now.",
        ["Quiero que ella salga ahorita.", "Quiero que ella sale ahorita.", "Quiero que ella sale ahora.", "Quiero que ella salgo ahorita."],
        1,
        "Salir → salga (go-verb). 'Salga' is the correct subjunctive; 'sale' is indicative. 'Ahorita' is very Mexican."
    ),
    (
        "I want you to contribute to the project.",
        ["Quiero que contribuyas al proyecto.", "Quiero que contribuyes al proyecto.", "Quiero que contribuis al proyecto.", "Quiero que contribuyan al proyecto."],
        1,
        "Contribuir → contribuya (i→y change). 'Contribuyas' is the tú subjunctive; 'contribuyes' is not a valid form for this verb."
    ),
    (
        "I hope she concludes the investigation.",
        ["Espero que concluya la investigación.", "Espero que concluye la investigación.", "Espero que concluye la investigación.", "Espero que concluiya la investigación."],
        1,
        "Concluir → concluya (i→y change). 'Concluya' is correct; 'concluiya' doesn't exist. Note: both option 2 and 3 are identical indicative forms."
    ),
    (
        "I want you to flee from that dangerous colonia.",
        ["Quiero que huyas de esa colonia peligrosa.", "Quiero que hules de esa colonia peligrosa.", "Quiero que huigas de esa colonia peligrosa.", "Quiero que huyes de esa colonia peligrosa."],
        1,
        "Huir → huya (i→y change). 'Huyas' is the tú subjunctive; 'hules' and 'huigas' don't exist. 'Colonia' is the Mexican word for neighborhood."
    ),
    (
        "I hope you choose the green chile and pay with cash.",
        ["Espero que elijas el chile verde y pagues en efectivo.", "Espero que eliges el chile verde y pagas en efectivo.", "Espero que escojas el chile verde y pague en efectivo.", "Espero que elijas el chile verde y pagueis en efectivo."],
        1,
        "Elegir → elijas (e→i) and pagar → pagues (g→gu). Both irregularities appear in one sentence. 'Chile verde' and 'en efectivo' are standard Mexican."
    ),
    (
        "I doubt that he comes and brings the mole.",
        ["Dudo que venga y traiga el mole.", "Dudo que viene y trae el mole.", "Dudo que viene y traiga el mole.", "Dudo que venga y trae el mole."],
        1,
        "Venir → venga and traer → traiga (both go-verbs). Both need subjunctive after 'dudo que'. Only option 1 has both in subjunctive."
    ),
    (
        "Maybe she sleeps through the whole night.",
        ["Quizás duerma toda la noche.", "Quizás dorme toda la noche.", "Quizás duerme toda la noche.", "Quizás dorma toda la noche."],
        1,
        "Dormir → duerma (o→ue stem change in subjunctive). 'Quizás' triggers subjunctive: 'duerma' is correct. 'Dorme' isn't a valid form; 'duerme' is indicative."
    ),
]

if __name__ == "__main__":
    run_exercises(translation_exercises, "Lección 5: Verbos Irregulares — Cambios en la Raíz y Ortográficos")
    choose_translation(multiple_choice, "Lección 5: Traducción Múltiple — Verbos Irregulares")