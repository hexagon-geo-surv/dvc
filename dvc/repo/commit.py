from typing import TYPE_CHECKING

from dvc.ui import ui

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
):
    stages_info = [
        info
        for info in self.stage.collect_granular(
            target, with_deps=with_deps, recursive=recursive
        )
        if not data_only or info.stage.is_data_source
    ]

    for stage, filter_info in stages_info:
        if not filter_info:
            stage.save(allow_missing=allow_missing)
            stage.commit(allow_missing=allow_missing, relink=relink)
        else:
            stage.add_outs(filter_info, allow_missing=allow_missing, relink=relink)

        stage.dump(update_pipeline=False)
        ui.rich_print(
            "\t[bold green]Committed".expandtabs(4),
            ui.rich_text(filter_info or stage.addressing),
        )
    return [s.stage for s in stages_info]
