"""Обратная совместимость — код в wms/wms.py"""
import importlib.util
from pathlib import Path

_path = Path(__file__).resolve().parent / 'wms' / 'wms.py'
_spec = importlib.util.spec_from_file_location('wms_module', _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

wms = _mod.wms
WMSSub = _mod.WMSSub

__all__ = ['wms', 'WMSSub']
