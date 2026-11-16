"""Authenticated source delivery; the runtime key is never in the image."""
import base64
import hashlib
import hmac
import io
import os
from pathlib import Path, PurePosixPath
import sys
import zipfile

from cryptography.fernet import Fernet


def unpack(ciphertext,secret,destination):
    if len(secret)<32:raise ValueError('Runtime configuration required')
    key=base64.urlsafe_b64encode(hmac.new(secret.encode(),b'sealed-release-v1',hashlib.sha256).digest())
    body=Fernet(key).decrypt(ciphertext)
    with zipfile.ZipFile(io.BytesIO(body)) as archive:
        entries=archive.infolist()
        if len(entries)>1000 or sum(x.file_size for x in entries)>50_000_000:
            raise ValueError('Invalid release size')
        names=set()
        for entry in entries:
            path=PurePosixPath(entry.filename)
            if (path.is_absolute() or '..' in path.parts or '\\' in entry.orig_filename or ':' in entry.filename
                    or entry.filename in names or (entry.external_attr>>16)&0o170000==0o120000):
                raise ValueError('Invalid release path')
            names.add(entry.filename)
        destination=Path(destination)
        destination.mkdir(parents=True,exist_ok=True)
        for entry in entries:
            target=destination/entry.filename
            if entry.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(archive.read(entry))


def main():
    os.umask(0o077)
    root=Path('/app/product')
    unpack(Path('/app/product.enc').read_bytes(),os.environ.get(os.environ.get('RUNTIME_KEY_ENV','BOOTSTRAP_SECRET'),''),root)
    (root/'.work').mkdir(exist_ok=True)
    os.environ.update(PYTHONPATH=os.pathsep.join(str(path) for path in root.iterdir() if path.is_dir()),
                      TEMP=str(root/'.work'),TMP=str(root/'.work'))
    os.chdir(root)
    os.execv(sys.executable,[sys.executable,'-B',str(root/os.environ['RUNTIME_ENTRYPOINT'])])


if __name__=='__main__':
    try:main()
    except Exception:
        print('Sealed runtime is not configured or the release is invalid',file=sys.stderr)
        raise SystemExit(1)
