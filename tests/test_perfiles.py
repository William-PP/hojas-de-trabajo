"""Pruebas de los perfiles por cliente guardados en SQLite (Fase 4)."""

from __future__ import annotations

from pathlib import Path

from dian_hojas.dominio.modelos import Cliente, PerfilCliente
from dian_hojas.infraestructura.repo_sqlite import RepoSqlite


def _perfil(numero: str = "1020396459", nombre: str = "Cliente Uno") -> PerfilCliente:
    return PerfilCliente(
        cliente=Cliente(nombre=nombre, tipo_identificacion="NIT", numero=numero),
        carpeta_salida="C:/salidas",
    )


def test_guarda_y_recupera_perfil(tmp_path: Path) -> None:
    repo = RepoSqlite(tmp_path / "memoria.sqlite")
    try:
        repo.guardar_perfil(_perfil())

        assert repo.perfiles() == (_perfil(),)
        assert repo.perfil("1020396459") == _perfil()
    finally:
        repo.cerrar()


def test_actualiza_el_perfil_existente(tmp_path: Path) -> None:
    repo = RepoSqlite(tmp_path / "memoria.sqlite")
    try:
        repo.guardar_perfil(_perfil())
        repo.guardar_perfil(_perfil(nombre="Cliente Renombrado"))

        assert len(repo.perfiles()) == 1
        assert repo.perfil("1020396459").cliente.nombre == "Cliente Renombrado"
    finally:
        repo.cerrar()


def test_conserva_ceros_a_la_izquierda_en_la_identificacion(tmp_path: Path) -> None:
    repo = RepoSqlite(tmp_path / "memoria.sqlite")
    try:
        repo.guardar_perfil(_perfil(numero="00123"))
        assert repo.perfil("00123").cliente.numero == "00123"
    finally:
        repo.cerrar()


def test_elimina_perfil(tmp_path: Path) -> None:
    repo = RepoSqlite(tmp_path / "memoria.sqlite")
    try:
        repo.guardar_perfil(_perfil())
        repo.eliminar_perfil("1020396459")
        assert repo.perfiles() == ()
        assert repo.perfil("1020396459") is None
    finally:
        repo.cerrar()
