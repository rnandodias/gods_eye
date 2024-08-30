from gods_eye.gods_eye_app import GodsEye

# instructors=["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val"]
instructors=["Mirla"]

gods_eye = GodsEye()
gods_eye.update_competency_assessment(instructors=instructors, page_title="1º Trimestre 2024", start="2024-01-01", end="2024-03-31")