from google_calendar.calendar_api import GoogleCalendarAPI

calendar_api = GoogleCalendarAPI()

# instructors=["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val"]
instructors=["João"]
priorities=[
    ('Igor', 'Modelo lógico x Modelo físico'),
    ('Igor', 'O que é e para que serve a modelagem de dados?'),
    ('Allan', '3774 - Crie uma IA com TensorFlow'),
    ('Allan', '3773 - Dominando Hugging Face Transformers com Python'),
    ('Allan', 'Métricas de avaliação para clusterização'),
    ('Marcelo', 'Séries temporais e suas aplicações'),
    ('Marcelo', '3777 - Power BI: Construindo cálculos com Dax'),
    ('Marcelo', 'Como a correlação é utilizada na prática'),
    ('Marcelo', 'Identação e boas práticas em medidas'),
    ('Marcelo', 'Tipos de dados no Power BI'),
    ('Val', 'Boosting'),
    ('Val', '3768 - Regressão: modelos boosting'),
    ('Val', '3765 - NLP: aprendendo processamento de linguagem natural'),
    ('Mirla', 'Árvores para Classificação e Regressão'),
    ('Mirla', '3767 - Regressão: árvores de regressão'),
    ('Mirla', '3764 - Clusterização: lidando com dados sem rótulo'),
    ('Afonso', '3766 - Regressão Linear: técnicas avançadas de modelagem'),
    ('Afonso', 'Carreiras em Dados [2024-06-14]'),
    ('Afonso', 'Análise de Dados [2024-05-03]'),
    ('Ana Duarte', 'Alinhamento da versão'),
    ('João', '9208 - Métricas de regressão'),
    ('João', '3769 - Regressão: Análise de Séries temporais'),
    ('João', 'Quais os algoritmos de clusterização e quando utilizar?'),
]
calendar_api.update_quarterly_calendars(quarter="2_Tri_2024", start_work_cycle="2024-04-01", instructors=instructors, priorities=priorities)