"""Cache verificável para GridSearchCV nacional, sem acesso ao teste reservado.

IDs controlam a origem; são removidos antes de ajustar qualquer estimador.
O cache compartilha árvores determinísticas e previsões OOF, não validações.
"""

import copy
import gc
import hashlib
import json
import logging
import os
import pickle
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, RegressorMixin, clone
from sklearn.exceptions import ConvergenceWarning

from enem_base.checkpointing import atomic_json, digest, identifiers_digest, run_lock
from enem_base.learning_curves import _predict
from enem_base.modeling import estimator_spec
from enem_base.provenance import sha256_file, verify_sha256

logger = logging.getLogger(__name__)


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def data_digest(frame):
    values = pd.util.hash_pandas_object(frame, index=False).to_numpy()
    return hashlib.sha256(values.tobytes()).hexdigest()


def target_digest(y):
    return hashlib.sha256(np.ascontiguousarray(y, dtype="<f8").tobytes()).hexdigest()


def save_pickle(path, model, context, **extra):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".pkl.tmp")
    with temporary.open("wb") as stream:
        pickle.dump(model, stream, protocol=5)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    meta = {"context": context, "sha256": sha256_file(path), **extra}
    atomic_json(path.with_suffix(".json"), meta)
    return meta


def load_pickle(path, context):
    meta = read_json(path.with_suffix(".json"))
    if meta["context"] != context:
        raise ValueError(f"Modelo local incompatível: {path}")
    verify_sha256(path, meta["sha256"], "Modelo local alterado")
    with path.open("rb") as stream:
        return pickle.load(stream), meta


def save_array(path, values, context, **extra):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".npy.tmp")
    with temporary.open("wb") as stream:
        np.save(stream, values, allow_pickle=False)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    atomic_json(
        path.with_suffix(".json"),
        {
            "context": context,
            "sha256": sha256_file(path),
            **extra,
        },
    )


def load_array(path, context):
    meta = read_json(path.with_suffix(".json"))
    if meta["context"] != context:
        raise ValueError(f"Previsões de outra configuração: {path}")
    verify_sha256(path, meta["sha256"], "Previsões alteradas")
    result = np.load(path, allow_pickle=False)
    if not np.isfinite(result).all():
        raise ValueError("Previsões não finitas no cache.")
    return result


def forest_prefix(model, n_estimators):
    """Mesmas primeiras árvores de um ajuste direto, com random_state inteiro fixo."""
    result = copy.deepcopy(model)
    forest = result.named_steps["regressor"]
    if not 1 <= n_estimators <= len(forest.estimators_):
        raise ValueError("Quantidade de árvores fora do cache ajustado.")
    forest.estimators_ = forest.estimators_[:n_estimators]
    forest.set_params(n_estimators=n_estimators)
    return result


def stacking_meta_fit(base_model, meta_features, y, alpha):
    result = copy.deepcopy(base_model)
    result.set_params(final_estimator__alpha=alpha)
    result.final_estimator_ = clone(result.final_estimator).fit(meta_features, y)
    return result


def oof_features(estimator, x, y, directory, context):
    """OOF equivalente a cross_val_predict, com um arquivo por base/dobra interna."""
    result = np.empty((len(x), len(estimator.estimators)), dtype=float)
    for column, (name, base) in enumerate(estimator.estimators):
        seen = np.zeros(len(x), dtype=bool)
        for fold, (training, validation) in enumerate(estimator.cv.split(x, y)):
            path = directory / f"oof-{name}-{fold}.npy"
            expected = {
                **context,
                "base": name,
                "inner_fold": fold,
                "parameters": estimator_spec(base),
                "training_positions_sha256": hashlib.sha256(training.tobytes()).hexdigest(),
                "validation_positions_sha256": hashlib.sha256(validation.tobytes()).hexdigest(),
            }
            if path.with_suffix(".json").exists():
                values = load_array(path, expected)
            else:
                started = time.perf_counter()
                logger.info(
                    "OOF %s/%s: %d treino, %d validação", name, fold, len(training), len(validation)
                )
                with warnings.catch_warnings(record=True) as notices:
                    warnings.simplefilter("always")
                    model = clone(base).fit(x.iloc[training], y[training])
                if any(issubclass(w.category, ConvergenceWarning) for w in notices):
                    raise ValueError("Base interna não convergiu; não persistir previsões OOF.")
                for notice in notices:
                    warnings.warn(str(notice.message), notice.category, stacklevel=2)
                values = _predict(model, x.iloc[validation], 100_000)
                save_array(path, values, expected, elapsed_seconds=time.perf_counter() - started)
                del model
                gc.collect()
            if values.shape != (len(validation),) or seen[validation].any():
                raise ValueError("Cobertura OOF incorreta.")
            result[validation, column] = values
            seen[validation] = True
        if not seen.all():
            raise ValueError("As previsões internas não cobrem o treino completo.")
    return result


def prior_curve_fit(protocol, name, fold, fraction, expected, train_ids):
    """Adotar somente um ajuste real cujo contexto já foi validado no CP3."""
    source = Path(protocol["checkpoint3_path"]) / name
    key = f"dobra-{fold}-fracao-{int(fraction * 100):03d}"
    point = source / "pontos" / f"{key}.json"
    manifest = read_json(source / "manifesto.json")
    verify_sha256(
        point, manifest["point_assets"][str(point.relative_to(source))], "Ponto anterior alterado"
    )
    saved = read_json(point)
    if (
        saved["context"]["parameters"] != estimator_spec(expected)
        or saved["context"]["point"]["train_ids_sha256"] != train_ids
    ):
        return None
    path = source / "modelos_ajustados" / f"{key}.pkl"
    verify_sha256(path, saved["fit"]["sha256"], "Ajuste anterior alterado")
    with path.open("rb") as stream:
        return pickle.load(stream)


def shared_fit(estimator, name, x, y, protocol, directory, context, fold, ids_hash):
    """Ajustar a configuração exata, compartilhando apenas componentes invariantes."""
    if name == "random_forest":
        count = estimator.get_params()["regressor__n_estimators"]
        maximum = max(protocol["spaces"][name]["regressor__n_estimators"])
        expanded = clone(estimator).set_params(regressor__n_estimators=maximum)
        structural = {**context, "parameters": estimator_spec(expanded)}
        base_path = directory / "shared" / (digest(structural) + ".pkl")
        if base_path.with_suffix(".json").exists():
            fitted, _ = load_pickle(base_path, structural)
        else:
            fitted = prior_curve_fit(protocol, name, fold, 1.0, expanded, ids_hash)
            reused = fitted is not None
            if not reused:
                logger.info(
                    "Ajustando floresta compartilhada, dobra %d, profundidade %s",
                    fold,
                    expanded.get_params()["regressor__max_depth"],
                )
                fitted = expanded.fit(x, y)
            save_pickle(base_path, fitted, structural, reused_checkpoint3=reused)
        return forest_prefix(fitted, count)
    if name == "stacking":
        alpha = estimator.get_params()["final_estimator__alpha"]
        canonical = clone(estimator).set_params(final_estimator__alpha=1.0)
        structural = {**context, "parameters": estimator_spec(canonical)}
        shared = directory / "shared" / digest(structural)
        base_path = shared / "bases.pkl"
        if base_path.with_suffix(".json").exists():
            fitted, _ = load_pickle(base_path, structural)
        else:
            fitted = prior_curve_fit(protocol, name, fold, 1.0, canonical, ids_hash)
            if fitted is None:
                raise ValueError("Bases completas do Stacking original não disponíveis.")
            save_pickle(base_path, fitted, structural, reused_checkpoint3=True)
        meta = oof_features(canonical, x, y, shared, structural)
        reference = stacking_meta_fit(fitted, meta, y, 1.0)
        # Confirmar a equivalência nacional antes de usar o cache para outros alphas.
        if not np.allclose(
            reference.final_estimator_.coef_, fitted.final_estimator_.coef_, rtol=1e-10, atol=1e-10
        ) or not np.allclose(
            reference.final_estimator_.intercept_,
            fitted.final_estimator_.intercept_,
            rtol=1e-10,
            atol=1e-10,
        ):
            raise ValueError("OOF recomposto não reproduz o combinador do Checkpoint 3.")
        return stacking_meta_fit(fitted, meta, y, alpha)
    return clone(estimator).fit(x, y)


class CachedCVRegressor(RegressorMixin, BaseEstimator):
    """Estimador sklearn para busca real, com persistência dos ajustes por dobra."""

    def __init__(self, estimator, name, protocol_path):
        self.estimator = estimator
        self.name = name
        self.protocol_path = protocol_path

    def fit(self, X, y):
        path = Path(self.protocol_path)
        protocol = read_json(path)
        verify_sha256(
            path,
            read_json(path.parent / "inicio_buscas.json")["protocol_sha256"],
            "Protocolo de busca alterado",
        )
        if list(X.columns) != [protocol["identifier"], *protocol["features"]]:
            raise ValueError("Entradas de busca incompatíveis.")
        x_hash, y_hash = data_digest(X), target_digest(y)
        matching = [
            p
            for p in protocol["folds"]
            if p["train_data_sha256"] == x_hash and p["train_target_sha256"] == y_hash
        ]
        if len(matching) != 1:
            raise ValueError("Treino não corresponde a uma dobra nacional registrada.")
        self.fold_ = matching[0]
        specification = estimator_spec(self.estimator)
        choices = protocol["candidates"][self.name]
        indices = [i for i, entry in enumerate(choices) if entry["estimator"] == specification]
        if len(indices) != 1:
            raise ValueError("Configuração fora do espaço de busca registrado.")
        self.candidate_ = indices[0]
        self.context_ = {
            "protocol_sha256": sha256_file(path),
            "model": self.name,
            "fold": self.fold_["fold"],
            "train_data_sha256": x_hash,
            "train_target_sha256": y_hash,
        }
        self.fit_context_ = {**self.context_, "parameters": specification}
        self.directory_ = path.parent / "buscas" / self.name
        self.fit_path_ = (
            self.directory_
            / "modelos_ajustados"
            / f"config-{self.candidate_:02d}-dobra-{self.fold_['fold']}.pkl"
        )
        with run_lock(self.fit_path_):
            if self.fit_path_.with_suffix(".json").exists():
                self.fitted_, self.fit_metadata_ = load_pickle(self.fit_path_, self.fit_context_)
                logger.info(
                    "%s config %02d dobra %d: ajuste reutilizado",
                    self.name,
                    self.candidate_,
                    self.fold_["fold"],
                )
            else:
                logger.info(
                    "%s config %02d dobra %d: ajuste",
                    self.name,
                    self.candidate_,
                    self.fold_["fold"],
                )
                started = time.perf_counter()
                with warnings.catch_warnings(record=True) as captured:
                    warnings.simplefilter("always")
                    self.fitted_ = shared_fit(
                        self.estimator,
                        self.name,
                        X[protocol["features"]],
                        np.asarray(y),
                        protocol,
                        path.parent / "cache_buscas" / self.name,
                        self.context_,
                        self.fold_["fold"],
                        identifiers_digest(X[protocol["identifier"]]),
                    )
                notices = [f"{w.category.__name__}: {w.message}" for w in captured]
                if any(issubclass(w.category, ConvergenceWarning) for w in captured):
                    raise ValueError("Configuração não convergiu; não congelar resultado.")
                self.fit_metadata_ = save_pickle(
                    self.fit_path_,
                    self.fitted_,
                    self.fit_context_,
                    elapsed_this_fit_seconds=time.perf_counter() - started,
                    warnings=notices,
                )
        self.n_features_in_ = X.shape[1]
        self.feature_names_in_ = np.asarray(X.columns, dtype=object)
        return self

    def predict(self, X):
        protocol = read_json(self.protocol_path)
        if data_digest(X) != self.fold_["validation_data_sha256"]:
            raise ValueError("A busca só pode prever a validação registrada da sua dobra.")
        context = {
            **self.fit_context_,
            "fit_sha256": self.fit_metadata_["sha256"],
            "validation_data_sha256": self.fold_["validation_data_sha256"],
        }
        path = (
            Path(self.protocol_path).parent
            / "cache_buscas"
            / "predicoes"
            / self.name
            / f"config-{self.candidate_:02d}-dobra-{self.fold_['fold']}.npy"
        )
        if path.with_suffix(".json").exists():
            values = load_array(path, context)
        else:
            started = time.perf_counter()
            values = _predict(self.fitted_, X[protocol["features"]], 100_000)
            save_array(path, values, context, elapsed_seconds=time.perf_counter() - started)
        if values.shape != (len(X),):
            raise ValueError("Previsões incompletas.")
        logger.info(
            "%s config %02d dobra %d: validação prevista",
            self.name,
            self.candidate_,
            self.fold_["fold"],
        )
        return values
