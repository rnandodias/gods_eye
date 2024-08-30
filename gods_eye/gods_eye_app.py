from notion.notion_api import NotionAPI
from google_calendar.calendar_api import GoogleCalendarAPI
from mongodb.mongodb import MongoDBManager
from discord.discord_api import DiscordBotSendUserMessage
from google_forms.forms_api import GoogleFormsAPI
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime, date, timedelta
import os
from gods_eye import utils

import json
import pandas as pd
from collections import Counter

class GodsEye:
    # --------------------------------------------------------------------------------------
    def __init__(self):
        load_dotenv()
        self.database_tasks = os.getenv('DATABASE_TASKS')
        self.database_users = os.getenv('DATABASE_USERS')
        self.page_results = os.getenv('PAGE_RESULTS')
        self.mapping_instructos = json.loads(os.getenv('MAPPING_INSTRUCTORS'))
        self.instructos_id_discord = json.loads(os.getenv('INSTRUCTOR_ID_DISCORD'))
        self.notion_users = json.loads(os.getenv('NOTION_USERS_ID'))
        self.mapping_instructos_inverted = {value: key for key, value in self.mapping_instructos.items()}
        self.calendar = GoogleCalendarAPI()
        self.notion = NotionAPI()
        self.mongo_manager = MongoDBManager()
        self.forms = GoogleFormsAPI()

    # TTTTTTTTTTTTTTT   AAAAAAAAA      SSSSSSSSSSS   KKK     KKKK  SSSSSSSSSSS
    # TTTTTTTTTTTTTTT  AAAAAAAAAAA    SSSSSSSSSSSSS  KKK    KKKK  SSSSSSSSSSSSS
    #      TTTT       AAAAA   AAAAA  SSSS       SSSS KKK   KKKK  SSSS       SSSS
    #      TTTT      AAAAA     AAAAA SSSS            KKK  KKKK   SSSS
    #      TTTT      AAAAAAAAAAAAAAA  SSSSSSSSSSSSS  KKKKKKK      SSSSSSSSSSSSS
    #      TTTT      AAAAAAAAAAAAAAA   SSSSSSSSSSSSS KKKKKKK       SSSSSSSSSSSSS
    #      TTTT      AAAAA     AAAAA            SSSS KKK  KKKK              SSSS
    #      TTTT      AAAAA     AAAAA SSSS       SSSS KKK   KKKK  SSSS       SSSS
    #      TTTT      AAAAA     AAAAA  SSSSSSSSSSSSS  KKK    KKKK  SSSSSSSSSSSSS
    #      TTTT      AAAAA     AAAAA   SSSSSSSSSSS   KKK     KKKK  SSSSSSSSSSS
    # --------------------------------------------------------------------------------------
    # Realiza o backup do database de tarefas e de seus comentários
    # --------------------------------------------------------------------------------------
    def backup_tasks_database(self):
        database = self.notion.retrieve_database(self.database_tasks)
        comments = []
        for page in tqdm(database):
            comments.append(self.notion.retrieve_comment(page['id']))
        document = {
            "last_update": datetime.now(),
            "type": "task",
            "database": database,
            "comments": comments
        }
        try:
            response = self.mongo_manager.insert_one("tasks_database", document)
            return response.inserted_id
        except Exception as e:
            print(f"Erro ao realizar o backup: {e}")

    # --------------------------------------------------------------------------------------
    # Realiza a recuparação do último backup do database de tarefas e de seus comentários
    # [EM CONSTRUÇÃO]
    # --------------------------------------------------------------------------------------
    def restore_tasks_database(self):
        document = self.mongo_manager.find_most_recent("tasks_database")
        if document:
            print(document)
        else:
            print("Nenhum documento encontrado.")        

    # --------------------------------------------------------------------------------------
    # Atualiza o database de tarefas com os eventos das agendas dos instrutores
    # --------------------------------------------------------------------------------------
    def update_tasks_database(self, backup=False):
        if backup == True:
            print('>>> Realizando backup do database de tarefas e comentários...')
            self.backup_tasks_database()

        print('>>> Carregando as agendas atualizadas...')
        events = self.calendar.get_updated_events()

        print('>>> Obtendo os IDs das páginas do database no Notion...')
        database = self.notion.retrieve_database(self.database_tasks)

        print('>>> Removendo tarefas do Notion que foram excluídas do Calendar...')
        notion_ids = [{"Page_id": page['id'], "Id": page['properties']['Id']['rich_text'][0]['text']['content']} for page in database if page['archived'] == False]
        events_ids = [event["id"] for event in events]
        for notion_id in notion_ids:
            if notion_id['Id'] not in events_ids:
                self.notion.delete_page(notion_id['Page_id'])

        print('>>> Atualizando/adicionando as tarefas no database...')
        all_responses = []
        deadlines = utils.get_deadline(database)
        for item in tqdm(events):
            # datetime.strptime(item['Start'], '%Y-%m-%d')
            # datetime.strptime(item['End'], '%Y-%m-%d')
            # datetime.strptime(item['Start Original'], '%Y-%m-%d')
            # datetime.strptime(item['End Original'], '%Y-%m-%d')
            data_input = utils.data_input(self.database_tasks, deadlines, item)
            patch = False
            for notion_id in notion_ids:
                if notion_id['Id'] == item['id']:
                    response = self.notion.update_page(notion_id['Page_id'], data_input)
                    patch = True
                    all_responses.append(response)
                    break
            if patch == False:
                response = self.notion.create_page(data_input)
                all_responses.append(response)

        return all_responses

    # UUUUU       UUUU   SSSSSSSSSSS   EEEEEEEEEEEEE  RRRRRRRRRRR      SSSSSSSSSSS  
    # UUUUU       UUUU  SSSSSSSSSSSSS  EEEEEEEEEEEEE  RRRRRRRRRRRR    SSSSSSSSSSSSS 
    # UUUUU       UUUU SSSS       SSSS EEEE           RRRR    RRRRR  SSSS       SSSS
    # UUUUU       UUUU SSSS            EEEE           RRRR    RRRRR  SSSS           
    # UUUUU       UUUU  SSSSSSSSSSSSS  EEEEEEEEEEE    RRRRRRRRRRRR    SSSSSSSSSSSSS 
    # UUUUU       UUUU   SSSSSSSSSSSSS EEEEEEEEEEE    RRRRRRRRRR       SSSSSSSSSSSSS
    # UUUUU       UUUU            SSSS EEEE           RRRR   RRRR               SSSS
    # UUUUU       UUUU SSSS       SSSS EEEE           RRRR    RRRR   SSSS       SSSS
    #  UUUUUUUUUUUUUU   SSSSSSSSSSSSS  EEEEEEEEEEEEE  RRRR     RRRR   SSSSSSSSSSSSS 
    #   UUUUUUUUUUU      SSSSSSSSSSS   EEEEEEEEEEEEE  RRRR      RRRR   SSSSSSSSSSS  
    # --------------------------------------------------------------------------------------
    # Envia mensagens com alertas sobre os conteúdos em desenvolvimento
    # --------------------------------------------------------------------------------------
    def send_task_reminder(self, instructors):
        today = date.today()
        greeting = utils.greeting(datetime.now().hour)

        print('>>> Obtendo as informações do database de tarefas...')
        database = self.notion.retrieve_database(self.database_tasks)

        print('>>> Verificando as tarefas por instrutor(a)...')
        for instructor in instructors:
            print(f'>>>>>> {instructor}')
            send = False
            pages = []
            message_header = f"""
# **{greeting}, {instructor}!**

Segue um resumo das suas atividades.
"""
            message_body = ""
            for page in database:
                if instructor == page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']:
                    pages.append(page)
                    start = page['properties']['Período Realizado']['date']['start']
                    end = page['properties']['Período Realizado']['date']['end']
                    message_input = f"""
> ## :white_check_mark: __{page['properties']['Produto']['rich_text'][0]['text']['content']}__
> **Título do Conteúdo**: {page['properties']['Título do Produto']['rich_text'][0]['text']['content']} 
> **Atividade**: {page['properties']['Atividade']['rich_text'][0]['text']['content']}"""
                    
                    if datetime.strptime(end, "%Y-%m-%d").date() == today:
                        send = True
                        message_body += f"""{message_input}
```diff
- TEM PRAZO DE ENTREGA PARA HOJE.
```"""
                    if datetime.strptime(end, "%Y-%m-%d").date() == today + timedelta(days=1):
                        send = True
                        message_body += f"""{message_input}
```diff
+ TEM PRAZO DE ENTREGA PARA AMANHÃ.
```"""
                    if datetime.strptime(start, "%Y-%m-%d").date() < today <= datetime.strptime(end, "%Y-%m-%d").date() - timedelta(days=2):
                        message_body += f"""{message_input}
> **Prazo de Entrega**: {datetime.strptime(end, "%Y-%m-%d").strftime("%d-%m-%Y")}
```diff
+ PRODUÇÃO EM ANDAMENTO...
```"""
                    if datetime.strptime(start, "%Y-%m-%d").date() == today:
                        send = True
                        if datetime.strptime(start, "%Y-%m-%d").date() != datetime.strptime(end, "%Y-%m-%d").date():
                            message_body += f"""{message_input}
> **Prazo de Entrega**: {datetime.strptime(end, "%Y-%m-%d").strftime("%d-%m-%Y")}
```diff
+ A PRODUÇÃO COMEÇA HOJE.
```"""
                    
                    if datetime.strptime(start, "%Y-%m-%d").date() == today + timedelta(days=1):
                        send = True
                        message_body += f"""{message_input}
```diff
+ A PRODUÇÃO COMEÇA AMANHÃ.
```"""
            if message_body == "":
                send = True
                message_body += f"""
```diff
- NENHUMA ATIVIDADE ENCONTRADA. VERIFIQUE SUA AGENDA.
```"""
            message = message_header + message_body + """
Caso as informações não estejam corretas, verifique e atualize sua agenda.

Bom trabalho e um excelente dia. :people_hugging:"""
            if send:
                # DiscordBotSendUserMessage(self.instructos_id_discord["Rodrigo"], message).run()
                DiscordBotSendUserMessage(self.instructos_id_discord[instructor], message).run()
            else:
                print(f"Nenhuma mensagem para {instructor}")

        return None
        
    # --------------------------------------------------------------------------------------
    # Envia mensagens de feedback semanais
    # --------------------------------------------------------------------------------------
    def send_weekly_feedback(self, instructors, start="2024-07-01", end="2024-08-23"):
        greeting = utils.greeting(datetime.now().hour)

        print('>>> Obtendo as informações do database de tarefas...')
        database = self.notion.retrieve_database(self.database_tasks)

        print('>>> Verificando as tarefas por instrutor(a)...')
        for instructor in instructors:
            print(f'>>>>>> {instructor}')
            message_header = f"""
# **{greeting}, {instructor}!**

Seguem os feedbacks de suas atividades no período de **{datetime.strptime(start, "%Y-%m-%d").strftime("%d/%m/%Y")}** até **{datetime.strptime(end, "%Y-%m-%d").strftime("%d/%m/%Y")}**.

> **__Instruções:__** Faça o download do arquivo, abra-o no **VSCode**, posicione o cursor em qualquer parte do texto e pressione **Ctrl+Shift+V** para visualizar o texto formatado.\n
"""
            message_feedback = ""
            for page in database:
                start_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["start"], "%Y-%m-%d")
                end_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["end"], "%Y-%m-%d")
                if (datetime.strptime(start, "%Y-%m-%d") <= start_page <= datetime.strptime(end, "%Y-%m-%d")) or (datetime.strptime(start, "%Y-%m-%d") <= end_page <= datetime.strptime(end, "%Y-%m-%d")):
                    if instructor == page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']:
                        comments = self.notion.retrieve_comment(page['id'])
                        message_comment = ""
                        if len(comments) > 0:
                            message_input = f"""
## __{page['properties']['Produto']['rich_text'][0]['text']['content']} - {page['properties']['Título do Produto']['rich_text'][0]['text']['content']}__\n
**Atividade**: {page['properties']['Atividade']['rich_text'][0]['text']['content']}\n
**DA Responsável**: {'-' if page['properties']['DA Responsável']['select'] == None else page['properties']['DA Responsável']['select']['name']}\n
"""
                            for comment in comments:
                                if comment['created_by']['id'] == self.notion_users['Rodrigo']:
                                    message_comment += "> Anotação técnica:\n\n"
                                else:
                                    message_comment += "> Anotação didática:\n\n"

                                message_comment += comment['rich_text'][0]['text']['content'] + "\n\n"

                            message_feedback += f"""{message_input}
{message_comment}
"""
                    
            message_footer = f"""
{instructor}, reserve um tempo para revisar os feedbacks e identificar possíveis pontos de ajuste. Vamos conversar sobre isso na nossa próxima reunião de 1:1.

Bom trabalho e um excelente dia. :people_hugging:"""
            
            if message_feedback:
                file_name = f'{instructor}.feedbacks.de.{datetime.strptime(start, "%Y-%m-%d").strftime("%d-%m-%Y")}.até.{datetime.strptime(end, "%Y-%m-%d").strftime("%d-%m-%Y")}'
                file_path = utils.create_feedback_file(file_name, message_feedback)
                DiscordBotSendUserMessage(self.instructos_id_discord["Rodrigo"], message_header, file_path).run()
                DiscordBotSendUserMessage(self.instructos_id_discord["Rodrigo"], message_footer).run()
                # DiscordBotSendUserMessage(self.instructos_id_discord["David"], message_header, file_path).run()
                # DiscordBotSendUserMessage(self.instructos_id_discord["David"], message_footer).run()
                # DiscordBotSendUserMessage(self.instructos_id_discord[instructor], message_header, file_path).run()
                # DiscordBotSendUserMessage(self.instructos_id_discord[instructor], message_footer).run()
            else:
                print(f"Nenhuma mensagem de feedback para {instructor}")

        return None
    
    # --------------------------------------------------------------------------------------
    # Cria o relatório de avaliação de desempenho trimestral dos instrutores
    # --------------------------------------------------------------------------------------
    def create_quarterly_report(self, instructors, start="2024-01-01", end="2024-03-31", page_title="1º Trimestre 2024"):
        print('>>> Obtendo os IDs das páginas do database no Notion...')
        database = self.notion.retrieve_database(self.database_tasks)

        print('>>> Aplicando filtro de período...')
        pages = []
        start = datetime.strptime(start, "%Y-%m-%d")
        end = datetime.strptime(end, "%Y-%m-%d")
        for page in database:
            start_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["start"], "%Y-%m-%d")
            end_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["end"], "%Y-%m-%d")
            if (start <= start_page <= end) or (start <= end_page <= end):
                instructor = page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']
                if instructor in instructors:
                    pages.append({
                        'id': page['id'],
                        'Instrutor(a)': page['properties']['Instrutor(a)']['rich_text'][0]['text']['content'],
                        'Tarefa': page['properties']['Tarefa']['title'][0]['text']['content']
                    })

        print('>>> Obtendo os comentários em cada página do database...')
        for page in tqdm(pages):
            comments = self.notion.retrieve_comment(page['id'])
            temp = []
            for comment in comments:
                for item in comment["rich_text"]:
                    temp.append(item["text"]["content"])
            page.update({'Comentários': temp})

        print('>>> Criando uma nova página de Review na página de avaliação de desempenho dos instrutores...')
        all_users = self.notion.retrieve_database(self.database_users)
        filtered_users = []
        for user in all_users:
            instructor = user['properties']['Nome']['rich_text'][0]['text']['content']
            if instructor in instructors:
                filtered_users.append(user)

        print('>>> Criando as avaliações de desempenho de cada instrutor...')
        for user in tqdm(filtered_users):
            input_gpt = []
            id = ''
            for page in pages:
                if user['properties']['Nome']['rich_text'][0]['text']['content'] == page['Instrutor(a)']:
                    blocks = self.notion.retrieve_block_children(user['id'])
                    for block in blocks:
                        if block['type'] == 'child_page':
                            if block['child_page']['title'] == 'Avalia\u00e7\u00f5es de Desempenho':
                                id = block['id']
                                for item in page['Comentários']:
                                    input_gpt.append({page['Tarefa']: item})
            if len(input_gpt) > 0:
                # split_text = list(divide_texto_em_blocos(json.dumps(input_gpt, indent=4, sort_keys=True, ensure_ascii=False)))
                # split_text = list(divide_texto_em_blocos(output_teste))
                input_gpt = utils.organizes_feedback(input_gpt)
                # Uso do GPT
                split_text = list(utils.split_text_into_blocks(input_gpt))
                # split_text = list(utils.split_text_into_blocks(utils.report(utils.prompt_create_report(input_gpt))))
                text_block = utils.create_text_blocks(split_text)
                children = [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {"rich_text": [{"type": "text", "text": {"content": f"Avaliação de Desempenho - {user['properties']['Nome']['rich_text'][0]['text']['content']}"}}]}
                    }
                ]
                children.extend(text_block)
                data = {
                    "children": children
                }
            data_json = {
                "parent": {"type": "page_id", "page_id": f"{id}"},
                "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/avd/AvDs.jpg"}},
                "icon": {"type": "external", "external": {"url": "https://www.notion.so/icons/chart-line_green.svg"}},
                "properties": {"title": {"title": [{"text": {"content": page_title}}]}}
            }
            _, page_content = self.notion.create_page(data_json)
            teste = self.notion.append_block_children(page_content['id'], data)

    # --------------------------------------------------------------------------------------
    # Cria o relatório de resultados trimestrais dos instrutores
    # --------------------------------------------------------------------------------------
    def create_quarterly_results_report(self, instructors, start="2024-01-01", end="2024-03-31", page_title="1º Trimestre 2024"):
        print('>>> Criando a página para os resultados trimestrais...')
        data_json = {
            "parent": {"type": "page_id", "page_id": self.page_results},
            "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/resultados/Resultados_capa_01.jpg"}},
            "icon": {"type": "external", "external": {"url": "https://www.notion.so/icons/activity_green.svg"}},
            "properties": {"title": {"title": [{"text": {"content": page_title}}]}}
        }
        _, page_content = self.notion.create_page(data_json)

        skills = ["Dedicação", "Cumprimento de acordos", "Qualidade das entregas", "Velocidade", "Resposta aos feedbacks", "Flexibilidade", "Colaboração", "Comunicação", "Assiduidade"]

        print('>>> Obtendo as informações do database de tarefas...')
        database = self.notion.retrieve_database(self.database_tasks)

        print('>>> Aplicando filtro de período...')
        results_skills = []
        for instructor in instructors:
            pages = []
            for page in database:
                start_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["start"], "%Y-%m-%d")
                end_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["end"], "%Y-%m-%d")
                if (datetime.strptime(start, "%Y-%m-%d") <= start_page <= datetime.strptime(end, "%Y-%m-%d")) or (datetime.strptime(start, "%Y-%m-%d") <= end_page <= datetime.strptime(end, "%Y-%m-%d")):
                    if instructor == page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']:
                        use_register = True
                        for skill in skills:
                            if page['properties'][skill]['select'] == None:
                                use_register = False

                        if use_register:
                            pages.append({
                                "Tarefa": {"title": [{"text": {"content": page['properties']['Tarefa']['title'][0]['text']['content']}}]},
                                "Id": {"rich_text": [{"text": {"content": page['properties']['Id']['rich_text'][0]['text']['content']}}]},
                                "Dedicação": {"select": page['properties']['Dedicação']['select'] if page['properties']['Dedicação']['select'] == None else {'name': page['properties']['Dedicação']['select']['name']}},
                                "Cumprimento de acordos": {"select": page['properties']['Cumprimento de acordos']['select'] if page['properties']['Cumprimento de acordos']['select'] == None else {'name': page['properties']['Cumprimento de acordos']['select']['name']}},
                                "Qualidade das entregas": {"select": page['properties']['Qualidade das entregas']['select'] if page['properties']['Qualidade das entregas']['select'] == None else {'name': page['properties']['Qualidade das entregas']['select']['name']}},
                                "Velocidade": {"select": page['properties']['Velocidade']['select'] if page['properties']['Velocidade']['select'] == None else {'name': page['properties']['Velocidade']['select']['name']}},
                                "Resposta aos feedbacks": {"select": page['properties']['Resposta aos feedbacks']['select'] if page['properties']['Resposta aos feedbacks']['select'] == None else {'name': page['properties']['Resposta aos feedbacks']['select']['name']}},
                                "Flexibilidade": {"select": page['properties']['Flexibilidade']['select'] if page['properties']['Flexibilidade']['select'] == None else {'name': page['properties']['Flexibilidade']['select']['name']}},
                                "Colaboração": {"select": page['properties']['Colaboração']['select'] if page['properties']['Colaboração']['select'] == None else {'name': page['properties']['Colaboração']['select']['name']}},
                                "Comunicação": {"select": page['properties']['Comunicação']['select'] if page['properties']['Comunicação']['select'] == None else {'name': page['properties']['Comunicação']['select']['name']}},
                                "Assiduidade": {"select": page['properties']['Assiduidade']['select'] if page['properties']['Assiduidade']['select'] == None else {'name': page['properties']['Assiduidade']['select']['name']}},
                            })

            print(f'>>> Obtendo estatísticas para o(a) instrutor(a) {instructor}...')
            dict_skills = {}
            for page in pages:
                for skill in skills:
                    dict_skills.update({skill: []})

            for page in pages:
                for skill in skills:
                    dict_skills[skill].append(page[skill]['select']['name'])

            dict_aux = {
                "Instrutor(a)": {"title": [{"text": {"content": instructor}}]},
                # "Id": {"rich_text": [{"text": {"content": instructor}}]},
            }
            for key, value in dict_skills.items():
                counter = Counter(value)
                max_freq = max(counter.values())
                modes = [item for item, freq in counter.items() if freq == max_freq]
                if len(modes) > 1:
                    numeros = [int(item.split('.')[0]) for item in modes]
                    menor_numero = min(numeros)
                    mode = next(item for item in modes if item.startswith(f"{menor_numero}."))
                else:
                    mode = modes[0]
                # mode = counter.most_common(1)[0][0]
                # print(counter.most_common(1))
                dict_aux.update({key: {"select": {'name': mode}}})

            results_skills.append(dict_aux)

        print(f'>>> Obtendo estatísticas para a Escola de Dados...')
        dict_skills = {}
        for page in results_skills:
            for skill in skills:
                dict_skills.update({skill: []})

        for page in results_skills:
            for skill in skills:
                dict_skills[skill].append(page[skill]['select']['name'])

        dict_aux = {
            "Instrutor(a)": {"title": [{"text": {"content": "Escola de Dados"}}]},
            # "Id": {"rich_text": [{"text": {"content": instructor}}]},
        }
        for key, value in dict_skills.items():
            counter = Counter(value)
            max_freq = max(counter.values())
            modes = [item for item, freq in counter.items() if freq == max_freq]
            if len(modes) > 1:
                numeros = [int(item.split('.')[0]) for item in modes]
                menor_numero = min(numeros)
                mode = next(item for item in modes if item.startswith(f"{menor_numero}."))
            else:
                mode = modes[0]
            # mode = counter.most_common(1)[0][0]
            # print(counter.most_common(1))
            dict_aux.update({key: {"select": {'name': mode}}})

        results_skills.append(dict_aux)

        response_create_database = self.notion.create_database(utils.data_results_competency_assessment_create(page_content['id']))
        all_responses_step_A = []
        for result_skills in reversed(results_skills):
            instructor = result_skills["Instrutor(a)"]["title"][0]["text"]["content"]
            
            if instructor == "Escola de Dados":
                data_json = {
                    "parent": {"type": "database_id", "database_id": response_create_database[1]['id']},
                    "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/resultados/escola_de_dados/Escola_de_dados_01.jpg"}},
                    "icon": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/resultados/escola_de_dados/icon.png"}},
                    "properties": result_skills
                }
            else:
                data_json = {
                    "parent": {"type": "database_id", "database_id": response_create_database[1]['id']},
                    "cover": {"type": "external", "external": {"url": f"https://storage.googleapis.com/alura-images/instrutores/{self.mapping_instructos_inverted[instructor].replace(' ', '%20')}.png"}},
                    "icon": {"type": "external", "external": {"url": f"https://storage.googleapis.com/alura-images/instrutores/{self.mapping_instructos_inverted[instructor].replace(' ', '%20')}.png"}},
                    "properties": result_skills
                }

            response = self.notion.create_page(data_json)
            all_responses_step_A.append(response)

        response_create_database = self.notion.create_database(utils.data_statistics_planning_create(page_content['id']))
        all_responses_step_B = []
        table_step_B = self.statistics(instructors, start=start, end=end)
        for result_skills in reversed(table_step_B):
            instructor = result_skills["Instrutor(a)"]["title"][0]["text"]["content"]
            data_json = {
                "parent": {"type": "database_id", "database_id": response_create_database[1]['id']},
                "cover": {"type": "external", "external": {"url": f"https://storage.googleapis.com/alura-images/instrutores/{self.mapping_instructos_inverted[instructor].replace(' ', '%20')}.png"}},
                "icon": {"type": "external", "external": {"url": f"https://storage.googleapis.com/alura-images/instrutores/{self.mapping_instructos_inverted[instructor].replace(' ', '%20')}.png"}},
                "properties": result_skills
            }

            response = self.notion.create_page(data_json)
            all_responses_step_B.append(response)

        

        return all_responses_step_A, all_responses_step_B
    
    # --------------------------------------------------------------------------------------
    # Atualiza a página de avaliação de competências dos instrutores
    # --------------------------------------------------------------------------------------
    def update_competency_assessment(self, instructors, page_title, start="2024-01-01", end="2024-03-31"):
        skills = ["Dedicação", "Cumprimento de acordos", "Qualidade das entregas", "Velocidade", "Resposta aos feedbacks", "Flexibilidade", "Colaboração", "Comunicação", "Assiduidade"]

        print('>>> Obtendo as informações do database de tarefas...')
        database = self.notion.retrieve_database(self.database_tasks)

        print('>>> Aplicando filtro de período...')
        for instructor in instructors:
            pages = []
            for page in database:
                start_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["start"], "%Y-%m-%d")
                end_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["end"], "%Y-%m-%d")
                if (datetime.strptime(start, "%Y-%m-%d") <= start_page <= datetime.strptime(end, "%Y-%m-%d")) or (datetime.strptime(start, "%Y-%m-%d") <= end_page <= datetime.strptime(end, "%Y-%m-%d")):
                    if instructor == page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']:
                        use_register = True
                        for skill in skills:
                            if page['properties'][skill]['select'] == None:
                                use_register = False

                        if use_register:
                            pages.append({
                                "Tarefa": {"title": [{"text": {"content": page['properties']['Tarefa']['title'][0]['text']['content']}}]},
                                "Id": {"rich_text": [{"text": {"content": page['properties']['Id']['rich_text'][0]['text']['content']}}]},
                                # "Produto": {"rich_text": [{"text": {"content": page['properties']['Produto']['rich_text'][0]['text']['content']}}]},
                                # "Código do Produto": {"rich_text": [{"text": {"content": page['properties']['Código do Produto']['rich_text'][0]['text']['content']}}]},
                                # "Título do Produto": {"rich_text": [{"text": {"content": page['properties']['Título do Produto']['rich_text'][0]['text']['content']}}]},
                                # "Instrutor(a)": {"rich_text": [{"text": {"content": page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']}}]},
                                # "Atividade": {"rich_text": [{"text": {"content": page['properties']['Atividade']['rich_text'][0]['text']['content']}}]},
                                "Dedicação": {"select": page['properties']['Dedicação']['select'] if page['properties']['Dedicação']['select'] == None else {'name': page['properties']['Dedicação']['select']['name']}},
                                "Cumprimento de acordos": {"select": page['properties']['Cumprimento de acordos']['select'] if page['properties']['Cumprimento de acordos']['select'] == None else {'name': page['properties']['Cumprimento de acordos']['select']['name']}},
                                "Qualidade das entregas": {"select": page['properties']['Qualidade das entregas']['select'] if page['properties']['Qualidade das entregas']['select'] == None else {'name': page['properties']['Qualidade das entregas']['select']['name']}},
                                "Velocidade": {"select": page['properties']['Velocidade']['select'] if page['properties']['Velocidade']['select'] == None else {'name': page['properties']['Velocidade']['select']['name']}},
                                "Resposta aos feedbacks": {"select": page['properties']['Resposta aos feedbacks']['select'] if page['properties']['Resposta aos feedbacks']['select'] == None else {'name': page['properties']['Resposta aos feedbacks']['select']['name']}},
                                "Flexibilidade": {"select": page['properties']['Flexibilidade']['select'] if page['properties']['Flexibilidade']['select'] == None else {'name': page['properties']['Flexibilidade']['select']['name']}},
                                "Colaboração": {"select": page['properties']['Colaboração']['select'] if page['properties']['Colaboração']['select'] == None else {'name': page['properties']['Colaboração']['select']['name']}},
                                "Comunicação": {"select": page['properties']['Comunicação']['select'] if page['properties']['Comunicação']['select'] == None else {'name': page['properties']['Comunicação']['select']['name']}},
                                "Assiduidade": {"select": page['properties']['Assiduidade']['select'] if page['properties']['Assiduidade']['select'] == None else {'name': page['properties']['Assiduidade']['select']['name']}},
                            })

            print('>>> Obtendo estatísticas...')
            dict_skills = {}
            for page in pages:
                for skill in skills:
                    dict_skills.update({skill: []})

            for page in pages:
                for skill in skills:
                    dict_skills[skill].append(page[skill]['select']['name'])

            dict_aux = {
                "Tarefa": {"title": [{"text": {"content": "Avaliação final"}}]},
                "Id": {"rich_text": [{"text": {"content": "Avaliação final"}}]},
            }
            for key, value in dict_skills.items():
                counter = Counter(value)
                max_freq = max(counter.values())
                modes = [item for item, freq in counter.items() if freq == max_freq]
                if len(modes) > 1:
                    numeros = [int(item.split('.')[0]) for item in modes]
                    menor_numero = min(numeros)
                    mode = next(item for item in modes if item.startswith(f"{menor_numero}."))
                else:
                    mode = modes[0]
                dict_aux.update({key: {"select": {'name': mode}}})

            pages.append(dict_aux)

            print('>>> Obtendo os IDs das páginas de acompanhamento dos instrutores...')
            user_pages = self.notion.retrieve_database(self.database_users)
            for user_page in user_pages:
                if instructor == user_page['properties']['Nome']['rich_text'][0]['text']['content']:
                    print(f">>> Iniciando o carregamento da página de acompanhamento de produção do(a) instrutor(a) {instructor}")
                    response = self.notion.find_page_title(user_page['id'], "Avaliação de Competências")
                    child_page_id = ""
                    if not response[0]:
                        data_json = {
                            "parent": {"type": "page_id", "page_id": f"{user_page['id']}"},
                            "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/instrutores/avaliacao_de_competencias/Avalia%C3%A7%C3%A3o_de_compet%C3%AAncias_03.jpg"}},
                            "icon": {"type": "external", "external": {"url": "https://www.notion.so/icons/brain_green.svg"}},
                            "properties": {"title": {"title": [{"text": {"content": "Avaliação de Competências"}}]}}
                        }
                        parent_page = self.notion.create_page(data_json)
                        data_json_child = {
                            "parent": {"type": "page_id", "page_id": f"{parent_page[1]['id']}"},
                            "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/instrutores/avaliacao_de_competencias/Avalia%C3%A7%C3%A3o_de_compet%C3%AAncias_03.jpg"}},
                            "icon": {"type": "external", "external": {"url": "https://www.notion.so/icons/brain_green.svg"}},
                            "properties": {"title": {"title": [{"text": {"content": page_title}}]}}
                        }
                        child_page = self.notion.create_page(data_json_child)
                        child_page_id = child_page[1]['id']
                        response_create_database = self.notion.create_database(utils.data_competency_assessment_create(child_page_id))
                        all_responses = []
                        for page in pages:
                            response = self.notion.create_page({
                                "parent": {"type": "database_id", "database_id": f"{response_create_database[1]['id']}"},
                                "properties": page
                            })
                            all_responses.append(response)

                    else:
                        child_page = self.notion.find_page_title(response[1]['id'], page_title)
                        if not child_page[0]:
                            data_json_child = {
                                "parent": {"type": "page_id", "page_id": f"{response[1]['id']}"},
                                "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/instrutores/avaliacao_de_competencias/Avalia%C3%A7%C3%A3o_de_compet%C3%AAncias_03.jpg"}},
                                "icon": {"type": "external", "external": {"url": "https://www.notion.so/icons/brain_green.svg"}},
                                "properties": {"title": {"title": [{"text": {"content": page_title}}]}}
                            }
                            child_page = self.notion.create_page(data_json_child)
                            child_page_id = child_page[1]['id']
                            response_create_database = self.notion.create_database(utils.data_competency_assessment_create(child_page_id))
                            all_responses = []
                            for page in pages:
                                response = self.notion.create_page({
                                    "parent": {"type": "database_id", "database_id": f"{response_create_database[1]['id']}"},
                                    "properties": page
                                })
                                all_responses.append(response)

                        else:
                            all_responses = []
                            bd_id = self.notion.retrieve_block_children(child_page[1]['id'])[0]['id']
                            database_competency_assessment = self.notion.retrieve_database(bd_id)
                            database_competency_assessment = [item['properties']['Id']['rich_text'][0]['text']['content'] for item in database_competency_assessment]
                            for page in pages:
                                if page['Id']['rich_text'][0]['text']['content'] not in database_competency_assessment:
                                    response = self.notion.create_page({
                                        "parent": {"type": "database_id", "database_id": f"{bd_id}"},
                                        "properties": page
                                    })
                                    all_responses.append(response)

        return all_responses

    # --------------------------------------------------------------------------------------
    # Atualiza a página de conteúdos produzidos por instrutor
    # --------------------------------------------------------------------------------------
    def update_produced_content(self, instructors):
        print('>>> Obtendo as informações do database de tarefas...')
        database = self.notion.retrieve_database(self.database_tasks)
 
        print('>>> Obtendo os IDs das páginas de acompanhamento dos instrutores...')
        user_pages = self.notion.retrieve_database(self.database_users)

        print('>>> Obtendo apenas os conteúdo finalizados...')
        for instructor in instructors:
            pages = []
            products = []
            for user_page in user_pages:
                if instructor == user_page['properties']['Nome']['rich_text'][0]['text']['content']:
                    user_page_id = user_page['id']

            for page in database:
                if instructor == page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']:
                    pages.append(page)
                    products.append(page['properties']['Título do Produto']['rich_text'][0]['text']['content'])
            products = list(set(products))

            for page in pages:
                for product in products:
                    if page['properties']['Título do Produto']['rich_text'][0]['text']['content'] == product:
                        if page['properties']['Status']['select']['name'] != 'Finalizada':
                            products.remove(product)

            produced_content = []
            for product in products:
                periods = []
                time = []
                product_type = ""
                product_code = ""
                for page in pages:
                    if page['properties']['Título do Produto']['rich_text'][0]['text']['content'] == product:
                        periods.append(page['properties']['Período Realizado']['date']['start'])
                        periods.append(page['properties']['Período Realizado']['date']['end'])
                        time.append(page['properties']['Tempo Gasto (em Dias)']['number'])
                        product_type = page['properties']['Produto']['rich_text'][0]['text']['content']
                        product_code = page['properties']['Código do Produto']['rich_text'][0]['text']['content']

                if product_type in ['Curso', 'Artigo', 'Podcast', 'Quinta com Dados', 'TechGuide', 'Alura+', 'Palestra', 'Curso (E)', 'Imersão', 'Artigo Pilar']:
                    produced_content.append({
                        "Produto": {"rich_text": [{"text": {"content": product_type}}]},
                        "Código do Produto": {"rich_text": [{"text": {"content": product_code}}]},
                        "Título do Produto": {"title": [{"text": {"content": product}}]},
                        "Instrutor(a)": {"rich_text": [{"text": {"content": instructor}}]},
                        "Período de Produção": {"date": {"start": list(utils.min_max_dates(periods))[0], "end": list(utils.min_max_dates(periods))[1]}},
                        "Tempo de Produção (em Dias)": {"number": sum(time)},
                        "Link": {"url": None}
                    })

            print(f">>> Iniciando o carregamento da página de conteúdos produzidos do(a) instrutor(a) {instructor}")
            response = self.notion.find_page_title(user_page_id, "Conteúdos Produzidos")
            child_page_id = ""
            if not response[0]:
                data_json = {
                    "parent": {"type": "page_id", "page_id": f"{user_page_id}"},
                    "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/instrutores/conteudos_produzidos/Conte%C3%BAdos_produzidos_02.jpg"}},
                    "icon": {"type": "external", "external": {"url": "https://www.notion.so/icons/science_green.svg"}},
                    "properties": {"title": {"title": [{"text": {"content": "Conteúdos Produzidos"}}]}}
                }
                produced_content_page = self.notion.create_page(data_json)
                response_create_database = self.notion.create_database(utils.data_produced_content_create(produced_content_page[1]['id']))
                all_responses = []
                for item in produced_content:
                    response = self.notion.create_page({
                        "parent": {"type": "database_id", "database_id": f"{response_create_database[1]['id']}"},
                        "icon": {"type": "external", "external": {"url": utils.icons(item['Produto']['rich_text'][0]['text']['content'])}},
                        "properties": item
                    })
                    all_responses.append(response)

            else:
                all_responses = []
                bd_id = self.notion.retrieve_block_children(response[1]['id'])[0]['id']
                database_produced_content = self.notion.retrieve_database(bd_id)
                database_produced_content = [item['properties']['Título do Produto']['title'][0]['text']['content'] for item in database_produced_content]
                for item in produced_content:
                    if item['Título do Produto']['title'][0]['text']['content'] not in database_produced_content:
                        response = self.notion.create_page({
                            "parent": {"type": "database_id", "database_id": f"{bd_id}"},
                            "icon": {"type": "external", "external": {"url": utils.icons(item['Produto']['rich_text'][0]['text']['content'])}},
                            "properties": item
                        })
                        all_responses.append(response)

        return all_responses

    # --------------------------------------------------------------------------------------
    # Cria estatísticas sobre a produção de conteúdo
    # --------------------------------------------------------------------------------------
    def statistics(self, instructors, start="2024-01-01", end="2024-03-31"):
        print('>>> Obtendo as informações do database de tarefas...')
        database = self.notion.retrieve_database(self.database_tasks)

        print('>>> Aplicando filtro de período...')
        pages = []
        start = datetime.strptime(start, "%Y-%m-%d")
        end = datetime.strptime(end, "%Y-%m-%d")
        for page in database:
            start_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["start"], "%Y-%m-%d")
            end_page = datetime.strptime(page["properties"]["Período Realizado"]["date"]["end"], "%Y-%m-%d")
            if (start <= start_page <= end) or (start <= end_page <= end):
                instructor = page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']
                if instructor in instructors:
                    pages.append(page)

        df = pd.DataFrame(pages)
        # df.to_csv('database.csv', sep=';', index=False)
        # print(df.head())
        df = pd.json_normalize(df['properties'])
        df["Id"] = pd.json_normalize(df["Id.rich_text"].explode())["text.content"]
        df["Instrutor(a)"] = pd.json_normalize(df["Instrutor(a).rich_text"].explode())["text.content"]
        df["Status"] = df["Status.select.name"]
        df["Tarefa"] = pd.json_normalize(df["Tarefa.title"].explode())["text.content"]
        df["Período Planejado - start"] = df["Período Planejado.date.start"]
        df["Período Planejado - end"] = df["Período Planejado.date.end"]
        df["Período Realizado - start"] = df["Período Realizado.date.start"]
        df["Período Realizado - end"] = df["Período Realizado.date.end"]
        df["Atividade"] = pd.json_normalize(df["Atividade.rich_text"].explode())["text.content"]
        df["Produto"] = pd.json_normalize(df["Produto.rich_text"].explode())["text.content"]
        df["Planejamento"] = df["Planejamento.select.name"]
        df["Código do Produto"] = pd.json_normalize(df["Código do Produto.rich_text"].explode())["text.content"]
        df["Título do Produto"] = pd.json_normalize(df["Título do Produto.rich_text"].explode())["text.content"]

        df["Qualidade das entregas"] = df["Qualidade das entregas.select.name"]
        df["Velocidade"] = df["Velocidade.select.name"]
        df["Resposta aos feedbacks"] = df["Resposta aos feedbacks.select.name"]
        df["Cumprimento de acordos"] = df["Cumprimento de acordos.select.name"]
        df["Comunicação"] = df["Comunicação.select.name"]
        df["Assiduidade"] = df["Assiduidade.select.name"]
        df["Dedicação"] = df["Dedicação.select.name"]
        df["Colaboração"] = df["Colaboração.select.name"]
        df["Flexibilidade"] = df["Flexibilidade.select.name"]

        columns = ["Id", "Instrutor(a)", "Status", "Tarefa", "Período Planejado - start", "Período Planejado - end", "Período Realizado - start", "Período Realizado - end", "Atividade", "Produto", "Planejamento", "Código do Produto", "Título do Produto", "Qualidade das entregas", "Velocidade", "Resposta aos feedbacks", "Cumprimento de acordos", "Comunicação", "Assiduidade", "Dedicação", "Colaboração", "Flexibilidade"]
        df = df[columns]
        df = df.query('Status != "Cancelada"')
        df = df.query('Produto != "FÉRIAS"')
        df = df.query('Produto != "ATESTADO"')
        # print(df.shape)

        table_aux = df.groupby(by=['Instrutor(a)', 'Título do Produto', 'Planejamento'])['Id'].count().reset_index()

        table_01 = pd.pivot_table(table_aux, values='Título do Produto', index=['Instrutor(a)'], columns=['Planejamento'], aggfunc="count").fillna(0.0)
        table_01['% de Demandas Não Planejadas'] = round(table_01['Não Planejada'] / (table_01['Não Planejada'] + table_01['Planejada']) * 100)
        table_01['% de Demandas Não Planejadas'] = table_01['% de Demandas Não Planejadas'].apply(lambda x: f"{x:.0f}%")
        table_01.reset_index(inplace=True)
        # print(table_01)
        data_json_table_01 = []
        for index, row in table_01.iterrows():
            data_json_table_01.append({
                "Instrutor(a)": {"title": [{"text": {"content": row['Instrutor(a)']}}]},
                "Não Planejada": {"number": row['Não Planejada']},
                "Planejada": {"number": row['Planejada']},
                "% de Demandas Não Planejadas": {"rich_text": [{"text": {"content": row['% de Demandas Não Planejadas']}}]}
            })

        return data_json_table_01

# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    gods_eye = GodsEye()
    response = ""
    # instructors=["Rodrigo", "Allan", "Afonso", "Bia", "Daniel", "Danielle", "Igor", "João", "Larissa", "Marcelo", "Mirla", "Val", "Victorino", "Sabino"]
    instructors=["Igor"]
    # instructors=[, "Larissa", "Sabino"]

    # Envia mensagem com feedbacks mensais
    gods_eye.send_weekly_feedback(instructors)

    # Envia mensagem sobre atividades
    # gods_eye.send_task_reminder(instructors)

    # response = gods_eye.create_quarterly_results_report(instructors=instructors, start="2024-01-01", end="2024-03-31", page_title="1º Trimestre 2024 (Teste)")
    # response = gods_eye.update_competency_assessment(instructors=instructors, page_title="1º Trimestre 2024", start="2024-01-01", end="2024-03-31")
    # response = gods_eye.update_produced_content(instructors)
    # response = gods_eye.add_competency_assessment()
    # response = gods_eye.update_tasks_database()
    # response = gods_eye.backup_tasks_database()
    # gods_eye.restore_tasks_database()
    # response = gods_eye.statistics(instructors)
    
    # notion = NotionAPI()
    # response = notion.retrieve_page("dad6e4a7708148928a4bb70c6ad1c158")

    # # response = gods_eye.create_quarterly_report(["João", "Marcelo"], start="2024-01-01", end="2024-03-31")
    try:
        print(json.dumps(response, indent=4, sort_keys=True, ensure_ascii=False))
    except:
        print(response)