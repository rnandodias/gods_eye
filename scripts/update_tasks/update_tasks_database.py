from gods_eye.gods_eye_app import GodsEye
from google_forms.forms_api import GoogleFormsAPI

gods_eye = GodsEye()
gods_eye.update_tasks_database()

forms_api = GoogleFormsAPI()
forms_api.get_form_responses()