from google_calendar.calendar_api import GoogleCalendarAPI

def create_agenda(name, email):
    calendar_api = GoogleCalendarAPI()
    calendar_api.create_agenda(name, email)

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Comando: python scripts/create_agenda.py <name> <email>")
        sys.exit(1)

    param1 = sys.argv[1]
    param2 = sys.argv[2]
    create_agenda(param1, param2)