# Bitácora del desarrollo asistido por inteligencia artificial

Autor: Héctor Manuel Salazar Rivera

## Agentes empleados

| Parte | Agente | Qué hizo |
|---|---|---|
| Punto 1, análisis formal (PDF del examen) | Codex | Complejidad temporal y espacial de los dos algoritmos y correctitud de Bubble Sort |
| Punto 1, anexo del análisis formal (`anexo_analisis_formal.pdf`) | Claude Code | Terminación, corrección de Quicksort, pivote por mediana de 3 y ajustes al examen |
| Punto 1, código, experimento y gráficas | Claude Code | Implementación, pruebas, experimento, pestaña de comparación y gráficas |
| Punto 2, animación | Claude Code | Pestaña de animación y su reproducción de eventos |
| Punto 3, documentos | Claude Code | README, informe de resultados y esta bitácora |

**Incumplimiento conocido:** el enunciado pide que la sección 2 use un agente diferente del empleado en la sección 1. El código de las dos secciones lo hizo el mismo agente, Claude Code, así que esa condición no se cumple.

## Instrucciones principales

Estas son las instrucciones dadas al agente de código, en orden. Se copian tal como se escribieron.

1. "Desde el punto 2 necesitamos empezar a aplicar ciertos algoritmos como bubble sort y quicksort, no se si mas. El codigo en ingles, explicacion en espanol. usa /write para escribir. Primero analisemos todo el documento y el entregable para saber que vamos a realizar." (adjunto: el enunciado en PDF)
2. "El punto 1 ya esta hecho: Examen 1 - Optimización y Métodos Computacionales.pdf Borra sorting_algorithms fue creado en un intento fallido ahorita. Crea una buena estructura para cada uno de los puntos, que todo quede ordenado, ademas que las animaciones si se peude sean hechas con /design y que hagas unas graficas de comparacioun entr algoritmos, y todos los datos obtenidos. Para el quicksort haga la eleccion del pivote con la formula de mediana de 3."
3. "The design is good enogugh, lets top with design audits"

## Intervenciones del estudiante

- Interrumpió el primer intento, que era un cuaderno de Jupyter, y pidió borrarlo.
- Indicó que el análisis formal ya estaba hecho en el PDF del examen.
- Eligió la mediana de 3 como pivote de Quicksort.
- Pidió una carpeta ordenada por punto, las gráficas de comparación y todos los datos.
- Dio por suficiente el diseño de la interfaz y detuvo las auditorías de diseño.
- Probó la aplicación y reportó dos problemas: una flecha que avanzó 5 pasos y el diálogo de Guardar. Los dos se investigaron; el resultado está en la validación.

## Validación realizada por el agente

Se ejecutó el 9 de noviembre de 2026, sobre el código entregado.

- **Pruebas:** 26 pruebas automáticas, todas pasan.
- **Prueba de las pruebas:** se rompió el código a propósito en 11 puntos, 7 en los algoritmos y 4 en la reproducción de la animación. En los 11 casos falló la prueba esperada. Después se restauró el código y las pruebas volvieron a pasar.
- **Aplicación real:** unos guiones manejaron los controles de la ventana real en 1320x860 y 1120x780, y revisaron atajos de teclado, pausa durante un intercambio, retroceso, entradas inválidas, detención de una corrida y guardado.
- **Diálogo real de Guardar:** un guion pulsó Guardar y manejó el diálogo de carpetas real de Tk 8.6.16. Funcionó con una carpeta existente, una carpeta nueva con espacios y acentos, al guardar dos veces en la misma carpeta y al cancelar. Una carpeta de solo lectura muestra el error en la ventana. Los 11 archivos guardados se volvieron a leer con los mismos datos. Si se escribe una ruta que pasa por un archivo, el propio diálogo de Tk devuelve la carpeta que estaba mostrando, y la aplicación guarda ahí; el mensaje de la ventana dice esa carpeta.
- **Flecha que avanzó 5 pasos:** se reprodujo. El guion toma el foco del teclado en Wayland, y las teclas que se escribían en ese momento en la terminal llegaron a la aplicación. El registro mostró teclas con marca de tiempo del teclado físico, que el guion no envió. La aplicación avanzó un paso por cada tecla, en reposo, en pausa, durante un intercambio y en reproducción, a las tres velocidades. No era un fallo de la aplicación. El foco vacío de otra corrida tiene la misma causa: Wayland a veces no deja que el guion tome el foco.
- **Contraste de colores:** se calculó para tres pares de colores de la interfaz y todos cumplen el mínimo.

## Lo que no se validó

- **Diseño:** la última crítica de la interfaz con puntaje dio 22/40, por debajo del mínimo de 32/40 que usa la herramienta. Se hicieron correcciones después, pero la crítica no se repitió y la auditoría final no se ejecutó: se detuvieron al dar el diseño por suficiente.
- **Causa de la pendiente de Bubble Sort:** la memoria caché es una hipótesis; no se midió.
