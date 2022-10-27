from bx_py_utils.path import assert_is_dir, assert_is_file

from manageprojects.git import Git


def init_git(path) -> tuple[Git, str]:
    git = Git(cwd=path, detect_root=False)
    git_path = git.init(verbose=False)
    assert git_path == path

    assert_is_dir(path / '.git')
    assert_is_file(path / '.git' / 'config')

    git.config('user.name', 'Mr. Test', verbose=False)
    assert git.get_config('user.name', verbose=False) == 'Mr. Test'

    git.config('user.email', 'foo-bar@test.tld', verbose=False)
    assert git.get_config('user.email', verbose=False) == 'foo-bar@test.tld'

    git.add('.', verbose=False)
    git.commit('The initial commit ;)', verbose=False)
    reflog = git.reflog(verbose=False)

    assert ' commit (initial)' in reflog
    assert 'The initial commit ;)' in reflog

    git_hash = git.get_current_hash(verbose=False)
    assert f'{git_hash} HEAD@' in reflog

    return git, git_hash
