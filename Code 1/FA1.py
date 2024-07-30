# Simulação de um ambiente federado
class FederatedServer:
    def __init__(self):
        self.global_counts = {}

    def send_task(self, clients, threshold):
        client_responses = []
        for client in clients:
            client_responses.append(client.find_heavy_hitters(threshold))
        self.aggregate(client_responses)

    def aggregate(self, client_responses):
        for response in client_responses:
            for item, count in response.items():
                if item in self.global_counts:
                    self.global_counts[item] += count
                else:
                    self.global_counts[item] = count

    def get_final_heavy_hitters(self, threshold):
        return {item: count for item, count in self.global_counts.items() if count >= threshold}


class Client:
    def __init__(self, data):
        self.data = data

    def report_counts(self):
        local_counts = {}
        for item in self.data:
            if item in local_counts:
                local_counts[item] += 1
            else:
                local_counts[item] = 1
        return local_counts

    def find_heavy_hitters(self, threshold):
        local_counts = self.report_counts()
        return {item: count for item, count in local_counts.items() if count >= threshold}


# Dados de exemplo para cada cliente
clients_data = [
    ['item2', 'item1', 'item3', 'item1', 'item2'],
    ['item2', 'item2', 'item1', 'item2'],
    ['item3', 'item3', 'item1', 'item2'],
    ['item4', 'item1', 'item2'],
    ['item1', 'item2', 'item3', 'item4'],
    ['item5', 'item2', 'item3', 'item4'],
    ['item5', 'item5', 'item3', 'item2', 'item1'],
    ['item6', 'item1', 'item2', 'item3']
]

# Criação de clientes
clients = [Client(data) for data in clients_data]

# Servidor federado
server = FederatedServer()

# Definindo o threshold
threshold = 2

# Servidor envia tarefa para encontrar heavy hitters para todos os clientes
server.send_task(clients, threshold)

# Recuperar e imprimir heavy hitters finais
print(server.get_final_heavy_hitters(threshold))  # Threshold ajustável conforme a necessidade

