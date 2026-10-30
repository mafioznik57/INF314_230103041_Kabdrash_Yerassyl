import argparse
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

from common import save_json
from salt import get_student_params


def command(args):
    try:
        return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL, timeout=6).strip()
    except (OSError, subprocess.SubprocessError):
        return ''


def detect_cpu():
    system = platform.system()
    model = platform.processor() or platform.machine()
    frequency_mhz = None
    physical = None
    caches = {}
    microarchitecture = None
    if system == 'Linux':
        info = Path('/proc/cpuinfo').read_text(errors='replace') if Path('/proc/cpuinfo').exists() else ''
        m = re.search(r'^model name\s*:\s*(.+)$', info, re.M)
        model = m.group(1) if m else model
        m = re.search(r'^cpu MHz\s*:\s*([\d.]+)', info, re.M)
        frequency_mhz = float(m.group(1)) if m else None
        physical_ids = re.findall(r'^physical id\s*:\s*(\d+)', info, re.M)
        core_ids = re.findall(r'^core id\s*:\s*(\d+)', info, re.M)
        if physical_ids and len(physical_ids) == len(core_ids):
            physical = len(set(zip(physical_ids, core_ids)))
        base = Path('/sys/devices/system/cpu/cpu0/cache')
        if base.exists():
            for entry in base.glob('index*'):
                try:
                    level = (entry / 'level').read_text().strip()
                    kind = (entry / 'type').read_text().strip()
                    size = (entry / 'size').read_text().strip()
                    if level == '1' and kind == 'Data':
                        caches['L1_data'] = size
                    elif level == '2':
                        caches['L2'] = size
                    elif level == '3':
                        caches['L3'] = size
                    caches['line_bytes'] = int((entry / 'coherency_line_size').read_text())
                except (OSError, ValueError):
                    pass
    elif system == 'Darwin':
        model = command(['sysctl', '-n', 'machdep.cpu.brand_string']) or model
        for key, label in [('hw.l1dcachesize', 'L1_data'), ('hw.l2cachesize', 'L2'), ('hw.l3cachesize', 'L3')]:
            value = command(['sysctl', '-n', key])
            if value.isdigit():
                caches[label] = int(value)
        physical_value = command(['sysctl', '-n', 'hw.physicalcpu'])
        physical = int(physical_value) if physical_value.isdigit() else None
        freq = command(['sysctl', '-n', 'hw.cpufrequency'])
        frequency_mhz = int(freq) / 1e6 if freq.isdigit() else None
    elif system == 'Windows':
        output = command(['powershell', '-NoProfile', '-Command',
                          'Get-CimInstance Win32_Processor | Select-Object Name,NumberOfCores,MaxClockSpeed,L2CacheSize,L3CacheSize | ConvertTo-Json -Compress'])
        if output:
            import json
            obj = json.loads(output)
            cpus = obj if isinstance(obj, list) else [obj]
            model = cpus[0].get('Name') or model
            physical = sum(int(c.get('NumberOfCores') or 0) for c in cpus) or None
            frequency_mhz = cpus[0].get('MaxClockSpeed')
            caches['L2'] = f"{cpus[0]['L2CacheSize']} KiB" if cpus[0].get('L2CacheSize') else None
            caches['L3'] = f"{cpus[0]['L3CacheSize']} KiB" if cpus[0].get('L3CacheSize') else None
    try:
        import psutil
        physical = physical or psutil.cpu_count(logical=False)
        if not frequency_mhz and psutil.cpu_freq():
            frequency_mhz = psutil.cpu_freq().max or psutil.cpu_freq().current
    except ImportError:
        pass
    return {'model': model, 'microarchitecture': microarchitecture,
            'base_frequency_mhz': frequency_mhz, 'physical_cores': physical,
            'logical_threads': os.cpu_count(), 'smt_possible': bool(physical and os.cpu_count() > physical),
            'cache': {'L1_data': caches.get('L1_data'), 'L2': caches.get('L2'),
                      'L3': caches.get('L3'), 'line_bytes': caches.get('line_bytes')},
            'note': 'Unknown fields are null; do not interpret null as zero.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--student-id', required=True)
    args = parser.parse_args()
    params = get_student_params(args.student_id)
    save_json('salted_params.json', params)
    save_json('host_profile.json', {'cpu': detect_cpu(), 'os': platform.platform(),
                                  'kernel': platform.release(), 'python': sys.version,
                                  'implementation': platform.python_implementation()})
    print('Created host_profile.json and salted_params.json')


if __name__ == '__main__':
    main()
