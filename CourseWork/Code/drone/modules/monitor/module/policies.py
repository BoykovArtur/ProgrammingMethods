# Политики безопасности шины событий (подмодули drone)
policies = (

    {"src": "wms", "dst": "communication"},
    {"src": "communication", "dst": "wms"},

    {"src": "communication", "dst": "encryption-decryption"},
    {"src": "encryption-decryption", "dst": "communication"},
    {"src": "encryption-decryption", "dst": "task-processing"},
    {"src": "task-processing", "dst": "encryption-decryption"},
    {"src": "task-processing", "dst": "delivery-orchestrator"},
    {"src": "task-processing", "dst": "emergency-braking"},
    {"src": "delivery-orchestrator", "dst": "task-processing"},
    {"src": "delivery-orchestrator", "dst": "navigation"},
    {"src": "delivery-orchestrator", "dst": "grip-control"},
    {"src": "grip-control", "dst": "cargo-grip-control"},
    {"src": "grip-control", "dst": "delivery-orchestrator"},
    {"src": "navigation", "dst": "delivery-orchestrator"},
    {"src": "navigation", "dst": "lidar-control"},
    {"src": "navigation", "dst": "cameras"},
    {"src": "navigation", "dst": "lidars"},
    {"src": "lidar-control", "dst": "navigation"},
    {"src": "lidar-control", "dst": "emergency-braking"},
    {"src": "lidar-control", "dst": "self-diagnostic"},
    {"src": "lidars", "dst": "lidar-control"},
    {"src": "navigation", "dst": "qr-validation"},
    {"src": "qr-recognition", "dst": "qr-validation"},
    {"src": "cameras", "dst": "qr-recognition"},
    {"src": "qr-validation", "dst": "emergency-braking"},
    {"src": "qr-validation", "dst": "self-diagnostic"},
    {"src": "qr-validation", "dst": "navigation"},
    {"src": "delivery-orchestrator", "dst": "emergency-braking"},
    {"src": "emergency-braking", "dst": "movement-system"},
    {"src": "movement-system", "dst": "emergency-braking"},
    {"src": "movement-system", "dst": "self-diagnostic"},
    {"src": "delivery-orchestrator", "dst": "cargo-grip-control"},
    {"src": "cargo-grip-control", "dst": "manipulators"},
    {"src": "manipulators", "dst": "cargo-grip-control"},
    {"src": "cargo-grip-control", "dst": "self-diagnostic"},
    {"src": "cargo-grip-control", "dst": "delivery-orchestrator"},
    {"src": "charging-controller", "dst": "charge-state-control"},
    {"src": "charge-state-control", "dst": "emergency-braking"},
    {"src": "charge-state-control", "dst": "self-diagnostic"},
    {"src": "self-diagnostic", "dst": "delivery-orchestrator"},

)


def check_operation(event_id, details) -> bool:
    src = details.get("source")
    dst = details.get("deliver_to")
    if not all((src, dst)):
        return False
    print(f"[info] checking policies for event {event_id}, {src}->{dst}")
    return {"src": src, "dst": dst} in policies
