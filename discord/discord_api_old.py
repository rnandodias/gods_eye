import discord
from dotenv import load_dotenv
import os
import asyncio
import sys

class DiscordBotSendUserMessage:
    def __init__(self, user_id, message=None):
        load_dotenv()
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        self.user_id = user_id
        self.message = message

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
                await user.send(self.message)
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
    # channel_id = 1239893679339081738
    user_id = '872424957127327744'
    message = "Olá, mundão!"
    DiscordBotSendUserMessage(user_id, message).run()