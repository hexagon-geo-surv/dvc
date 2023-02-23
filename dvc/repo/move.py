import os

from dvc.exceptions import MoveNotDataSourceError
from dvc.repo.scm_context import scm_context

from . import locked


def _expand_target_path(from_path, to_path):
    if os.path.isdir(to_path):
        return os.path.join(to_path, os.path.basename(from_path))
    return to_path


@locked
@scm_context
def move(self, from_path, to_path):
    """
    Renames an output file and modifies the stage associated
    to reflect the change on the pipeline.

    If the output has the same name as its stage, it would
    also rename the corresponding .dvc file.

    E.g.
          Having: (hello, hello.dvc)

          $ dvc move hello greetings

          Result: (greeting, greeting.dvc)

    It only works with outputs generated by `add` or `import`,
    also known as data sources.
    """
    from dvc import output
    from dvc.dvcfile import DVC_FILE_SUFFIX
    from dvc.stage import Stage

    from_out = output.loads_from(Stage(self), [from_path])[0]
    assert from_out.protocol == "local"

    to_path = _expand_target_path(from_path, to_path)

    outs = self.find_outs_by_path(from_out.fspath)
    assert len(outs) == 1
    out = outs[0]
    stage = out.stage

    if not stage.is_data_source:
        raise MoveNotDataSourceError(stage.addressing)

    stage_name = os.path.splitext(os.path.basename(stage.path))[0]
    from_name = os.path.basename(from_out.fspath)
    if stage_name == from_name:
        new_fname = os.path.join(
            os.path.dirname(to_path),
            os.path.basename(to_path) + DVC_FILE_SUFFIX,
        )
        new_wdir = os.path.abspath(os.path.join(os.curdir, os.path.dirname(to_path)))
        to_path = os.path.relpath(to_path, new_wdir)
        new_stage = self.stage.create(
            single_stage=True,
            fname=new_fname,
            wdir=new_wdir,
            outs=[to_path],
            meta=stage.meta,
        )

        os.unlink(stage.path)
        stage = new_stage
    else:
        to_path = os.path.relpath(to_path, stage.wdir)

    to_out = output.loads_from(stage, [to_path], out.use_cache, out.metric)[0]

    out.move(to_out)
    stage.save()
    stage.dump()
