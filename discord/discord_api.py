import discord
from dotenv import load_dotenv
import os
import asyncio
import sys

class DiscordBotSendUserMessage:
    def __init__(self, user_id, message=None, file_path=None):
        load_dotenv()
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        self.user_id = user_id
        self.message = message
        self.file_path = file_path
        
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        self.client = discord.Client(intents=intents)
        
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        @self.client.event
        async def on_ready():
            print(f'{self.client.user} online!')
            user = await self.client.fetch_user(self.user_id)
            try:
                print(f'Enviando mensagem para {user.name}!')
                if self.message:
                    await user.send(self.message)
                if self.file_path:
                    print(f'Enviando arquivo {self.file_path} para {user.name}!')
                    await user.send(file=discord.File(self.file_path))
                    # os.remove(self.file_path)
                    # print(f"Arquivo {self.file_path} apagado com sucesso.")
            except Exception as e:
                print(f'Ocorreu um erro: {e}')
            finally:
                await self.client.close()

    def run(self):
        self.client.run(self.token)

    def stop(self):
        self.client.close()


# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    from gods_eye.utils import create_feedback_file
    user_id = '872424957127327744'
    message = "Aqui está o arquivo que você pediu."

    content = """
# Este é um exemplo de arquivo MD.
### Ele foi criado usando Python.
Você pode usar este arquivo para testar o envio via Discord.
"""

    file_path = create_feedback_file("feedback_example", content)

    bot = DiscordBotSendUserMessage(user_id, message, file_path)
    bot.run()
