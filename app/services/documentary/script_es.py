"""Guion del documental «¿Cómo sobrevivían los humanos a la Edad de Hielo?».

Cada escena tiene una lista de cláusulas. Cada cláusula se sintetiza por
separado, de modo que los tiempos de la narración, de los subtítulos y de las
escenas se conocen con exactitud (sin estimaciones).
"""

TITLE = "¿CÓMO SOBREVIVÍAN LOS HUMANOS A LA EDAD DE HIELO?"
END_CARD = "Así comenzó nuestra historia."

# (pausa tras la cláusula en segundos, texto)
SCENES = [
    {   # 1 – el mundo helado
        "id": "mundo_helado",
        "clauses": [
            ("Hace más de veinte mil años,", 0.25),
            ("enormes glaciares cubrían gran parte del planeta.", 0.5),
            ("El frío extremo ponía a prueba a cada ser humano.", 0.0),
        ],
    },
    {   # 2 – caza y pieles
        "id": "caza",
        "clauses": [
            ("Para resistir, cazaban mamuts,", 0.25),
            ("y con sus pieles confeccionaban abrigos gruesos.", 0.45),
            ("Los huesos se convertían en herramientas.", 0.0),
        ],
    },
    {   # 3 – el fuego
        "id": "fuego",
        "clauses": [
            ("El fuego lo cambió todo.", 0.45),
            ("Les daba calor y luz,", 0.2),
            ("alejaba a las fieras,", 0.2),
            ("y permitía cocinar los alimentos.", 0.0),
        ],
    },
    {   # 4 – refugio
        "id": "refugio",
        "clauses": [
            ("Cuando llegaban las tormentas,", 0.25),
            ("se refugiaban en cuevas,", 0.2),
            ("o levantaban tiendas con huesos y pieles.", 0.0),
        ],
    },
    {   # 5 – comunidad
        "id": "comunidad",
        "clauses": [
            ("Su mayor fortaleza era la comunidad.", 0.45),
            ("Compartían la comida,", 0.2),
            ("cuidaban a los niños,", 0.2),
            ("y transmitían su sabiduría junto a la hoguera.", 0.0),
        ],
    },
    {   # 6 – amanecer
        "id": "amanecer",
        "clauses": [
            ("Gracias a su ingenio, su unión y su valentía,", 0.3),
            ("la humanidad superó el hielo.", 0.5),
            ("Y así, comenzó nuestra historia.", 0.0),
        ],
    },
]
