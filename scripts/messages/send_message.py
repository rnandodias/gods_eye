# --------------------------------------------------------------------------------------
# Procedimento para verificar o término de uma tarefa e enviar o formulário de feedback
# para pessoa responsável pelo acompanhamento do instrutor
from gods_eye.gods_eye_app import GodsEye
from google_forms.forms_api import GoogleFormsAPI
from datetime import datetime

today = datetime.now().date()
instructors=["Rodrigo", "Daniel", "Allan", "Afonso", "Bia", "Danielle", "Igor", "João", "Larissa", "Marcelo", "Mirla", "Val", "Victorino", "Sabino"]
# instructors=["Rodrigo"]

gods_eye = GodsEye()
forms_api = GoogleFormsAPI()

gods_eye.send_task_reminder(instructors)
forms_api.get_form_responses()

# Os formulários de feedback são enviados toda terça-feira
if today.weekday() == 1:
    forms_api.send_feedback_form()
