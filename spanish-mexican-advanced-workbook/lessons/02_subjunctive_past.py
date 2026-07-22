import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from workbook_engine import run_exercises, choose_translation

translation_exercises = [
    {
        "question": "Translate: 'If I had more time, I would travel to Chiapas.'",
        "answer": ["Si tuviera más tiempo, viajaría a Chiapas", "Si tuviera más tiempo, viajaría a Chiapas."],
        "hint": "Si + imperfect subjunctive, conditional in main clause",
        "explanation": "Type 2 conditional: 'si' + imperfect subjunctive ('tuviera' from 'tener'), main clause in conditional ('viajaría'). Mexican Spanish strongly prefers the -ra form over -se. Chiapas is known for Palenque ruins and indigenous cultures.",
        "context": "Si clause: conditional sentence"
    },
    {
        "question": "Translate: 'If we were in Guadalajara, we would eat birria.'",
        "answer": ["Si estuviéramos en Guadalajara, comeríamos birria", "Si estuviéramos en Guadalajara, comeríamos birria."],
        "hint": "Si + imperfect subjunctive (nosotros), conditional",
        "explanation": "'Estuviéramos' is the nosotros imperfect subjunctive of 'estar'. Mexican Spanish overwhelmingly uses -ra forms; 'estuviésemos' sounds archaic/literary. Birria is a Jalisco specialty — Guadalajara's iconic dish of slow-braised meat in chile broth.",
        "context": "Si clause: conditional sentence"
    },
    {
        "question": "Translate: 'If she knew how to make pozole, she would invite us.'",
        "answer": ["Si ella supiera hacer pozole, nos invitaría", "Si supiera hacer pozole, nos invitaría", "Si ella supiera hacer pozole, nos invitaría."],
        "hint": "Si + imperfect subjunctive, conditional",
        "explanation": "'Supiera' is the imperfect subjunctive of 'saber' (to know how). Note: 'saber' in subjunctive conveys 'if she knew how.' Pozole — hominy stew with pork or chicken — is central to Mexican celebrations, especially Independence Day.",
        "context": "Si clause: conditional sentence"
    },
    {
        "question": "Translate: 'If the chiles were less spicy, I would eat more.'",
        "answer": ["Si los chiles fueran menos picantes, comería más", "Si los chiles estuvieran menos picantes, comería más", "Si los chiles fueran menos picantes, comería más."],
        "hint": "Si + imperfect subjunctive of ser/estar, conditional",
        "explanation": "' Fueran' (from 'ser') or 'estuvieran' (from 'estar') both work here. 'Picante' is the Mexican Spanish adjective for spicy — don't use 'especiado.' In Mexican Spanish, 'chile' refers to both the fresh and dried fruit; 'picante' describes the heat.",
        "context": "Si clause: conditional sentence"
    },
    {
        "question": "Translate: 'I wish I had visited the pyramids of Teotihuacán when I was younger.'",
        "answer": ["Ojalá hubiera visitado las pirámides de Teotihuacán cuando era más joven", "Ojalá hubiese visitado las pirámides de Teotihuacán cuando era más joven", "Ojalá visitara las pirámides de Teotihuacán cuando era más joven"],
        "hint": "Ojalá + imperfect subjunctive (or past perfect subjunctive for past regrets)",
        "explanation": "'Ojalá' + imperfect subjunctive expresses a wish about the present/future. For past regrets, Mexican Spanish commonly uses 'ojalá + hubiera + past participle' (past perfect subjunctive). Teotihuacán — the City of the Gods — is Mexico's most visited archaeological site.",
        "context": "Past wishes and regrets: ojalá"
    },
    {
        "question": "Translate: 'If only it rained less in Veracruz during summer!'",
        "answer": ["Ojalá lloviera menos en Veracruz durante el verano", "Ojalá lloviera menos en Veracruz en verano", "Ojalá lloviera menos en Veracruz durante el verano!"],
        "hint": "Ojalá + imperfect subjunctive",
        "explanation": "'Ojalá' + imperfect subjunctive expresses a contrary-to-fact wish. 'Lloviera' from 'llover'. Veracruz is Mexico's rainiest major port city, and its humid summers are legendary. 'Ojalá' comes from Arabic 'in sha' Allah' — a linguistic legacy of Moorish Spain.",
        "context": "Past wishes and regrets: ojalá"
    },
    {
        "question": "Translate: 'I wish my grandmother were here to make me tamales.'",
        "answer": ["Ojalá mi abuela estuviera aquí para hacerme tamales", "Ojalá mi abuela estuviera aquí para prepararme tamales", "Ojalá mi abuela estuviera aquí para hacerme tamales."],
        "hint": "Ojalá + imperfect subjunctive of estar",
        "explanation": "'Ojalá' + imperfect subjunctive expresses a present contrary-to-fact wish. 'Estuviera' from 'estar'. Mexican grandmothers ('abuelitas') are the heart of tamal-making, especially during Christmas and Candlemas (Día de la Candelaria, Feb 2).",
        "context": "Past wishes and regrets: ojalá"
    },
    {
        "question": "Translate: 'I would like a café de olla, please.' (polite request with conditional)",
        "answer": ["Me gustaría un café de olla, por favor", "Me gustaría un café de olla, por favor."],
        "hint": "Conditional for polite requests",
        "explanation": "The conditional 'me gustaría' softens the request compared to 'me gusta' or 'quiero'. Café de olla is traditional Mexican coffee brewed in a clay pot with cinnamon and piloncillo (unrefined cane sugar) — a beloved regional specialty.",
        "context": "Polite requests: conditional"
    },
    {
        "question": "Translate: 'Could you tell me where the zócalo is?' (polite request)",
        "answer": ["Podría decirme dónde está el zócalo", "Podría decirme dónde queda el zócalo", "Me podría decir dónde está el zócalo", "Podría decirme dónde está el zócalo?"],
        "hint": "Conditional of poder for politeness",
        "explanation": "'Podría' (conditional of 'poder') makes requests polite and deferential — more courteous than '¿Puede decirme?' The 'zócalo' is Mexico City's main square (formally Plaza de la Constitución), but every Mexican town has its own zócalo.",
        "context": "Polite requests: conditional"
    },
    {
        "question": "Translate: 'We would like to order the chapulines, please.' (polite restaurant request)",
        "answer": ["Quisiéramos pedir los chapulines, por favor", "Nos gustaría pedir los chapulines, por favor", "Quisiéramos ordenar los chapulines, por favor"],
        "hint": "Conditional of querer for polite ordering",
        "explanation": "'Quisiéramos' (conditional of 'querer', nosotros) is a very polite way to order in Mexican restaurants. Chapulines — toasted grasshoppers seasoned with chile and lime — are an Oaxacan delicacy and a sustainable protein source dating back to pre-Columbian times.",
        "context": "Polite requests: conditional"
    },
    {
        "question": "Translate: 'He acts as if he were the owner of the hacienda.'",
        "answer": ["Actúa como si fuera el dueño de la hacienda", "Se comporta como si fuera el dueño de la hacienda", "Actúa como si fuera el dueño de la hacienda."],
        "hint": "Como si + imperfect subjunctive",
        "explanation": "'Como si' (as if/as though) always triggers the subjunctive because it describes an unreal situation. 'Fuera' is imperfect subjunctive of 'ser'. In Mexico, 'hacienda' refers to the grand colonial estates — many now converted into luxury hotels, especially in the Yucatán.",
        "context": "Como si: unreal comparison"
    },
    {
        "question": "Translate: 'She speaks Spanish as if she were born in Puebla.'",
        "answer": ["Habla español como si hubiera nacido en Puebla", "Habla español como si naciera en Puebla", "Hablara español como si naciera en Puebla", "Habla español como si hubiera nacido en Puebla."],
        "hint": "Como si + past perfect subjunctive for past unreality",
        "explanation": "'Como si' + past perfect subjunctive ('hubiera nacido') for a past unreal condition. You can also use 'como si naciera' (imperfect subjunctive) for a less time-specific comparison. Puebla is famous for its distinctive accent and expressions like 'órale' and 'aborrajado'.",
        "context": "Como si: unreal comparison"
    },
    {
        "question": "Translate: 'They treat the migrants as if they were criminals.'",
        "answer": ["Tratan a los migrantes como si fueran criminales", "Tratan a los migrantes como si fueran delincuentes", "Tratan a los migrantes como si fueran criminales."],
        "hint": "Como si + imperfect subjunctive",
        "explanation": "'Como si' + 'fueran' (imperfect subjunctive of 'ser'). 'Delincuentes' is also commonly used in Mexican Spanish for criminals. This construction always uses subjunctive because it describes a hypothetical/counterfactual comparison.",
        "context": "Como si: unreal comparison"
    },
    {
        "question": "Translate: 'If God wills, we will arrive safely in Monterrey.'",
        "answer": ["Si Dios quiere, llegaremos bien a Monterrey", "Si Dios quiere, llegaremos sanos y salvos a Monterrey", "Si Dios quiere, llegaremos bien a Monterrey."],
        "hint": "Si Dios quiere — a Mexican expression of hope",
        "explanation": "'Si Dios quiere' (God willing) is an extremely common Mexican expression, used when talking about future plans. Note: despite 'si', this takes INDICATIVE ('quiere', 'llegaremos') because it expresses hope, not a contrary-to-fact condition. Monterrey is Mexico's northern business hub.",
        "context": "Mexican expression: si Dios quiere"
    },
    {
        "question": "Translate: 'Excuse me, may I pass through?' (using 'con permiso')",
        "answer": ["Con permiso, ¿puedo pasar?", "Con permiso, ¿me permite pasar?", "Con permiso, ¿puedo pasar?"],
        "hint": "Con permiso — Mexican politeness formula",
        "explanation": "'Con permiso' (with permission) is uniquely Mexican/Central American — used when squeezing past someone, entering a room, or leaving a table. It's more polite than 'permiso' alone. In Mexico, 'con permiso' is essential social etiquette.",
        "context": "Mexican expression: con permiso"
    },
    {
        "question": "Translate: 'If I could, I would live in San Cristóbal de las Casas.'",
        "answer": ["Si pudiera, viviría en San Cristóbal de las Casas", "Si pudiera, viviría en San Cristóbal de las Casas."],
        "hint": "Si + imperfect subjunctive, conditional",
        "explanation": "'Pudiera' is the imperfect subjunctive of 'poder'; 'viviría' is conditional. San Cristóbal de las Casas, in Chiapas, is a magical town (pueblo mágico) known for its indigenous Tzotzil and Tzeltal cultures and colonial architecture.",
        "context": "Si clause: conditional sentence"
    },
    {
        "question": "Translate: 'If I had known about the traffic, I would have left earlier for the mercado.'",
        "answer": ["Si hubiera sabido del tráfico, habría salido más temprano para el mercado", "Si hubiera sabido del tráfico, habría salido más temprano al mercado", "Si hubiera sabido del tráfico, habría salido más temprano para el mercado."],
        "hint": "Si + past perfect subjunctive, conditional perfect result",
        "explanation": "Type 3 conditional (past unreal): 'si + hubiera + past participle' in the condition, 'habría + past participle' in the result. This is a counterfactual about the past. 'Mercado' refers to a traditional Mexican market — the traffic getting there is a real concern in CDMX.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If she had tried the mole negro, she would have loved it.'",
        "answer": ["Si ella hubiera probado el mole negro, lo habría amado", "Si hubiera probado el mole negro, lo habría amado", "Si ella hubiera probado el mole negro, lo habría encantado"],
        "hint": "Si + past perfect subjunctive, conditional perfect",
        "explanation": "Type 3 conditional: 'si hubiera probado' (past perfect subjunctive), 'habría amado' (conditional perfect). Mole negro from Oaxaca is one of the most complex sauces in world cuisine — with over 30 ingredients including chile mulato, chocolate, and spices.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If we had gone to Guadalajara, we would have eaten birria at the original restaurant.'",
        "answer": ["Si hubiéramos ido a Guadalajara, habríamos comido birria en el restaurante original", "Si hubiéramos ido a Guadalajara, habríamos comido birria en el restaurante original."],
        "hint": "Si + past perfect subjunctive (nosotros), conditional perfect",
        "explanation": "Type 3 conditional: 'si hubiéramos ido' (nosotros past perfect subjunctive), 'habríamos comido' (conditional perfect). Guadalajara is the birthplace of birria — a slow-braised meat stew — and the original birrierías in the city are legendary.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If the flight had not been delayed, we would have arrived in Cancún on time.'",
        "answer": ["Si el vuelo no hubiera estado retrasado, habríamos llegado a Cancún a tiempo", "Si el vuelo no se hubiera retrasado, habríamos llegado a Cancún a tiempo", "Si el vuelo no hubiera estado demorado, habríamos llegado a Cancún a tiempo"],
        "hint": "Si + past perfect subjunctive, conditional perfect",
        "explanation": "Type 3 conditional: 'si no hubiera estado retrasado' or 'si no se hubiera retrasado'. 'Habríamos llegado' is conditional perfect. In Mexican Spanish, 'retrasado' and 'demorado' are both used for delayed flights. Cancún is Mexico's most famous Caribbean resort.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If I had grown up in Oaxaca, I would speak Zapotec.'",
        "answer": ["Si me hubiera criado en Oaxaca, hablaría zapoteco", "Si me hubiera criado en Oaxaca, hablaría zapoteco."],
        "hint": "Mixed conditional: si + past perfect subjunctive, present conditional result",
        "explanation": "Mixed conditional (Type 3/2): past condition with present result. 'Si me hubiera criado' (past perfect subjunctive), 'hablaría' (present conditional). Oaxaca has the largest Zapotec-speaking population in Mexico — growing up there naturally includes indigenous language exposure.",
        "context": "Mixed conditional: past condition, present result"
    },
    {
        "question": "Translate: 'If she had studied at UNAM, she would be a doctor now.'",
        "answer": ["Si ella hubiera estudiado en la UNAM, sería doctora ahora", "Si hubiera estudiado en la UNAM, sería doctora ahora", "Si ella hubiera estudiado en la UNAM, sería médica ahora"],
        "hint": "Mixed conditional: past condition, present result",
        "explanation": "Mixed conditional: 'si hubiera estudiado' (past unreal) + 'sería' (present result, conditional). UNAM is Mexico's largest and most prestigious university — attending there opens doors to any career, especially medicine.",
        "context": "Mixed conditional: past condition, present result"
    },
    {
        "question": "Translate: 'If the metro had been working, we would be at the Zócalo already.'",
        "answer": ["Si el metro hubiera estado funcionando, ya estaríamos en el Zócalo", "Si el metro hubiera estado funcionando, ya estaríamos en el Zócalo."],
        "hint": "Mixed conditional: si + past perfect subjunctive, present conditional",
        "explanation": "Mixed conditional: past condition ('si hubiera estado funcionando') with present result ('ya estaríamos'). The CDMX Metro frequently has service interruptions, and being stuck is a daily reality for millions. 'Zócalo' is the main plaza in Mexico City.",
        "context": "Mixed conditional: past condition, present result"
    },
    {
        "question": "Translate: 'If only I had tried the cochinita pibil when I was in Mérida!'",
        "answer": ["Ojalá hubiera probado la cochinita pibil cuando estaba en Mérida", "Ojalá hubiese probado la cochinita pibil cuando estaba en Mérida", "Ojalá hubiera probado la cochinita pibil cuando estuve en Mérida"],
        "hint": "Ojalá + past perfect subjunctive for past regrets",
        "explanation": "'Ojalá + hubiera + past participle' expresses a past regret — a wish about something that didn't happen. 'Hubiera probado' is past perfect subjunctive. Cochinita pibil is Yucatán's signature dish — missing it in Mérida is a culinary tragedy.",
        "context": "Ojalá: past regrets with past perfect subjunctive"
    },
    {
        "question": "Translate: 'If only we had visited the Frida Kahlo Museum when we were in CDMX!'",
        "answer": ["Ojalá hubiéramos visitado el Museo de Frida Kahlo cuando estábamos en la CDMX", "Ojalá hubiéramos visitado el Museo Frida Kahlo cuando estábamos en la CDMX"],
        "hint": "Ojalá + past perfect subjunctive (nosotros) for past regrets",
        "explanation": "'Ojalá hubiéramos visitado' — nosotros past perfect subjunctive for a past regret. The Frida Kahlo Museum (Casa Azul) in Coyoacán, CDMX, is one of Mexico's most visited museums — it's a genuine regret to miss it.",
        "context": "Ojalá: past regrets with past perfect subjunctive"
    },
    {
        "question": "Translate: 'If only my grandmother had taught me how to make tamales!'",
        "answer": ["Ojalá mi abuela me hubiera enseñado a hacer tamales", "Ojalá mi abuelita me hubiera enseñado a hacer tamales", "Ojalá mi abuela me hubiera enseñado a preparar tamales"],
        "hint": "Ojalá + past perfect subjunctive for past regrets",
        "explanation": "'Ojalá me hubiera enseñado' expresses a deep past regret. In Mexican families, tamal-making ('hacer tamales') is traditionally passed from grandmother to grandchild. 'Abuelita' adds the affectionate diminutive common in Mexican Spanish.",
        "context": "Ojalá: past regrets with past perfect subjunctive"
    },
    {
        "question": "Translate: 'I would like to order the chilaquiles verdes, please.'",
        "answer": ["Quisiera pedir los chilaquiles verdes, por favor", "Me gustaría pedir los chilaquiles verdes, por favor", "Quisiera ordenar los chilaquiles verdes, por favor"],
        "hint": "Quisiera — conditional/softened request in restaurants",
        "explanation": "'Quisiera' (imperfect subjunctive of 'querer') is used as a polite way to order in Mexican restaurants — more deferential than 'quiero'. Chilaquiles verdes — tortilla chips in tomatillo salsa — are a quintessential Mexican breakfast.",
        "context": "Polite requests: quisiera"
    },
    {
        "question": "Translate: 'Could you bring me the check, please?'",
        "answer": ["Podría traerme la cuenta, por favor", "Me podría traer la cuenta, por favor", "Podría traerme la cuenta, por favor?"],
        "hint": "Podría — conditional for polite requests",
        "explanation": "'Podría' (conditional of 'poder') makes the request much more polite than 'puede'. In Mexican restaurants, 'la cuenta' is the check/bill (not 'el cheque' or 'la factura'). Mexicans value courtesy in service interactions.",
        "context": "Polite requests: podría"
    },
    {
        "question": "Translate: 'We would like a table for four near the patio, please.'",
        "answer": ["Quisiéramos una mesa para cuatro cerca del patio, por favor", "Nos gustaría una mesa para cuatro cerca del patio, por favor", "Quisiéramos una mesa para cuatro cerca del patio, por favor."],
        "hint": "Quisiéramos — conditional for polite restaurant requests",
        "explanation": "'Quisiéramos' (nosotros imperfect subjunctive of 'querer') is the standard polite way to request in Mexican restaurants. Many traditional restaurants in Guadalajara and San Miguel de Allende have beautiful interior patios.",
        "context": "Polite requests: quisiéramos"
    },
    {
        "question": "Translate: 'He acts as if he had never eaten tacos al pastor before.'",
        "answer": ["Actúa como si nunca hubiera comido tacos al pastor", "Se comporta como si nunca hubiera comido tacos al pastor antes"],
        "hint": "Como si + past perfect subjunctive",
        "explanation": "'Como si + hubiera + past participle' describes a past unreal comparison. 'Hubiera comido' is past perfect subjunctive. Tacos al pastor are so ubiquitous in Mexico that never having tried them would be extraordinary.",
        "context": "Como si: past perfect subjunctive"
    },
    {
        "question": "Translate: 'She speaks French as if she had grown up in Montreal.'",
        "answer": ["Habla francés como si se hubiera criado en Montreal", "Hablara francés como si se hubiera criado en Montreal"],
        "hint": "Como si + past perfect subjunctive",
        "explanation": "'Como si se hubiera criado' uses past perfect subjunctive to describe an unreal past condition. 'Criarse' means 'to grow up'. The comparison is to a counterfactual past — she didn't actually grow up in Montreal.",
        "context": "Como si: past perfect subjunctive"
    },
    {
        "question": "Translate: 'They treat the tourists as if they had never seen a pyramid.'",
        "answer": ["Tratan a los turistas como si nunca hubieran visto una pirámide", "Tratan a los turistas como si jamás hubieran visto una pirámide"],
        "hint": "Como si + past perfect subjunctive",
        "explanation": "'Como si hubieran visto' — past perfect subjunctive for a past unreal comparison. Mexico's pyramids (Teotihuacán, Chichén Itzá, Palenque) are so iconic that tourists certainly have seen them, making this a sarcastic comparison.",
        "context": "Como si: past perfect subjunctive"
    },
    {
        "question": "Translate: 'Even if it rained, we would still go to the tianguis.'",
        "answer": ["Aunque lloviera, iríamos al tianguis", "Aunque lloviera, seguiríamos yendo al tianguis", "Incluso si lloviera, iríamos al tianguis"],
        "hint": "Aunque + imperfect subjunctive for 'even if'",
        "explanation": "'Aunque + imperfect subjunctive' means 'even if' (hypothetical concession). 'Lloviera' is the imperfect subjunctive of 'llover'. A 'tianguis' is a traditional open-air market (from Nahuatl 'tianquiztli') — rain or shine, vendors show up because it's their livelihood.",
        "context": "Aunque: even if + imperfect subjunctive"
    },
    {
        "question": "Translate: 'Even if the metro were crowded, I would still take it.'",
        "answer": ["Aunque el metro estuviera lleno, lo tomaría", "Aunque el metro estuviera saturado, lo tomaría igual", "Aunque el metro estuviera lleno, yo lo tomaría"],
        "hint": "Aunque + imperfect subjunctive for 'even if'",
        "explanation": "'Aunque estuviera' (even if it were) + 'tomaría' (I would take). The CDMX Metro is one of the world's busiest — it's always crowded during rush hour, but Mexicans take it anyway because it's the fastest way across the city.",
        "context": "Aunque: even if + imperfect subjunctive"
    },
    {
        "question": "Translate: 'Even if I had more money, I wouldn't buy a car in CDMX.'",
        "answer": ["Aunque tuviera más dinero, no compraría un coche en la CDMX", "Aunque tuviera más dinero, no me compraría un carro en la CDMX", "Aunque tuviera más dinero, no compraría un auto en la CDMX"],
        "hint": "Aunque + imperfect subjunctive for 'even if'",
        "explanation": "'Aunque tuviera' (even if I had) + 'no compraría' (I wouldn't buy). In Mexican Spanish, 'coche' and 'carro' are both used for car; 'auto' is also common. CDMX traffic and parking make car ownership impractical — the metro is more efficient.",
        "context": "Aunque: even if + imperfect subjunctive"
    },
    {
        "question": "Translate: 'Unless you (informal) tried the cochinita, you wouldn't understand.'",
        "answer": ["A menos que probaras la cochinita, no entenderías", "A menos que probaras la cochinita, no entenderías."],
        "hint": "A menos que + imperfect subjunctive",
        "explanation": "'A menos que' (unless) triggers the subjunctive. With a hypothetical/unreal condition, use the imperfect subjunctive 'probaras'. Cochinita pibil — Yucatecan slow-roasted pork — is so uniquely flavorful that understanding it requires tasting it.",
        "context": "A menos que: unless + imperfect subjunctive"
    },
    {
        "question": "Translate: 'We won't go to Chichén Itzá unless the weather improved.'",
        "answer": ["No iremos a Chichén Itzá a menos que mejorara el clima", "No iremos a Chichén Itzá a menos que el clima mejorara", "No vamos a ir a Chichén Itzá a menos que el tiempo mejorara"],
        "hint": "A menos que + imperfect subjunctive",
        "explanation": "'A menos que mejorara' — unless it improved (imperfect subjunctive). This describes a hypothetical condition. Chichén Itzá in Yucatán — one of the New Seven Wonders of the World — is an outdoor site; rain makes the experience difficult.",
        "context": "A menos que: unless + imperfect subjunctive"
    },
    {
        "question": "Translate: 'Unless she spoke Nahuatl, she couldn't work in that community.'",
        "answer": ["A menos que hablara náhuatl, no podría trabajar en esa comunidad", "A menos que hablara náhuatl, no podría trabajar en esa comunidad."],
        "hint": "A menos que + imperfect subjunctive",
        "explanation": "'A menos que hablara' — unless she spoke (imperfect subjunctive). In many indigenous communities in Veracruz, Puebla, and Guerrero, Nahuatl is the primary language — social workers, teachers, and doctors need it to communicate effectively.",
        "context": "A menos que: unless + imperfect subjunctive"
    },
    {
        "question": "Translate: 'I'll bring an umbrella in case it rained.'",
        "answer": ["Voy a llevar un paraguas por si lloviera", "Llevaré un paraguas por si lloviera", "Voy a llevar paraguas por si lloviera"],
        "hint": "Por si + imperfect subjunctive for 'in case'",
        "explanation": "'Por si + imperfect subjunctive' expresses a hypothetical precaution. 'Lloviera' is the imperfect subjunctive. 'Paraguas' (umbrella) is essential during Mexico's rainy season (June-September). 'Llevar' means 'to bring/take' something with you.",
        "context": "Por si: in case + imperfect subjunctive"
    },
    {
        "question": "Translate: 'I'll save a seat at the cantina in case you came later.'",
        "answer": ["Voy a guardar un lugar en la cantina por si vinieras más tarde", "Guardaré un asiento en la cantina por si vinieras más tarde", "Voy a guardar un lugar en la cantina por si llegaras más tarde"],
        "hint": "Por si + imperfect subjunctive for 'in case'",
        "explanation": "'Por si vinieras' — in case you came (imperfect subjunctive). 'Guardar un lugar' means to save a seat. In Mexico, cantinas can fill up quickly after work — saving a seat is a common courtesy among friends.",
        "context": "Por si: in case + imperfect subjunctive"
    },
    {
        "question": "Translate: 'She'll order the aguachile in case the tacos weren't available.'",
        "answer": ["Va a pedir el aguachile por si no hubiera tacos", "Pedirá el aguachile por si no hubiera tacos"],
        "hint": "Por si + imperfect subjunctive for 'in case'",
        "explanation": "'Por si no hubiera' — in case there weren't (imperfect subjunctive of 'haber'). Aguachile — Sinaloan ceviche with lime, chile, and cucumber — is a popular coastal dish. Ordering it as a backup when tacos aren't available is a very Mexican move.",
        "context": "Por si: in case + imperfect subjunctive"
    },
    {
        "question": "Translate: 'If I had known about the Day of the Dead parade, I would have gone.'",
        "answer": ["Si hubiera sabido del desfile del Día de los Muertos, habría ido", "Si hubiera sabido del desfile de Día de Muertos, habría ido", "Si hubiese sabido del desfile del Día de los Muertos, habría ido"],
        "hint": "Type 3 conditional: si + past perfect subjunctive, conditional perfect",
        "explanation": "Type 3 (past unreal): 'si hubiera sabido' (past perfect subjunctive), 'habría ido' (conditional perfect). Mexico City's Día de los Muertos parade — inspired by the James Bond film 'Spectre' — has become a massive annual event since 2016.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If they had sold esquites at the tianguis, we would have bought some.'",
        "answer": ["Si hubieran vendido esquites en el tianguis, habríamos comprado", "Si hubieran vendido esquites en el tianguis, habríamos comprado algunos"],
        "hint": "Type 3 conditional: si + past perfect subjunctive, conditional perfect",
        "explanation": "Type 3: 'si hubieran vendido' (ellos past perfect subjunctive), 'habríamos comprado' (nosotros conditional perfect). 'Esquites' (corn in a cup) are a staple at Mexican tianguis (open-air markets) — their absence would be surprising and disappointing.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If the cantina had had mezcal, I would have ordered one.'",
        "answer": ["Si la cantina hubiera tenido mezcal, habría pedido uno", "Si la cantina hubiera tenido mezcal, habría ordenado uno"],
        "hint": "Type 3 conditional: si + past perfect subjunctive, conditional perfect",
        "explanation": "Type 3: 'si hubiera tenido' (past perfect subjunctive of 'tener'), 'habría pedido' (conditional perfect). A cantina without mezcal is increasingly rare in CDMX — the mezcal renaissance has made it nearly obligatory on any respectable bar menu.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If I had been born in Puebla, I would eat mole every week.'",
        "answer": ["Si hubiera nacido en Puebla, comería mole cada semana", "Si hubiera nacido en Puebla, comería mole todas las semanas"],
        "hint": "Mixed conditional: past condition, present result",
        "explanation": "Mixed conditional: 'si hubiera nacido' (past perfect subjunctive) + 'comería' (present conditional). Being born in Puebla is a past condition; eating mole weekly is the present hypothetical result. Puebla is the birthplace of mole poblano — the most famous mole in Mexico.",
        "context": "Mixed conditional: past condition, present result"
    },
    {
        "question": "Translate: 'If he had taken the pesero, he would be here by now.'",
        "answer": ["Si hubiera tomado el pesero, ya estaría aquí", "Si se hubiera tomado el pesero, ya estaría aquí", "Si hubiera tomado el microbús, ya estaría aquí"],
        "hint": "Mixed conditional: past condition, present result",
        "explanation": "Mixed conditional: 'si hubiera tomado' (past unreal) + 'ya estaría' (present result). 'Pesero' or 'microbús' is the small bus unique to CDMX — taking it instead of walking would have gotten him here by now.",
        "context": "Mixed conditional: past condition, present result"
    },
    {
        "question": "Translate: 'I wish I had visited Teotihuacán during the equinox.'",
        "answer": ["Ojalá hubiera visitado Teotihuacán durante el equinoccio", "Ojalá hubiese visitado Teotihuacán durante el equinoccio"],
        "hint": "Ojalá + past perfect subjunctive for past regrets",
        "explanation": "'Ojalá hubiera visitado' — past perfect subjunctive for a past regret. During the spring equinox, thousands gather at Teotihuacán to receive energy from the sun — it's a spectacular cultural event combining pre-Hispanic tradition with New Age spirituality.",
        "context": "Ojalá: past regrets with past perfect subjunctive"
    },
    {
        "question": "Translate: 'If only the rosca de reyes had had a muñequito for me!'",
        "answer": ["Ojalá la rosca de reyes me hubiera salido un muñequito", "Ojalá me hubiera tocado un muñequito en la rosca de reyes"],
        "hint": "Ojalá + past perfect subjunctive for past regrets",
        "explanation": "'Ojalá me hubiera salido/tocado' — past perfect subjunctive for a past wish. The 'rosca de reyes' (Three Kings bread) contains a tiny baby Jesus figurine ('muñequito'). Whoever finds it must host a party on February 2 (Día de la Candelaria) and make tamales.",
        "context": "Ojalá: past regrets with past perfect subjunctive"
    },
    {
        "question": "Translate: 'I would like a cup of atole, please.'",
        "answer": ["Me gustaría una taza de atole, por favor", "Quisiera una taza de atole, por favor", "Me gustaría un atole, por favor"],
        "hint": "Me gustaría — conditional for polite ordering",
        "explanation": "'Me gustaría' softens the request compared to 'quiero'. Atole — a warm, thick corn-based drink — comes in many flavors (chocolate/champurrado, strawberry, guava, walnut) and is especially popular during Las Posadas and cold mornings.",
        "context": "Polite requests: me gustaría"
    },
    {
        "question": "Translate: 'Could you recommend a good market for chiles?'",
        "answer": ["Podría recomendarme un buen mercado para chiles", "Me podría recomendar un buen mercado para chiles", "Podría recomendarme un buen mercado de chiles"],
        "hint": "Podría — conditional for polite requests",
        "explanation": "'Podría recomendarme' — conditional of 'poder' for a polite request. Much more courteous than '¿Puede recomendarme?'. The Mercado de la Merced in CDMX is the largest dried chile market in Mexico — any local would point you there.",
        "context": "Polite requests: podría"
    },
    {
        "question": "Translate: 'We would like to visit the pyramids of Teotihuacán tomorrow.'",
        "answer": ["Quisiéramos visitar las pirámides de Teotihuacán mañana", "Nos gustaría visitar las pirámides de Teotihuacán mañana"],
        "hint": "Quisiéramos — conditional for polite expressions of desire",
        "explanation": "'Quisiéramos' (imperfect subjunctive of 'querer' used as polite conditional) is a very Mexican way to express a polite desire. Teotihuacán — the City of the Gods, with the Pyramid of the Sun and Moon — is a day trip from CDMX and one of Mexico's must-see archaeological sites.",
        "context": "Polite requests: quisiéramos"
    },
    {
        "question": "Translate: 'They celebrated as if they had won the championship.'",
        "answer": ["Celebraron como si hubieran ganado el campeonato", "Celebraron como si hubiesen ganado el campeonato"],
        "hint": "Como si + past perfect subjunctive",
        "explanation": "'Como si hubieran ganado' — past perfect subjunctive for a past unreal comparison. 'Celebraron' is preterite (they celebrated). In Mexico, soccer (fútbol) championships trigger massive celebrations — the comparison implies they celebrated just as wildly as if they'd actually won.",
        "context": "Como si: past perfect subjunctive"
    },
    {
        "question": "Translate: 'She looked at the menu as if she had never seen enchiladas before.'",
        "answer": ["Miró el menú como si nunca hubiera visto enchiladas", "Miró el menú como si jamás hubiera visto enchiladas antes"],
        "hint": "Como si + past perfect subjunctive",
        "explanation": "'Como si hubiera visto' — past perfect subjunctive for a past unreal comparison. Enchiladas are one of the most common Mexican dishes — pretending not to recognize them on a menu would be quite an act.",
        "context": "Como si: past perfect subjunctive"
    },
    {
        "question": "Translate: 'Even if the line were long, I would wait for the tacos al pastor.'",
        "answer": ["Aunque la fila fuera larga, esperaría los tacos al pastor", "Aunque la fila estuviera larga, esperaría los tacos al pastor", "Aunque la fila fuera larga, esperaría por los tacos al pastor"],
        "hint": "Aunque + imperfect subjunctive for 'even if'",
        "explanation": "'Aunque + imperfect subjunctive' = 'even if' (hypothetical concession). 'Fuera larga' or 'estuviera larga' both work for describing the line. Mexicans will happily wait 30+ minutes at a good taco al pastor stand — it's worth it.",
        "context": "Aunque: even if + imperfect subjunctive"
    },
    {
        "question": "Translate: 'Even if the restaurant were expensive, we would still go for the mole.'",
        "answer": ["Aunque el restaurante fuera caro, iríamos por el mole", "Aunque el restaurante estuviera caro, iríamos por el mole igual"],
        "hint": "Aunque + imperfect subjunctive for 'even if'",
        "explanation": "'Aunque fuera caro' — even if it were expensive (imperfect subjunctive of 'ser'). Mole is one of Mexico's most labor-intensive dishes — some recipes take days — so paying more at a restaurant that makes it from scratch is justified.",
        "context": "Aunque: even if + imperfect subjunctive"
    },
    {
        "question": "Translate: 'Unless it were very late, I would go to the mercado for fresh chiles.'",
        "answer": ["A menos que fuera muy tarde, iría al mercado por chiles frescos", "A menos que estuviera muy tarde, iría al mercado por chiles frescos"],
        "hint": "A menos que + imperfect subjunctive",
        "explanation": "'A menos que fuera/estuviera muy tarde' — unless it were very late (imperfect subjunctive). Mexican mercados are at their best in the early morning when produce is freshest — going late means missing out on the best chiles.",
        "context": "A menos que: unless + imperfect subjunctive"
    },
    {
        "question": "Translate: 'I'll pack some snacks in case we couldn't find food at the bus station.'",
        "answer": ["Voy a empacar algunos snacks por si no encontráramos comida en la central camionera", "Llevaré algunas botanas por si no encontráramos comida en la central de autobuses", "Voy a llevar botanas por si no encontráramos comida en la central camionera"],
        "hint": "Por si + imperfect subjunctive for 'in case'",
        "explanation": "'Por si no encontráramos' — in case we couldn't find (imperfect subjunctive). 'Central camionera' is the uniquely Mexican term for a bus station (also 'central de autobuses'). 'Botanas' is Mexican Spanish for snacks — more common than 'snacks' or 'aperitivos'.",
        "context": "Por si: in case + imperfect subjunctive"
    },
    {
        "question": "Translate: 'I'll buy extra jamaica water in case my cousins came over.'",
        "answer": ["Voy a comprar agua de jamaica extra por si vinieran mis primos", "Compraré más agua de jamaica por si mis primos llegaran"],
        "hint": "Por si + imperfect subjunctive for 'in case'",
        "explanation": "'Por si vinieran' — in case they came (imperfect subjunctive of 'venir'). 'Agua de jamaica' (hibiscus water) is one of Mexico's three essential aguas frescas — it's customary to have it ready when family drops by unexpectedly.",
        "context": "Por si: in case + imperfect subjunctive"
    },
    {
        "question": "Translate: 'If I had had more time, I would have explored the mercado de Sonora.'",
        "answer": ["Si hubiera tenido más tiempo, habría explorado el mercado de Sonora", "Si hubiera tenido más tiempo, habría explorado el mercado de Sonora."],
        "hint": "Type 3 conditional: si + past perfect subjunctive, conditional perfect",
        "explanation": "Type 3: 'si hubiera tenido' (past perfect subjunctive of 'tener') + 'habría explorado' (conditional perfect). The Mercado de Sonora in CDMX is famous for its esoteric and herbal section — a fascinating place to explore if you have time.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If we had arrived earlier, we would have gotten good seats at the Lucha Libre.'",
        "answer": ["Si hubiéramos llegado más temprano, habríamos conseguido buenos asientos en la Lucha Libre", "Si hubiéramos llegado más temprano, habríamos conseguido buenos asientos en la Lucha Libre."],
        "hint": "Type 3 conditional: si + past perfect subjunctive (nosotros), conditional perfect",
        "explanation": "Type 3: 'si hubiéramos llegado' (nosotros past perfect subjunctive) + 'habríamos conseguido' (conditional perfect). Lucha Libre — Mexican professional wrestling — is a beloved spectacle at Arena México in CDMX, and good seats sell out fast.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
    {
        "question": "Translate: 'If he had taken the pesero, he would have arrived on time for the posada.'",
        "answer": ["Si hubiera tomado el pesero, habría llegado a tiempo para la posada", "Si se hubiera tomado el pesero, habría llegado a tiempo para la posada"],
        "hint": "Type 3 conditional: si + past perfect subjunctive, conditional perfect",
        "explanation": "Type 3: 'si hubiera tomado' (past perfect subjunctive) + 'habría llegado' (conditional perfect). 'Pesero' is CDMX's small bus. 'Posada' refers to the traditional Christmas celebration — arriving late to it would be a genuine social failing.",
        "context": "Si clause: Type 3 conditional (past unreal)"
    },
]

multiple_choice = [
    (
        "If I had more money, I would buy a house in Cuernavaca.",
        [
            "Si tenía más dinero, compraba una casa en Cuernavaca.",
            "Si tuve más dinero, compré una casa en Cuernavaca.",
            "Si tuviera más dinero, compraría una casa en Cuernavaca.",
            "Si tendría más dinero, compré una casa en Cuernavaca."
        ],
        3,
        "Type 2 conditional: 'si' + imperfect subjunctive ('tuviera'), main clause conditional ('compraría'). Neither preterite nor imperfect indicative works here. Cuernavaca is called 'la ciudad de la eterna primavera' (city of eternal spring)."
    ),
    (
        "Which form of imperfect subjunctive is strongly preferred in Mexican Spanish?",
        [
            "Hablásemos (the -se form)",
            "Habláramos (the -ra form)",
            "Hablaremos (the future subjunctive)",
            "Hablábamos (the imperfect indicative)"
        ],
        2,
        "Mexican Spanish overwhelmingly prefers the -ra form of the imperfect subjunctive (hablara, comiera, viviera). The -se form (hablase, comiese, viviese) sounds archaic or literary in Mexico, though it's more common in Spain."
    ),
    (
        "I wish I had tried the mezcal in Oaxaca.",
        [
            "Ojalá probé el mezcal en Oaxaca.",
            "Ojalá probaría el mezcal en Oaxaca.",
            "Ojalá probara el mezcal en Oaxaca.",
            "Ojalá hubiera probado el mezcal en Oaxaca."
        ],
        4,
        "For a past regret, 'ojalá + past perfect subjunctive' (hubiera probado) is most precise in Mexican Spanish. 'Probara' (imperfect subjunctive) can also work but is vaguer about timeline. Oaxaca is Mexico's mezcal heartland."
    ),
    (
        "Could you recommend a good taco stand?",
        [
            "¿Puedes recomendarme un buen puesto de tacos?",
            "¿Podrías recomendarme un buen puesto de tacos?",
            "¿Pudieras recomendarme un buen puesto de tacos?",
            "¿Podrás recomendarme un buen puesto de tacos?"
        ],
        2,
        "The conditional 'podrías' makes the request more polite than the indicative 'puedes'. In Mexican culture, politeness is paramount — the conditional is the norm for requests. 'Puesto de tacos' is the authentic term; 'taquería' is also used but 'puesto' specifically means a street stand."
    ),
    (
        "She acts as if she knew everything about Mexican cuisine.",
        [
            "Actúa como si sabe todo sobre la cocina mexicana.",
            "Actúa como si supo todo sobre la cocina mexicana.",
            "Actúa como si supiera todo sobre la cocina mexicana.",
            "Actúa como si sabría todo sobre la cocina mexicana."
        ],
        3,
        "'Como si' always triggers subjunctive because it describes an unreal situation. 'Supiera' (imperfect subjunctive of 'saber') is correct. 'Sabe' is indicative and wrong here. Mexican cuisine is UNESCO Intangible Cultural Heritage."
    ),
    (
        "If we were rich, we would eat mariscada every day.",
        [
            "Si fuimos ricos, comimos mariscada todos los días.",
            "Si somos ricos, comemos mariscada todos los días.",
            "Si fuéramos ricos, comeríamos mariscada todos los días.",
            "Si seríamos ricos, comeríamos mariscada todos los días."
        ],
        3,
        "Type 2 conditional: 'si fuéramos' (imperfect subjunctive of 'ser'), 'comeríamos' (conditional). 'Mariscada' is a Mexican seafood platter — popular in coastal states like Sinaloa, Nayarit, and Baja California."
    ),
    (
        "Which is the correct Mexican expression for 'God willing'?",
        [
            "Si Dios quiera",
            "Si Dios quiere",
            "Ojalá que Dios",
            "Dios mediante quiere"
        ],
        2,
        "'Si Dios quiere' uses INDICATIVE because it expresses a hope about the real future, not a contrary-to-fact condition. 'Si Dios quiera' (subjunctive) is incorrect — the 'si' here is not conditional but temporal. This is a very common Mexican expression."
    ),
    (
        "They spoke as if they had been to every cantina in Guanajuato.",
        [
            "Hablaban como si iban a cada cantina en Guanajuato.",
            "Hablaban como si fueran a cada cantina en Guanajuato.",
            "Hablaban como si habían estado en cada cantina en Guanajuato.",
            "Hablaban como si hubieran estado en cada cantina en Guanajuato."
        ],
        4,
        "'Como si' + past perfect subjunctive ('hubieran estado') for past unreal situations. 'Habían estado' is indicative and incorrect. Guanajuato is famous for its cantinas in the historic center and callejoneada musical tradition."
    ),
    (
        "I would like a mezcal, please. (polite ordering in a bar)",
        [
            "Quiero un mezcal, por favor.",
            "Me gustaría un mezcal, por favor.",
            "Quisiera un mezcal, por favor.",
            "Both 2 and 3 are correct and polite."
        ],
        4,
        "Both 'me gustaría' (conditional of 'gustar') and 'quisiera' (imperfect subjunctive of 'querer' used as polite conditional) are correct and very Mexican. 'Quisiera' is extremely common in Mexican restaurants and shops as a softened, deferential way to order."
    ),
    (
        "If the flight weren't delayed, we would be in Cancún by now.",
        [
            "Si el vuelo no estuviera retrasado, ya estaríamos en Cancún.",
            "Si el vuelo no estaba retrasado, ya estábamos en Cancún.",
            "Si el vuelo no estuvo retrasado, ya estuvimos en Cancún.",
            "Si el vuelo no estará retrasado, ya estaremos en Cancún."
        ],
        1,
        "Type 2 conditional: 'si + imperfect subjunctive, conditional'. 'Estaría retrasado' becomes 'estuviera retrasado'. 'Estaríamos' is conditional. In Mexican Spanish, 'retrasado' or 'retrasado' is used for delayed flights; 'cancelado' for cancelled. Cancún is Mexico's most famous Caribbean resort."
    ),
    (
        "If I had known about the traffic, I would have left earlier for the mercado.",
        [
            "Si sabía del tráfico, salí más temprano para el mercado.",
            "Si sabría del tráfico, saldría más temprano para el mercado.",
            "Si hubiera sabido del tráfico, habría salido más temprano para el mercado.",
            "Si supiera del tráfico, saliera más temprano para el mercado."
        ],
        3,
        "Type 3 conditional: 'si + past perfect subjunctive (hubiera sabido), conditional perfect (habría salido)'. This expresses a past unreal condition. 'Sabía' is imperfect indicative and wrong here. 'Mercado' refers to Mexico's traditional markets."
    ),
    (
        "If she had tried the mole negro, she would have loved it.",
        [
            "Si probó el mole negro, lo amó.",
            "Si probaba el mole negro, lo amaba.",
            "Si hubiera probado el mole negro, lo habría amado.",
            "Si probaría el mole negro, lo amaría."
        ],
        3,
        "Type 3 conditional: 'si hubiera probado' (past perfect subjunctive), 'habría amado' (conditional perfect). Both preterite ('probó/amó') and imperfect ('probaba/amaba') are wrong for counterfactual past. Mole negro is Oaxaca's most complex sauce."
    ),
    (
        "If we had gone to Guadalajara, we would have eaten birria at the original restaurant.",
        [
            "Si fuimos a Guadalajara, comimos birria en el restaurante original.",
            "Si hubiéramos ido a Guadalajara, habríamos comido birria en el restaurante original.",
            "Si íbamos a Guadalajara, comíamos birria en el restaurante original.",
            "Si iríamos a Guadalajara, comeríamos birria en el restaurante original."
        ],
        2,
        "Type 3 conditional: 'si hubiéramos ido' (nosotros past perfect subjunctive), 'habríamos comido' (conditional perfect). 'Fuimos' and 'íbamos' are indicative tenses. Guadalajara is the birthplace of birria."
    ),
    (
        "If I had grown up in Oaxaca, I would speak Zapotec.",
        [
            "Si crecía en Oaxaca, hablaba zapoteco.",
            "Si crecí en Oaxaca, hablé zapoteco.",
            "Si hubiera crecido en Oaxaca, hablaría zapoteco.",
            "Si crecería en Oaxaca, hablaría zapoteco."
        ],
        3,
        "Mixed conditional: past condition + present result. 'Si hubiera crecido' (past perfect subjunctive) + 'hablaría' (present conditional). 'Crecía/hablaba' (imperfect) and 'crecí/hablé' (preterite) are wrong for this counterfactual. Oaxaca has Mexico's largest Zapotec-speaking population."
    ),
    (
        "If she had studied at UNAM, she would be a doctor now.",
        [
            "Si estudió en la UNAM, es doctora ahora.",
            "Si estudiaba en la UNAM, era doctora ahora.",
            "Si hubiera estudiado en la UNAM, sería doctora ahora.",
            "Si estudiara en la UNAM, será doctora ahora."
        ],
        3,
        "Mixed conditional: 'si hubiera estudiado' (past perfect subjunctive) + 'sería' (present conditional). Past unreal condition with present result. UNAM is Mexico's largest and most prestigious university."
    ),
    (
        "If only I had tried the cochinita pibil when I was in Mérida!",
        [
            "Ojalá probé la cochinita pibil cuando estaba en Mérida.",
            "Ojalá probaba la cochinita pibil cuando estaba en Mérida.",
            "Ojalá hubiera probado la cochinita pibil cuando estaba en Mérida.",
            "Ojalá probaría la cochinita pibil cuando estaba en Mérida."
        ],
        3,
        "'Ojalá + past perfect subjunctive' expresses a past regret: 'hubiera probado'. 'Probé' (preterite) and 'probaba' (imperfect) are indicative and wrong. 'Probaría' is conditional, also wrong. Cochinita pibil is Yucatán's signature dish."
    ),
    (
        "If only my grandmother had taught me to make tamales!",
        [
            "Ojalá mi abuela me enseñaba a hacer tamales.",
            "Ojalá mi abuela me enseñó a hacer tamales.",
            "Ojalá mi abuela me hubiera enseñado a hacer tamales.",
            "Ojalá mi abuela me enseñaría a hacer tamales."
        ],
        3,
        "Past regret: 'ojalá + hubiera enseñado' (past perfect subjunctive). 'Enseñó' (preterite) and 'enseñaba' (imperfect) are indicative. In Mexican families, tamal-making is traditionally passed from grandmother to grandchild."
    ),
    (
        "I would like to order the chilaquiles verdes, please.",
        [
            "Quiero pedir los chilaquiles verdes, por favor.",
            "Quisiera pedir los chilaquiles verdes, por favor.",
            "Quisiera pedí los chilaquiles verdes, por favor.",
            "Pido los chilaquiles verdes, por favor."
        ],
        2,
        "'Quisiera' (imperfect subjunctive of 'querer') is used as a polite way to order in Mexican restaurants — much more deferential than 'quiero'. Chilaquiles verdes are tortilla chips in tomatillo salsa, a beloved Mexican breakfast."
    ),
    (
        "Could you bring me the check, please?",
        [
            "¿Puedes traerme la cuenta, por favor?",
            "¿Podrías traerme la cuenta, por favor?",
            "¿Pudiste traerme la cuenta, por favor?",
            "¿Traerme la cuenta, por favor?"
        ],
        2,
        "The conditional 'podrías' makes the request more polite than 'puedes'. In Mexican restaurants, 'la cuenta' is the bill — not 'el cheque' or 'la factura'. Politeness in service interactions is highly valued in Mexican culture."
    ),
    (
        "He acts as if he had never eaten tacos al pastor before.",
        [
            "Actúa como si nunca comió tacos al pastor.",
            "Actúa como si nunca comía tacos al pastor.",
            "Actúa como si nunca hubiera comido tacos al pastor.",
            "Actúa como si nunca comería tacos al pastor."
        ],
        3,
        "'Como si + past perfect subjunctive' for a past unreal comparison: 'hubiera comido'. 'Comió' (preterite) and 'comía' (imperfect) are indicative and wrong. Tacos al pastor are so ubiquitous in Mexico that never having tried them would be extraordinary."
    ),
    (
        "They celebrated as if they had won the championship.",
        [
            "Celebraron como si ganaron el campeonato.",
            "Celebraron como si ganaban el campeonato.",
            "Celebraron como si hubieran ganado el campeonato.",
            "Celebraron como si ganarían el campeonato."
        ],
        3,
        "'Como si + past perfect subjunctive': 'hubieran ganado'. 'Ganaron' (preterite) and 'ganaban' (imperfect) are indicative. In Mexico, soccer championships trigger massive celebrations — this comparison implies wild celebrating."
    ),
    (
        "Even if it rained, we would still go to the tianguis.",
        [
            "Aunque llovió, fuimos al tianguis.",
            "Aunque llueve, vamos al tianguis.",
            "Aunque lloviera, iríamos al tianguis.",
            "Aunque lloverá, iremos al tianguis."
        ],
        3,
        "'Aunque + imperfect subjunctive' for 'even if' (hypothetical concession): 'lloviera'. The conditional 'iríamos' follows. 'Llovió' and 'llueve' are indicative. A 'tianguis' is a traditional open-air market — vendors show up rain or shine."
    ),
    (
        "Even if I had more money, I wouldn't buy a car in CDMX.",
        [
            "Aunque tuve más dinero, no compré un coche en la CDMX.",
            "Aunque tengo más dinero, no compro un coche en la CDMX.",
            "Aunque tuviera más dinero, no compraría un coche en la CDMX.",
            "Aunque tendría más dinero, no compro un coche en la CDMX."
        ],
        3,
        "'Aunque + imperfect subjunctive' = 'even if': 'tuviera' + conditional 'compraría'. 'Tuve' (preterite) and 'tengo' (present) are indicative. CDMX traffic makes car ownership impractical despite any amount of money."
    ),
    (
        "Unless you tried the cochinita, you wouldn't understand.",
        [
            "A menos que probaste la cochinita, no entiendes.",
            "A menos que pruebes la cochinita, no entiendes.",
            "A menos que probaras la cochinita, no entenderías.",
            "A menos que probarás la cochinita, no entenderás."
        ],
        3,
        "'A menos que + imperfect subjunctive' for hypothetical 'unless': 'probaras' + conditional 'no entenderías'. 'Probaste' (preterite) is wrong. 'Pruebes' (present subjunctive) would work for a future possibility, but this sentence describes a hypothetical."
    ),
    (
        "We won't go to Chichén Itzá unless the weather improved.",
        [
            "No iremos a Chichén Itzá a menos que mejora el clima.",
            "No iremos a Chichén Itzá a menos que mejoró el clima.",
            "No iremos a Chichén Itzá a menos que mejorara el clima.",
            "No iremos a Chichén Itzá a menos que mejorará el clima."
        ],
        3,
        "'A menos que + imperfect subjunctive' for hypothetical 'unless': 'mejorara'. 'Mejora' and 'mejoró' are indicative. Chichén Itzá — a New Wonder of the World in Yucatán — is an outdoor archaeological site where weather matters."
    ),
    (
        "I'll bring an umbrella in case it rained.",
        [
            "Voy a llevar un paraguas por si llueve.",
            "Voy a llevar un paraguas por si llovió.",
            "Voy a llevar un paraguas por si lloviera.",
            "Voy a llevar un paraguas por si lloverá."
        ],
        3,
        "'Por si + imperfect subjunctive' for hypothetical 'in case': 'lloviera'. This describes a hypothetical future possibility. 'Llueve' (present indicative) is used for real-time observation, not hypothetical precautions. 'Paraguas' is essential during Mexico's rainy season (June-September)."
    ),
    (
        "I'll save a seat at the cantina in case you came later.",
        [
            "Guardaré un asiento en la cantina por si vienes más tarde.",
            "Guardaré un asiento en la cantina por si viniste más tarde.",
            "Guardaré un asiento en la cantina por si vinieras más tarde.",
            "Guardaré un asiento en la cantina por si vendrás más tarde."
        ],
        3,
        "'Por si + imperfect subjunctive' for hypothetical 'in case': 'vinieras'. 'Vienes' (present indicative) is used when the possibility is likely, but 'vinieras' emphasizes uncertainty. Cantinas fill up quickly after work — saving a seat is common courtesy."
    ),
    (
        "Which is the correct form for: 'If I had known about the Day of the Dead parade, I would have gone'?",
        [
            "Si sabía del desfile del Día de los Muertos, iba.",
            "Si supe del desfile del Día de los Muertos, fui.",
            "Si hubiera sabido del desfile del Día de los Muertos, habría ido.",
            "Si sabría del desfile del Día de los Muertos, iría."
        ],
        3,
        "Type 3 conditional: 'si hubiera sabido' (past perfect subjunctive) + 'habría ido' (conditional perfect). 'Sabía/iba' and 'supe/fui' are indicative pairs. Mexico City's Día de los Muertos parade has been a massive event since 2016."
    ),
    (
        "If the cantina had had mezcal, I would have ordered one.",
        [
            "Si la cantina tuvo mezcal, pedí uno.",
            "Si la cantina tenía mezcal, pedía uno.",
            "Si la cantina hubiera tenido mezcal, habría pedido uno.",
            "Si la cantina tendría mezcal, pediría uno."
        ],
        3,
        "Type 3: 'si hubiera tenido' (past perfect subjunctive) + 'habría pedido' (conditional perfect). 'Tuvo/pedí' and 'tenía/pedía' are indicative pairs and wrong for counterfactual past. A cantina without mezcal is increasingly rare in CDMX."
    ),
    (
        "If I had been born in Puebla, I would eat mole every week.",
        [
            "Si nací en Puebla, como mole cada semana.",
            "Si nacía en Puebla, comía mole cada semana.",
            "Si hubiera nacido en Puebla, comería mole cada semana.",
            "Si nacería en Puebla, comería mole cada semana."
        ],
        3,
        "Mixed conditional: 'si hubiera nacido' (past perfect subjunctive) + 'comería' (present conditional). 'Nací/como' and 'nacía/comía' are indicative. Being born is a past event; eating mole weekly is a present hypothetical result. Puebla is the birthplace of mole poblano."
    ),
    (
        "If he had taken the pesero, he would be here by now.",
        [
            "Si tomó el pesero, está aquí ya.",
            "Si tomaba el pesero, estaba aquí ya.",
            "Si hubiera tomado el pesero, ya estaría aquí.",
            "Si tomaría el pesero, estará aquí ya."
        ],
        3,
        "Mixed conditional: 'si hubiera tomado' (past perfect subjunctive) + 'estaría' (present conditional). Past unreal condition with present result. 'Pesero' is CDMX's small bus — taking it would have gotten him here by now."
    ),
    (
        "I wish I had visited Teotihuacán during the equinox.",
        [
            "Ojalá visité Teotihuacán durante el equinoccio.",
            "Ojalá visitaba Teotihuacán durante el equinoccio.",
            "Ojalá hubiera visitado Teotihuacán durante el equinoccio.",
            "Ojalá visitaría Teotihuacán durante el equinoccio."
        ],
        3,
        "Past regret: 'ojalá + hubiera visitado' (past perfect subjunctive). 'Visité' and 'visitaba' are indicative. During the spring equinox, thousands gather at Teotihuacán to receive energy from the sun — a spectacular cultural event."
    ),
    (
        "We would like to visit the pyramids of Teotihuacán tomorrow.",
        [
            "Queremos visitar las pirámides de Teotihuacán mañana.",
            "Quisiéramos visitar las pirámides de Teotihuacán mañana.",
            "Queríamos visitar las pirámides de Teotihuacán mañana.",
            "Quisimos visitar las pirámides de Teotihuacán mañana."
        ],
        2,
        "'Quisiéramos' (imperfect subjunctive of 'querer') is the polite way to express a desire in Mexican Spanish. 'Queremos' is too direct for polite contexts. Teotihuacán — the City of the Gods — is a must-see archaeological site near CDMX."
    ),
    (
        "She looked at the menu as if she had never seen enchiladas before.",
        [
            "Miró el menú como si nunca vio enchiladas.",
            "Miró el menú como si nunca veía enchiladas.",
            "Miró el menú como si nunca hubiera visto enchiladas.",
            "Miró el menú como si nunca vería enchiladas."
        ],
        3,
        "'Como si + past perfect subjunctive': 'hubiera visto'. 'Vio' (preterite) and 'veía' (imperfect) are indicative and wrong after 'como si'. Enchiladas are one of the most common Mexican dishes — not recognizing them would be extraordinary."
    ),
    (
        "Even if the line were long, I would wait for the tacos al pastor.",
        [
            "Aunque la fila es larga, espero los tacos al pastor.",
            "Aunque la fila era larga, esperaba los tacos al pastor.",
            "Aunque la fila fuera larga, esperaría los tacos al pastor.",
            "Aunque la fila será larga, esperaré los tacos al pastor."
        ],
        3,
        "'Aunque + imperfect subjunctive' for hypothetical 'even if': 'fuera larga' + conditional 'esperaría'. 'Es larga' and 'era larga' are indicative. Mexicans happily wait at good taco al pastor stands — the line is part of the experience."
    ),
    (
        "I'll pack some snacks in case we couldn't find food at the bus station.",
        [
            "Voy a empacar botanas por si no encontramos comida en la central camionera.",
            "Voy a empacar botanas por si no encontramos comida en la central camionera.",
            "Voy a empacar botanas por si no encontráramos comida en la central camionera.",
            "Voy a empacar botanas por si no encontraremos comida en la central camionera."
        ],
        3,
        "'Por si + imperfect subjunctive' for hypothetical 'in case': 'no encontráramos'. 'Botanas' is Mexican Spanish for snacks. 'Central camionera' is the uniquely Mexican term for a bus station. The imperfect subjunctive emphasizes the hypothetical nature of the possibility."
    ),
    (
        "I'll buy extra agua de jamaica in case my cousins came over.",
        [
            "Voy a comprar más agua de jamaica por si mis primos vienen.",
            "Voy a comprar más agua de jamaica por si mis primos vinieron.",
            "Voy a comprar más agua de jamaica por si mis primos vinieran.",
            "Voy a comprar más agua de jamaica por si mis primos vendrán."
        ],
        3,
        "'Por si + imperfect subjunctive' for hypothetical 'in case': 'vinieran'. 'Vienen' (present) works for likely scenarios, but 'vinieran' emphasizes the hypothetical possibility. 'Agua de jamaica' (hibiscus water) is a staple agua fresca always ready for unexpected family visits."
    ),
    (
        "If the flight had not been delayed, we would have arrived in Cancún on time.",
        [
            "Si el vuelo no estaba retrasado, llegamos a Cancún a tiempo.",
            "Si el vuelo no estuvo retrasado, llegamos a Cancún a tiempo.",
            "Si el vuelo no hubiera estado retrasado, habríamos llegado a Cancún a tiempo.",
            "Si el vuelo no estaría retrasado, llegaríamos a Cancún a tiempo."
        ],
        3,
        "Type 3: 'si no hubiera estado retrasado' (past perfect subjunctive) + 'habríamos llegado' (conditional perfect). 'Estaba' and 'estuvo' are indicative and wrong for counterfactual past. Cancún is Mexico's most famous Caribbean resort destination."
    ),
    (
        "If we had arrived earlier, we would have gotten good seats at the Lucha Libre.",
        [
            "Si llegamos más temprano, conseguimos buenos asientos en la Lucha Libre.",
            "Si hubiéramos llegado más temprano, habríamos conseguido buenos asientos en la Lucha Libre.",
            "Si llegábamos más temprano, conseguíamos buenos asientos en la Lucha Libre.",
            "Si llegaríamos más temprano, conseguiríamos buenos asientos en la Lucha Libre."
        ],
        2,
        "Type 3: 'si hubiéramos llegado' (nosotros past perfect subjunctive) + 'habríamos conseguido' (conditional perfect). 'Llegamos/conseguimos' (present) and 'llegábamos/conseguíamos' (imperfect) are wrong for counterfactual past. Lucha Libre at Arena México sells out fast."
    ),
    (
        "Unless it were very late, I would go to the mercado for fresh chiles.",
        [
            "A menos que es muy tarde, voy al mercado por chiles frescos.",
            "A menos que era muy tarde, iba al mercado por chiles frescos.",
            "A menos que fuera muy tarde, iría al mercado por chiles frescos.",
            "A menos que será muy tarde, iré al mercado por chiles frescos."
        ],
        3,
        "'A menos que + imperfect subjunctive' for hypothetical 'unless': 'fuera muy tarde' + conditional 'iría'. 'Es' and 'era' are indicative and wrong. Mexican mercados are at their best in the early morning when produce is freshest."
    ),
]

if __name__ == "__main__":
    run_exercises(translation_exercises, title="Lesson 2: Imperfect Subjunctive & Conditional in Mexican Spanish — Translation Exercises")
    choose_translation(multiple_choice, title="Lesson 2: Imperfect Subjunctive & Conditional in Mexican Spanish — Multiple Choice")