"""Utilitários de escrita/leitura local (Parquet e JSON) com particionamento."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def partition_dir(base: Path, entity: str, key: str, value: str) -> Path:
    """Monta um diretório particionado `base/entity/key=value/`."""
    return base / entity / f"{key}={value}"


def write_parquet(dataframe: pd.DataFrame, path: Path) -> Path:
    """Grava um DataFrame em Parquet com compressão Snappy."""
    path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_parquet(
        path,
        index=False,
        engine="pyarrow",
        compression="snappy",
    )
    return path


def read_parquet(path: Path) -> pd.DataFrame:
    """Lê um arquivo Parquet."""
    return pd.read_parquet(path, engine="pyarrow")


def read_parquet_dir(directory: Path) -> pd.DataFrame:
    """Lê e concatena todos os Parquet de um diretório (recursivo)."""
    files = sorted(directory.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"Nenhum Parquet encontrado em: {directory}")
    frames = [read_parquet(f) for f in files]
    return pd.concat(frames, ignore_index=True)


def write_json(payload: dict, path: Path) -> Path:
    """Grava um dicionário como JSON legível (UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return path


def append_jsonl(payload: dict, path: Path) -> Path:
    """Anexa um registro em um arquivo JSON Lines (auditoria estruturada)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(payload, ensure_ascii=False, default=str)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return path
