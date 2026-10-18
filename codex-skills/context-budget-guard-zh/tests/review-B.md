# 独立评审 B：context-budget-guard-zh / frozen-r1

结论：**BLOCK**。正常缺证、限额、scope 隔离和只读检查均工作；但在本机 Windows 上复现了一次误报 UNCHANGED，以及一次并发目录替换导致的短暂项目外写锁。两项都命中 acceptance.md 的硬门槛，不能沿用已有测试通过作为交付通过。

## 身份与输入

- 真实代理：`/root/snapshot_review`；角色：独立评审 B；作者：`/root`。
- 日期：2026-10-19；平台：Windows / PowerShell / 本机 Python。
- 只读输入：`D:/文档/ChatGPT/AI 2/skill-validation/context-budget-guard-zh/frozen-r1`。
- 标准：同级 `acceptance.md`；读取实际标准、完整脚本、测试、技能正文、操作说明、模板和清单。
- 七个文件 SHA256 全部与 `frozen-r1-hashes.json` 一致；脚本摘要 `D7460338940F3ED70095EDAFBEF084464CE0CDB0742A7DA497DAFB9AEC272D4D`。
- 初评未读取其他评审，未继承作者推理历史，未递归委派，未改冻结对象或真实技能，未提交或发布。附加验证只使用系统临时目录。

## 已验证结果

原有 13 个 unittest 全部通过，无跳过。独立补充案例结果如下：

| 案例 | 实际结果 | 判定 |
| --- | --- | --- |
| manifest 缺失 | UNKNOWN | 安全降级 |
| manifest > 128 KiB | UNKNOWN | 控制文件预算有效 |
| 清单项是目录 | UNKNOWN | 不读取目录 |
| baseline 截断、非法日期 | UNKNOWN | 不缺证放行 |
| 五个 8 MiB 文件，合计 40 MiB | UNKNOWN / file budget exceeded | 总量 32 MiB 限额有效 |
| 把相同源文件与缓存复制到不同根 | CHANGED | 项目根隔离有效 |
| 注入原子替换失败 | UNKNOWN；旧基线逐字节不变，无残留临时文件或锁 | 失败保存安全 |
| 六线程同时 record | 一次 RECORDED、五次 UNKNOWN；后续 check 为 UNCHANGED | 普通并发 record 保守串行 |
| 文件读至 EOF 时同尺寸改写并恢复 mtime | **UNCHANGED；实际文件为新内容** | 阻断 B1 |
| cache 验证后替换为指向项目外的目录符号链接 | **项目外 .state.lock 曾被创建**；随后 UNKNOWN 且清理锁 | 阻断 B2 |

代码审查确认：没有递归扫描、网络/模型调用或第三方依赖；每次对显式清单做完整 SHA256；check 不推进基线；记录只写控制文件；新文件、外部状态及期限不由静态哈希自动证明。2 秒是可协作读取预算，OS 阻塞和最终 fsync 不受硬超时中断，文档已有准确限制，未发现把它宣传为严格实时保证。

## B1：Windows 创建时间不能检测“读后同尺寸写入并还原 mtime”

- 严重性：P1 / BLOCK。
- 定位：`scripts/context_snapshot.py:69-94`，特别是 88-93；最终复查同样使用该指纹，位于 149-152；短路位于 183-192、238-239。
- 根因：本机运行时 `st_ctime_ns` 是创建时间。写入同一个既有文件不会更新它；写入者恢复原 `mtime` 后，前后 `(dev, ino, size, mtime, ctime)` 完全相同。SHA256 算到的是读出的旧内容，文件此时已经变成新内容，函数仍接受旧读取结果。
- 实测：基线为 128 个 `A`。在脚本读取该文件返回 EOF 的时点，原位写成 128 个 `B` 并恢复原 `mtime`。最终 JSON `status=UNCHANGED`、`can_skip_repeated_analysis=true`，实际文件首字节 `B`，前后 `st_ctime_ns` 相等。未伪造 stat、SHA256 或脚本比较结果；mock 仅把实际写入安排到可重复的竞争窗口。
- 影响：并发写入者具有恢复时间戳行为时，会错误允许跳过重复分析。普通“读完后任意时刻又有新写入”本来无法由非事务快照阻止，这里复现更窄：**写入发生在读取尚未完成且最终复查之前，现有稳定读取检测仍未识别**。
- 最小修订：取得能够证明当前读取期间未修改的依据；Windows 可读取真正的 `FILE_BASIC_INFO.ChangeTime` 并做前后与最终复核，或对明确静止的本地输入短暂持有拒写/拒删除句柄。不得只再查一遍相同 mtime/创建时间。无可靠支持时 UNKNOWN，禁止短路；保留“非事务、运行输入不短路”的现有边界。
- 复验：原 13 测试，加下方完整复现；还应验证已存在写句柄/保存竞争、异常清理和预算降级。

## B2：cache 路径校验和首次写锁之间存在目录替换窗口

- 严重性：P2 / BLOCK（严格按本次“任何越界修改”门槛；前提是另一个本地执行者能替换项目缓存目录）。
- 定位：`scripts/context_snapshot.py:224-227` 完成路径校验；`196-203` 随后按字符串路径创建/清除锁，未固定目录；`206-215` 的临时文件与替换也依赖可变化的缓存路径。
- 实测：在 `os.open(cache/'.state.lock', ...)` 前，把已校验 cache 重命名为 `old-cache`，在原地址建立指向项目外临时目录的目录符号链接。原代码确实在项目外创建 `.state.lock`。之后读取控制文件时才检测符号链接、抛 Unknown，finally 又经该路径清除了项目外锁。
- 影响：非恶意静态本地目录正常使用时不会自行出现；该脚本当前并不能把“拒绝已有符号链接”当作并发路径安全保证。虽然最后无残留，创建/删除外部文件已构成越界修改。没有证明能任意覆盖外部已有 state，不作该扩展声称。
- 最小修订：首次创建锁/临时文件之前固定并验证缓存目录及必要祖先的身份，持有不允许替换的目录句柄，或采用不跟随链接的目录相对安全操作；对最终句柄路径再次核对项目归属。单纯把 reject_links 再向前/向后挪一次不能关闭竞争窗口。操作系统/路径类型不能可靠支持时，保守禁用 record。
- 复验：下方复现必须不再在外部目录创建文件；原静态符号链接拒绝测试、正常 record、原子失败、六并发 record 均需保持。

## 完整可重跑反例

以下代码保存到系统临时目录，以 `python -B` 运行；所有构造文件均在 TemporaryDirectory，冻结脚本只被导入读取。`Path.open` / `os.open` 替换仅提供确定的竞争时点；真正的文件写入、时间恢复、目录重命名、链接创建与原脚本逻辑均实际执行。

```python
import importlib.util, json, os, pathlib, tempfile
from types import SimpleNamespace
from unittest.mock import patch

SCRIPT = pathlib.Path(r'D:/文档/ChatGPT/AI 2/skill-validation/context-budget-guard-zh/frozen-r1/scripts/context_snapshot.py')
spec = importlib.util.spec_from_file_location('review_snapshot', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture(base):
    root = pathlib.Path(base) / 'project'
    root.mkdir()
    cache = root / '.context-cache'
    cache.mkdir()
    (root / 'source.txt').write_bytes(b'A' * 128)
    manifest = {
        'schema_version': 1, 'scope_id': 'project/task/student-A',
        'current_status': 'checked', 'last_verified_at': None,
        'open_issues': [], 'external_dependencies': [],
        'files': [{'path': 'source.txt', 'kind': 'evidence', 'field': 'result'}],
    }
    (cache / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
    return root, cache

def run(root, command):
    return m.run(SimpleNamespace(root=str(root), cache_dir='.context-cache', command=command))

# B1：读至 EOF 后真实改写，恢复时间戳，然后原脚本继续 fstat/stat。
with tempfile.TemporaryDirectory() as temp:
    root, cache = fixture(temp)
    run(root, 'record')
    target = root / 'source.txt'
    stamp = target.stat()
    original_open = pathlib.Path.open
    fired = [False]
    class ReadHook:
        def __init__(self, handle): self.handle = handle
        def __enter__(self): return self
        def __exit__(self, *args): self.handle.close()
        def fileno(self): return self.handle.fileno()
        def read(self, count):
            data = self.handle.read(count)
            if not data and not fired[0]:
                fired[0] = True
                with original_open(target, 'wb') as writer:
                    writer.write(b'B' * 128)
                os.utime(target, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            return data
    def hooked_open(path, *args, **kwargs):
        handle = original_open(path, *args, **kwargs)
        return ReadHook(handle) if path == target and args and args[0] == 'rb' else handle
    with patch.object(pathlib.Path, 'open', hooked_open):
        result = run(root, 'check')
    print('B1:', result['status'], 'actual=', target.read_bytes()[:1],
          'same_ctime=', stamp.st_ctime_ns == target.stat().st_ctime_ns)

# B2：首次写锁前替换目录，记录项目外写锁的真实出现。
with tempfile.TemporaryDirectory() as temp:
    root, cache = fixture(temp)
    outside = pathlib.Path(temp) / 'outside'
    outside.mkdir()
    original_os_open = m.os.open
    observed = {}
    def hooked_os_open(path, *args, **kwargs):
        if pathlib.Path(path) == cache / '.state.lock':
            cache.rename(root / 'old-cache')
            cache.symlink_to(outside, target_is_directory=True)
            fd = original_os_open(path, *args, **kwargs)
            observed['outside_lock_created'] = (outside / '.state.lock').exists()
            return fd
        return original_os_open(path, *args, **kwargs)
    try:
        with patch.object(m.os, 'open', hooked_os_open):
            run(root, 'record')
    except Exception as exc:
        observed['error'] = type(exc).__name__ + ': ' + str(exc)
    observed['outside_lock_remains'] = (outside / '.state.lock').exists()
    cache.unlink()
    print('B2:', json.dumps(observed))
```

本机输出关键事实：

```text
B1: UNCHANGED actual= b'B' same_ctime= True
B2: outside_lock_created=true; error=Unknown: symlink/reparse path unsupported; outside_lock_remains=false
```

## 对作者提出的 r2 方案的预评估（非复验）

作者在 B 已独立形成并报告 B1 后提出：Windows 一次持有全部输入与 manifest 的拒写/拒删除只读句柄，取得全部句柄后再读取/复查；取锁失败立即 UNKNOWN；非 Windows 不宣称可短路。

该方案能够关闭 B1 的特定竞争，但仍需真实实现验证，不能自动视作通过。它不引入依赖或常驻任务，限制在 64 文件/2 秒预算内，规模有限。不过，锁成功后才开始的编辑器保存/重命名可能收到共享冲突，属于对正常外部写入的真实影响；必须限定已停止写入的静态输入，持续写入来源不短路、不等待、不重试，所有出口立即释放句柄，文档不能承诺完全无干扰。若采用真正 ChangeTime 复核可避免主动阻止外部保存，但同样必须验证其语义和失败降级。

仅保护输入文件不能单独修复 B2；需要在首次写锁前保护缓存目录路径，并核对最终句柄归属。复验还须包括同目录替换、父目录替换、已有写句柄、后来的写打开、预算/异常后句柄释放、record 临时文件与状态文件替换、根/scope 变化、check 基线不变。

## 其他范围结论与未验证项

- 地图模板含真实签名、职责、数据流、测试入口、最近变更、来源与身份；证据索引含原路径/摘要/报告位置/验证状态；符合本轮模板要求。
- 3–8 条是软目标；没有自动全局记忆写入，长期条目仅候选；禁止有损压缩保护内容，混合文本无法分离时保留原件；符合文字要求。
- 独立评审包允许评审者读更多原件，没有删减领域验收；小任务旁路、失败仅退出优化；没有框架或常驻部署。
- 本轮未验证真实大型项目的节省比例或长期吞吐；不能承诺性能完全无损。静态小文件原有测试与附加测试均在秒级完成。
- 本轮没有检查 Git 发布动作，发布尚不属于此只读冻结评审输入。
- 本报告为内部独立评审，不是正式平台认证或用户最终验收。r1 结论保留为 BLOCK；修订后必须针对新冻结版本重新验证。

# r2 独立复验追加（r1 原始结论不变）

复验结论：**PASS，限本轮文档明确的本机 Windows、显式有限清单、已停止持续写入的静态任务范围。** r1 的 B1、B2 已针对新实现分别闭环；不将 r1 的 BLOCK 改写为通过。

## 新输入与变更范围

- 同一真实独立代理 `/root/snapshot_review`，2026-10-19；仍未读取其他评审。
- 新冻结输入：同级 `frozen-r2`，七个 SHA256 均与 `frozen-r2-hashes.json` 一致。
- 脚本 SHA256：`9502A394F691C2F85D24B76A2C522182C8D007178B9FBC46C712A782FCC9D853`。
- 实际变更：脚本、测试、SKILL.md、references/operation.md；其余三个文件摘要保持 r1。
- 复核完整新脚本、新增测试与文档差异；复验仍只在系统临时目录构造案例，未修改冻结目录或真实技能。

## 阻断闭环证据

| 复验 | 实际结果 | 结论 |
| --- | --- | --- |
| r2 的全部 16 个测试 | 全通过，无跳过 | 正常流程、原保护、新增回归有效 |
| 按 r1 原始反例，在读取 EOF 时写 A→B 并恢复 mtime | UNKNOWN：file change stamp changed while reading；实际仍是 B | B1 关闭 |
| 同样在 EOF 改写，但写入句柄事先已打开且保持不关闭 | UNKNOWN；真正 ChangeTime 确实变化 | 不是只依赖写入者关闭句柄 |
| 首次 os.open(.state.lock) 前试图替换 cache | cache.rename 被拒，UNKNOWN，未创建锁/外部文件 | B2 原始窗口关闭 |
| 相同时点试图重命名项目根 | rename 被拒，UNKNOWN | 固定必要祖先有效 |
| 相同时点试图重命名系统临时任务祖先 | rename 被拒，UNKNOWN | 祖先固定没有只保护最后一级 |
| 已有写入句柄，固定目录时继续写输入；在 cache 创建/删除普通文件 | 正常写入成功；record 为 RECORDED，随后真实修改 check 为 CHANGED | 没有给输入添加拒写锁 |
| 注入 os.replace 失败 | UNKNOWN；旧 state 字节不变，无锁/临时文件残留；之后项目目录可重命名 | 失败清理和目录句柄释放有效 |
| 六线程同时 record | 一次 RECORDED、五次 UNKNOWN，后续 check 为 UNCHANGED | 普通写入串行规则未退化 |
| 64 个 128 字节文件 | record 274.67ms / check 213.69ms | 新 API 调用在本机小文件上未耗尽预算 |
| 4 个 8 MiB 文件，正好合计 32 MiB | record 106.90ms / check 67.99ms | 合法大边界仍可执行 |

独立复验的 B1 仍采用 r1 报告完整代码的 ReadHook，只把 SCRIPT 改为 frozen-r2、捕获 run 抛出的 Unknown 作为安全结果。B2 仍在原 os.open 写锁位置安排真实目录重命名；r2 的操作系统共享保护令该动作直接报 OSError，不再到达外部写锁。扩展根/祖先案例只把待重命名对象由 cache 改为 root/root.parent。以上没有伪造 stat、ChangeTime、摘要或目录共享检查结果。

## 实现检查

- `scripts/context_snapshot.py:37-86`：Windows FILE_BASIC_INFO 真实 ChangeTime，FILE_SHARE_READ|WRITE|DELETE 读取属性；创建时间不再代替变化时间；只读 API 失败仍走现有 UNKNOWN。
- `139-167`：读取前后核对新增 stamp，保留原有句柄身份/大小/mtime 检查。`222-224` 再做整批末尾检查，覆盖读后至整批完成之间的普通变更。
- `89-100`、`318-320`：record 先由祖先到 cache 打开 GENERIC_READ 目录句柄、仅共享 READ|WRITE、拒绝重解析点，然后才能创建写锁和临时文件。ExitStack 与 contextmanager 在失败后释放，不需要权限修改或常驻服务。
- `103-111`：保留 UNC/设备与 reparse 拒绝，新增映射网络盘拒绝。
- 新功能仍全部使用 Python 标准库；没有网络、模型、新第三方依赖、递归目录扫描、后台进程或全局配置变更。

## 保留边界

- 真正 ChangeTime 修复本次普通并发写入反例，但不是防恶意篡改签名，也不是所有文件同一瞬间的事务快照。持续运行实验、追加日志或平台状态仍必须走原工作流；现有文字未弱化该要求。
- record 会在短期内拒绝 cache 及其祖先目录自身的重命名/删除；这是已明确披露的相互影响。它允许目录内文件正常读写，未在本机复验中阻止普通输入保存。正在重组目录时不能 record，失败应立即降级，不等待或重试。
- 复验的毫秒数只说明本次机器与样本没有明显新瓶颈，不能推导长期负载、其它文件系统、所有机器“完全性能无损”或节省百分比。
- Windows API、权限、网络盘或路径不支持时保守 UNKNOWN；本轮没有为非 Windows record 作通过承诺。
- r1 其他文档边界与原始评审意见保留。Git 发布与远端一致性由主代理单独验证，不由本次 PASS 代替。

到本次 r2 复验结束，没有仍未关闭的必选阻断项。
