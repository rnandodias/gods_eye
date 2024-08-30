from datetime import timedelta, datetime, date
import copy
import pandas as pd
import json
# Recursos para o gráfico
import os
import plotly.express as px
import plotly.graph_objs as go

# --------------------------------------------------------------------------------------
# Função para tratamento de datas 
def parse_date(date_str):
    for fmt in ('%Y-%m-%d', '%Y-%m-%dT%H:%M:%SZ'):
        try:
            return datetime.strptime(str(date_str), fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return ''

# --------------------------------------------------------------------------------------
# Função para configurar um evento de agenda 
def configure_updated_events(event, instructor):
    today = datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d')
    start = parse_date(event['start'].get('dateTime', event['start'].get('date')))
    end = parse_date(event['end'].get('dateTime', event['end'].get('date')))

    if 'description' in event:
        description = event['description']
        if 'Programação original: ' in event['description']:
            planejamento = "Planejada"
            start_original = event['description'].split()[2]
            end_original = event['description'].split()[4]
        else:
            planejamento = "Não Planejada"
            start_original = "2000-01-01"
            end_original = "2000-01-02"
    else:
        planejamento = "Não Planejada"
        start_original = "2000-01-01"
        end_original = "2000-01-02"
        description = ""

    atividade = event['summary'].split('-')[-1].strip()

    status = 'Não Iniciada'
    if datetime.strptime(start, '%Y-%m-%d') <= today <= datetime.strptime(end, '%Y-%m-%d') - timedelta(1):
        status = 'Em Progresso'
    elif today < datetime.strptime(start, '%Y-%m-%d'):
        status = 'Não Iniciada'
    elif today > datetime.strptime(end, '%Y-%m-%d') - timedelta(1):
        status = 'Finalizada'

    if 'Evento cancelado' in description:
        status = 'Cancelada'
    elif 'Evento pausado' in description:
        status = 'Pausada'

    return {
        "id": event['id'],
        "Pessoa": instructor,
        "Start": start,
        "End": end,
        "Start Original": start_original,
        "End Original": end_original,
        "Tarefa": event['summary'],
        "Planejamento": planejamento,
        "Anotações": description,
        "Atividade": atividade,
        "Última Atualização": event['updated'],
        "Status": status
    }

# --------------------------------------------------------------------------------------
# Função para identificar a data de entrega da última demanda ou férias 
def find_last_task_or_vacation_date(events):
    try:
        agendas = pd.read_json(json.dumps(events), orient='records')
        agendas = agendas[['Pessoa', 'End']].groupby(by=['Pessoa']).max().reset_index().rename(columns={'Pessoa': 'Instrutor', 'End': 'Final'})
        return agendas
    except Exception as e:
        print(f"Falha ao obter os últimos eventos: {e}")
        return None
    
# --------------------------------------------------------------------------------------
# Função para leitura de planilha do Google Sheets
def read_google_sheets(sheet_id, sheet_name):
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    sheet = pd.read_csv(url)
    return sheet

# --------------------------------------------------------------------------------------
# Função para leitura e tratamento da planilha de PLANEJAMENTO
def read_planning_sheet(sheet_id, sheet_name):
    planning = read_google_sheets(sheet_id, sheet_name)

    # Substituindo os valores nulos da coluna Formação
    # Essa coluna vem da planilha como uma célula mesclada que ocupada todas as linhas de uma formação
    # Este prcedimento substitui os NaN por strings vazias e depois repete o título da formação para as linhas vazias
    planning['Formação'].fillna('', inplace=True)
    for i in range(len(planning)):
        if planning.loc[i, 'Formação']=='':
            planning.loc[i, 'Formação'] = planning.loc[i-1, 'Formação']

    # Este procedimento elimina as linhas que identificam os PASSOS das formações
    planning.drop(planning[planning['Prioridade'].isnull()].index, inplace=True)
    planning['Count'] = 1

    # Este procedimento gera uma solução para quando o conteúdo tem mais de um instrutor
    planning['Grupo Instrutor'] = planning['Instrutor'].str.split(', ')
    planning['Total Instrutor'] = planning['Instrutor'].str.split(', ').str.len()
    planning = planning.explode(['Grupo Instrutor'], ignore_index=True)

    return planning

# --------------------------------------------------------------------------------------
# Função para leitura e tratamento da planilha de PLANEJAMENTO
def read_contacts_sheet(sheet_id, instructors, quarter='2_Tri_2024', sheet_name='F%C3%A9rias'):
    contacts = read_google_sheets(sheet_id, sheet_name)

    contacts=contacts[['Nome', 'Previsão de início', 'Quantidade de dias que irá utilizar', 'Previsão de volta']].copy()
    contacts.rename(columns={'Previsão de início': 'inicio_ferias', 'Quantidade de dias que irá utilizar': 'duracao_ferias', 'Previsão de volta': 'fim_ferias'}, inplace=True)
    contacts.dropna(inplace=True)
    contacts['inicio_ferias'] = pd.to_datetime(contacts['inicio_ferias'], dayfirst=True)
    contacts['fim_ferias'] = pd.to_datetime(contacts['fim_ferias'], dayfirst=True)
    contacts['Nome'] = contacts['Nome'].map(instructors)

    # quarter_ident = pd.Period(f"{quarter.split('_')[-1]}Q{quarter.split('_')[0]}")
    # inicio_trimestre = quarter_ident.start_time
    # fim_trimestre = quarter_ident.end_time

    # filtro = (
    #     (contacts['inicio_ferias'] >= inicio_trimestre) & (contacts['inicio_ferias'] <= fim_trimestre) |
    #     (contacts['fim_ferias'] >= inicio_trimestre) & (contacts['fim_ferias'] <= fim_trimestre)
    # )
    # contacts = contacts[filtro]

    contacts_json = {}
    for i, nome, inicio_ferias, duracao_ferias, fim_ferias in contacts.itertuples():
        if not pd.isna(nome):
            contacts_json.update({
                nome: {
                    'inicio_ferias': str(inicio_ferias)[:10],
                    'duracao_ferias': duracao_ferias,
                    'fim_ferias': str(fim_ferias)[:10]
                }
            })
    return contacts_json

# --------------------------------------------------------------------------------------
# Função para verificar sobreposição de datas (utiliizada para considerar as férias)
def check_overlapping_dates(initial_date, final_date, start_vacation):
    """
    `verifica_sobreposicao(initial_date, final_date, start_vacation)` ► Identifica se alguma atividade tem sobreposição com o período de férias do instrutor
    - `initial_date` ► Determina a data de início da atividade. Deve ser uma string no seguinte formato: `'{yyyy}-{mm}-{dd}'`. Exemplo: `'2024-01-15'`
    - `final_date` ► Determina a data de término da atividade. Deve ser uma string no seguinte formato: `'{yyyy}-{mm}-{dd}'`. Exemplo: `'2024-01-15'`
    - `start_vacation` ► Determina a data de início das férias. Deve ser uma string no seguinte formato: `'{yyyy}-{mm}-{dd}'`. Exemplo: `'2024-01-15'`
    """
    if pd.isnull(start_vacation):
        return False
    if (initial_date <= start_vacation and final_date > start_vacation):
        return True  # Existe sobreposição
    return False  # Não há sobreposição

# --------------------------------------------------------------------------------------
# Função para criar evento para cursos, Alura+ e artigos
def create_event(instructor, type, name, initial_date, vacation=()):
    """
    Programando datas para as entregas das etapas de construção dos conteúdos

    Cursos:
    - Planejamento, pesquisa e estudo em até 5 dias
    - Ementa e projeto prontos e revisados em até 10 dias
    - Planos de aula prontos e revisados em até 10 dias
    - Curso enviado para a edição em até 10 dias
    - Atividades prontas e revisadas em até 10 dias

    Cursos Especiais (produzidos por pessoal externo e gravado por pessoal interno):
    - Estudo em até 10 dias
    - Curso enviado para a edição em até 10 dias

    Cursos Especiais (produzidos por pessoal externo dedicado):
    - Estudo, ementa, projeto e planos de aula em até 7 dias
    - Gravação das aulas e atividades em até 7 dias

    Alura+:
    - Projeto pronto e revisado em até 3 dias
    - Plano de aula pronto e revisado em até 1 dia
    - Alura+ enviado para a edição em até 1 dia

    Artigos:
    - Artigo escrito e revisado em até 5 dias

    Palestra:
    - Material de apresentação e revisado em até 7 dias

    Podcast (nessa categoria entra o Quinta com Dados):
    - Preparação de conteúdo em até 7 dias corridos a partir da sexta-feira anterior ao evento

    `create_event(instructor, type, name, initial_date, vacation=())` ► Gera o JSON que será enviado para a API do Google Calendar com os planejamentos definidos para cada instrutor

        `instructor` ► Nome do instrutor responsável pela atividade

        `type` ► Determina o tipo de conteúdo. Atualmente pode assumir os seguintes valores:
        - 'Curso'
        - 'Curso (E)'
        - 'Alura+'
        - 'Artigo'
        - 'Palestra'
        - 'Podcast'
        
        `name` ► Define o nome da atividade que deve seguir o seguinte padrão:
        - 'Curso' → `{ID do curso} - {Nome do curso}`
        - 'Curso (E)' → `{ID do curso} - {Nome do curso}`
        - 'Alura+' → `{ID do Alura+} - {Nome do Alura+}`
        - 'Artigo' → `{Nome do artigo}`
        - 'Palestra' → `{Nome da palestra}`
        - 'Podcast' → `{Nome do podcast}`

        `initial_date` ► Determina a data de início da atividade. Deve ser uma string no seguinte formato: `'{yyyy}-{mm}-{dd}'`. Exemplo: `'2024-01-15'`

        `vacation` ► É uma tupla que tem como primeiro elemento a data de início das férias e como segundo elemento o número de dias de duração das férias. É um parâmetro opcional da função. Deve seguir o seguinte formato: `('{yyyy}-{mm}-{dd}', dd)`. Exemplo: `('2024-01-15', 15)` (Férias começando no dia 15 de janeiro de 2024 com 15 dias de duração)    
    """
    events = []
    final_date = date(2000, 1, 1)

    if vacation:
        start_of_vacation, vacation_duration = vacation
        year, month, day = [int(item) for item in start_of_vacation.split('-')]
        start_of_vacation = date(year, month, day)
    else:
        start_of_vacation = pd.NaT

    if type == 'Curso':
        steps = [
            'Planejamento, pesquisa e estudo',
            'Ementa e projeto',
            'Planos de aula',
            'Gravação das aulas',
            'Atividades'
        ]
        deadlines = [5, 10, 10, 5, 5]
        color = '9'
    elif type == 'Curso (E)':
        if instructor == 'Victorino': # Quando o curso é produzido por especialista externo em duas etapas de 7 dias cada.
            steps = [
                'Estudo, ementa, projeto e planos de aula',
                'Gravação das aulas e atividades'
            ]
            deadlines = [7, 7]
        elif instructor == 'Sabino': # Quando o curso é produzido por especialista externo em duas etapas de 7 dias cada.
            steps = [
                'Estudo, ementa, projeto e planos de aula',
                'Gravação das aulas e atividades'
            ]
            deadlines = [7, 7]
        else: # Quando o material é todo produzido por especialista externo e as gravações ficam por conta da escola.
            steps = [
                'Estudo',
                'Gravação das aulas'
            ]
            deadlines = [10, 5]
        color = '9'
    elif type == 'Alura+':
        steps = [
            'Projeto',
            'Planos de aula',
            'Gravação'
        ]
        deadlines = [3, 1, 1]
        color = '4'
    elif type == 'Artigo':
        steps = [
            'Escrita'
        ]
        deadlines = [5]
        color = '11'
    elif type == 'Artigo Pilar':
        steps = [
            'Escrita'
        ]
        deadlines = [5]
        color = '6'
    elif type == 'Imersão':
        steps = [
            'Suporte'
        ]
        deadlines = [5]
        color = '8'
    elif type == 'Palestra':
        steps = [
            'Material de apresentação',
            'Dia do evento'
        ]
        deadlines = [6, 1]
        color = '5'
    elif type == 'Podcast' or type == 'Quinta com Dados':
        steps = [
            'Preparação para o evento',
            'Dia do evento'
        ]
        deadlines = [6, 1]
        color = '10'
    elif type == 'TechGuide':
        steps = [
            'Atualização/Criação do guia',
            'Entrega'
        ]
        deadlines = [11, 1]
        color = '1'
    else:
        steps = []
        deadlines = []
        color = ''

    for i, step in enumerate(steps):
        if i == 0:
            year, month, day = [int(item) for item in initial_date.split('-')]
            initial_date = date(year, month, day)
            if initial_date.weekday() in [5, 6]:
                initial_date += timedelta(days=7 - initial_date.weekday())
            final_date = initial_date + timedelta(days=deadlines[0])
        else:
            initial_date = final_date
            # if initial_date.weekday() in [5, 6]:
            #     initial_date += timedelta(days=7 - initial_date.weekday())
            final_date = initial_date + timedelta(days=deadlines[i])

        base_event = {
            'summary': f'{type} - {name} - {step}',
            'description': f'Programação original: {str(initial_date)} até {str(final_date)}',
            'start': {
                'date': str(initial_date),
                'timeZone': 'America/Sao_Paulo',
            },
            'end': {
                'date': str(final_date),
                'timeZone': 'America/Sao_Paulo',
            },
            'colorId': color,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 24 * 60},
                ],
            },
        }

        if check_overlapping_dates(initial_date, final_date, start_of_vacation):
            if (initial_date != start_of_vacation):
                evento_inicial = copy.deepcopy(base_event)
                evento_inicial['start']['date'] = str(initial_date)
                evento_inicial['end']['date'] = str(start_of_vacation)
                evento_inicial['description'] = f'Programação original: {str(initial_date)} até {str(start_of_vacation)}'
                events.append(evento_inicial)

            vacation = copy.deepcopy(base_event)
            vacation['summary'] = 'Férias'
            vacation['start']['date'] = str(start_of_vacation)
            vacation['end']['date'] = str(start_of_vacation + timedelta(days=vacation_duration))
            vacation['description'] = f'Programação original: {str(start_of_vacation)} até {str(start_of_vacation + timedelta(days=vacation_duration))}'
            vacation['colorId'] = '2'
            events.append(vacation)

            evento_final = copy.deepcopy(base_event)
            evento_final['start']['date'] = str(start_of_vacation + timedelta(days=vacation_duration))
            evento_final['end']['date'] = str(final_date + timedelta(days=vacation_duration))
            evento_final['description'] = f'Programação original: {str(start_of_vacation + timedelta(days=vacation_duration))} até {str(final_date + timedelta(days=vacation_duration))}'
            events.append(evento_final)

            final_date = final_date + timedelta(days=vacation_duration)
        else:
            events.append(base_event)

    return events, str(final_date)

# --------------------------------------------------------------------------------------
# Função para alterar a prioridade de um ou mais eventos de um ou mais instrutores
def prioritize_events(plan, input):
    """
    `prioritize_events(plan, input)` ► Função para alterar a prioridade de um ou mais eventos de um ou mais instrutores
        `plan` ► DataFrame Pandas contendo o planejamento completo do período.
        `input` ► Lista de tuplas com as informações do instrutor e do conteúdo que será desenvolvido e que precisa alterar a prioridade.
            Exemplo:
            [('Instrutor A', 'Conteúdo A'), ('Instrutor B', 'Conteúdo B'), ('Instrutor C', 'Conteúdo C')]
    """
    for instructor, content in input:
        auxiliar = plan.query(f'`Grupo Instrutor` == "{instructor}" and Conteúdos == "{content}"').copy()
        indice = plan.query(f'`Grupo Instrutor` == "{instructor}" and Conteúdos == "{content}"').index
        plan.drop(indice, axis=0, inplace=True)
        plan = pd.concat([auxiliar, plan])

    return plan

# --------------------------------------------------------------------------------------
# Função para criar o JSON com todas as agendas dos instrutores e suas atividades planejadas
def create_agenda(start_work_cycle, plan, instructors, last_task_or_vacation_date, ferias_compilado):
    year, month, day = [int(item) for item in start_work_cycle.split('-')]
    start_work_cycle = date(year, month, day)

    # if vacation:
    #     start_of_vacation, vacation_duration = vacation
    #     year, month, day = [int(item) for item in start_of_vacation.split('-')]
    #     start_of_vacation = date(year, month, day)
    # else:
    #     start_of_vacation = pd.NaT

    # str(start_of_vacation + timedelta(days=vacation_duration))

    scheduling = {}
    for instructor in instructors:
        agenda = []
        try:
            if last_task_or_vacation_date is not None:
                ultima_entrega = pd.to_datetime(last_task_or_vacation_date.query('Instrutor == @instructor')['Final'].values[0])
                ultima_entrega = date(ultima_entrega.year, ultima_entrega.month, ultima_entrega.day)
            else:
                ultima_entrega = start_work_cycle

            if ultima_entrega > start_work_cycle:
                inicio = str(ultima_entrega)
            else:
                inicio = str(start_work_cycle)
        except:
            inicio = str(start_work_cycle)

        for i in plan.query('Prioridade in ["Alta", "Média"] and `Grupo Instrutor` in @instructors and `Status Atual` not in ["Pós-produção", "Finalizado"]').sort_values(by=['Grupo Instrutor', 'Prioridade']).index:
            if plan['Grupo Instrutor'][i] == instructor:
                try:
                    ferias = (ferias_compilado[instructor]['inicio_ferias'], ferias_compilado[instructor]['duracao_ferias'])
                except:
                    ferias = ()
                # print(instructor, '->', ferias, '->', ultima_entrega)
                if plan['Tipo'][i] == 'Quinta com Dados' or plan['Tipo'][i] == 'Palestra' or plan['Tipo'][i] == 'Podcast':
                    year, month, day = [int(item) for item in plan['Conteúdos'][i].split()[-1].replace('[', '').replace(']', '').split('-')]
                    evento, _ = create_event(instructor, plan['Tipo'][i], plan['Conteúdos'][i], str(date(year, month, day) - timedelta(days=6)), ferias)
                elif plan['Tipo'][i] == 'TechGuide' or plan['Tipo'][i] == 'Imersão':
                    year, month, day = [int(item) for item in plan['Conteúdos'][i].split()[-1].replace('[', '').replace(']', '').split('-')]
                    evento, _ = create_event(instructor, plan['Tipo'][i], plan['Conteúdos'][i], str(date(year, month, day)), ferias)
                else:
                    evento, inicio = create_event(instructor, plan['Tipo'][i], plan['Conteúdos'][i], inicio, ferias)

                agenda.append(
                    evento
                )
        scheduling.update({instructor: agenda})

        agendas = []
        for pessoa, products in scheduling.items():
            for product in products:
                for item in product:
                    agendas.append({
                        "Pessoa": pessoa,
                        "Start": item["start"]["date"],
                        "End": item["end"]["date"],
                        "Tarefa": item['summary']
                    })

    # with open('agendas_3_tri_2024.json', 'w') as arquivo_json:
    #     json.dump(agendas, arquivo_json)
    # # print(agendas)
    # create_timeline(scheduling, "Organização do Planejamento 3 Tri 2024")

    # df = pd.DataFrame(agendas)
    # df['End'] = pd.to_datetime(df['End'])

    # # df['Semana'] = df['End'].dt.isocalendar().week
    # df['Ano'] = df['End'].dt.year
    # df['Mês'] = df['End'].dt.month
    # df['Produto'] = df['Tarefa'].apply(lambda x: x.split(' - ')[0])
    # df['Atividade'] = df['Tarefa'].apply(lambda x: x.split(' - ')[-1])
    # # tabela_resumo = df.groupby('Semana', 'Atividade').agg({'Soma': 'count'}).reset_index()
    # # print(df)
    # # # tabela_resumo.columns = ['Semana', 'Atividade', 'Soma']
    # # # df.groupby(by=['Semana', 'Atividade'])['Id'].count().reset_index()
    # data_corte = pd.to_datetime('2024-07-01')
    # df = df[df['End']>= data_corte]
    # df = df.query('Produto in ["Curso"]')
    # df['Count'] = 1

    # # tabela_pivot = df.pivot_table(index=['Ano', 'Mês', 'Semana'], columns=['Tarefa'], values='Count', aggfunc='sum', fill_value='-')
    # tabela_pivot = df.pivot_table(index=['Ano', 'Mês'], columns=['Atividade'], values='Count', aggfunc='sum', fill_value='-')

    # tabela_pivot = tabela_pivot.sort_index()

    # print(tabela_pivot)

    # with open('agendas_3_tri_2024.json', 'w') as arquivo_json:
    #     json.dump(scheduling, arquivo_json)

    return scheduling

# --------------------------------------------------------------------------------------
# Cria e configura o DataFrame que servirá de input para construção da timeline
def create_timeline(quarterly_planning_events_json, filename):
    timeline = []
    for pessoa in quarterly_planning_events_json:
        for agenda in quarterly_planning_events_json[pessoa]:
            for etapa in agenda:
                timeline.append(
                    dict(
                        Tarefa=' - '.join([item.strip() for item in etapa['summary'].split('-')[:-1]]),
                        Atividade=etapa['summary'].split('-')[-1].strip(),
                        Início=etapa['start']['date'],
                        Término=etapa['end']['date'],
                        Responsável=pessoa,
                        Descrição=etapa['summary'],
                        Produto=etapa['summary'].split('-')[0].strip()
                    )
                )
    df = pd.DataFrame(timeline)

    mapeamento_atividades = {
        'Estudo, ementa, projeto e planos de aula': 'Estruturação',
        'Gravação das aulas e atividades': 'Gravação e atividades',
        'Planos de aula': 'Planos de aula',
        'Atividades': 'Atividades',
        'Planejamento, pesquisa e estudo': 'Estudo',
        'Estudo': 'Estudo',
        'Ementa e projeto': 'Projeto',
        'Gravação das aulas': 'Gravação',
        'Escrita': 'Escrita',
        'Projeto': 'Projeto',
        'Gravação': 'Gravação',
        'Material de apresentação': 'Material',
        'Férias': 'Férias',
        'Apresentação': 'Palestra',
        'Desenvolvimento': 'PDI',
        'Palestrando dados': 'Palestrando Dados',
        'Preparação para o evento': 'Preparação',
        'Dia do evento': 'Evento',
        'Suporte': 'Suporte',
        'Atualização/Criação do guia': 'Desenvolvimento',
        'Entrega': 'Entrega'
    }

    df['Atividade'] = df['Atividade'].map(mapeamento_atividades)
    df.sort_values(by=['Responsável', 'Início'], ignore_index=True, inplace=True)
    config_timeline(df, filename)
    return df

# --------------------------------------------------------------------------------------
# Cria a timeline com as atividades programadas
def config_timeline(df, nome):
    produtos = ['Curso', 'Curso (E)', 'Artigo', 'Artigo Pilar', 'Alura+', 'Férias', 'Palestra', 'Quinta com Dados', 'TechGuide', 'Podcast', 'Imersão']
    hoje = datetime.now()
    inicio_tri = '2024-04-01'
    fim_tri = '2024-06-30'
    hoje_formatado = hoje.strftime("%Y-%m-%d")
    orders = list(df['Tarefa'])
    fig = px.timeline(
        df,
        x_start="Início",
        x_end="Término",
        y="Responsável",
        hover_name="Tarefa",
        color_discrete_sequence=['#636EFA', '#636EFA', '#DC2127', '#DC2127', '#D75413', '#008800', '#FFFF00', '#E1E1E1', '#E1E1E1', '#E1E1E1', '#E1E1E1'],
        category_orders={'Produto': produtos},
        opacity=.7,
        text="Atividade",
        range_x=None,
        range_y=None,
        template='plotly_dark',
        height=600,
        color='Produto'
    )

    fig.update_layout(
        font=dict(
            family="Arial",
            size=24,
            color="darkgray"
        ),
        xaxis_range=[df['Início'].min(), df['Término'].max()],
        xaxis = dict(
            title="",
            showgrid=True,
            rangeslider_visible=False,
            side ="bottom",
            tickmode = 'array',
            tickformat="%d/%b \n",
            ticklabelmode="period",
            ticks="outside",
            tickson="boundaries",
            tickwidth=.1,
            layer='below traces',
            ticklen=20,
            tickfont=dict(
                family='Arial',
                size=24,
                color='darkgray'
            ),
            rangeselector=dict(
                buttons=list([
                    dict(count=7, label="1 semana", step="day", stepmode="backward"),
                    dict(count=1, label="1 mês", step="month", stepmode="backward"),
                    dict(count=3, label="3 meses", step="month", stepmode="backward"),
                    dict(step="all", label="Tudo")
                ]),
                x=.37,
                y=-.2,
                font=dict(
                    family="Arial",
                    size=14,
                    color="darkgray"
                )
            )
        ),
        yaxis = dict(
            title= "Pessoas Instrutoras",
            autorange="reversed",
            automargin=True,
            anchor="free",
            ticklen=10,
            showgrid=True,
            showticklabels=True,
            tickfont=dict(
                family='Arial',
                size=16,
                color='darkgray'
            )
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.0,
            title="",
            xanchor="right",
            x=1,
            font=dict(
                family="Arial",
                size=14,
                color="darkgray"
            )
        )
    )

    fig.update_traces(
        marker_line_color='rgb(8,48,107)',
        marker_line_width=1.5,
        opacity=0.95,
        textposition='inside',
        insidetextanchor='middle'
    )

    fig.add_vline(x=inicio_tri, line_width=2, line_color="white")

    fig.add_vline(x=hoje_formatado, line_width=3, line_color="red")

    fig.add_vline(x=fim_tri, line_width=2, line_color="white")

    fig.write_html(nome + ".html")
    go.FigureWidget(fig)
    fig.show()