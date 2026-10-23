
import multiprocessing as mp
from multiprocessing import shared_memory
import os
import time
import numpy as np

STUDENT_ID = 230103041
SIZES = (100_000, 1_000_000, 10_000_000)


def pipe_receiver(conn):
    try:
        conn.send('READY')
        while True:
            msg = conn.recv()
            if msg is None:
                break
        
            conn.send((len(msg), int(msg[0]), int(msg[-1])))
    finally:
        conn.close()


def shared_receiver(conn):
    try:
        conn.send('READY')
        while True:
            msg = conn.recv()
            if msg is None:
                break
            name, length = msg
            shm = shared_memory.SharedMemory(name=name)
            try:
                view = np.ndarray((length,), dtype=np.int64, buffer=shm.buf)
                conn.send((length, int(view[0]), int(view[-1])))
                del view
            finally:
                shm.close()
    finally:
        conn.close()


def benchmark_pipe(ctx, data):
    parent, child = ctx.Pipe()
    proc = ctx.Process(target=pipe_receiver, args=(child,))
    proc.start()
    child.close()
    assert parent.recv() == 'READY'
    try:
        start = time.perf_counter()
        parent.send(data)
        response = parent.recv() 
        elapsed = (time.perf_counter() - start) * 1000
        expected = (len(data), int(data[0]), int(data[-1]))
        assert response == expected, 'Pipe data mismatch'
        parent.send(None)
    finally:
        parent.close()
        proc.join(timeout=10)
        if proc.is_alive():
            proc.terminate()
            proc.join()
    assert proc.exitcode == 0, f'Pipe child exit code {proc.exitcode}'
    return elapsed


def benchmark_shared(ctx, data):

    shm = shared_memory.SharedMemory(create=True, size=data.nbytes)
    parent = child = proc = None
    try:
        view = np.ndarray(data.shape, dtype=data.dtype, buffer=shm.buf)
        view[:] = data
        del view
        parent, child = ctx.Pipe()
        proc = ctx.Process(target=shared_receiver, args=(child,))
        proc.start()
        child.close()
        assert parent.recv() == 'READY'
        start = time.perf_counter()
        parent.send((shm.name, len(data)))
        response = parent.recv()
        elapsed = (time.perf_counter() - start) * 1000
        expected = (len(data), int(data[0]), int(data[-1]))
        assert response == expected, 'Shared memory data mismatch'
        parent.send(None)
    finally:
        if parent is not None:
            parent.close()
        if proc is not None:
            proc.join(timeout=10)
            if proc.is_alive():
                proc.terminate()
                proc.join()
        shm.close()
        shm.unlink()
    assert proc.exitcode == 0, f'Shared child exit code {proc.exitcode}'
    return elapsed


def main():
    ctx = mp.get_context('spawn')  
    rng = np.random.default_rng(STUDENT_ID)
    lines = [f'Student ID: {STUDENT_ID}', 'Task 4 - CPU IPC Transfer vs Shared Memory',
             'Array dtype: int64',
             'Measurement: one-way data handoff plus acknowledgement; child startup excluded.',
             'Note: shared-memory initial allocation/copy excluded (already-shared buffer).',
             '', f'{"N":>12} | {"Pipe (ms)":>14} | {"Shared (ms)":>14} | {"Pipe/Shared":>12}',
             '-' * 66]
    for n in SIZES:
        arr = rng.integers(1, 11, size=n, dtype=np.int64)
        pipe_ms = benchmark_pipe(ctx, arr)
        shared_ms = benchmark_shared(ctx, arr)
        lines.append(f'{n:12,d} | {pipe_ms:14.3f} | {shared_ms:14.3f} | {pipe_ms / shared_ms:12.2f}x')
    result = '\n'.join(lines) + '\n'
    print(result, end='')
    with open('task4_output.txt', 'w', encoding='utf-8') as f:
        f.write(result)


if __name__ == '__main__':
    mp.freeze_support()
    main()
