#!/usr/bin/env python3
import time
import random
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from enum import IntEnum

class Permission(IntEnum):
    NONE = 0
    READ = 1
    WRITE = 2
    EXECUTE = 4
    READ_WRITE = READ | WRITE
    READ_EXECUTE = READ | EXECUTE
    ALL = READ | WRITE | EXECUTE

@dataclass(frozen=True)
class Task:
    pid: int
    priority: int
    state: str
    burst_time: int

class PageTableEntry:
    def __init__(self, pid, base_addr, size, permissions, present=True):
        self.pid = pid
        self.base_addr = base_addr
        self.size = size
        self.permissions = permissions
        self.present = present

    def can_access(self, addr, perm):
        if not self.present:
            return False
        if addr < self.base_addr or addr >= self.base_addr + self.size:
            return False
        return (self.permissions & perm) == perm

class PageTable:
    def __init__(self):
        self.entries = {}

    def add_entry(self, entry, page_id):
        self.entries[(entry.pid, page_id)] = entry

    def lookup(self, pid, addr):
        for (entry_pid, _), entry in self.entries.items():
            if entry_pid == pid and entry.can_access(addr, Permission.READ):
                return entry
        return None

    def verify_isolation(self, pid1, pid2):
        pages1 = [entry for (entry_pid, _), entry in self.entries.items() if entry_pid == pid1]
        pages2 = [entry for (entry_pid, _), entry in self.entries.items() if entry_pid == pid2]
        for p1 in pages1:
            for p2 in pages2:
                if not (p1.base_addr + p1.size <= p2.base_addr or p2.base_addr + p2.size <= p1.base_addr):
                    return False
        return True

class Scheduler:
    def __init__(self):
        self.ready_queue = []
        self.running_task = None
        self.blocked_tasks = set()
        self.next_pid = 0

    def add_task(self, priority, burst_time):
        task = Task(pid=self.next_pid, priority=priority, state='ready', burst_time=burst_time)
        self.next_pid += 1
        self.ready_queue.append(task)
        return task

    def schedule(self):
        if not self.ready_queue:
            self.running_task = None
            return None
        self.ready_queue.sort(key=lambda t: -t.priority)
        task = self.ready_queue.pop(0)
        task = Task(pid=task.pid, priority=task.priority, state='running', burst_time=task.burst_time)
        self.running_task = task
        return task

    def block_task(self, pid):
        for i, task in enumerate(self.ready_queue):
            if task.pid == pid:
                task = self.ready_queue.pop(i)
                task = Task(pid=task.pid, priority=task.priority, state='blocked', burst_time=task.burst_time)
                self.blocked_tasks.add(task)
                return
        if self.running_task and self.running_task.pid == pid:
            task = self.running_task
            task = Task(pid=task.pid, priority=task.priority, state='blocked', burst_time=task.burst_time)
            self.blocked_tasks.add(task)
            self.running_task = None

    def unblock_task(self, pid):
        for task in list(self.blocked_tasks):
            if task.pid == pid:
                self.blocked_tasks.remove(task)
                task = Task(pid=task.pid, priority=task.priority, state='ready', burst_time=task.burst_time)
                self.ready_queue.append(task)
                break

    def verify_queue_invariant(self):
        all_tasks = set(self.ready_queue) | self.blocked_tasks
        if self.running_task:
            all_tasks.add(self.running_task)
        for task in all_tasks:
            if task.state == 'ready' and task not in self.ready_queue:
                return False
            if task.state == 'running' and task != self.running_task:
                return False
            if task.state == 'blocked' and task not in self.blocked_tasks:
                return False
        return True

class KernelState:
    def __init__(self, num_processes=10, memory_size=1024):
        self.page_table = PageTable()
        self.scheduler = Scheduler()
        self.file_descriptors = {}
        self.num_processes = num_processes

    def setup_process_memory(self, pid, base_addr, size, perm):
        entry = PageTableEntry(pid=pid, base_addr=base_addr, size=size, permissions=perm)
        self.page_table.add_entry(entry, page_id=pid)

    def syscall(self, pid, operation, *args):
        if operation == 'access_memory':
            addr, perm = args[0], args[1]
            entry = self.page_table.lookup(pid, addr)
            if entry and entry.can_access(addr, perm):
                return (True, f"Memory access granted: {addr}")
            return (False, f"Memory access denied: {addr}")
        elif operation == 'block':
            self.scheduler.block_task(pid)
            return (True, f"Process {pid} blocked")
        elif operation == 'unblock':
            self.scheduler.unblock_task(pid)
            return (True, f"Process {pid} unblocked")
        elif operation == 'open_file':
            fd, path = args[0], args[1]
            if pid not in self.file_descriptors:
                self.file_descriptors[pid] = {}
            self.file_descriptors[pid][fd] = path
            return (True, f"File {path} opened with fd {fd}")
        elif operation == 'close_file':
            fd = args[0]
            if pid in self.file_descriptors and fd in self.file_descriptors[pid]:
                del self.file_descriptors[pid][fd]
                return (True, f"File descriptor {fd} closed")
            return (False, f"Invalid file descriptor {fd}")
        return (False, f"Unknown operation: {operation}")

    def verify_isolation_invariant(self):
        for i in range(self.num_processes):
            for j in range(i + 1, self.num_processes):
                if not self.page_table.verify_isolation(i, j):
                    return False
        return True

def test_page_table_access():
    print("Testing page table access control...")
    pt = PageTable()
    entry1 = PageTableEntry(pid=0, base_addr=0, size=256, permissions=Permission.READ_WRITE)
    entry2 = PageTableEntry(pid=1, base_addr=256, size=256, permissions=Permission.READ)
    pt.add_entry(entry1, page_id=0)
    pt.add_entry(entry2, page_id=1)
    assert pt.lookup(0, 100) is not None
    assert pt.lookup(1, 300) is not None
    assert pt.lookup(0, 300) is None
    assert pt.lookup(1, 100) is None
    assert pt.lookup(2, 100) is None
    assert entry1.can_access(100, Permission.READ)
    assert entry1.can_access(100, Permission.WRITE)
    assert not entry2.can_access(300, Permission.WRITE)
    print("  Page table access control tests passed")
    return {"passed": 8, "failed": 0}

def test_memory_isolation():
    print("Testing memory isolation...")
    kernel = KernelState(num_processes=4)
    kernel.setup_process_memory(0, 0, 256, Permission.READ_WRITE)
    kernel.setup_process_memory(1, 256, 256, Permission.READ_WRITE)
    kernel.setup_process_memory(2, 512, 256, Permission.READ_WRITE)
    kernel.setup_process_memory(3, 768, 256, Permission.READ_WRITE)
    assert kernel.verify_isolation_invariant()
    success, _ = kernel.syscall(0, 'access_memory', 300, Permission.READ)
    assert not success
    success, _ = kernel.syscall(1, 'access_memory', 100, Permission.READ)
    assert not success
    print("  Memory isolation tests passed")
    return {"passed": 3, "failed": 0}

def test_scheduler_invariants():
    print("Testing scheduler invariants...")
    sched = Scheduler()
    task1 = sched.add_task(priority=1, burst_time=5)
    task2 = sched.add_task(priority=3, burst_time=3)
    task3 = sched.add_task(priority=2, burst_time=7)
    assert sched.verify_queue_invariant()
    running = sched.schedule()
    assert running.pid == task2.pid
    assert sched.verify_queue_invariant()
    sched.block_task(task2.pid)
    assert sched.verify_queue_invariant()
    assert any(t.state == 'blocked' and t.pid == task2.pid for t in sched.blocked_tasks)
    sched.unblock_task(task2.pid)
    assert sched.verify_queue_invariant()
    running = sched.schedule()
    assert running.pid == task2.pid
    print("  Scheduler invariant tests passed")
    return {"passed": 6, "failed": 0}

def test_syscall_transitions():
    print("Testing system call transitions...")
    kernel = KernelState(num_processes=2)
    kernel.setup_process_memory(0, 0, 512, Permission.READ_WRITE)
    kernel.setup_process_memory(1, 512, 512, Permission.READ_WRITE)
    success, msg = kernel.syscall(0, 'access_memory', 100, Permission.READ)
    assert success
    success, msg = kernel.syscall(0, 'access_memory', 600, Permission.READ)
    assert not success
    success, msg = kernel.syscall(0, 'open_file', 3, '/etc/passwd')
    assert success
    success, msg = kernel.syscall(0, 'close_file', 3)
    assert success
    success, msg = kernel.syscall(0, 'close_file', 3)
    assert not success
    kernel.scheduler.add_task(priority=1, burst_time=5)
    pid = kernel.scheduler.next_pid - 1
    success, msg = kernel.syscall(pid, 'block')
    assert success
    print("  System call transition tests passed")
    return {"passed": 6, "failed": 0}

def test_permission_matrix():
    print("Testing permission matrix...")
    entry = PageTableEntry(pid=0, base_addr=0, size=256, permissions=Permission.ALL)
    assert entry.can_access(100, Permission.READ)
    assert entry.can_access(100, Permission.WRITE)
    assert entry.can_access(100, Permission.EXECUTE)
    assert entry.can_access(100, Permission.READ_WRITE)
    assert entry.can_access(100, Permission.READ_EXECUTE)
    entry_restricted = PageTableEntry(pid=0, base_addr=0, size=256, permissions=Permission.READ)
    assert not entry_restricted.can_access(100, Permission.WRITE)
    assert not entry_restricted.can_access(100, Permission.READ_WRITE)
    entry_not_present = PageTableEntry(pid=0, base_addr=0, size=256, permissions=Permission.ALL, present=False)
    assert not entry_not_present.can_access(100, Permission.READ)
    print("  Permission matrix tests passed")
    return {"passed": 7, "failed": 0}

def test_inductive_invariants():
    print("Testing inductive invariants...")
    kernel = KernelState(num_processes=4)
    for i in range(4):
        kernel.setup_process_memory(i, i * 256, 256, Permission.READ_WRITE)
        kernel.scheduler.add_task(priority=i % 3, burst_time=5)
    assert kernel.verify_isolation_invariant()
    assert kernel.scheduler.verify_queue_invariant()
    for step in range(100):
        pid = random.randint(0, 3)
        op = random.choice(['access_memory', 'block', 'unblock'])
        if op == 'access_memory':
            addr = random.randint(0, 1023)
            perm = random.choice([Permission.READ, Permission.WRITE])
            kernel.syscall(pid, 'access_memory', addr, perm)
        elif op == 'block':
            kernel.syscall(pid, 'block')
        elif op == 'unblock':
            kernel.syscall(pid, 'unblock')
        assert kernel.verify_isolation_invariant()
        assert kernel.scheduler.verify_queue_invariant()
    print("  Inductive invariant tests passed (100 steps)")
    return {"passed": 200, "failed": 0}

def benchmark_kernel_operations():
    print("\nBenchmarking kernel operations...")
    results = {}
    kernel = KernelState(num_processes=10)
    for i in range(10):
        kernel.setup_process_memory(i, i * 100, 100, Permission.READ_WRITE)
    iterations = 10000
    start = time.perf_counter_ns()
    for _ in range(iterations):
        pid = random.randint(0, 9)
        addr = random.randint(0, 999)
        kernel.syscall(pid, 'access_memory', addr, Permission.READ)
    end = time.perf_counter_ns()
    results['syscall'] = (end - start) / iterations
    print(f"  Syscall: {results['syscall']:.2f} ns/op")
    pt = kernel.page_table
    start = time.perf_counter_ns()
    for _ in range(iterations):
        pid = random.randint(0, 9)
        addr = random.randint(0, 999)
        pt.lookup(pid, addr)
    end = time.perf_counter_ns()
    results['lookup'] = (end - start) / iterations
    print(f"  Page lookup: {results['lookup']:.2f} ns/op")
    sched = kernel.scheduler
    for i in range(10, 100):
        sched.add_task(priority=random.randint(1, 5), burst_time=random.randint(1, 10))
    iterations = 1000
    start = time.perf_counter_ns()
    for _ in range(iterations):
        if sched.ready_queue:
            sched.schedule()
            if sched.running_task:
                pid = sched.running_task.pid
                sched.block_task(pid)
                sched.unblock_task(pid)
    end = time.perf_counter_ns()
    results['schedule'] = (end - start) / iterations
    print(f"  Schedule cycle: {results['schedule']:.2f} ns/op")
    return results

def run_all_tests():
    print("=" * 70)
    print("DCA Chapter 25: Operating Systems and Certified Kernels Verification")
    print("=" * 70)
    print()
    results = {}
    results['page_table'] = test_page_table_access()
    results['isolation'] = test_memory_isolation()
    results['scheduler'] = test_scheduler_invariants()
    results['syscalls'] = test_syscall_transitions()
    results['permissions'] = test_permission_matrix()
    results['invariants'] = test_inductive_invariants()
    benchmark = benchmark_kernel_operations()
    print("\n" + "=" * 70)
    print("VERIFICATION SUMMARY")
    print("=" * 70)
    total_passed = sum(r['passed'] for r in results.values())
    total_failed = sum(r['failed'] for r in results.values())
    for test_name, result in results.items():
        print(f"{test_name}: {result['passed']}/{result['passed'] + result['failed']} passed")
    print(f"\nTotal: {total_passed}/{total_passed + total_failed} tests passed")
    if total_failed == 0:
        print("\nALL TESTS PASSED!")
        return {'results': results, 'benchmark': benchmark, 'all_passed': True}
    else:
        print(f"\n{total_failed} TESTS FAILED!")
        return {'results': results, 'benchmark': benchmark, 'all_passed': False}

if __name__ == "__main__":
    verification_results = run_all_tests()
    exit(0 if verification_results['all_passed'] else 1)
