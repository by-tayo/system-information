#!/usr/bin/env python3
"""
Windows Task-Manager-style info (console view).

Covers:
- Processes summary (like "Processes" tab)
- Process details (like "Details" tab)
- Performance summary (CPU, Memory, Disk, Network)
- Users (like "Users" tab)
- Services (like "Services" tab)

Requirements:
    - Run on Windows
    - pip install psutil
"""

import platform
import psutil
from typing import List


# ---------- guard: Windows only ----------

if platform.system() != "Windows":
    raise SystemExit("This script is intended to run on Windows only.")


# ---------- helpers ----------

def format_gib(bytes_val: int) -> str:
    return f"{bytes_val / (2 ** 30):.2f} GiB"


# ---------- performance (CPU, Memory, Disk, Network) ----------

def print_performance_summary():
    print("=== Performance (summary) ===")

    # CPU
    cpu_percent = psutil.cpu_percent(interval=1.0)
    print(f"CPU usage   : {cpu_percent:.1f}%")

    # Memory
    mem = psutil.virtual_memory()
    print(
        f"Memory      : {mem.percent:.1f}% "
        f"({format_gib(mem.used)} / {format_gib(mem.total)})"
    )

    # Disks
    disk_io = psutil.disk_io_counters(perdisk=True)
    print("Disks I/O   :")
    for name, io in disk_io.items():
        print(
            f"  {name}: reads={io.read_bytes}B writes={io.write_bytes}B"
        )

    # Network (aggregated)
    net = psutil.net_io_counters()
    print(
        f"Network I/O : sent={net.bytes_sent}B recv={net.bytes_recv}B"
    )

    print()


# ---------- processes summary (Processes tab feel) ----------

def get_top_processes(limit: int = 10):
    # Prime CPU% to get meaningful numbers
    for p in psutil.process_iter(['pid', 'name']):
        try:
            p.cpu_percent(None)
        except psutil.NoSuchProcess:
            pass

    psutil.cpu_percent(interval=0.5)

    procs = []
    for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_info']):
        try:
            info = p.info
        except psutil.NoSuchProcess:
            continue

        mem_info = info.get("memory_info")
        rss = getattr(mem_info, "rss", 0) if mem_info else 0

        procs.append(
            {
                "pid": info.get("pid"),
                "name": info.get("name") or "",
                "username": info.get("username") or "",
                "cpu_percent": info.get("cpu_percent", 0.0),
                "memory_rss_gib": format_gib(rss),
            }
        )

    procs.sort(key=lambda x: x["cpu_percent"], reverse=True)
    return procs[:limit]


def print_processes_summary(limit: int = 10):
    print(f"=== Processes (top {limit} by CPU) ===")
    top = get_top_processes(limit)
    if not top:
        print("No processes found.\n")
        return

    # Roughly like Processes tab: Name, PID, User, CPU, Memory
    for p in top:
        print(
            f"PID {p['pid']:<6} "
            f"CPU {p['cpu_percent']:5.1f}%  "
            f"MEM {p['memory_rss_gib']:>8}  "
            f"USER {p['username']}  "
            f"NAME {p['name']}"
        )
    print()


# ---------- details (Details tab style) ----------

def print_process_details(limit: int = 25):
    """
    Approximate Task Manager 'Details' tab:
      Name, PID, Status, User name, CPU, Memory (RSS), Description.
    """
    # Prime CPU
    for p in psutil.process_iter(['pid', 'name']):
        try:
            p.cpu_percent(None)
        except psutil.NoSuchProcess:
            pass
    psutil.cpu_percent(interval=0.5)

    rows: List[dict] = []
    for p in psutil.process_iter(
        ['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_info']
    ):
        try:
            info = p.info
        except psutil.NoSuchProcess:
            continue

        mem_info = info.get("memory_info")
        rss = getattr(mem_info, "rss", 0) if mem_info else 0

        rows.append(
            {
                "pid": info.get("pid"),
                "name": info.get("name") or "",
                "status": info.get("status") or "",
                "username": info.get("username") or "",
                "cpu_percent": info.get("cpu_percent", 0.0),
                "memory_rss_gib": format_gib(rss),
                # Simple description: same as name; could be extended with exe/cmdline
                "description": info.get("name") or "",
            }
        )

    rows.sort(key=lambda x: x["cpu_percent"], reverse=True)
    rows = rows[:limit]

    print(f"=== Details (top {limit} by CPU) ===")
    print("Name                            PID    Status      User              CPU%   Mem (RSS)   Description")
    print("-" * 100)
    for r in rows:
        print(
            f"{r['name'][:28]:<30}"
            f"{r['pid']:<7}"
            f"{r['status'][:10]:<12}"
            f"{r['username'][:16]:<18}"
            f"{r['cpu_percent']:5.1f}%  "
            f"{r['memory_rss_gib']:<10}"
            f"{r['description'][:30]}"
        )
    print()


# ---------- users (Users tab) ----------

def print_users():
    print("=== Users ===")
    users = psutil.users()
    if not users:
        print("No active user sessions detected.\n")
        return

    for u in users:
        print(
            f"User: {u.name}  "
            f"Host: {u.host or '-'}  "
            f"Terminal: {u.terminal or '-'}  "
            f"Started: {u.started}"
        )
    print()


# ---------- services (Services tab) ----------

def print_services(limit: int = 30):
    """
    Approximate Services tab:
      Name, PID, Description (display_name), Status, Group (N/A here).
    """
    print(f"=== Services (showing first {limit}) ===")
    try:
        services = list(psutil.win_service_iter())
    except Exception as e:
        print(f"Error reading services: {e}\n")
        return

    # Sort by name for deterministic output
    services.sort(key=lambda s: s.name().lower())

    for s in services[:limit]:
        try:
            info = s.as_dict()
        except Exception:
            continue

        name = info.get("name", "")
        display_name = info.get("display_name", "")
        status = info.get("status", "")
        pid = info.get("pid", None)

        print(
            f"Name: {name:<30}  "
            f"PID: {str(pid) if pid is not None else '-':<6}  "
            f"Status: {status:<10}  "
            f"Description: {display_name}"
        )
    print()


# ---------- main ----------

def main():
    print_performance_summary()
    print_processes_summary(limit=10)
    print_process_details(limit=25)
    print_users()
    print_services(limit=30)


if __name__ == "__main__":
    main()
