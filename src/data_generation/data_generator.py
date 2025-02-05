class DataGenerator:
    def __init__(self, description=None):
        self.description = description
        self.n_qubits = None
        self.layers = None

    def initialize(self, n_qubits: int, layers: int):
        self.n_qubits = n_qubits
        self.layers = layers

    def generate_data(self):
        pass
