"""
Contexto multempresa por petición.

FASE 3:
    La empresa se establece desde la ruta `/api/companies/<id>/...`.
    No hay autenticación todavía (llega en FASE 16). Se documenta aquí
    para no olvidar la deuda.

FASE 16:
    La empresa se establecerá exclusivamente desde el JWT
    (claim `company_id`). La ruta deberá coincidir con el JWT
    o devolver 403. Este módulo será el único punto de lectura.
"""

from flask import g


def set_current_company(company_id):
    g.current_company_id = company_id


def get_current_company_id():
    return getattr(g, 'current_company_id', None)


def clear_current_company():
    g.current_company_id = None