# -*- coding: utf-8 -*-
"""解锁被 CWD 占用的目录：杀掉所有以该目录为工作目录的进程，然后验证。

用法:
    python unlock_project.py <dir>            # 只列出
    python unlock_project.py --kill <dir>     # 列出并杀掉
"""
import ctypes
import ctypes.wintypes as wt
import os
import sys
import time

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
nt = ctypes.WinDLL("ntdll")

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
PROCESS_VM_READ = 0x0010
PROCESS_TERMINATE = 0x0001

GENERIC_READ = 0x80000000
FILE_SHARE_READ = 0x00000001
FILE_SHARE_WRITE = 0x00000002
FILE_SHARE_DELETE = 0x00000004
OPEN_EXISTING = 3
FILE_FLAG_BACKUP_SEMANTICS = 0x02000000
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

k32.CreateFileW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                            ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
                            ctypes.c_void_p]
k32.CreateFileW.restype = ctypes.c_void_p
k32.CloseHandle.argtypes = [ctypes.c_void_p]


class PROCESS_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [("Reserved1", ctypes.c_void_p),
                ("PebBaseAddress", ctypes.c_void_p),
                ("Reserved2", ctypes.c_void_p * 2),
                ("UniqueProcessId", ctypes.c_void_p),
                ("Reserved3", ctypes.c_void_p)]


def _read(h, addr, size):
    buf = ctypes.create_string_buffer(size)
    n = ctypes.c_size_t(0)
    if not k32.ReadProcessMemory(ctypes.c_void_p(h), ctypes.c_void_p(addr),
                                 buf, size, ctypes.byref(n)):
        return None
    return buf.raw if n.value == size else None


def _u64(raw, off=0):
    return int.from_bytes(raw[off:off + 8], "little")


def proc_cwd(pid):
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION | PROCESS_VM_READ, False, pid)
        if not h:
            return None
    try:
        pbi = PROCESS_BASIC_INFORMATION()
        ret = ctypes.c_ulong(0)
        if nt.NtQueryInformationProcess(ctypes.c_void_p(h), 0, ctypes.byref(pbi),
                                        ctypes.sizeof(pbi), ctypes.byref(ret)) != 0:
            return None
        peb = pbi.PebBaseAddress
        if not peb:
            return None
        raw = _read(h, peb + 0x20, 8)
        if not raw:
            return None
        pp = _u64(raw)
        if not pp:
            return None
        raw = _read(h, pp + 0x38, 16)
        if not raw:
            return None
        length = int.from_bytes(raw[0:2], "little")
        bufptr = _u64(raw, 8)
        if length == 0 or not bufptr:
            return ""
        raw = _read(h, bufptr, length)
        return raw.decode("utf-16-le", "replace") if raw else None
    finally:
        k32.CloseHandle(ctypes.c_void_p(h))


def all_pids():
    f = getattr(k32, "K32EnumProcesses")
    arr = (wt.DWORD * 8192)()
    got = wt.DWORD(0)
    if not f(ctypes.byref(arr), ctypes.sizeof(arr), ctypes.byref(got)):
        raise RuntimeError("EnumProcesses failed")
    return list(arr)[:got.value // ctypes.sizeof(wt.DWORD)]


def proc_name(pid):
    h = k32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return "?"
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wt.DWORD(len(buf))
        if k32.QueryFullProcessImageNameW(ctypes.c_void_p(h), 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value)
        return "?"
    finally:
        k32.CloseHandle(ctypes.c_void_p(h))


def can_rename_probe(path):
    """用重命名探测是否可被替换（同步流程真正需要的操作）"""
    if not os.path.isdir(path):
        return None
    tmp = os.path.join(os.path.dirname(path), "__unlock_probe_" + str(int(time.time() * 1000) % 100000))
    try:
        os.rename(path, tmp)
    except OSError:
        return False
    try:
        os.rename(tmp, path)
    except OSError:
        pass
    return True


def holders(target):
    t = target.lower().rstrip("\\")
    out = []
    for pid in all_pids():
        if pid in (0, 4):
            continue
        if pid == os.getpid():
            continue
        cwd = proc_cwd(pid)
        if not cwd:
            continue
        if cwd.lower().rstrip("\\") == t:
            out.append((pid, proc_name(pid)))
    return out


def main():
    args = sys.argv[1:]
    do_kill = "--kill" in args
    args = [a for a in args if not a.startswith("--")]
    if not args:
        print("用法: python unlock_project.py [--kill] <dir>")
        return 1
    target = os.path.abspath(args[0])

    print("目标: %s" % target)
    print("占用前可重命名: %s" % can_rename_probe(target))
    print()

    hs = holders(target)
    print("=== 以该目录为工作目录(CWD)的进程：%d 个 ===" % len(hs))
    for pid, name in hs:
        print("   PID=%-7d %s" % (pid, name))
    print()

    if not do_kill:
        print("(未加 --kill，只列出)")
        return 0

    print("=== 开始结束这些进程 ===")
    killed, failed = 0, 0
    for pid, name in hs:
        h = k32.OpenProcess(PROCESS_TERMINATE, False, pid)
        if not h:
            print("   PID=%-7d %-16s 打不开，跳过 (err=%d)" % (pid, name, ctypes.get_last_error()))
            failed += 1
            continue
        ok = k32.TerminateProcess(ctypes.c_void_p(h), 1)
        k32.CloseHandle(ctypes.c_void_p(h))
        print("   PID=%-7d %-16s %s" % (pid, name, "已结束" if ok else "失败"))
        killed += 1 if ok else 0
        failed += 0 if ok else 1
    print("   已结束 %d 个，失败 %d 个" % (killed, failed))
    print()

    time.sleep(1.5)
    print("=== 复验 ===")
    still = holders(target)
    print("仍然持有 CWD 的进程: %d 个" % len(still))
    for pid, name in still:
        print("   PID=%-7d %s" % (pid, name))
    probe = can_rename_probe(target)
    print("现在可重命名(=同步能成功): %s" % probe)
    return 0


if __name__ == "__main__":
    sys.exit(main())
