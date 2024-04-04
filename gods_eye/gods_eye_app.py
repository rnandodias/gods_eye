from notion.notion_api import NotionAPI
from google_calendar.calendar_api import GoogleCalendarAPI
from mongodb.mongodb import MongoDBManager
from dotenv import load_dotenv
from tqdm import tqdm
from datetime import datetime
import os
from gods_eye import utils

import json
import pandas as pd

class GodsEye:
    # --------------------------------------------------------------------------------------
    def __init__(self):
        load_dotenv()
        self.database_tasks = os.getenv('DATABASE_TASKS')
        self.database_users = os.getenv('DATABASE_USERS')
        self.calendar = GoogleCalendarAPI()
        self.notion = NotionAPI()
        self.mongo_manager = MongoDBManager()

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
    # Atualiza as páginas de tarefas dos instrutores com a avaliação de competências
    # [EM CONSTRUÇÃO]
    # --------------------------------------------------------------------------------------
    # def add_competency_assessment(self):
    #     print('>>> Adiconando as colunas de avaliação de competências nas tarefas dos instrutores...')
    #     json_data = {
    #         "properties": {
    #             "Dedicação": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. Demonstra interesse mínimo em suas responsabilidades como instrutor.", "color": "red"},
    #                         {"name": "2. Mostra interesse em suas responsabilidades e realiza suas tarefas de forma consistente.", "color": "orange"},
    #                         {"name": "3. Mostra um alto nível de comprometimento e dedicação em suas responsabilidades.", "color": "yellow"},
    #                         {"name": "4. Demonstra um comprometimento excepcional e paixão por suas responsabilidades como instrutor.", "color": "green"},
    #                     ]
    #                 }
    #             },
    #             "Cumprimento de acordos": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. Frequentemente não cumpre prazos ou compromissos estabelecidos.", "color": "red"},
    #                         {"name": "2. Geralmente cumpre prazos e compromissos estabelecidos.", "color": "orange"},
    #                         {"name": "3. Sempre cumpre prazos e compromissos estabelecidos de maneira confiável.", "color": "yellow"},
    #                         {"name": "4. É extremamente confiável e sempre cumpre prazos e compromissos.", "color": "green"},
    #                     ]
    #                 }
    #             },
    #             "Qualidade das entregas": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. As entregas têm muitos erros e não atendem aos padrões mínimos de qualidade.", "color": "red"},
    #                         {"name": "2. As entregas são satisfatórias embora possam ocasionalmente conter erros menores.", "color": "orange"},
    #                         {"name": "3. As entregas são sempre de alta qualidade atendendo ou excedendo os padrões estabelecidos.", "color": "yellow"},
    #                         {"name": "4. As entregas são de nível superior refletindo um alto padrão de excelência e inovação.", "color": "green"},
    #                     ]
    #                 }
    #             },
    #             "Velocidade": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. Realiza tarefas de forma lenta e com pouca eficiência.", "color": "red"},
    #                         {"name": "2. Realiza tarefas em um ritmo razoável e dentro dos prazos definidos.", "color": "orange"},
    #                         {"name": "3. Realiza tarefas de forma rápida e eficiente sem comprometer a qualidade.", "color": "yellow"},
    #                         {"name": "4. Realiza tarefas de forma extremamente rápida mantendo altos padrões de qualidade.", "color": "green"},
    #                     ]
    #                 }
    #             },
    #             "Resposta aos feedbacks": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. Tem dificuldade em aceitar feedbacks e pouco esforço é feito para melhorar.", "color": "red"},
    #                         {"name": "2. Aceita feedbacks de forma construtiva e faz esforços para melhorar.", "color": "orange"},
    #                         {"name": "3. Aceita e implementa feedbacks de forma proativa buscando constantemente melhorar seu desempenho.", "color": "yellow"},
    #                         {"name": "4. Valoriza e integra feedbacks de forma excepcional mostrando desejo contínuo por desenvolvimento.", "color": "green"},
    #                     ]
    #                 }
    #             },
    #             "Flexibilidade": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. Resiste a mudanças e tem dificuldade em se adaptar a novas situações.", "color": "red"},
    #                         {"name": "2. É capaz de se adaptar a mudanças e novas situações com alguma orientação.", "color": "orange"},
    #                         {"name": "3. Adapta-se facilmente a mudanças e é capaz de lidar com diversas situações sem dificuldade.", "color": "yellow"},
    #                         {"name": "4. Mostrou habilidade excepcional em se adaptar a qualquer situação e liderar mudanças efetivamente.", "color": "green"},
    #                     ]
    #                 }
    #             },
    #             "Colaboração": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. Tende a trabalhar de forma isolada e não contribui para o trabalho em equipe.", "color": "red"},
    #                         {"name": "2. Trabalha bem em equipe e contribui para objetivos compartilhados.", "color": "orange"},
    #                         {"name": "3. Colabora efetivamente com colegas e lidera iniciativas de equipe quando necessário.", "color": "yellow"},
    #                         {"name": "4. É um líder colaborativo capaz de inspirar e motivar colegas para alcançar objetivos comuns.", "color": "green"},
    #                     ]
    #                 }
    #             },
    #             "Comunicação": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. Comunicação é confusa e não eficaz.", "color": "red"},
    #                         {"name": "2. Comunica de forma clara e eficaz na maioria das situações.", "color": "orange"},
    #                         {"name": "3. Comunica de forma clara e concisa em uma variedade de contextos.", "color": "yellow"},
    #                         {"name": "4. Comunica de forma envolvente e persuasiva inspirando e influenciando os outros.", "color": "green"},
    #                     ]
    #                 }
    #             },
    #             "Assiduidade": {
    #                 "select": {
    #                     "options": [
    #                         {"name": "1. Ausências frequentes e falta de comprometimento com os horários.", "color": "red"},
    #                         {"name": "2. Comparece regularmente e cumpre os horários de trabalho.", "color": "orange"},
    #                         {"name": "3. É altamente confiável em relação à presença e pontualidade.", "color": "yellow"},
    #                         {"name": "4. É um exemplo de pontualidade e presença consistente.", "color": "green"},
    #                     ]
    #                 }
    #             }
    #         }
    #     }
    #     response = self.notion.update_database(self.database_tasks, json_data)
    #     return response

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
        for item in tqdm(events):
            data_input = utils.data_input(self.database_tasks, item)
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
    # Cria o relatório de avaliação de desempenho trimestral dos instrutores
    # --------------------------------------------------------------------------------------
    def create_quarterly_report(self, instructors, start="2024-01-01", end="2024-03-31"):
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
                split_text = list(utils.split_text_into_blocks(utils.report(utils.prompt_create_report(input_gpt))))
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
                self.notion.append_block_children(id, data)

    # --------------------------------------------------------------------------------------
    # Atualiza o database de acompanhamento de produção dos instrutores
    # [EM CONSTRUÇÃO]
    # --------------------------------------------------------------------------------------
    def monitoring_production(self, instructors, page_title, start="2024-01-01", end="2024-03-31"):
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
        
        print('>>> Obtendo os IDs das páginas de acompanhamento dos instrutores...')
        user_pages = self.notion.retrieve_database(self.database_users)
        for user_page in user_pages:
            instructor = user_page['properties']['Nome']['rich_text'][0]['text']['content']
            if instructor in instructors:
                print(f">>> Iniciando o carregamento da página de acompanhamento de produção do(a) instrutor(a) {instructor}")
                response = self.notion.find_page_title(user_page['id'], "Acompanhamento da Produção")
                child_page_id = ""
                if not response[0]:
                    data_json = {
                        "parent": {"type": "page_id", "page_id": f"{user_page['id']}"},
                        "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/avd/90cfa4a4-a1fc-4656-b708-8f610eab24ab.webp"}},
                        "icon": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/avd/054a40da-bce6-4fbc-97ef-3001ae18bcf4.webp"}},
                        "properties": {"title": {"title": [{"text": {"content": "Acompanhamento da Produção"}}]}}
                    }
                    parent_page = self.notion.create_page(data_json)
                    data_json_child = {
                        "parent": {"type": "page_id", "page_id": f"{parent_page[1]['id']}"},
                        "icon": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/avd/f4dbddce-7a06-4c68-b839-b4c5cd3df407.webp"}},
                        "cover": {"external": {"url": "https://storage.googleapis.com/alura-images/avd/45fb1024-d3fd-4462-8837-765aa69ef679.webp"}},
                        "properties": {"title": {"title": [{"text": {"content": page_title}}]}}
                    }
                    child_page = self.notion.create_page(data_json_child)
                    child_page_id = child_page[1]['id']
                    print('ID -> ', child_page_id)
                    self.notion.create_database(utils.data_competency_assessment_create(child_page_id))
                else:
                    child_page = self.notion.find_page_title(response[1]['id'], page_title)
                    if not child_page[0]:
                        data_json_child = {
                            "parent": {"type": "page_id", "page_id": f"{response[1]['id']}"},
                            "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/avd/90cfa4a4-a1fc-4656-b708-8f610eab24ab.webp"}},
                            "icon": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/avd/054a40da-bce6-4fbc-97ef-3001ae18bcf4.webp"}},
                            "properties": {"title": {"title": [{"text": {"content": page_title}}]}}
                        }
                        child_page = self.notion.create_page(data_json_child)
                        child_page_id = child_page[1]['id']
                        self.notion.create_database(utils.data_competency_assessment_create(child_page_id))
                    else:
                        child_page_id = child_page[1]['id']
                
                print(">>> Carregando as avaliações de competências...")

                print(child_page_id)

        # for page in database:
        #     if page['id'] == "3d5506e0-fc37-43a7-8efb-c4ce0463c0fc":
        #         print(json.dumps(page, indent=4, sort_keys=True, ensure_ascii=False))


        return None

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
        df.to_csv('database.csv', sep=';', index=False)
        print(df.head())

        # print('>>> Carregando as informações de planejamento...')
        # planning = utils.read_planning_sheet(self.planning_sheet_id, f"{quarter}_Produtos_Planejado")
        # instructors = ["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val", "Ana Hashimoto", "Pedro Moura", "Sabino", "Victorino"]
        # Planejamento = planning.query(
        #         'Prioridade in ["Alta"] and Objetivo not in ["Publicado", "Backlog", "Produzindo"] and `Status Atual` not in ["Pós-produção"] and `Grupo Instrutor` in @instructors'
        #     ).pivot_table(
        #         values=['Count'],
        #         index=['Grupo Instrutor'],
        #         columns=['Tipo'],
        #         aggfunc='sum',
        #         margins=True,
        #         margins_name='Total'
        #     ).fillna('-')
        # print(Planejamento)

# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    gods_eye = GodsEye()
    response = ""
    instructors=["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val"]
    # response = gods_eye.add_competency_assessment()
    # response = gods_eye.update_tasks_database()
    # response = gods_eye.backup_tasks_database()
    # gods_eye.restore_tasks_database()
    # response = gods_eye.monitoring_production(instructors=["João"], page_title="1º Trimestre 2024", start="2024-01-01", end="2024-03-31")
    response = gods_eye.statistics(instructors)
    
    # response = gods_eye.create_quarterly_report(["João"], start="2024-01-01", end="2024-03-31")
    # try:
    #     print(json.dumps(response, indent=4, sort_keys=True, ensure_ascii=False))
    # except:
    #     print(response)