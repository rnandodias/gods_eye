from gods_eye.gods_eye_app import GodsEye

instructors=["Afonso", "Allan", "Bia", "Danielle", "Igor", "João", "Marcelo", "Mirla", "Val"]
# instructors=["Val"]

gods_eye = GodsEye()
gods_eye.create_quarterly_report(instructors=instructors, start="2024-04-01", end="2024-06-30", page_title="2º Trimestre 2024")