import os
import util as u
import sys

def setup_botw(git: bool) -> str | None:
    """Setup botw parameter directory"""
    botw_dir = u.home("botw")
    err = u.ensure(not os.path.exists(botw_dir), "botw directory already exists")
    if err: return err
    os.makedirs(botw_dir, exist_ok=True)
    _paths = [
        "Actor/ActorLink/",
        "Actor/GeneralParamList/",
        "Cooking/"
    ]
    _recur_paths = [
        "Message/",
    ]
    if git:
        _git = u.which("git")
        err = u.shell([_git, "init"], botw_dir)
        if err: return err
        _repo = "https://github.com/leoetlino/botw"
        err = u.shell([_git, "remote", "add", "origin", _repo], botw_dir)
        if err: return err
        err = u.shell([_git, "config", "core.sparseCheckout", "true"], botw_dir)
        if err: return err
        with u.fopenw(os.path.join(botw_dir, ".git", "info", "sparse-checkout")) as f:
            for _p in _paths + _recur_paths:
                f.write(_p + "\n")

        err = u.shell([_git, "pull", "--depth=1", "origin", "master"], cwd=botw_dir)
        if err: return err

        return

    gcloud = u.which("gcloud")
    for _p in _paths:
        os.makedirs(os.path.join(botw_dir, _p), exist_ok=True)
        err = u.shell([gcloud, "storage", "cp", f"gs://ist-private/leoetlino-botw/{_p}*", os.path.join(botw_dir, _p)])
        if err: return err
    for _p in _recur_paths:
        os.makedirs(os.path.join(botw_dir, _p), exist_ok=True)
        err = u.shell([gcloud, "storage", "cp", "-r", f"gs://ist-private/leoetlino-botw/{_p}*", os.path.join(botw_dir, _p)])
        if err: return err

if __name__ == "__main__":
    # If GitHub source ever goes down, use gcloud backup
    u.fatal(setup_botw(len(sys.argv) <= 1 or sys.argv[1] != "--gcloud"))
