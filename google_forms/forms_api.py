from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from notion.notion_api import NotionAPI
from mongodb.mongodb import MongoDBManager
from discord.discord_api import DiscordBotSendUserMessage
import os
from google_calendar import utils
from gods_eye import utils as gods_eye_utils
from dotenv import load_dotenv
from datetime import datetime, date, timedelta

import json
import pandas as pd
import re

class GoogleFormsAPI:
    # --------------------------------------------------------------------------------------
    def __init__(self):
        load_dotenv()
        self.database_tasks = os.getenv('DATABASE_TASKS')
        self.scopes = eval(os.getenv('GOOGLE_SCOPES'))
        self.credentials_file = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
        self.creds = None
        self.mongo_manager = MongoDBManager()
        self.notion = NotionAPI()
        self.service = self.authenticate()[0]
        self.drive = self.authenticate()[1]
        self.planning_sheet_id = os.getenv('PLANNING_SHEET_ID')
        self.contacts_sheet_id = os.getenv('CONTACTS_SHEET_ID')
        self.mapping_instructos = json.loads(os.getenv('MAPPING_INSTRUCTORS'))
        self.da_id_discord = json.loads(os.getenv('DA_ID_DISCORD'))
        self.google_forms_base_id = os.getenv('GOOGLE_FORMS_BASE_ID')
        self.mapping_questions = [
            {'questionId': '51bbe231', 'columnName': 'Dedicação DA'},
            {'questionId': '1be81f6d', 'columnName': 'Cumprimento de acordos DA'},
            {'questionId': '0905138e', 'columnName': 'Qualidade das entregas DA'},
            {'questionId': '0833128c', 'columnName': 'Velocidade DA'},
            {'questionId': '7a8c427b', 'columnName': 'Resposta aos feedbacks DA'},
            {'questionId': '4735efef', 'columnName': 'Flexibilidade DA'},
            {'questionId': '01eccc0f', 'columnName': 'Colaboração DA'},
            {'questionId': '00e05b81', 'columnName': 'Comunicação DA'},
            {'questionId': '74e08aa4', 'columnName': 'Assiduidade DA'},
            {'questionId': '2005863d', 'columnName': 'Feedback DA'}
        ]

    # --------------------------------------------------------------------------------------
    def load_credentials(self):
        try:
            self.mongo_manager.delete_many("google_credentials", {})
            self.mongo_manager.insert_one("google_credentials", self.credentials_file)
            print("Credenciais carregadas com sucesso.")
        except Exception as e:
            print(f"Falha ao carregar credenciais. {e}")

    # --------------------------------------------------------------------------------------
    def authenticate(self):
        try:
            credentials_info = self.mongo_manager.find_one("google_credentials", {})
            token_info = self.mongo_manager.find_one("google_token", {})
            
            if token_info:
                creds = Credentials.from_authorized_user_info(token_info, self.scopes)
                if creds.expired and creds.refresh_token:
                    try:
                        creds.refresh(Request())
                        self.mongo_manager.replace_one("google_token", {}, json.loads(creds.to_json()))
                    except Exception as e:
                        print("Falha ao atualizar o token, requerendo novo consentimento...")
                        creds = None
            else:
                creds = None
                
            if not creds:
                if credentials_info:
                    # Modificação aqui para forçar o consentimento
                    flow = InstalledAppFlow.from_client_config(credentials_info, self.scopes)
                else:
                    raise Exception("Credenciais não encontradas no MongoDB.")
                
                creds = flow.run_local_server(port=0)
                self.mongo_manager.delete_many("google_token", {})
                self.mongo_manager.insert_one("google_token", json.loads(creds.to_json()))

            self.creds = creds
            return build('forms', 'v1', credentials=self.creds), build('drive', 'v3', credentials=self.creds)
        
        except Exception as e:
            print(f"Falha na autenticação: {e}")
            return None, None

    # --------------------------------------------------------------------------------------
    # Obtendo o ID do formulário base
    def get_forms_id(self):
        # Define a query para buscar arquivos do tipo Google Forms
        query = "mimeType='application/vnd.google-apps.form' and trashed=false"

        # Faz a requisição para listar os arquivos
        results = self.drive.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        forms = []
        if not items:
            print('Nenhum formulário encontrado.')
        else:
            # print('Formulários:')
            for item in items:
                matches = re.findall(r'\[(.*?)\]', item['name'])
                if len(matches) > 0 and matches[0] == 'Olho de Deus':
                    forms.append({'form_id': item['id'], 'page_id': matches[2]})

        return forms

    # --------------------------------------------------------------------------------------
    # Cria uma cópia do formulário BASE e configura de acordo com a atividade alvo
    def copy_forms_base(self, task_id, instructor, title, task):
        form_base_id = self.google_forms_base_id

        # Copiando o formulário base
        form = self.drive.files().copy(fileId=form_base_id).execute()
        form_id = form['id']
        file_metadata = {
            'name': f'[Olho de Deus][{form_id}][{task_id}]'
        }
        form = self.drive.files().update(fileId=form_id, body=file_metadata).execute()
        form = self.service.forms().get(formId=form_id).execute()

        items = form.get('items', [])
        for item in items:
            if item['title'] == 'INFORMAÇÕES SOBRE A ATIVIDADE':
                item_id = item['itemId']

        item_text = f'''
Pessoa instrutora: {instructor}
Produto: {title}
Atividade: {task}
'''
        # Atualizando o novo formulário
        update_body = {
            "requests": [
                {
                    "updateItem": {
                        "item": {
                            "itemId": item_id,
                            "textItem": {},
                            'title': 'INFORMAÇÕES SOBRE A ATIVIDADE',
                            "description": item_text
                        },
                        "location": {
                            "index": 0
                        },
                        "updateMask": "description"
                    }
                }
            ]
        }
        self.service.forms().batchUpdate(formId=form_id, body=update_body).execute()

        print(f'Formulário de acompanhamento enviado com sucesso!')

        return form['responderUri']

    # --------------------------------------------------------------------------------------
    # Envia formulário de acompanhamento para pessoa responsável pelo acompanhamento didático
    def send_feedback_form(self):
        today = date.today()
        greeting = gods_eye_utils.greeting(datetime.now().hour)

        print('>>> Obtendo as informações do database de tarefas...')
        database = self.notion.retrieve_database(self.database_tasks)

        print(f'>>> Verificando as tarefas que foram terminadas na semana anterior...')
        start_of_week = today - timedelta(days=today.weekday() + 7)
        end_of_week = start_of_week + timedelta(days=6)

        for page in database:
            end = page['properties']['Período Realizado']['date']['end']
            product = page['properties']['Produto']['rich_text'][0]['text']['content']

            if product in ['Curso', 'Curso (E)', 'Artigo', 'Artigo Pilar']:
                # if datetime.strptime(end, "%Y-%m-%d").date() == today - timedelta(days=days):
                if start_of_week <= datetime.strptime(end, "%Y-%m-%d").date() <= end_of_week:
                    da = page['properties']['DA Responsável']['select'] if page['properties']['DA Responsável']['select'] == None else page['properties']['DA Responsável']['select']['name']
                    if da == None:
                        print("Não foi encontrado(a) o(a) responsável pela didática desta atividade.")
                        continue

                    instructor = page['properties']['Instrutor(a)']['rich_text'][0]['text']['content']
                    if instructor in ['Victorino', 'Sabino']:
                        print("O procedimento de feedback não acontece para instrutores externos.")
                        continue

                    task = page['properties']['Atividade']['rich_text'][0]['text']['content']
                    if task == 'Planejamento, pesquisa e estudo':
                        print("O procedimento de feedback não acontece para a fase de planejamento, pesquisa e estudo de um curso.")
                        continue

                    task_id = page['id']
                    title = page['properties']['Título do Produto']['rich_text'][0]['text']['content']
                    form_link = self.copy_forms_base(task_id, instructor, title, task)
                    message = f"""
# **{greeting}, {da}!**

Segue o [formulário de acompanhamento]({form_link}) para a seguinte atividade:
- **Pessoa instrutora:** {instructor}
- **Produto:** {title}
- **Atividade:** {task}

Bom trabalho e um excelente dia. :people_hugging:"""
                    DiscordBotSendUserMessage(self.da_id_discord[da], message).run()
                    DiscordBotSendUserMessage(self.da_id_discord["Rodrigo"], message).run()

        return None

    # --------------------------------------------------------------------------------------
    # Itera nos forms criados e verifica quais já receberam uma resposta
    def get_form_responses(self):
        # Obtendo a identificaação dos forms disponíveis
        forms = self.get_forms_id()

        for form in forms:
            # Obtendo as respostas
            form_responses = self.service.forms().responses().list(formId=form['form_id']).execute()
            responses = form_responses.get('responses', [])
            if len(responses) == 0:
                print("Formulário aguardando resposta.")
                continue

            # Atualizando a página do database do Notion
            json_questions = {'properties': {}}
            for item in self.mapping_questions:
                if item['columnName'] != 'Feedback DA':
                    json_questions['properties'][item['columnName']] = {
                        'select': {
                            'name': responses[0]['answers'][item['questionId']]['textAnswers']['answers'][0]['value']
                        }
                    }
                else:
                    json_comment = {
                        "parent": {"page_id": form['page_id']},
                        "rich_text": [{"text": {"content": responses[0]['answers'][item['questionId']]['textAnswers']['answers'][0]['value']}}]
                    }            

            questions_updated = self.notion.update_page(form['page_id'], json_questions)

            comment_updated = self.notion.create_comment(json_comment)

            if questions_updated[0] == 200 and comment_updated[0] == 200:
                self.drive.files().delete(fileId=form['form_id']).execute()
                greeting = gods_eye_utils.greeting(datetime.now().hour)
                for da in ["David", "Rodrigo"]:
                    message = f"""
# **{greeting}, {da}!**

Formulário de feedback enviado com sucesso!
- **Identificador da atividade:** {form['page_id']}

Bom trabalho e um excelente dia. :people_hugging:"""
                    DiscordBotSendUserMessage(self.da_id_discord[da], message).run()

        return None

    # --------------------------------------------------------------------------------------
    # Rotina para criar um formulário
    def create_form(self):
        try:
            IMAGE_ITEM = {
                'requests': [
                    {
                        'createItem': {
                            'item': {
                                'title': 'Olho de Deus',
                                'imageItem': {
                                    'image': {
                                        'sourceUri': 'https://storage.googleapis.com/alura-images/olho-de%20deus/Olho_de_Deus_capa_01.jpg',
                                        'altText': 'Texto alternativo para a imagem'
                                    }
                                }
                            },
                            'location': {
                                'index': 0
                            }
                        }
                    }
                ]
            }      

            NEW_FORM = {
                'info': {
                    'title': 'Formulário de Acompanhamento'
                }
            }

            DESCRIPTION = {
                "requests": [
                    {
                        "updateFormInfo": {
                            "info": {
                                "description": ('''
**Modelo de avaliação:**
**1 - Iniciante:** A pessoa está nos estágios iniciais de desenvolvimento nesta competência. Ela pode ter conhecimento básico, mas ainda precisa de orientação e supervisão significativa para realizar tarefas relacionadas a essa competência de forma eficaz.

**2 - Competente:** A pessoa demonstra um nível adequado de habilidade e conhecimento nesta competência. Ela pode trabalhar de forma independente na maioria das tarefas relacionadas a essa competência, com supervisão mínima. No entanto, ainda pode precisar de suporte ocasional para lidar com desafios mais complexos.

**3 - Proficiente:** A pessoa possui um alto nível de habilidade e conhecimento nesta competência. Ela pode realizar tarefas relacionadas a essa competência de forma eficaz e eficiente, com pouco ou nenhum suporte. Além disso, ela é capaz de lidar com desafios e situações imprevistas de maneira autônoma.

**4 - Especialista:** A pessoa é altamente qualificada e experiente nesta competência. Ela não apenas executa tarefas relacionadas a essa competência de maneira excelente, mas também é capaz de oferecer orientação e liderança para outros na área. Sua experiência e conhecimento são reconhecidos e respeitados dentro e fora da organização.'''
                                )
                            },
                            "updateMask": "description",
                        }
                    }
                ]
            }

            NEW_QUESTION = {
                "requests": [
                    {
                        "createItem": {
                            "item": {
                                "title": (
                                    "**Dedicação**"
                                ),
                                "questionItem": {
                                    "question": {
                                        "required": True,
                                        "choiceQuestion": {
                                            "type": "RADIO",
                                            "options": [ 
                                                {"value": "1 - Demonstra interesse mínimo em suas responsabilidades como instrutor."},
                                                {"value": "2 - Mostra interesse em suas responsabilidades e realiza suas tarefas de forma consistente."},
                                                {"value": "3 - Mostra um alto nível de comprometimento e dedicação em suas responsabilidades."},
                                                {"value": "4 - Demonstra um comprometimento excepcional e paixão por suas responsabilidades como instrutor."},
                                            ],
                                            "shuffle": False,
                                        },
                                    }
                                },
                            },
                            "location": {"index": 0},
                        }
                    }
                ]
            }

            form = self.service.forms().create(body=NEW_FORM).execute()
            self.service.forms().batchUpdate(formId=form["formId"], body=NEW_QUESTION).execute()
            self.service.forms().batchUpdate(formId=form["formId"], body=DESCRIPTION).execute()
            self.service.forms().batchUpdate(formId=form["formId"], body=IMAGE_ITEM).execute()
            form = self.service.forms().get(formId=form["formId"]).execute()
            print(form)
            print(form['responderUri'])

        except Exception as e:
            print(f"Falha ao criar o formulário: {e}")
            return None

# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    forms_api = GoogleFormsAPI()
    # forms_api.create_form()
    # print(forms_api.get_forms_id())
    # forms_api.copy_forms_base('lkajjs34fawksnglw', 'Rodrigo', 'Curso', 'Gravação das aulas')
    forms_api.get_form_responses()