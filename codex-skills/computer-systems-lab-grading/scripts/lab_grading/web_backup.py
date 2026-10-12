"""Consistent local snapshots and checked restore into a new directory only."""
import json
from contextlib import closing
from pathlib import Path, PurePosixPath
import sqlite3
import tempfile
import uuid
import zipfile

from .documents import sha256_file
from .engine import require
from .storage import now


def create_backup(service):
    with service.lock:
        require(not service.store.active(),'请等待所有批阅任务结束后备份')
        root=service.store.root;bid=uuid.uuid4().hex
        output=service.store.path('backups/'+bid+'.zip');output.parent.mkdir(exist_ok=True)
        manifest={'schema':1,'created_at':now(),'files':{}}
        try:
            with tempfile.TemporaryDirectory(prefix='lab-backup-') as temporary,zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as archive:
                files=sorted(root.rglob('*'))
                for file in files:
                    if not file.is_file() or file.is_symlink():continue
                    relative=file.relative_to(root).as_posix()
                    if relative.startswith('backups/') or file.name=='.owner.lock' or file.name.endswith(('-wal','-shm','-journal')):continue
                    source=file
                    if file.suffix=='.sqlite3':
                        source=Path(temporary)/(uuid.uuid4().hex+'.sqlite3')
                        with closing(sqlite3.connect(file)) as original,closing(sqlite3.connect(source)) as snapshot:original.backup(snapshot)
                    manifest['files'][relative]={'sha256':sha256_file(source),'size':source.stat().st_size}
                    archive.write(source,relative)
                archive.writestr('backup-manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2))
        except BaseException:
            output.unlink(missing_ok=True);raise
        return dict(id=bid,path=str(output),files=len(manifest['files']),size=output.stat().st_size,sha256=sha256_file(output))


def restore_backup(archive_path,destination):
    """Never overwrite a working database. Verify all bytes before atomic install."""
    destination=Path(destination).resolve()
    require(not destination.exists(),'恢复目录已存在，请指定一个新的空目录名')
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        infos=archive.infolist();names=[i.filename for i in infos]
        require(len(names)==len(set(names)) and len(names)<=50000,'备份包含重复条目或文件过多')
        require('backup-manifest.json' in names,'缺少备份校验清单')
        require(archive.getinfo('backup-manifest.json').file_size<=20*1024*1024,'校验清单过大')
        manifest=json.loads(archive.read('backup-manifest.json'))
        require(manifest.get('schema')==1 and isinstance(manifest.get('files'),dict),'不支持的备份版本')
        require(set(names)==set(manifest['files'])|{'backup-manifest.json'},'备份文件清单不一致')
        require(sum(i.file_size for i in infos)<=16*1024**3,'备份解压大小超过16GB')
        require('teaching.sqlite3' in manifest['files'],'缺少教学数据库')
        for info in infos:
            name=info.filename;parts=PurePosixPath(name).parts
            require(not name.startswith('/') and '\\' not in name and ':' not in name and '..' not in parts and not info.is_dir(),'备份路径不安全')
            require((info.external_attr>>16)&0o170000 != 0o120000,'备份不能包含符号链接')
        # TemporaryDirectory is owned by this operation, never an existing data root.
        with tempfile.TemporaryDirectory(prefix='.lab-restore-',dir=destination.parent) as temp:
            staging=Path(temp).resolve()/'data';staging.mkdir()
            for name,metadata in manifest['files'].items():
                target=(staging/name).resolve();require(target.is_relative_to(staging),'恢复路径越界')
                require(archive.getinfo(name).file_size==metadata['size'],'备份大小校验失败')
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.open(name) as source,target.open('xb') as out:
                    while chunk:=source.read(1024*1024):out.write(chunk)
                require(sha256_file(target)==metadata['sha256'],'备份内容指纹不一致')
            for database in staging.rglob('*.sqlite3'):
                with closing(sqlite3.connect(database)) as db:require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','备份数据库损坏')
            require(not destination.exists(),'恢复目录在操作期间已创建')
            staging.rename(destination)
    return dict(destination=str(destination),files=len(manifest['files']))
