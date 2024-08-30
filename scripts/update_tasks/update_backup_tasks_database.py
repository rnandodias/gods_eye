from gods_eye.gods_eye_app import GodsEye
from google_forms.forms_api import GoogleFormsAPI
from datetime import datetime

instructors=["Afonso", "Allan", "Bia", "Daniel", "Danielle", "Igor", "João", "Larissa", "Marcelo", "Mirla", "Val"]
today = datetime.now().date()

gods_eye = GodsEye()
forms_api = GoogleFormsAPI()

# Os formulários de feedback são enviados toda terça-feira
if today.weekday() == 1:
    gods_eye.update_tasks_database(backup=True)
else:
    gods_eye.update_tasks_database()

forms_api.get_form_responses()

gods_eye.update_produced_content(instructors)