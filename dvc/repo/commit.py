from typing import TYPE_CHECKING

from . import locked

if TYPE_CHECKING:
    from . import Repo


@locked
def commit(
    self: "Repo",
    target,
    with_deps=False,
    recursive=False,
    allow_missing=False,
    data_only=False,
    relink=True,
    **kwargs,
):
    stages_info = [
        info
        for info in self.stage.collect_granular(
            target, with_deps=with_deps, recursive=recursive
        )
        if not data_only or info.stage.is_data_source
    ]
    for stage, filter_info in stages_info:
        stage.add_outs(filter_info, allow_missing=allow_missing, relink=relink)
        stage.dump(update_pipeline=False)
    return [s.stage for s in stages_info]
