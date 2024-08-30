from datetime import timedelta, datetime
import openai
from dotenv import load_dotenv
import os
import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------
# Função para retornar cumprimentos
# --------------------------------------------------------------------------------------
def greeting(hour):
    if 5 <= hour < 12:
        greeting = "Bom dia"
    elif 12 <= hour < 18:
        greeting = "Boa tarde"
    else:
        greeting = "Boa noite"

    return greeting

# --------------------------------------------------------------------------------------
# Função para retornar cumprimentos
# --------------------------------------------------------------------------------------
def create_feedback_file(file_name, content):
    file_path = f"docs/feedback/{file_name}.md"
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)
    return file_path

# --------------------------------------------------------------------------------------
# Função para retornar a data mais antiga e a mais recente em uma lista de datas no formato string
# --------------------------------------------------------------------------------------
def min_max_dates(lst_dates):
    datas = [datetime.strptime(data, "%Y-%m-%d") for data in lst_dates]

    start_date = min(datas)
    end_date = max(datas)

    return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

# --------------------------------------------------------------------------------------
# Função para criar uma avaliação de desempenho com o ChatGPT
# --------------------------------------------------------------------------------------
def report(prompt):
    try:
        load_dotenv()
        client = openai.OpenAI(api_key=os.getenv('OPENAI_CREDENTIALS'))
        response = client.chat.completions.create(
            model = "gpt-4",
            messages = [{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content
    except Exception as e:
        print(f"Erro ao realizar o backup: {e}")
        return ""

# --------------------------------------------------------------------------------------
# Função para definir os ícones dos produtos
# --------------------------------------------------------------------------------------
def icons(produto):
    if produto in ['Alura+']:
        icon_url = "https://storage.googleapis.com/alura-images/atividades/icons/icon-alura-mais.svg"
    elif produto in ['Artigo', 'Artigo Pilar']:
        icon_url = "https://storage.googleapis.com/alura-images/atividades/icons/icon-articles.svg"
    elif produto in ['Curso', 'Curso (E)', 'Formação']:
        icon_url = "https://storage.googleapis.com/alura-images/atividades/icons/icon-formacoes.svg"
        # icon_url = "https://storage.googleapis.com/alura-images/atividades/icons/stats-courses.svg"
    elif produto in ['Imersão']:
        icon_url = "https://storage.googleapis.com/alura-images/atividades/icons/icon-imersoes.svg"
    elif produto in ['Podcast', 'Quinta com Dados', 'Palestra']:
        icon_url = "https://storage.googleapis.com/alura-images/atividades/icons/icon-podcasts.svg"
    elif produto in ['TechGuide']:
        icon_url = "https://storage.googleapis.com/alura-images/atividades/icons/icon-techguide.svg"
    elif produto in ['Demanda Interna']:
        icon_url = "https://www.notion.so/icons/hammer_green.svg"
    elif produto in ['PDI']:
        icon_url = "https://www.notion.so/icons/brain_green.svg"
    elif produto in ['Férias']:
        icon_url = "https://www.notion.so/icons/palm-tree_green.svg"
    else:
        icon_url = "https://www.notion.so/icons/science_green.svg"

    return icon_url

# --------------------------------------------------------------------------------------
# Função para criar os deadlines dos cursos
# --------------------------------------------------------------------------------------
def get_deadline(database):
    rows = []
    for page in database:
        code = page['properties']['Código do Produto']['rich_text'][0]['text']['content']
        product = page['properties']['Produto']['rich_text'][0]['text']['content']
        end = page["properties"]["Período Realizado"]["date"]["end"]
        if product in ["Curso", "Curso (E)"]:
            rows.append([code, product, end])

    df = pd.DataFrame(rows, columns=['code', 'product', 'end'])
    df["end"] = pd.to_datetime(df["end"])
    df["deadline"] = df.groupby(['code', 'product'])['end'].transform('max').dt.strftime('%Y-%m-%d')

    return df

# --------------------------------------------------------------------------------------
# Função para obter um valor de um DataFrame
# --------------------------------------------------------------------------------------
def get_value(df, condition, column):
    try:
        result = df.loc[condition, column]
        if result.empty:
            return ""
        return result.values[0]
    except IndexError:
        return ""

# --------------------------------------------------------------------------------------
# Função para tratar e criar os dados que serão utilizados na atualização do database de tarefas
# --------------------------------------------------------------------------------------
def data_input(database_id, deadlines, item):
    # --------------------------------------------------------------------------------------
    # Criando as informações de Código e Título das atividades
    # Obs.: Somente Cursos, Cursos Especiais e Alura+ têm códigos
    codigo = ""
    titulo = ""
    if item['Tarefa'].split('-')[0].strip() in ['Curso', 'Curso (E)', 'Alura+']:
        codigo = item['Tarefa'].split('-')[1].strip()
        titulo = '-'.join(item['Tarefa'].split('-')[2:-1]).strip()
    else:
        codigo = ""
        titulo = '-'.join(item['Tarefa'].split('-')[1:-1]).strip()

    # --------------------------------------------------------------------------------------
    # Criando um contador de tempo (em dias) de execução das atividades
    # Obs.: Finais de semana são contabilizados
    if item['Status'] == 'Finalizada':
        tempo_gasto = (datetime.strptime(item['End'], '%Y-%m-%d') - datetime.strptime(item['Start'], '%Y-%m-%d')).days
    elif item['Status'] == 'Em Progresso':
        tempo_gasto = (datetime.strptime(datetime.now().strftime('%Y-%m-%d'), '%Y-%m-%d') - datetime.strptime(item['Start'], '%Y-%m-%d')).days + 1
    else:
        tempo_gasto = 0

    # --------------------------------------------------------------------------------------
    # Criando um contador de tempo (em dias úteis) de execução das atividades
    # Obs.: Finais de semana não são contabilizados
    if item['Status'] == 'Finalizada':
        tempo_gasto_sem_fds = int(np.busday_count(datetime.strptime(item['Start'], '%Y-%m-%d').date(), datetime.strptime(item['End'], '%Y-%m-%d').date()))
    elif item['Status'] == 'Em Progresso':
        tempo_gasto_sem_fds = int(np.busday_count(datetime.strptime(item['Start'], '%Y-%m-%d').date(), datetime.now().date() + timedelta(days=1)))
    else:
        tempo_gasto_sem_fds = 0

    # --------------------------------------------------------------------------------------
    # Obtendo o deadline dos cursos
    # deadline = datetime.strptime(get_value(deadlines, deadlines['code'] == codigo, 'deadline'), "%Y-%m-%d")
    deadline = get_value(deadlines, deadlines['code'] == codigo, 'deadline')

    # --------------------------------------------------------------------------------------
    # Definindo os ícones e imagens das páginas do database
    produto = item['Tarefa'].split('-')[0].strip()

    properties = {
        "Id": {"rich_text": [{"text": {"content": f"{item['id']}"}}]},
        "Instrutor(a)": {"rich_text": [{"text": {"content": f"{item['Pessoa']}"}}]},
        "Status": {"select": {"name": f"{item['Status']}"}},
        "Tarefa": {"title": [{"text": {"content": f"{item['Tarefa']}"}}]},
        "Período Planejado": {"date": {"start": f"{item['Start Original']}", "end": f"{(datetime.strptime(item['End Original'], '%Y-%m-%d') - timedelta(1)).strftime('%Y-%m-%d')}"}},
        "Período Realizado": {"date": {"start": f"{item['Start']}", "end": f"{(datetime.strptime(item['End'], '%Y-%m-%d') - timedelta(1)).strftime('%Y-%m-%d')}"}},
        "Anotações": {"rich_text": [{"text": {"content": f"{item['Anotações']}"}}]},
        "Atividade": {"rich_text": [{"text": {"content": f"{item['Atividade']}"}}]},
        "Produto": {"rich_text": [{"text": {"content": produto}}]},
        "Última Atualização": {"date": {"start": f"{item['Última Atualização']}"}},
        "Planejamento": {"select": {"name": f"{item['Planejamento']}"}},
        "Código do Produto": {"rich_text": [{"text": {"content": f"{codigo}"}}]},
        "Título do Produto": {"rich_text": [{"text": {"content": f"{titulo}"}}]},
        "Tempo Gasto (em Dias)": {"number": tempo_gasto},
        "Tempo Gasto (em Dias Úteis)": {"number": tempo_gasto_sem_fds}
    }

    if deadline != "":
        properties.update({"Deadline": {"date": {"start": f"{deadline}", "end": f"{deadline}"}}})

    return {
        "parent": {"type": "database_id", "database_id": f"{database_id}"},
        # "cover": {"type": "external", "external": {"url": "https://storage.googleapis.com/alura-images/resultados/escola_de_dados/Escola_de_dados_01.jpg"}},
        "icon": {"type": "external", "external": {"url": icons(produto)}},
        "properties": properties
    }

# --------------------------------------------------------------------------------------
# Função para configurar o database de conteúdos produzidos
# --------------------------------------------------------------------------------------
def data_produced_content_create(page_id):
    return {
        "parent": {"type": "page_id", "page_id": f"{page_id}"},
        "is_inline": True,
        "title": [{"type": "text", "text": {"content": "Conteúdos Produzidos", "link": None}}],
        "properties": {
            "Produto": {"rich_text": {}},
            "Código do Produto": {"rich_text": {}},
            "Título do Produto": {"type": "title", "title": {}},
            "Nome na Plataforma": {"rich_text": {}},
            "Instrutor(a)": {"rich_text": {}},
            "Período de Produção": {"type": "date", "date": {}},
            "Tempo de Produção (em Dias)": {"type": "number", "number": {}},
            "Link": {"type": "url", "url": {}}
        }
    }

# --------------------------------------------------------------------------------------
# Função para configurar o database de avaliação de competências
# --------------------------------------------------------------------------------------
def data_competency_assessment_create(page_id):
    return {
        "parent": {"type": "page_id","page_id": f"{page_id}"},
        "is_inline": True,
        "title": [{"type": "text","text": {"content": "Avaliação de Competências","link": None}}],
        "properties": {
            "Tarefa": {"type": "title","title": {}},
            "Id": {"rich_text": {}},
            # "Produto": {"rich_text": {}},
            # "Código do Produto": {"rich_text": {}},
            # "Título do Produto": {"rich_text": {}},
            # "Instrutor(a)": {"rich_text": {}},
            # "Atividade": {"rich_text": {}},
            "Dedicação": {
                "select": {
                    "options": [
                        {"name": "1. Demonstra interesse mínimo em suas responsabilidades como instrutor.", "color": "red"},
                        {"name": "2. Mostra interesse em suas responsabilidades e realiza suas tarefas de forma consistente.", "color": "orange"},
                        {"name": "3. Mostra um alto nível de comprometimento e dedicação em suas responsabilidades.", "color": "yellow"},
                        {"name": "4. Demonstra um comprometimento excepcional e paixão por suas responsabilidades como instrutor.", "color": "green"},
                    ]
                }
            },
            "Cumprimento de acordos": {
                "select": {
                    "options": [
                        {"name": "1. Frequentemente não cumpre prazos ou compromissos estabelecidos.", "color": "red"},
                        {"name": "2. Geralmente cumpre prazos e compromissos estabelecidos.", "color": "orange"},
                        {"name": "3. Sempre cumpre prazos e compromissos estabelecidos de maneira confiável.", "color": "yellow"},
                        {"name": "4. É extremamente confiável e sempre cumpre prazos e compromissos.", "color": "green"},
                    ]
                }
            },
            "Qualidade das entregas": {
                "select": {
                    "options": [
                        {"name": "1. As entregas têm muitos erros e não atendem aos padrões mínimos de qualidade.", "color": "red"},
                        {"name": "2. As entregas são satisfatórias embora possam ocasionalmente conter erros menores.", "color": "orange"},
                        {"name": "3. As entregas são sempre de alta qualidade atendendo ou excedendo os padrões estabelecidos.", "color": "yellow"},
                        {"name": "4. As entregas são de nível superior refletindo um alto padrão de excelência e inovação.", "color": "green"},
                    ]
                }
            },
            "Velocidade": {
                "select": {
                    "options": [
                        {"name": "1. Realiza tarefas de forma lenta e com pouca eficiência.", "color": "red"},
                        {"name": "2. Realiza tarefas em um ritmo razoável e dentro dos prazos definidos.", "color": "orange"},
                        {"name": "3. Realiza tarefas de forma rápida e eficiente sem comprometer a qualidade.", "color": "yellow"},
                        {"name": "4. Realiza tarefas de forma extremamente rápida mantendo altos padrões de qualidade.", "color": "green"},
                    ]
                }
            },
            "Resposta aos feedbacks": {
                "select": {
                    "options": [
                        {"name": "1. Tem dificuldade em aceitar feedbacks e pouco esforço é feito para melhorar.", "color": "red"},
                        {"name": "2. Aceita feedbacks de forma construtiva e faz esforços para melhorar.", "color": "orange"},
                        {"name": "3. Aceita e implementa feedbacks de forma proativa buscando constantemente melhorar seu desempenho.", "color": "yellow"},
                        {"name": "4. Valoriza e integra feedbacks de forma excepcional mostrando desejo contínuo por desenvolvimento.", "color": "green"},
                    ]
                }
            },
            "Flexibilidade": {
                "select": {
                    "options": [
                        {"name": "1. Resiste a mudanças e tem dificuldade em se adaptar a novas situações.", "color": "red"},
                        {"name": "2. É capaz de se adaptar a mudanças e novas situações com alguma orientação.", "color": "orange"},
                        {"name": "3. Adapta-se facilmente a mudanças e é capaz de lidar com diversas situações sem dificuldade.", "color": "yellow"},
                        {"name": "4. Mostrou habilidade excepcional em se adaptar a qualquer situação e liderar mudanças efetivamente.", "color": "green"},
                    ]
                }
            },
            "Colaboração": {
                "select": {
                    "options": [
                        {"name": "1. Tende a trabalhar de forma isolada e não contribui para o trabalho em equipe.", "color": "red"},
                        {"name": "2. Trabalha bem em equipe e contribui para objetivos compartilhados.", "color": "orange"},
                        {"name": "3. Colabora efetivamente com colegas e lidera iniciativas de equipe quando necessário.", "color": "yellow"},
                        {"name": "4. É um líder colaborativo capaz de inspirar e motivar colegas para alcançar objetivos comuns.", "color": "green"},
                    ]
                }
            },
            "Comunicação": {
                "select": {
                    "options": [
                        {"name": "1. Comunicação é confusa e não eficaz.", "color": "red"},
                        {"name": "2. Comunica de forma clara e eficaz na maioria das situações.", "color": "orange"},
                        {"name": "3. Comunica de forma clara e concisa em uma variedade de contextos.", "color": "yellow"},
                        {"name": "4. Comunica de forma envolvente e persuasiva inspirando e influenciando os outros.", "color": "green"},
                    ]
                }
            },
            "Assiduidade": {
                "select": {
                    "options": [
                        {"name": "1. Ausências frequentes e falta de comprometimento com os horários.", "color": "red"},
                        {"name": "2. Comparece regularmente e cumpre os horários de trabalho.", "color": "orange"},
                        {"name": "3. É altamente confiável em relação à presença e pontualidade.", "color": "yellow"},
                        {"name": "4. É um exemplo de pontualidade e presença consistente.", "color": "green"},
                    ]
                }
            }
        }
    }

# --------------------------------------------------------------------------------------
# Função para configurar o database de resultados gerais da avaliação de competências
# --------------------------------------------------------------------------------------
def data_results_competency_assessment_create(page_id):
    return {
        "parent": {"type": "page_id","page_id": f"{page_id}"},
        "is_inline": True,
        "title": [{"type": "text","text": {"content": "Avaliação de Competências dos Instrutores","link": None}}],
        "properties": {
            "Instrutor(a)": {"type": "title","title": {}},
            # "Id": {"rich_text": {}},
            # "Atividade": {"rich_text": {}},
            "Dedicação": {
                "select": {
                    "options": [
                        {"name": "1. Demonstra interesse mínimo em suas responsabilidades como instrutor.", "color": "red"},
                        {"name": "2. Mostra interesse em suas responsabilidades e realiza suas tarefas de forma consistente.", "color": "orange"},
                        {"name": "3. Mostra um alto nível de comprometimento e dedicação em suas responsabilidades.", "color": "yellow"},
                        {"name": "4. Demonstra um comprometimento excepcional e paixão por suas responsabilidades como instrutor.", "color": "green"},
                    ]
                }
            },
            "Cumprimento de acordos": {
                "select": {
                    "options": [
                        {"name": "1. Frequentemente não cumpre prazos ou compromissos estabelecidos.", "color": "red"},
                        {"name": "2. Geralmente cumpre prazos e compromissos estabelecidos.", "color": "orange"},
                        {"name": "3. Sempre cumpre prazos e compromissos estabelecidos de maneira confiável.", "color": "yellow"},
                        {"name": "4. É extremamente confiável e sempre cumpre prazos e compromissos.", "color": "green"},
                    ]
                }
            },
            "Qualidade das entregas": {
                "select": {
                    "options": [
                        {"name": "1. As entregas têm muitos erros e não atendem aos padrões mínimos de qualidade.", "color": "red"},
                        {"name": "2. As entregas são satisfatórias embora possam ocasionalmente conter erros menores.", "color": "orange"},
                        {"name": "3. As entregas são sempre de alta qualidade atendendo ou excedendo os padrões estabelecidos.", "color": "yellow"},
                        {"name": "4. As entregas são de nível superior refletindo um alto padrão de excelência e inovação.", "color": "green"},
                    ]
                }
            },
            "Velocidade": {
                "select": {
                    "options": [
                        {"name": "1. Realiza tarefas de forma lenta e com pouca eficiência.", "color": "red"},
                        {"name": "2. Realiza tarefas em um ritmo razoável e dentro dos prazos definidos.", "color": "orange"},
                        {"name": "3. Realiza tarefas de forma rápida e eficiente sem comprometer a qualidade.", "color": "yellow"},
                        {"name": "4. Realiza tarefas de forma extremamente rápida mantendo altos padrões de qualidade.", "color": "green"},
                    ]
                }
            },
            "Resposta aos feedbacks": {
                "select": {
                    "options": [
                        {"name": "1. Tem dificuldade em aceitar feedbacks e pouco esforço é feito para melhorar.", "color": "red"},
                        {"name": "2. Aceita feedbacks de forma construtiva e faz esforços para melhorar.", "color": "orange"},
                        {"name": "3. Aceita e implementa feedbacks de forma proativa buscando constantemente melhorar seu desempenho.", "color": "yellow"},
                        {"name": "4. Valoriza e integra feedbacks de forma excepcional mostrando desejo contínuo por desenvolvimento.", "color": "green"},
                    ]
                }
            },
            "Flexibilidade": {
                "select": {
                    "options": [
                        {"name": "1. Resiste a mudanças e tem dificuldade em se adaptar a novas situações.", "color": "red"},
                        {"name": "2. É capaz de se adaptar a mudanças e novas situações com alguma orientação.", "color": "orange"},
                        {"name": "3. Adapta-se facilmente a mudanças e é capaz de lidar com diversas situações sem dificuldade.", "color": "yellow"},
                        {"name": "4. Mostrou habilidade excepcional em se adaptar a qualquer situação e liderar mudanças efetivamente.", "color": "green"},
                    ]
                }
            },
            "Colaboração": {
                "select": {
                    "options": [
                        {"name": "1. Tende a trabalhar de forma isolada e não contribui para o trabalho em equipe.", "color": "red"},
                        {"name": "2. Trabalha bem em equipe e contribui para objetivos compartilhados.", "color": "orange"},
                        {"name": "3. Colabora efetivamente com colegas e lidera iniciativas de equipe quando necessário.", "color": "yellow"},
                        {"name": "4. É um líder colaborativo capaz de inspirar e motivar colegas para alcançar objetivos comuns.", "color": "green"},
                    ]
                }
            },
            "Comunicação": {
                "select": {
                    "options": [
                        {"name": "1. Comunicação é confusa e não eficaz.", "color": "red"},
                        {"name": "2. Comunica de forma clara e eficaz na maioria das situações.", "color": "orange"},
                        {"name": "3. Comunica de forma clara e concisa em uma variedade de contextos.", "color": "yellow"},
                        {"name": "4. Comunica de forma envolvente e persuasiva inspirando e influenciando os outros.", "color": "green"},
                    ]
                }
            },
            "Assiduidade": {
                "select": {
                    "options": [
                        {"name": "1. Ausências frequentes e falta de comprometimento com os horários.", "color": "red"},
                        {"name": "2. Comparece regularmente e cumpre os horários de trabalho.", "color": "orange"},
                        {"name": "3. É altamente confiável em relação à presença e pontualidade.", "color": "yellow"},
                        {"name": "4. É um exemplo de pontualidade e presença consistente.", "color": "green"},
                    ]
                }
            }
        }
    }

# --------------------------------------------------------------------------------------
# Função para configurar o database de resultados com as Atividades Planejadas X Não Planejadas
# --------------------------------------------------------------------------------------
def data_statistics_planning_create(page_id):
    return {
        "parent": {"type": "page_id","page_id": f"{page_id}"},
        "is_inline": True,
        "title": [{"type": "text","text": {"content": "Atividades Planejadas X Não Planejadas","link": None}}],
        "properties": {
            "Instrutor(a)": {"type": "title","title": {}},
            "Não Planejada": {"number": {}},
            "Planejada": {"number": {}},
            "% de Demandas Não Planejadas": {"rich_text": {}},
        }
    }

# --------------------------------------------------------------------------------------
# Função para organizar os feedback dos instrutores no formato de texto
# --------------------------------------------------------------------------------------
def organizes_feedback(json_feedback):
    formatted_text = f"--------------------------------------------------------------------------------------------\n"
    for item in json_feedback:
        for key, value in item.items():
            parts = key.split(' - ')
            if len(parts) == 4:
                produto = parts[0]
                codigo = parts[1]
                titulo = parts[2]
                atividade = parts[3]
            elif len(parts) == 3:
                produto = parts[0]
                codigo = '-'
                titulo = parts[1]
                atividade = parts[2]
            else:
                produto = '-'
                codigo = '-'
                titulo = parts
                atividade = '-'

            feedback = value
            
            formatted_text += f"Produto: {produto}\n"
            formatted_text += f"Código: {codigo}\n"
            formatted_text += f"Título: {titulo}\n"
            formatted_text += f"Atividade: {atividade}\n"
            formatted_text += f"Feedback: {feedback}\n"
            formatted_text += f"--------------------------------------------------------------------------------------------\n"
    
    return formatted_text

# --------------------------------------------------------------------------------------
# Função para dividir um texto em blocos de 2000 caracteres sem partir palavras
# --------------------------------------------------------------------------------------
def split_text_into_blocks(text, limit=2000):
    start = 0
    text = str(text)
    while start < len(text):
        if len(text) - start <= limit:
            yield text[start:]
            break
        end = text.rfind(' ', start, start + limit)
        if end == -1:
            end = start + limit
        yield text[start:end]
        start = end + 1

# --------------------------------------------------------------------------------------
# Função para retornar os blocos de texto em parte para a API do Notion
# --------------------------------------------------------------------------------------
def create_text_blocks(blocks):
    return [
        {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": str(block)}}
                ]
            }
        } for block in blocks
    ]

# --------------------------------------------------------------------------------------
# Função para configurar o prompt para construção das avaliações de desempenho
# --------------------------------------------------------------------------------------
def prompt_create_report(data):
    return f'''
    Os textos abaixo são o resultado do acompanhamento trimestral de um instrutor de uma escola que cria cursos on-line para a área de data science, machine learning, business intelligance, engenharia de dados e áreas correlatas. Este texto está no formato JSON e possui a seguinte estrutura:

    [{{"Título da Tarefa":"Texto do Acompanhamento"}}, {{"Título da Tarefa":"Texto do Acompanhamento"}}, ..., {{"Título da Tarefa":"Texto do Acompanhamento"}}]

    Observe que o "Título da Tarefa" tem uma construção específica e que o último termo do título, que pode ser obtido logo após o último caractere "-", determina qual atividade foi elaborada naquele momento.

    Segue o JSON:

    {str(data)}

    A partir do JSON acima eu gostaria que fosse feita uma análise detalhada deste instrutor e de suas atividades.
    
    Em suas análises busque sempre destacar os pontos de atenção e possíveis pontos de melhoria. Sugira formas de resolver os problemas, mas também não deixe de destacar os pontos positivos do trabalho. Com essa análise responda aos seguintes questionamentos:

    1. Essa pessoa atingiu com qualidade e dentro do prazo os resultados e/ou metas que se comprometeu ao longo do trimestre?
        Observações: Leve em consideração a entrega, os prazos e a qualidade dos resultados e/ou metas alinhados com a pessoa no início do ciclo. Lembre-se que entregar um resultado, tarefa ou projeto com qualidade também implica em entregar dentro do prazo combinado.
        Ao final atribua uma das seguintes classificação para essa pessoa: Não atende o esperado; Atende parcialmente o esperado; Atende o esperado; Supera o esperado.
        
    2. Qual foi o impacto dessa pessoa em relação aos objetivos da área?
        Observações: Leve em consideração o quanto essa pessoa se esforçou para que os objetivos da área, além dos seus individuais, fossem atingidos, colaborando com o desenvolvimento dos colegas e se preocupando com o impacto das suas atividades para o time.
        Ao final atribua uma das seguintes classificação para essa pessoa: Não atende o esperado; Atende parcialmente o esperado; Atende o esperado; Supera o esperado.
        
    3. Com base nas duas perguntas acima, comente sobre os pontos positivos e pontos de maior dificuldade nas entregas combinadas ao longo do trimestre.
        Observações: Dê exemplos claros (indicadores, feedbacks, dados) dos motivos pelos quais você enquadra como positivo ou que teve dificuldades.
        
    4. Essa pessoa aplica com constância as habilidades técnicas necessárias para realizar suas atividades do dia-a-dia?
        Observações: Leve em consideração as habilidades e/ou competências técnicas que são exigidas na função atual dessa pessoa, e que foram combinadas com ela desde o início da jornada ou ciclo, e a constância que essa pessoa as aplica em seu dia a dia.
        Ao final atribua uma das seguintes classificação para essa pessoa: Não atende o esperado; Atende parcialmente o esperado; Atende o esperado; Supera o esperado.
        
    5. Essa pessoa está aplicando os valores da empresa com constância na hora de realizar suas atividades do dia-a-dia?
        Observações: Leve em consideração os valores da Alura e as competências comportamentais que são exigidas na função, cargo e nível dessa pessoa, e que foram combinadas com ela desde o início da jornada ou ciclo.
        Este quadro abaixo apresenta algumas competências relacionadas aos nossos valores.
        | **Valores**                                   | **Descrição**                                                                                                                                                                 | **Competências relacionadas **                           |
        |-----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|----------------------------------------------------------|
        | **Diversidade - Unimos as diferenças**        | Valorizamos e respeitamos a pluralidade - ela é importante para o mundo e para nós também. A combinação das nossas individualidades nos leva mais longe.                      | Empatia, flexibilidade                                   |
        | **Desenvolvimento - Aprendemos para crescer** | Somos uma empresa de educação e vivemos isso aqui dentro - estudar, aprender e explorar novos conhecimentos nos faz evoluir constantemente.                                   | Busca por feedback, curiosidade por novos conhecimentos  |
        | **Colaboração - Construímos em conjunto**     | Estamos sempre disponíveis para dar e receber ajuda: combinando nossas diferenças e nossos conhecimentos, somos capazes de criar experiências e resultados cada vez melhores. | Mentoria, escuta ativa                                   |
        | **Dedicação - Fazemos o nosso melhor**        | Entregamos sempre o melhor resultado possível para o momento, aprendendo e evoluindo com nossos erros.                                                                        | Comprometimento, auto responsabilidade                   |
        | **Encantar - Criamos experiências incríveis** | Trabalhamos para oferecer a melhor experiência da vida de quem se conecta com a gente, criando as condições para que possam atingir seus objetivos.                           | Relacionamento interpessoal, negociação                  |
        Ao final atribua uma das seguintes classificação para essa pessoa: Não atende o esperado; Atende parcialmente o esperado; Atende o esperado; Supera o esperado.

    6. Como a pessoa se desenvolveu em resposta aos feedbacks que recebeu ao longo do ciclo?
        Observações: Ao abordar seu desenvolvimento em resposta aos feedbacks, reflita sobre como eles contribuíram para aumentar sua compreensão sobre suas habilidades, pontos fortes e áreas de melhoria. Descreva ações tomadas, como mudanças no comportamento, aquisição de novas habilidades ou ajustes em suas abordagens.
        Lembre-se de fornecer exemplos concretos e resultados observáveis para ilustrar seu crescimento e desenvolvimento em resposta aos feedbacks ao longo do ciclo.
        Ao final atribua uma das seguintes classificação para essa pessoa: Não atende o esperado; Atende parcialmente o esperado; Atende o esperado; Supera o esperado.
        
    7. Revise a avaliação de desempenho, verifique o planejamento de entregas do seu time para o próximo tri, e pontue ao menos 2 habilidades ou competências que serão necessárias desenvolver para que sejam contempladas no PDI. Estas podem estar relacionadas à Hard Skills (habilidades técnicas) ou Soft Skills (habilidades humanas/comportamentais).

    Nas suas respostas não reproduza as observações, retorne apenas as perguntas e as suas respostas. Caso não seja possível responder alguma pergunta basta deixar em branco.
    '''
