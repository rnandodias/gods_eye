from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os

class MongoDBManager:
    def __init__(self):
        load_dotenv()
        self.client = MongoClient(os.getenv('MONGODB_URI'))
        self.db = self.client[os.getenv('DB_NAME')]

    def create_collection(self, collection_name):
        """Cria uma nova coleção no banco de dados."""
        return self.db.create_collection(collection_name)

    def insert_one(self, collection_name, document):
        """Insere um documento na coleção especificada."""
        collection = self.db[collection_name]
        return collection.insert_one(document)

    def insert_many(self, collection_name, documents):
        """Insere vários documentos na coleção especificada."""
        collection = self.db[collection_name]
        return collection.insert_many(documents)

    def update_one(self, collection_name, query, update):
        """Atualiza um documento na coleção especificada."""
        collection = self.db[collection_name]
        return collection.update_one(query, update)

    def replace_one(self, collection_name, query, replace):
        """Substitui um documento na coleção especificada."""
        collection = self.db[collection_name]
        return collection.replace_one(query, replace)

    def find_one(self, collection_name, query):
        """Busca um documento na coleção especificada."""
        collection = self.db[collection_name]
        return collection.find_one(query)

    def find_many(self, collection_name, query):
        """Busca vários documentos na coleção especificada."""
        collection = self.db[collection_name]
        return collection.find(query)
    
    def find_most_recent(self, collection_name):
        """Encontra o documento mais recente baseado no campo 'last_update'."""
        collection = self.db[collection_name]
        # Usando find com sort e limit para obter o documento mais recente
        result = collection.find().sort("last_update", -1).limit(1)
        try:
            # Tenta obter o primeiro (e único) documento do cursor retornado
            return next(result, None)
        except StopIteration:
            # Retorna None se nenhum documento for encontrado
            return None

    def delete_one(self, collection_name, query):
        """Deleta um documento na coleção especificada."""
        collection = self.db[collection_name]
        return collection.delete_one(query)

    def delete_many(self, collection_name, query):
        """Deleta vários documentos na coleção especificada."""
        collection = self.db[collection_name]
        return collection.delete_many(query)

# --------------------------------------------------------------------------------------
if __name__ == '__main__':
    mongo_manager = MongoDBManager()
    # Cria a collection para armazenar os backups do database tasks
    # mongo_manager.create_collection("tasks_database")

    # Cria a collection para armazenar as credenciais do Google Calendar
    # mongo_manager.create_collection("google_credentials")
    # mongo_manager.create_collection("google_token")
    