"""Pruebas de los siete cuadres."""

from datetime import date
from decimal import Decimal

from dian_hojas.dominio.cuadres import (
    cuadre_bloques,
    cuadre_cantidad,
    cuadre_cliente,
    cuadre_cufe_unico,
    cuadre_otros_impuestos,
    cuadre_periodo,
    cuadre_total,
    ejecutar_cuadres,
    hay_cuadres_fallidos,
)
from dian_hojas.dominio.enums import Bloque
from dian_hojas.dominio.modelos import Cliente, Periodo, ResultadoMes, construir_resultado
from tests.herramientas.documentos import documento

CLIENTE = Cliente(nombre="Cliente Uno", numero="1020396459")
PERIODO = Periodo(anio=2026, mes=10)


def resultado(*documentos):
    return construir_resultado(tuple(documentos))


def test_c1_ok():
    docs = [documento(indice=i, cufe=f"c{i}") for i in range(3)]
    cuadre = cuadre_cantidad(resultado(*docs), filas_dian=3)
    assert cuadre.ok


def test_c1_reporte_de_documentos_sin_clasificar():
    docs = [
        documento(indice=0, cufe="ok"),
        documento(indice=1, cufe="raro", tipo_texto="Documento raro"),
    ]
    cuadre = cuadre_cantidad(resultado(*docs), filas_dian=2)
    assert not cuadre.ok
    assert "sin clasificar" in cuadre.detalle
    assert "raro"[:8] in cuadre.detalle


def test_c1_falla_si_la_cantidad_no_coincide():
    docs = [documento(indice=0, cufe="c0")]
    cuadre = cuadre_cantidad(resultado(*docs), filas_dian=2)
    assert not cuadre.ok


def test_c1_cuenta_los_excluidos_justificados():
    docs = [
        documento(indice=0, cufe="venta", tipo_texto="Factura electrónica", grupo_texto="Emitido"),
        documento(indice=1, cufe="respuesta", tipo_texto="Application response"),
    ]
    cuadre = cuadre_cantidad(resultado(*docs), filas_dian=2)
    assert cuadre.ok
    assert "2 documentos" in cuadre.detalle


def test_c2_ok_y_falla():
    docs = [
        documento(indice=0, cufe="a", iva=Decimal("100"), total=Decimal("1100")),
        documento(indice=1, cufe="b", iva=Decimal("200"), total=Decimal("2200")),
    ]
    res = resultado(*docs)
    assert cuadre_total(res, Decimal("3300")).ok
    assert cuadre_total(res, Decimal("3200")).ok is False


def test_c2_tolera_un_centavo():
    docs = [documento(indice=0, cufe="a", iva=Decimal("0"), total=Decimal("100.00"))]
    assert cuadre_total(resultado(*docs), Decimal("100.01")).ok


def test_c3_detecta_cufe_repetido():
    docs = [
        documento(indice=0, cufe="mismo"),
        documento(indice=1, cufe="mismo"),
        documento(indice=2, cufe="otro"),
    ]
    cuadre = cuadre_cufe_unico(resultado(*docs))
    assert not cuadre.ok
    assert "mismo" in cuadre.detalle


def test_c3_ok():
    docs = [documento(indice=i, cufe=f"c{i}") for i in range(3)]
    assert cuadre_cufe_unico(resultado(*docs)).ok


def test_c4_ok_con_construccion_normal():
    docs = [
        documento(indice=0, cufe="v", tipo_texto="Factura electrónica", grupo_texto="Emitido"),
        documento(indice=1, cufe="c", tipo_texto="Factura electrónica", grupo_texto="Recibido"),
    ]
    assert cuadre_bloques(resultado(*docs)).ok


def test_c5_fuera_del_periodo():
    docs = [
        documento(indice=0, cufe="dentro", fecha_emision=date(2026, 10, 1)),
        documento(indice=1, cufe="fuera", fecha_emision=date(2026, 9, 30)),
    ]
    cuadre = cuadre_periodo(resultado(*docs), PERIODO)
    assert not cuadre.ok
    assert "2026-09-30" in cuadre.detalle


def test_c5_ok():
    docs = [documento(indice=0, cufe="a", fecha_emision=date(2026, 10, 31))]
    assert cuadre_periodo(resultado(*docs), PERIODO).ok


def test_c6_cliente_ausente():
    docs = [documento(indice=0, cufe="a", nit_receptor="999", nit_emisor="888")]
    cuadre = cuadre_cliente(resultado(*docs), CLIENTE)
    assert not cuadre.ok
    assert "no aparece" in cuadre.detalle


def test_c6_cliente_con_nit_de_verificacion_y_puntos():
    cliente = Cliente(nombre="Cliente", numero="901.320.747", digito_verificacion="4")
    docs = [documento(indice=0, cufe="a", nit_emisor="901320747", nit_receptor="1020396459")]
    assert cuadre_cliente(resultado(*docs), cliente).ok


def test_c6_cliente_como_receptor():
    docs = [documento(indice=0, cufe="a", nit_receptor="1020396459")]
    assert cuadre_cliente(resultado(*docs), CLIENTE).ok


def test_c7_otros_impuestos():
    docs = [
        documento(indice=0, cufe="ok"),
        documento(indice=1, cufe="inc", impuestos_otros=Decimal("500")),
    ]
    cuadre = cuadre_otros_impuestos(resultado(*docs))
    assert not cuadre.ok
    assert "otros impuestos" in cuadre.detalle


def test_c7_ok():
    docs = [documento(indice=0, cufe="a", impuestos_otros=Decimal("0"))]
    assert cuadre_otros_impuestos(resultado(*docs)).ok


def test_ejecutar_cuadres_devuelve_los_siete_en_orden():
    docs = [documento(indice=0, cufe="a", nit_receptor="1020396459")]
    cuadres = ejecutar_cuadres(
        resultado(*docs), CLIENTE, PERIODO, filas_dian=1, total_dian=Decimal("11900")
    )
    assert [c.codigo for c in cuadres] == ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
    assert not hay_cuadres_fallidos(cuadres)


def test_hay_cuadres_fallidos_ignora_no_bloqueantes():
    from dian_hojas.dominio.cuadres import ResultadoCuadre

    cuadres = (ResultadoCuadre("X", "prueba", False, "detalle", bloqueante=False),)
    assert not hay_cuadres_fallidos(cuadres)


def test_c4_detecta_documento_en_dos_bloques():
    doc = documento(indice=0, cufe="a")
    res = ResultadoMes(
        documentos=(doc,),
        bloques={
            Bloque.FACTURAS_COMPRAS: (doc,),
            Bloque.FACTURAS_VENTAS: (doc,),
            Bloque.DEVOLUCIONES_COMPRAS: (),
            Bloque.DEVOLUCIONES_VENTAS: (),
            Bloque.NOMINA: (),
        },
        excluidos=(),
        no_clasificados=(),
    )
    cuadre = cuadre_bloques(res)
    assert not cuadre.ok
    assert "más de un bloque" in cuadre.detalle
