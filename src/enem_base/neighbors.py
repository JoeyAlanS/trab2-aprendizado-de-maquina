"""KNN exato: distância euclidiana preservada, com one-hot armazenado em bits.

Para X=[z,b], onde z é escalar e b é binário:
  distância² = (z_query - z_treino)² + Hamming(b_query, b_treino).
Dentro de cada valor distinto de z, a primeira parcela é constante. Portanto,
os k vizinhos globais estão na união dos k vizinhos de cada grupo de z.
IndexBinaryFlat examina todas as linhas do grupo; não é busca aproximada.
"""

import numpy as np
from joblib import effective_n_jobs
from sklearn.neighbors import KNeighborsRegressor
from sklearn.utils.validation import check_is_fitted, validate_data

from enem_base.preprocessing import dense_knn_input


def _pack(matrix):
    """Empacotar somente valores já binários, sem limiar/quantização de contínuos."""
    n, features = matrix.shape
    width = max(32, ((features - 1 + 255) // 256) * 32)
    packed = np.zeros((n, width), dtype=np.uint8)
    numeric = np.empty(n, dtype=np.float64)
    for start in range(0, n, 25000):
        stop = min(start + 25000, n)
        block = dense_knn_input(matrix[start:stop])
        numeric[start:stop] = block[:, 0]
        binary = block[:, 1:]
        if not np.logical_or(binary == 0, binary == 1).all():
            return None, None
        values = np.packbits(binary.astype(np.uint8), axis=1)
        packed[start:stop, : values.shape[1]] = values
    return numeric, packed


class ExactProfileKNeighborsRegressor(KNeighborsRegressor):
    """Mantém a predição/ponderação de KNeighborsRegressor; acelera vizinhos exatos.

    Usa o índice binário apenas com métrica euclidiana, uma coluna numérica e
    até 256 valores distintos dessa coluna. Outras representações utilizam
    o backend denso do sklearn. Empates seguem o backend fixado e a ordem de treino.
    """

    def fit(self, X, y):
        X, y = validate_data(self, X, y, accept_sparse="csr", y_numeric=True)
        self.binary_backend_ = False
        numeric, packed = _pack(X)
        compatible = (
            self.metric == "euclidean" or (self.metric == "minkowski" and self.p == 2)
        ) and self.algorithm in {"auto", "brute"}
        values = np.unique(numeric) if numeric is not None else []
        if not compatible or not len(values) or len(values) > 256 or self.metric_params:
            return super().fit(dense_knn_input(X), y)

        import faiss

        faiss.omp_set_num_threads(effective_n_jobs(self.n_jobs))
        self.indices_ = []
        for value in values:
            positions = np.flatnonzero(numeric == value)
            index = faiss.IndexBinaryFlat(packed.shape[1] * 8)
            index.add(np.ascontiguousarray(packed[positions]))
            self.indices_.append((float(value), positions, index))
        self._y = np.asarray(y, dtype=np.float64)
        self.n_samples_fit_ = len(y)
        self.binary_backend_ = True
        self.backend_name_ = "faiss_IndexBinaryFlat_exact_partitioned_euclidean"
        self.n_numeric_groups_ = len(values)
        return self

    def kneighbors(self, X=None, n_neighbors=None, return_distance=True):
        check_is_fitted(self)
        if not self.binary_backend_:
            return super().kneighbors(
                dense_knn_input(X) if X is not None else None,
                n_neighbors=n_neighbors,
                return_distance=return_distance,
            )
        if X is None:
            raise ValueError("Forneça explicitamente as entradas para a consulta de vizinhos.")
        X = validate_data(self, X, accept_sparse="csr", reset=False)
        k = self.n_neighbors if n_neighbors is None else n_neighbors
        if not isinstance(k, (int, np.integer)) or not 0 < k <= self.n_samples_fit_:
            raise ValueError("Quantidade de vizinhos inválida.")
        numeric, packed = _pack(X)
        if numeric is None:
            raise ValueError("A validação contém valores não binários no bloco one-hot.")
        distances = np.empty((len(numeric), k), dtype=np.float64)
        indices = np.empty((len(numeric), k), dtype=np.int64)
        for start in range(0, len(numeric), 2048):
            stop = min(start + 2048, len(numeric))
            candidates_d, candidates_i = [], []
            for value, positions, index in self.indices_:
                count = min(k, len(positions))
                hamming, local = index.search(packed[start:stop], count)
                squared = hamming.astype(np.float64) + (numeric[start:stop, None] - value) ** 2
                candidates_d.append(squared)
                candidates_i.append(positions[local])
            squared = np.concatenate(candidates_d, axis=1)
            global_indices = np.concatenate(candidates_i, axis=1)
            order = np.lexsort((global_indices, squared), axis=1)[:, :k]
            distances[start:stop] = np.sqrt(np.take_along_axis(squared, order, axis=1))
            indices[start:stop] = np.take_along_axis(global_indices, order, axis=1)
        return (distances, indices) if return_distance else indices
