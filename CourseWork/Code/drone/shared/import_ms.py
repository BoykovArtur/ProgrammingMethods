"""Загрузка классов бизнес-логики из drone/modules/<module>/module/."""
import importlib.util
import sys
from pathlib import Path

MS_ROOT = Path(__file__).resolve().parent.parent
MODULES = MS_ROOT / 'modules'
IDL = MS_ROOT / 'shared' / 'idl'

if str(IDL) not in sys.path:
    sys.path.insert(0, str(IDL))

# (subsystem, module_file) -> (folder, file_stem)
MODULE_MAP = {
    ('central-control', 'delivery_orchestrator'): ('delivery_orchestrator', 'delivery_orchestrator'),
    ('communication', 'communication_module'): ('communication', 'communication_module'),
    ('communication', 'encryption_decryption'): ('encryption', 'encryption_decryption'),
    ('charging', 'charge_state_control'): ('charge_state_control', 'charge_state_control'),
    ('charging', 'charging_controller'): ('charging_controller', 'charging_controller'),
    ('cargo-grip', 'cargo_grip_control'): ('cargo_grip_control', 'cargo_grip_control'),
    ('cargo-grip', 'manipulators'): ('manipulators', 'manipulators'),
    ('coordination-lidar', 'lidar_control'): ('lidar_status_control', 'lidar_control'),
    ('coordination-lidar', 'lidars'): ('lidars', 'lidars'),
    ('coordination-qr', 'qr_recognition'): ('qr_recognition', 'qr_recognition'),
    ('coordination-qr', 'qr_validation'): ('qr_validation', 'qr_validation'),
    ('movement', 'movement_system'): ('movement', 'movement_system'),
    ('self-diagnostic', 'self_diagnostic_module'): ('self_diagnostic', 'self_diagnostic_module'),
}

_cache = {}


def _resolve_path(subsystem: str, module_file: str):
    folder, stem = MODULE_MAP.get(
        (subsystem, module_file), (subsystem, module_file)
    )
    return MODULES / folder / 'module' / f'{stem}.py'


def _load_module(subsystem: str, module_file: str):
    key = ('mod', subsystem, module_file)
    if key in _cache:
        return _cache[key]
    path = _resolve_path(subsystem, module_file)
    if not path.exists():
        raise FileNotFoundError(f'Модуль не найден: {path}')
    mod_name = f'ms_{subsystem}_{module_file}'
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    _cache[key] = mod
    return mod


def load_class(subsystem: str, module_file: str, class_name: str):
    key = ('cls', subsystem, module_file, class_name)
    if key in _cache:
        return _cache[key]
    mod = _load_module(subsystem, module_file)
    cls = getattr(mod, class_name)
    _cache[key] = cls
    return cls


def load_symbol(subsystem: str, module_file: str, name: str):
    mod = _load_module(subsystem, module_file)
    return getattr(mod, name)
