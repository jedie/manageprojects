from bx_py_utils.path import assert_is_dir, assert_is_file

from manageprojects.git import Git


def init_git(path, comment='The initial commit ;)') -> tuple[Git, str]:
    git = Git(cwd=path, detect_root=False)
    git_path = git.init(
        branch_name='main',
        user_name='Mr. Test',
        user_email='foo-bar@test.tld',
        verbose=False,
    )
    assert git_path == path

    assert_is_dir(path / '.git')
    assert_is_file(path / '.git' / 'config')

    assert git.get_config('user.name', verbose=False)
    assert git.get_config('user.email', verbose=False)

    git.add('.', verbose=False)
    git.commit(comment, verbose=False)
    reflog = git.reflog(verbose=False)

    assert ' commit (initial)' in reflog, reflog
    assert comment in reflog, reflog

    git_hash = git.get_current_hash(verbose=False)
    assert f'{git_hash} HEAD@' in reflog, reflog

    return git, git_hash
