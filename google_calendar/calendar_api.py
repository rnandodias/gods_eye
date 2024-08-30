from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from mongodb.mongodb import MongoDBManager
import os
from google_calendar import utils
from dotenv import load_dotenv
from datetime import datetime

import json
import pandas as pd

class GoogleCalendarAPI:
    # --------------------------------------------------------------------------------------
    def __init__(self):
        load_dotenv()
        self.scopes = eval(os.getenv('GOOGLE_SCOPES'))
        self.credentials_file = json.loads(os.getenv('GOOGLE_CREDENTIALS'))
        self.creds = None
        self.mongo_manager = MongoDBManager()
        self.service = self.authenticate()
        self.planning_sheet_id = os.getenv('PLANNING_SHEET_ID')
        self.contacts_sheet_id = os.getenv('CONTACTS_SHEET_ID')
        self.mapping_instructos = json.loads(os.getenv('MAPPING_INSTRUCTORS'))

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
            return build('calendar', 'v3', credentials=self.creds)
        except Exception as e:
            print(f"Falha na autenticação: {e}")
            return None

    # def authenticate(self):
    #     try:
    #         credentials_info = self.mongo_manager.find_one("google_credentials", {})
    #         token_info = self.mongo_manager.find_one("google_token", {})
            
    #         if token_info:
    #             creds = Credentials.from_authorized_user_info(token_info, self.scopes)
    #             if creds.expired and creds.refresh_token:
    #                 creds.refresh(Request())
    #                 self.mongo_manager.replace_one("google_token", {}, json.loads(creds.to_json()))
    #         else:
    #             if credentials_info:
    #                 flow = InstalledAppFlow.from_client_config(credentials_info, self.scopes)
    #             else:
    #                 raise Exception("Credenciais não encontradas no MongoDB.")
                
    #             creds = flow.run_local_server(port=0)
    #             self.mongo_manager.insert_one("google_token", json.loads(creds.to_json()))

    #         self.creds = creds
    #         return build('calendar', 'v3', credentials=self.creds)
    #     except Exception as e:
    #         print(f"Falha na autenticação: {e}")
    #         return None

    # --------------------------------------------------------------------------------------
    # Rotina para criar uma agenda de trabalho
    def create_agenda(self, name, email):
        try:
            users = ['romulo.henriquemv@gmail.com']
            if email not in users:
                users.append(email)
            
            agenda_body = {
                'summary': 'Alura - ' + name,
                'description': f'Agenda de trabalho.\nPessoa instrutora: {name}'
            }
            agenda = self.service.calendars().insert(body=agenda_body).execute()
            print(agenda)

            for user in users:
                acl_body = {
                    'scope': {
                        'type': 'user',
                        'value': user,
                    },
                    'role': 'owner',
                }
                acl = self.service.acl().insert(
                    calendarId=agenda['id'], body=acl_body
                ).execute()
                print(acl)

        except Exception as e:
            print(f"Falha ao criar agenda de trabalho: {e}")
            return None

    # --------------------------------------------------------------------------------------
    def get_updated_events(self):
        try:
            calendar_list = self.service.calendarList().list().execute()

            # Criando um dicionário com as pessoas e os ids das agendas
            instructors = {}
            for calendar in calendar_list.get("items"):
                if calendar.get("summary").split('-')[0].strip() == 'Alura':
                    instructors.update({
                        calendar.get("summary").split('-')[-1].strip(): calendar.get("id")
                    })

            # Obtendo e tratando os conteúdos das agendas das pessoas
            agendas = []
            for instructor, id in instructors.items():
                events_result = self.service.events().list(
                    calendarId=id, 
                    # timeMin=datetime(2024, 7, 1, 0, 0, 0).isoformat() + 'Z',
                    singleEvents=True,
                    orderBy='startTime'
                ).execute()
                events = events_result.get('items', [])

                # if not events:
                #     print('Nenhum evento próximo encontrado.')
                #     return
                
                for event in events:
                    agendas.append(utils.configure_updated_events(event, instructor))

            return agendas
        except Exception as e:
            print(f"Falha na obtenção dos eventos das agendas pessoais: {e}")
            return None

    # --------------------------------------------------------------------------------------
    def create_quarterly_planning_events_json(self, quarter="2_Tri_2024", start_work_cycle="2024-04-01", instructors=[], priorities=[]):
        print('>>> Obtendo as datas das últimas entregas ou das férias de cada instrutor...')
        events = self.get_updated_events()
        last_task_or_vacation_date = utils.find_last_task_or_vacation_date(events)

        print('>>> Carregando as informações de planejamento...')
        planning = utils.read_planning_sheet(self.planning_sheet_id, f"{quarter}_Produtos_Planejado")

        # planning_copy = planning.copy()
        # planning_copy = planning_copy.query('Prioridade in ["Alta", "Média"] and `Grupo Instrutor` in @instructors and `Status Atual` not in ["Pós-produção", "Finalizado"]').sort_values(by=['Grupo Instrutor', 'Prioridade'])
        # lista_de_tuplas=list(zip(planning_copy['Grupo Instrutor'], planning_copy['Conteúdos']))
        # with open('lista_de_tuplas.txt', 'w') as f:
        #     for tupla in lista_de_tuplas:
        #         f.write(f"{tupla}\n")

        print('>>> Considerando algumas prioridade no planejamento...')
        planning = utils.prioritize_events(planning, priorities)

        print('>>> Carregando as informações sobre pessoal em condições especiais (férias etc.)...')
        vacation = utils.read_contacts_sheet(self.contacts_sheet_id, self.mapping_instructos, quarter)

        print('>>> Montando o planejamento...')
        agenda = utils.create_agenda(start_work_cycle, planning, instructors, last_task_or_vacation_date, vacation)

        return agenda

    # --------------------------------------------------------------------------------------
    def update_quarterly_calendars(self, quarter="2_Tri_2024", start_work_cycle="2024-04-01", instructors=[], priorities=[]):
        try:
            agendas_json = self.create_quarterly_planning_events_json(quarter, start_work_cycle, instructors, priorities)

            calendar_list = self.service.calendarList().list().execute()

            instructors_info = {}
            for calendar in calendar_list.get("items"):
                if calendar.get("summary").split('-')[0].strip() == 'Alura':
                    instructors_info.update({
                        calendar.get("summary").split('-')[-1].strip(): calendar.get("id")
                    })

            for instructor in instructors:
                for events in agendas_json[instructor]:
                    for event in events:
                        event = self.service.events().insert(calendarId=instructors_info[instructor], body=event).execute()
                        print('Event created: %s' % (event.get('htmlLink')))

        except Exception as e:
            print(f"Falha ao atualizar os eventos das agendas pessoais: {e}")
            return None

    # --------------------------------------------------------------------------------------
    def statistics(self, quarter="2_Tri_2024"):
        print('>>> Carregando as informações de planejamento...')
        planning = utils.read_planning_sheet(self.planning_sheet_id, f"{quarter}_Produtos_Planejado")
        instructors = ["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val", "Ana Hashimoto", "Pedro Moura", "Sabino", "Victorino", "Daniel", "David"]
        Planejamento = planning.query(
                'Prioridade in ["Alta"] and Objetivo not in ["Publicado", "Backlog", "Produzindo"] and `Status Atual` not in ["Pós-produção"] and `Grupo Instrutor` in @instructors'
            ).pivot_table(
                values=['Count'],
                index=['Grupo Instrutor'],
                columns=['Tipo'],
                aggfunc='sum',
                margins=True,
                margins_name='Total'
            ).fillna('-')
        print(Planejamento)

# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    calendar_api = GoogleCalendarAPI()

    # response = calendar_api.get_updated_events()
    # print(json.dumps(response, indent=4, sort_keys=True, ensure_ascii=False))

    # --------------------------------------------------------------------------------------
    # Tentando a criação do planejamento de 2024/02
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

    response = calendar_api.create_quarterly_planning_events_json(instructors=instructors, priorities=priorities)
    lista=[]
    for item in response:
        for i in response[item]:
            for j in i:
                # print(i)
                # if j['summary'].split('-')[-1] in [' Atividades', ' Escrita', ' Gravação das aulas', ' Gravação']:
                if j['summary'].split('-')[-1] in [' Gravação das aulas']:
                    lista.append((j['summary'], j['end']['date']))

    df = pd.DataFrame(lista, columns=['Atividade', 'Data de Término'])
    df['Data de Término'] = pd.to_datetime(df['Data de Término'])
    df['Mês'] = df['Data de Término'].dt.strftime('%B')
    df['Semana'] = df['Data de Término'].dt.isocalendar().week
    sumario_semanal = df.groupby(['Mês', 'Semana']).size().reset_index(name='Total de Atividades')
    meses_pt = {
        'January': 'Janeiro', 'February': 'Fevereiro', 'March': 'Março',
        'April': 'Abril', 'May': 'Maio', 'June': 'Junho',
        'July': 'Julho', 'August': 'Agosto', 'September': 'Setembro',
        'October': 'Outubro', 'November': 'Novembro', 'December': 'Dezembro'
    }
    sumario_semanal['Mês'] = sumario_semanal['Mês'].map(meses_pt)
    sumario_semanal.sort_values(by='Semana', ascending=True, inplace=True)
    print(sumario_semanal)
    calendar_api.statistics()
    utils.create_timeline(response, "Planejamento 2 Tri 2024")
    # --------------------------------------------------------------------------------------
    
    # print(json.dumps(response['João'], indent=4, sort_keys=True, ensure_ascii=False))
    # print(json.dumps(response, indent=4, sort_keys=True, ensure_ascii=False))
    # print(response)

    # for produtos in response['Allan']:
    #     for index, produto in enumerate(produtos):
    #         if index == 0:
    #             print(f"{produto['summary']}")
    #             print('='*120)
    #         print(f"{produto['start']['date']} - {produto['end']['date']}")

    # calendar_api.load_credentials()
    # response = calendar_api.get_updated_events()

    # plan = utils.read_planning_sheet('1LpjnGCZZGOD9s1pl6vcEAtOEkVG3oYvC-uSxavXfyUw', '2_Tri_2024_Produtos_Planejado')

    # print(utils.create_event.__doc__)
