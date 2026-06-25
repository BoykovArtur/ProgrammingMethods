from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class RouteSegment:
    qr_code: str
    distance: float


@dataclass
class RobotStatus:
    """Снимок состояния робота (IDL)."""
    id: str
    coordinates_qr: str = ''
    battery_percent: int = 100
    is_charging: bool = False
    is_move_shelf: bool = False
    is_move_station: bool = False
    take_shelf: bool = False
    is_move_back: bool = False
    is_move_home: bool = False
    route: List[str] = field(default_factory=list)
    speed: int = 0
    obstacle_distance: int = 10
    movement_interrupted: bool = False
    task_done: bool = False
    task_message: Optional[str] = None
    hacked: bool = False
    hacked_noticed: bool = False
    crossing_noticed: bool = False
    something_broken: bool = False
    something_broken_noticed: bool = False
    grab_correctly: bool = True
