import shutil
from os.path import join

import pytest

from dvc.repo import Repo
from dvc_data.hashfile.hash_info import HashInfo
from dvc_data.hashfile.meta import Meta


@pytest.mark.parametrize("add_or_commit", [Repo.add, Repo.commit])
def test_virtual_update(tmp_dir, dvc, remote, add_or_commit):
    tmp_dir.gen({"dir": {"foo": "foo", "bar": "bar"}})

    (stage,) = dvc.add("dir")
    out = stage.outs[0]

    assert out.hash_info == HashInfo(
        name="md5", value="5ea40360f5b4ec688df672a4db9c17d1.dir"
    )
    assert out.meta == Meta(isdir=True, size=6, nfiles=2)

    assert dvc.push() == 3
    dvc.cache.local.clear()

    tmp_dir.gen(
        {"dir": {"foobar": "foobar", "lorem": "ipsum", "subdir": {"file": "file"}}}
    )
    (stage,) = add_or_commit(dvc, "dir/foobar")

    out = stage.outs[0]
    assert out.hash_info == HashInfo(
        name="md5", value="a5beca056acbef9e0013347efdc2b751.dir"
    )
    assert out.meta == Meta(isdir=True, size=12, nfiles=3)
    assert dvc.push() == 2

    (stage,) = add_or_commit(dvc, "dir/subdir")
    out = stage.outs[0]
    assert out.hash_info == HashInfo(
        name="md5", value="de78e9fff7c3478c6b316bf08437d0f6.dir"
    )
    assert out.meta == Meta(isdir=True, size=16, nfiles=4)
    assert dvc.push() == 2


@pytest.mark.parametrize("add_or_commit", [Repo.add, Repo.commit])
def test_virtual_remove(tmp_dir, dvc, remote, add_or_commit):
    tmp_dir.gen(
        {
            "dir": {
                "foo": "foo",
                "bar": "bar",
                "subdir": {"lorem": "lorem", "ipsum": "ipsum"},
            }
        }
    )

    (stage,) = dvc.add("dir")
    out = stage.outs[0]

    assert out.hash_info == HashInfo(
        name="md5", value="15b0e3c73ad2c748ce206988cb6b7319.dir"
    )
    assert out.meta == Meta(isdir=True, size=16, nfiles=4)

    assert dvc.push() == 5
    dvc.cache.local.clear()

    (tmp_dir / "dir" / "foo").unlink()
    (stage,) = add_or_commit(dvc, "dir/foo")

    out = stage.outs[0]
    assert out.hash_info == HashInfo(
        name="md5", value="991ea7d558d320d8817a0798e9c676f1.dir"
    )
    assert out.meta == Meta(isdir=True, size=None, nfiles=3)

    assert dvc.push() == 1

    shutil.rmtree(tmp_dir / "dir" / "subdir")
    (stage,) = add_or_commit(dvc, "dir/subdir")

    out = stage.outs[0]
    assert out.hash_info == HashInfo(
        name="md5", value="91aaa9bb58b657d623ef143b195a67e4.dir"
    )
    assert out.meta == Meta(isdir=True, size=None, nfiles=1)
    assert dvc.push() == 1


@pytest.mark.parametrize("add_or_commit", [Repo.add, Repo.commit])
def test_partial_checkout_and_update(M, tmp_dir, dvc, remote, add_or_commit):
    tmp_dir.gen({"dir": {"foo": "foo", "subdir": {"lorem": "lorem"}}})

    (stage,) = dvc.add("dir")
    out = stage.outs[0]

    assert out.hash_info == HashInfo(
        name="md5", value="22a16c9bf84b3068bc2206d88a6b5776.dir"
    )
    assert out.meta == Meta(isdir=True, size=8, nfiles=2)

    assert dvc.push() == 3
    dvc.cache.local.clear()
    shutil.rmtree("dir")

    assert dvc.pull("dir/subdir") == M.dict(
        added=[join("dir", "")],
        fetched=1,
    )
    assert (tmp_dir / "dir").read_text() == {"subdir": {"lorem": "lorem"}}

    tmp_dir.gen({"dir": {"subdir": {"ipsum": "ipsum"}}})
    (stage,) = add_or_commit(dvc, "dir/subdir/ipsum")

    out = stage.outs[0]
    assert out.hash_info == HashInfo(
        name="md5", value="06d953a10e0b0ffacba04876a9351e39.dir"
    )
    assert out.meta == Meta(isdir=True, size=13, nfiles=3)
    assert dvc.push() == 2