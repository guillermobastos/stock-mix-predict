📊 Predicción de Precios y Clasificación de Cambios

Este proyecto utiliza Machine Learning para predecir la dirección de los precios financieros basándose en datos históricos. Se entrenan varios modelos para clasificar cambios futuros en distintas categorías y visualizar las predicciones con gráficos.

🚀 Características Principales

Cálculo de cambios porcentuales a 1 semana, 2 semanas y 1 mes.

Clasificación de cambios futuros en 5 categorías basadas en percentiles.

Predicción con modelos de Machine Learning:

Random Forest

XGBoost

Gradient Boosting

LightGBM

Visualización de predicciones con bandas de confianza y tendencias proyectadas.

📂 Estructura del Proyecto

📁 Proyecto
│── 📜 clasificador-2w.ipynb       # Jupyter Notebook con todo el flujo de trabajo
│── 📜 README.md            # Documentación del proyecto

🛠 Instalación y Requisitos

Clonar el repositorio:

git clone https://github.com/guillermobastos/stock-2w-predict.git
cd stock-2w-predict

Abrir el Jupyter Notebook:

jupyter notebook

Luego, ejecutar clasificador-2w.ipynb.

📊 Método de Clasificación

Los cambios porcentuales de precio se clasifican en cinco categorías según percentiles históricos:

Clase

Interpretación

0

Venta muy fuerte

1

Venta moderada

2

Neutral

3

Compra moderada

4

Compra muy fuerte

Los percentiles se calculan dinámicamente en función del dataset.

📉 Visualización de Predicciones

Se generan gráficos que:

Muestran el precio histórico.

Proyectan posibles escenarios futuros con bandas de confianza.

Permiten comparar predicciones entre diferentes modelos.

Ejemplo de predicción:


🔍 Evaluación del Modelo

Los modelos se evalúan en función de:

Precisión en la clasificación (Future_Class_2w).

Distribución de predicciones comparadas con los valores reales.


# Futuras implementaciones 
1. Añadir los resultados trimestrales
2. Noticias de interés que hayan afectado considerablemente a la acción
3. Datos de los días previos a una gran subida o una gran bajada
4. Añadir tendencias tanto de la acción, mercado
5. Estado financiero de la empresa
6. Implementar una estrategia de hiperparametrización automática.
7. Probar modelos más avanzados como Redes Neuronales.

📌 Autor

[Guillermo Bastos Ribas]📧 Contacto: [guilleribastos@gmail.com]🔗 LinkedIn: [www.linkedin.com/in/guillermo-bastos-4aba6b156]
