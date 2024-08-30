from google_calendar.calendar_api import GoogleCalendarAPI

calendar_api = GoogleCalendarAPI()

# instructors=["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val", "Daniel", "David", "Rodrigo"]
instructors=["Afonso"]
priorities=[
    ('Bia', 'Storytelling com dados'),
    ('Bia', 'Engenharia reversa com o Power Architect'),
    ('Bia', '3811 - Modelagem de dados: Modelo físico'),
    ('Bia', 'O que é normalização?'),
    ('Igor', 'Qualidade de dados na Cloud'),
    ('Igor', 'Dicionário de Dados'),
    ('Igor', '3809 - Modelagem de dados: Modelo lógico'),
    ('Igor', 'Modelo lógico x Modelo físico'),
    ('Igor', 'O que é e para que serve a modelagem de dados?'),
    ('Allan', '3774 - TensorFlow Keras: Completando textos com redes LSTM'),
    ('Allan', '3773 - TensorFlow Keras: Classificando imagens com redes convolucionais'),
    ('Allan', 'Métricas de avaliação para clusterização'),
    ('Marcelo', 'CRAN, R forge e Git hub: Aonde encontrar meu pacote?'),
    ('Marcelo', 'Governança de dados em um Data Lake'),
    ('Marcelo', 'Séries temporais e suas aplicações'),
    ('Marcelo', 'Como a correlação é utilizada na prática'),
    ('Marcelo', 'Identação e boas práticas em medidas'),
    ('Marcelo', '3777 - Power BI: Construindo cálculos com Dax'),
    ('Marcelo', 'Power BI: DAX Cheat Sheet'),
    ('Marcelo', 'Tipos de dados no Power BI'),
    ('Marcelo', 'Como criar sua conta do Power BI (Colocar dentro do curso)'),
    ('Val', 'Boosting'),
    ('Val', '3765 - NLP: aprendendo processamento de linguagem natural'),
    ('Val', '3768 - Regressão: modelos boosting'),
    ('Mirla', 'Árvores para Classificação e Regressão'),
    ('Mirla', 'PLN: o que é Processamento de Linguagem Natural?'),
    ('Mirla', '3764 - Clusterização: lidando com dados sem rótulo'),
    ('Mirla', '3767 - Regressão: árvores de regressão'),
    ('Afonso', '3766 - Regressão Linear: técnicas avançadas de modelagem'),
    ('Afonso', 'Carreiras em Dados [2024-06-14]'),
    ('Afonso', 'Análise de Dados [2024-05-03]'),
    ('Ana Duarte', 'Importando uma planilha do Excel e tratando células mescladas'),
    ('Ana Duarte', 'Alinhamento da versão'),
    ('João', '9208 - Métricas de regressão'),
    ('João', '3769 - Regressão: Análise de Séries temporais'),
    ('João', 'Quais os algoritmos de clusterização e quando utilizar?'),
]
calendar_api.update_quarterly_calendars(quarter="2_Tri_2024", start_work_cycle="2024-04-01", instructors=instructors, priorities=priorities)