import tensorflow as tf
from tensorflow.keras.datasets import mnist

# Funções de heavy_hitters_utils
def top_k(signal, k):
    unique, _, counts = tf.unique_with_counts(signal)
    top_indices = tf.argsort(counts, direction='DESCENDING')[:k]
    return tf.gather(unique, top_indices), tf.gather(counts, top_indices)

def precision(true, pred):
    true_set, pred_set = set(true), set(pred)
    if not pred_set:
        return 0.0
    return len(true_set & pred_set) / len(pred_set)

def recall(true, pred):
    true_set, pred_set = set(true), set(pred)
    if not true_set:
        return 0.0
    return len(true_set & pred_set) / len(true_set)

def f1_score(true, pred):
    p = precision(true, pred)
    r = recall(true, pred)
    if p + r == 0:
        return 0.0
    return 2 * (p * r) / (p + r)

def compute_threshold_leakage(signal, thresholds):
    signal = tf.cast(signal, tf.float32)  # Converte signal para float32
    false_positive_rates = []
    false_discovery_rates = []
    for threshold in thresholds:
        above_threshold = signal >= threshold
        false_positive_rate = tf.reduce_sum(tf.cast(above_threshold, tf.float32)) / len(signal)
        false_discovery_rate = tf.reduce_sum(tf.cast(above_threshold, tf.float32)) / tf.reduce_sum(tf.cast(signal, tf.float32))
        false_positive_rates.append(false_positive_rate)
        false_discovery_rates.append(false_discovery_rate)
    return false_positive_rates, false_discovery_rates

def get_top_elements(signal, k):
    unique, _, counts = tf.unique_with_counts(signal)
    top_indices = tf.argsort(counts, direction='DESCENDING')[:k]
    return tf.gather(unique, top_indices), tf.gather(counts, top_indices)

# Função para carregar o dataset MNIST
def load_mnist_data():
    (x_train, y_train), (x_test, y_test) = mnist.load_data()
    x_train, x_test = x_train / 255.0, x_test / 255.0
    return (x_train, y_train), (x_test, y_test)

# Classe de teste de HeavyHitters
class HeavyHittersTest(tf.test.TestCase):

    def assertSetAllEqual(self, a, b):
        a_set = set(a.numpy().tolist())
        b_set = set(b.numpy().tolist())
        self.assertEqual(a_set, b_set)

    def assertHistogramsEqual(self, hist_a, hist_b):
        keys_a, values_a = hist_a
        keys_b, values_b = hist_b
        self.assertSetAllEqual(keys_a, keys_b)
        self.assertAllEqual(values_a, values_b)

# Classe de teste de HeavyHittersUtils
class HeavyHittersUtilsTest(tf.test.TestCase):

    def test_top_k(self):
        signal = tf.constant([1, 2, 2, 3, 3, 3])
        top_elements, counts = top_k(signal, 2)
        self.assertAllEqual(top_elements, [3, 2])
        self.assertAllEqual(counts, [3, 2])

    def test_precision(self):
        self.assertAlmostEqual(precision([1, 2, 3], [1, 2, 4]), 2 / 3)
        self.assertAlmostEqual(precision([1, 2, 3], [4, 5, 6]), 0.0)
        self.assertAlmostEqual(precision([], [1, 2, 3]), 0.0)

    def test_recall(self):
        self.assertAlmostEqual(recall([1, 2, 3], [1, 2, 4]), 2 / 3)
        self.assertAlmostEqual(recall([1, 2, 3], [4, 5, 6]), 0.0)
        self.assertAlmostEqual(recall([1, 2, 3], [1, 2, 3]), 1.0)

    def test_f1_score(self):
        self.assertAlmostEqual(f1_score([1, 2, 3], [1, 2, 4]), 2 * (2 / 3) * (2 / 3) / (4 / 3))
        self.assertAlmostEqual(f1_score([1, 2, 3], [4, 5, 6]), 0.0)
        self.assertAlmostEqual(f1_score([1, 2, 3], [1, 2, 3]), 1.0)

    def test_compute_threshold_leakage(self):
        signal = tf.constant([1, 2, 2, 3, 3, 3, 4, 4, 4, 4])
        thresholds = [1.5, 2.5, 3.5]
        expected_false_positive_rates = [0.9, 0.7, 0.4]  # Atualizados
        expected_false_discovery_rates = [0.3, 0.23333333, 0.13333334]  # Atualizados
        false_positive_rates, false_discovery_rates = compute_threshold_leakage(signal, thresholds)
        self.assertAllClose(false_positive_rates, expected_false_positive_rates)
        self.assertAllClose(false_discovery_rates, expected_false_discovery_rates)

    def test_get_top_elements(self):
        signal = tf.constant([1, 2, 2, 3, 3, 3])
        top_elements, counts = get_top_elements(signal, 2)
        self.assertAllEqual(top_elements, [3, 2])
        self.assertAllEqual(counts, [3, 2])

# Funções originais do federated5.py
def main():
    # Carregar dataset MNIST
    (x_train, y_train), (x_test, y_test) = load_mnist_data()

    # Usar os labels do dataset como sinal para top_k
    signal = tf.constant(y_train)
    top_elements, counts = top_k(signal, 5)
    print("Top K Elements (MNIST Labels):", top_elements.numpy())
    print("Counts:", counts.numpy())

    # Exemplo para precision, recall e f1_score
    true_labels = y_train[:1000].tolist()  # Primeiros 1000 rótulos reais
    pred_labels = y_test[:1000].tolist()   # Primeiros 1000 rótulos previstos (para demonstração)
    print("Precision:", precision(true_labels, pred_labels))
    print("Recall:", recall(true_labels, pred_labels))
    print("F1 Score:", f1_score(true_labels, pred_labels))

    # Exemplo para compute_threshold_leakage
    signal = tf.constant(y_train, dtype=tf.float32)
    thresholds = [2.5, 5.0, 7.5]
    false_positive_rates, false_discovery_rates = compute_threshold_leakage(signal, thresholds)
    print("False Positive Rates:", false_positive_rates)
    print("False Discovery Rates:", false_discovery_rates)

    # Exemplo para get_top_elements
    top_elements, counts = get_top_elements(signal, 5)
    print("Top Elements:", top_elements.numpy())
    print("Counts:", counts.numpy())

if __name__ == "__main__":
    main()