"""Adaptador de repositorio local (SQLite) de proveedor → concepto de retención."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from dian_hojas.dominio.modelos import Cliente, PerfilCliente

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

TABLA_PERFILES = """
CREATE TABLE IF NOT EXISTS perfiles_cliente (
    numero TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    tipo_identificacion TEXT NOT NULL DEFAULT 'NIT',
    digito_verificacion TEXT,
    carpeta_salida TEXT NOT NULL DEFAULT ''
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
        self.con.execute(TABLA_PERFILES)
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

    # --- Perfiles por cliente (Fase 4) -------------------------------------------------

    def guardar_perfil(self, perfil: PerfilCliente) -> None:
        """Crea o actualiza el perfil, usando el número de identificación como clave."""
        cliente = perfil.cliente
        self.con.execute(
            "INSERT INTO perfiles_cliente "
            "(numero, nombre, tipo_identificacion, digito_verificacion, carpeta_salida) "
            "VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(numero) DO UPDATE SET "
            "nombre = excluded.nombre, "
            "tipo_identificacion = excluded.tipo_identificacion, "
            "digito_verificacion = excluded.digito_verificacion, "
            "carpeta_salida = excluded.carpeta_salida",
            (
                cliente.numero,
                cliente.nombre,
                cliente.tipo_identificacion,
                cliente.digito_verificacion,
                perfil.carpeta_salida,
            ),
        )
        self.con.commit()

    def perfiles(self) -> tuple[PerfilCliente, ...]:
        """Todos los perfiles guardados, ordenados por nombre."""
        filas = self.con.execute(
            "SELECT numero, nombre, tipo_identificacion, digito_verificacion, carpeta_salida "
            "FROM perfiles_cliente ORDER BY nombre COLLATE NOCASE, numero"
        ).fetchall()
        return tuple(self._perfil_de_fila(fila) for fila in filas)

    def perfil(self, numero: str) -> PerfilCliente | None:
        fila = self.con.execute(
            "SELECT numero, nombre, tipo_identificacion, digito_verificacion, carpeta_salida "
            "FROM perfiles_cliente WHERE numero = ?",
            (numero,),
        ).fetchone()
        return self._perfil_de_fila(fila) if fila is not None else None

    def eliminar_perfil(self, numero: str) -> None:
        self.con.execute("DELETE FROM perfiles_cliente WHERE numero = ?", (numero,))
        self.con.commit()

    @staticmethod
    def _perfil_de_fila(fila) -> PerfilCliente:
        numero, nombre, tipo, digito, carpeta = fila
        return PerfilCliente(
            cliente=Cliente(
                nombre=str(nombre),
                numero=str(numero),
                tipo_identificacion=str(tipo),  # type: ignore[arg-type]
                digito_verificacion=str(digito) if digito else None,
            ),
            carpeta_salida=str(carpeta or ""),
        )

    def cerrar(self) -> None:
        self.con.close()
