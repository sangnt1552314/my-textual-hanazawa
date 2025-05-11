from dotenv import load_dotenv
from components import HanazawaApp

load_dotenv()

if __name__ == "__main__":
    app = HanazawaApp()
    app.run()