# # --------------------------------------------------------------------------------------
# # Atualizando o database de Conteúdos Produzidos de cada instrutor
# # Adicionando apenas uma coluna ao database
# # --------------------------------------------------------------------------------------
# from notion.notion_api import NotionAPI
# from dotenv import load_dotenv
# import os
# import json

# instructors=["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val"]
# json_data = {
#     "properties": {
#         "Nome na Plataforma": {"rich_text": {}},
#     }
# }
# notion = NotionAPI()
# load_dotenv()
# database_users = os.getenv('DATABASE_USERS')
# user_pages = notion.retrieve_database(database_users)

# for instructor in instructors:
#     for user_page in user_pages:
#         if instructor == user_page['properties']['Nome']['rich_text'][0]['text']['content']:
#             results = notion.retrieve_block_children(user_page['id'])
#             for result in results:
#                 if result['child_page']['title'] == 'Conteúdos Produzidos':
#                     response = notion.update_database(notion.retrieve_block_children(result['id'])[0]['id'], json_data)
#                     print(json.dumps(response[0], indent=4, sort_keys=True, ensure_ascii=False))
#                     print(50*'=')
# # --------------------------------------------------------------------------------------
# # --------------------------------------------------------------------------------------
# # Atualizando o database de Conteúdos Produzidos de cada instrutor
# # Adicionando conteúdos criados antes do Olho de Deus
# # --------------------------------------------------------------------------------------
# from notion.notion_api import NotionAPI
# from gods_eye.utils import icons
# from dotenv import load_dotenv
# import os
# import json

# import requests
# from bs4 import BeautifulSoup
# import pandas as pd
# import quopri

# file_path = "./docs/extra_content_alura.mhtml"
# instructors=["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val"]
# instructors_name=[
#     "Afonso Augusto Rios", 
#     "Allan Segovia Spadini", 
#     "Ana  Duarte", 
#     "Beatriz Magalhães", 
#     "Danielle Oliveira", 
#     "Igor Nascimento Alves", 
#     "João Vitor de Miranda", 
#     "Marcelo Cruz", 
#     "Mirla Costa", 
#     "Valquíria Alencar"
# ]

# with open(file_path, 'rb') as file:
#     mhtml = file.read()

# decoded_content = quopri.decodestring(mhtml).decode('utf-8')

# soup = BeautifulSoup(decoded_content, 'html.parser')
# table = soup.find('table', class_="panel-body table table-hover")

# headers = [th.text.strip() for th in table.find_all('th')]

# data = []
# rows = table.find_all('tr')
# for row in rows[1:]:
#     cols = row.find_all('td')
#     row_data = []
#     for i, col in enumerate(cols):
#         if headers[i] == 'URL interna':
#             link = col.find('a')['href'] if col.find('a') else None
#             row_data.append(link)
#         else:
#             row_data.append(col.text.strip())
#     data.append(row_data)

# df = pd.DataFrame(data, columns=headers)
# df = df[['Id', 'Título', 'Autor', 'SubCategoria', 'Tipo', 'Tipo do conteúdo', 'DC', 'DP', 'URL interna']]

# produced_content = []
# for item in df.to_dict('records'):
#     if item['Autor'] in instructors_name:
#         produced_content.append({
#             "Título do Produto": {"title": [{"text": {"content": item['Título']}}]},
#             "Nome na Plataforma": {"rich_text": [{"text": {"content": item['Título']}}]},
#             "Link": {"url": item['URL interna'].replace('relatorios', 'cursos')},
#             "Código do Produto": {"rich_text": [{"text": {"content": item['Id']}}]},
#             "Instrutor(a)": {"rich_text": [{"text": {"content": item['Autor']}}]},
#             "Produto": {"rich_text": [{"text": {"content": item['Tipo do conteúdo']}}]}
#         })

# notion = NotionAPI()
# load_dotenv()
# database_users = os.getenv('DATABASE_USERS')
# user_pages = notion.retrieve_database(database_users)

# all_responses = []
# for instructor in zip(instructors, instructors_name):
#     for user_page in user_pages:
#         if instructor[0] == user_page['properties']['Nome']['rich_text'][0]['text']['content']:
#             results = notion.retrieve_block_children(user_page['id'])
#             for result in results:
#                 if result['child_page']['title'] == 'Conteúdos Produzidos':
#                     for item in produced_content:
#                         if item['Instrutor(a)']['rich_text'][0]['text']['content'] == instructor[1]:
#                             response = notion.create_page({
#                                 "parent": {"type": "database_id", "database_id": notion.retrieve_block_children(result['id'])[0]['id']},
#                                 "icon": {"type": "external", "external": {"url": icons(item['Produto']['rich_text'][0]['text']['content'])}},
#                                 "properties": item
#                             })
#                             all_responses.append(response)

#                     # response = notion.update_database(notion.retrieve_block_children(result['id'])[0]['id'], json_data)
# print(json.dumps(response[0], indent=4, sort_keys=True, ensure_ascii=False))
# print(50*'=')
# # --------------------------------------------------------------------------------------
# # --------------------------------------------------------------------------------------
# # Criando uma timeline para avaliação do fluxo de trabalho em determinado período
# # --------------------------------------------------------------------------------------
# from google_calendar.calendar_api import GoogleCalendarAPI
# from google_calendar.utils import create_timeline
# import json

# calendar_api = GoogleCalendarAPI()
# agendas = calendar_api.get_updated_events()
# # print(json.dumps(agendas, indent=4, sort_keys=True, ensure_ascii=False))
# # create_timeline(agendas, "Organização do Planejamento 3 Tri 2024", '2024-05-01')
# create_timeline(agendas, "Organização do Planejamento 3 Tri 2024")

# # --------------------------------------------------------------------------------------
# # --------------------------------------------------------------------------------------
# # Atualiza as páginas de tarefas dos instrutores com a avaliação de competências dos DA's
# # --------------------------------------------------------------------------------------
# from notion.notion_api import NotionAPI
# from gods_eye.utils import icons
# from dotenv import load_dotenv
# import os

# notion = NotionAPI()
# load_dotenv()
# database_id = os.getenv('DATABASE_TASKS')
# database = notion.retrieve_database(database_id)

# print(">>> Adiconando as colunas de avaliação de competências dos DA's nas tarefas dos instrutores...")
# json_data = {
#     "properties": {
#         "Nome do Responsável DA": {"rich_text": {}},
#         "Dedicação DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. Demonstra interesse mínimo em suas responsabilidades como instrutor.", "color": "red"},
#                     {"name": "2. Mostra interesse em suas responsabilidades e realiza suas tarefas de forma consistente.", "color": "orange"},
#                     {"name": "3. Mostra um alto nível de comprometimento e dedicação em suas responsabilidades.", "color": "yellow"},
#                     {"name": "4. Demonstra um comprometimento excepcional e paixão por suas responsabilidades como instrutor.", "color": "green"},
#                 ]
#             }
#         },
#         "Cumprimento de acordos DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. Frequentemente não cumpre prazos ou compromissos estabelecidos.", "color": "red"},
#                     {"name": "2. Geralmente cumpre prazos e compromissos estabelecidos.", "color": "orange"},
#                     {"name": "3. Sempre cumpre prazos e compromissos estabelecidos de maneira confiável.", "color": "yellow"},
#                     {"name": "4. É extremamente confiável e sempre cumpre prazos e compromissos.", "color": "green"},
#                 ]
#             }
#         },
#         "Qualidade das entregas DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. As entregas têm muitos erros e não atendem aos padrões mínimos de qualidade.", "color": "red"},
#                     {"name": "2. As entregas são satisfatórias embora possam ocasionalmente conter erros menores.", "color": "orange"},
#                     {"name": "3. As entregas são sempre de alta qualidade atendendo ou excedendo os padrões estabelecidos.", "color": "yellow"},
#                     {"name": "4. As entregas são de nível superior refletindo um alto padrão de excelência e inovação.", "color": "green"},
#                 ]
#             }
#         },
#         "Velocidade DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. Realiza tarefas de forma lenta e com pouca eficiência.", "color": "red"},
#                     {"name": "2. Realiza tarefas em um ritmo razoável e dentro dos prazos definidos.", "color": "orange"},
#                     {"name": "3. Realiza tarefas de forma rápida e eficiente sem comprometer a qualidade.", "color": "yellow"},
#                     {"name": "4. Realiza tarefas de forma extremamente rápida mantendo altos padrões de qualidade.", "color": "green"},
#                 ]
#             }
#         },
#         "Resposta aos feedbacks DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. Tem dificuldade em aceitar feedbacks e pouco esforço é feito para melhorar.", "color": "red"},
#                     {"name": "2. Aceita feedbacks de forma construtiva e faz esforços para melhorar.", "color": "orange"},
#                     {"name": "3. Aceita e implementa feedbacks de forma proativa buscando constantemente melhorar seu desempenho.", "color": "yellow"},
#                     {"name": "4. Valoriza e integra feedbacks de forma excepcional mostrando desejo contínuo por desenvolvimento.", "color": "green"},
#                 ]
#             }
#         },
#         "Flexibilidade DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. Resiste a mudanças e tem dificuldade em se adaptar a novas situações.", "color": "red"},
#                     {"name": "2. É capaz de se adaptar a mudanças e novas situações com alguma orientação.", "color": "orange"},
#                     {"name": "3. Adapta-se facilmente a mudanças e é capaz de lidar com diversas situações sem dificuldade.", "color": "yellow"},
#                     {"name": "4. Mostrou habilidade excepcional em se adaptar a qualquer situação e liderar mudanças efetivamente.", "color": "green"},
#                 ]
#             }
#         },
#         "Colaboração DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. Tende a trabalhar de forma isolada e não contribui para o trabalho em equipe.", "color": "red"},
#                     {"name": "2. Trabalha bem em equipe e contribui para objetivos compartilhados.", "color": "orange"},
#                     {"name": "3. Colabora efetivamente com colegas e lidera iniciativas de equipe quando necessário.", "color": "yellow"},
#                     {"name": "4. É um líder colaborativo capaz de inspirar e motivar colegas para alcançar objetivos comuns.", "color": "green"},
#                 ]
#             }
#         },
#         "Comunicação DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. Comunicação é confusa e não eficaz.", "color": "red"},
#                     {"name": "2. Comunica de forma clara e eficaz na maioria das situações.", "color": "orange"},
#                     {"name": "3. Comunica de forma clara e concisa em uma variedade de contextos.", "color": "yellow"},
#                     {"name": "4. Comunica de forma envolvente e persuasiva inspirando e influenciando os outros.", "color": "green"},
#                 ]
#             }
#         },
#         "Assiduidade DA": {
#             "select": {
#                 "options": [
#                     {"name": "1. Ausências frequentes e falta de comprometimento com os horários.", "color": "red"},
#                     {"name": "2. Comparece regularmente e cumpre os horários de trabalho.", "color": "orange"},
#                     {"name": "3. É altamente confiável em relação à presença e pontualidade.", "color": "yellow"},
#                     {"name": "4. É um exemplo de pontualidade e presença consistente.", "color": "green"},
#                 ]
#             }
#         }
#     }
# }
# notion.update_database(database_id, json_data)