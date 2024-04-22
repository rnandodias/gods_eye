from gods_eye.gods_eye_app import GodsEye

instructors=["Afonso", "Allan", "Ana Duarte", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val"]

gods_eye = GodsEye()
gods_eye.create_quarterly_report(instructors=instructors, start="2024-01-01", end="2024-03-31", page_title="1º Trimestre 2024")