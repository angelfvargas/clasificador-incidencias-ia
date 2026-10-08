"""Entrena los clasificadores de tickets (tipo, prioridad, equipo).

Compara un baseline (clase más frecuente) con TF-IDF + regresión logística
y TF-IDF + SVM lineal, y guarda el mejor modelo por tarea con sus métricas.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw" / "tickets_multilang_20k.csv"
MODELS = ROOT / "ai_service" / "models"
SEED = 42
TASKS = {"categoria": "type", "prioridad": "priority", "equipo": "queue"}


def load_data(path=RAW):
    d = pd.read_csv(path)
    d = d[d.language == "en"].copy()
    d["text"] = d.subject.fillna("") + " . " + d.body.fillna("")
    d = d[d.text.str.strip() != "."].drop_duplicates("text")
    return d.reset_index(drop=True)


def split(d):
    # train 70 / validación 15 / test 15, estratificado por tipo, sin textos repetidos entre conjuntos
    train, rest = train_test_split(d, test_size=0.30, random_state=SEED, stratify=d["type"])
    val, test = train_test_split(rest, test_size=0.50, random_state=SEED, stratify=rest["type"])
    return train, val, test


def candidates():
    tfidf = dict(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
    return {
        "baseline_mas_frecuente": Pipeline([("tfidf", TfidfVectorizer(**tfidf)), ("clf", DummyClassifier(strategy="most_frequent"))]),
        "tfidf_logreg": Pipeline([("tfidf", TfidfVectorizer(**tfidf)), ("clf", LogisticRegression(max_iter=2000, class_weight="balanced"))]),
        "tfidf_svm": Pipeline([("tfidf", TfidfVectorizer(**tfidf)), ("clf", LinearSVC(class_weight="balanced", random_state=SEED))]),
    }


def main():
    d = load_data()
    train, val, test = split(d)
    version = datetime.now(timezone.utc).strftime("v%Y%m%d%H%M")
    report = {"version": version, "seed": SEED, "datos": {"train": len(train), "val": len(val), "test": len(test)}, "tareas": {}}

    for task, col in TASKS.items():
        val_scores = {}
        for name, pipe in candidates().items():
            pipe.fit(train.text, train[col])
            val_scores[name] = f1_score(val[col], pipe.predict(val.text), average="macro")
        best = max(val_scores, key=val_scores.get)
        # el elegido se reentrena con train+val y se evalúa una sola vez en test
        final = candidates()[best].fit(pd.concat([train.text, val.text]), pd.concat([train[col], val[col]]))
        pred = final.predict(test.text)
        labels = sorted(d[col].unique())
        report["tareas"][task] = {
            "columna": col,
            "macro_f1_validacion": {k: round(v, 4) for k, v in val_scores.items()},
            "modelo_elegido": best,
            "test": {
                "macro_f1": round(f1_score(test[col], pred, average="macro"), 4),
                "exactitud": round(accuracy_score(test[col], pred), 4),
                "por_clase": classification_report(test[col], pred, output_dict=True, zero_division=0),
                "etiquetas": labels,
                "matriz_confusion": confusion_matrix(test[col], pred, labels=labels).tolist(),
            },
        }
        joblib.dump(final, MODELS / f"{task}.joblib")
        print(f"{task}: elegido {best} | test macro-F1 {report['tareas'][task]['test']['macro_f1']}")

    (MODELS / "metricas.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    test[["text", *TASKS.values()]].to_csv(ROOT / "data" / "processed" / "test.csv", index=False)
    print("versión", version)


if __name__ == "__main__":
    sys.exit(main())
