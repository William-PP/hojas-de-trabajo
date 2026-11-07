"""Adaptador de repositorio local (SQLite) de proveedor → concepto de retención."""

from __future__ import annotations

import sqlite3
from pathlib import Path

TABLA_PROVEEDOR_CONCEPTO = """
CREATE TABLE IF NOT EXISTS proveedor_concepto (
    nit TEXT PRIMARY KEY,
    concepto TEXT NOT NULL
)
"""

TABLA_DECISIONES = """
CREATE TABLE IF NOT EXISTS decisiones_retefuente (
    folio TEXT PRIMARY KEY,
    concepto TEXT NOT NULL,
    aceptada INTEGER NOT NULL DEFAULT 0
)
"""


class ErrorRepositorio(RuntimeError):
    """No se pudo leer o escribir la memoria local de retención."""


class RepoSqlite:
    """Puerto de memoria proveedor → concepto, con decisiones del usuario."""

    def __init__(self, ruta: Path) -> None:
        self.ruta = Path(ruta)
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(self.ruta)
        self.con.execute(TABLA_PROVEEDOR_CONCEPTO)
        self.con.execute(TABLA_DECISIONES)
        self.con.commit()

    def concepto_de_proveedor(self, nit: str) -> str | None:
        fila = self.con.execute(
            "SELECT concepto FROM proveedor_concepto WHERE nit = ?",
            (nit,),
        ).fetchone()
        return str(fila[0]) if fila is not None else None

    def asignar_concepto(self, nit: str, concepto: str) -> None:
        self.con.execute(
            "INSERT INTO proveedor_concepto (nit, concepto) VALUES (?, ?) "
            "ON CONFLICT(nit) DO UPDATE SET concepto = excluded.concepto",
            (nit, concepto),
        )
        self.con.commit()

    def decision(self, folio: str) -> str | None:
        fila = self.con.execute(
            "SELECT concepto FROM decisiones_retefuente WHERE folio = ?",
            (folio,),
        ).fetchone()
        return str(fila[0]) if fila is not None else None

    def guardar_decision(self, folio: str, concepto: str, aceptada: bool) -> None:
        self.con.execute(
            "INSERT INTO decisiones_retefuente (folio, concepto, aceptada) VALUES (?, ?, ?) "
            "ON CONFLICT(folio) DO UPDATE SET concepto = excluded.concepto, aceptada = excluded.aceptada",
            (folio, concepto, int(aceptada)),
        )
        self.con.commit()

    def cerrar(self) -> None:
        self.con.close()
