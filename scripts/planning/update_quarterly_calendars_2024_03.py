from google_calendar.calendar_api import GoogleCalendarAPI

calendar_api = GoogleCalendarAPI()

# instructors=["Afonso", "Allan", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val", "Daniel", "Larissa"]
# instructors=["João"]
# instructors=["Victorino"]

priorities=[
    ('Allan', 'Modelos matemáticos utilizados em séries temporais'),
    ('Allan', 'Arquiteturas de redes neurais'),
    ('Allan', 'O que são redes neurais e como funcionam'),
    ('Allan', '3982 - TensorFlow/Keras: Gerando imagens com Deep Learning'),
    ('Allan', '3981 - TensorFlow/Keras: Reconhecimento de áudio'),
    ('Marcelo', 'Explorando modelos para linguagem natural'),
    ('Marcelo', '4025 - Engenharia de Analytics: Curso 3'),
    ('Marcelo', '3976 - NLP: resumindo textos com Hugging Face'),
    ('Afonso', 'Aplicações do R'),
    ('Afonso', '4024 - Engenharia de Analytics: Curso 2'),
    ('Afonso', '3819 - R: Aplicando Data Visualization com ggplot2'),
    ('Victorino', '4013 - Administração com PostgreSQL: Replicação e Alta Disponibilidade'),
    ('Victorino', '4012 - Administração com PostgreSQL: Desempenho e Otimização'),
    ('Victorino', '3980 - Data Storytelling - Tableau'),
    ('Victorino', '4011 - Administração com PostgreSQL: Backup e Recuperação'),
    ('Victorino', '4010 - Administração com PostgreSQL: Administração e Monitoramento'),
    ('Larissa', 'Métricas de regressão'),
    ('Larissa', 'O que são Transformers'),
    ('Larissa', 'Hugging Face'),
    ('Larissa', 'Chatbot [2024-07-30]'),
]
# Construção de gráficos e tabelas em fase de planejamento
# agendas_json = calendar_api.create_quarterly_planning_events_json(
#     quarter="3_Tri_2024", 
#     start_work_cycle="2024-07-12", 
#     instructors=instructors, 
#     priorities=priorities
# )

# Atualização dos calendários

# calendar_api.update_quarterly_calendars(
#     quarter="3_Tri_2024", 
#     start_work_cycle="2024-07-08", 
#     instructors=["Daniel"], 
#     priorities=priorities
# )

# calendar_api.update_quarterly_calendars(
#     quarter="3_Tri_2024", 
#     start_work_cycle="2024-07-01", 
#     instructors=["Afonso", "Allan", "Danielle", "Igor", "Marcelo", "Mirla", "Val"], 
#     priorities=priorities
# )

# calendar_api.update_quarterly_calendars(
#     quarter="3_Tri_2024", 
#     start_work_cycle="2024-07-04", 
#     instructors=["Bia", "João"], 
#     priorities=priorities
# )

# calendar_api.update_quarterly_calendars(
#     quarter="3_Tri_2024", 
#     start_work_cycle="2024-07-12", 
#     instructors=["Victorino"], 
#     priorities=priorities
# )

# calendar_api.update_quarterly_calendars(
#     quarter="3_Tri_2024", 
#     start_work_cycle="2024-07-15", 
#     instructors=["Sabino"], 
#     priorities=priorities
# )

# calendar_api.update_quarterly_calendars(
#     quarter="3_Tri_2024", 
#     start_work_cycle="2024-07-29", 
#     instructors=["Larissa"], 
#     priorities=priorities
# )
