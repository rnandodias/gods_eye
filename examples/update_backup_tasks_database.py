from gods_eye.gods_eye_app import GodsEye

instructors=["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val"]

gods_eye = GodsEye()
gods_eye.update_tasks_database(backup=True)
gods_eye.update_produced_content(instructors)