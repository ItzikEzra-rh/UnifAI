import os
import sys
import pipes
import subprocess

try:
    FileNotFoundError
except NameError:
    # Python 2
    FileNotFoundError = IOError

FIXUPS = ['_', 'OLDPWD', 'PWD', 'SHLVL']


def read_envbash(envbash, bash='bash', env=os.environ, missing_ok=False, fixups=None, args=None):
    try:
        with open(envbash):
            pass
    except FileNotFoundError:
        if missing_ok:
            return
        raise

    quoted_args = ' '.join(pipes.quote(x) for x in args or [])

    inline = '''
        set -a
        source {} {} >/dev/null
        {} -c "import os; print(repr(dict(os.environ)))"
    '''.format(pipes.quote(envbash), quoted_args, pipes.quote(sys.executable))
    with open(os.devnull) as null:
        output, _ = subprocess.Popen(
            [bash, '-c', inline],
            stdin=null, stdout=subprocess.PIPE, stderr=None,
            bufsize=-1, close_fds=True, env=env,
        ).communicate()

    if not output:
        raise ValueError("{} exited early".format(envbash))

    nenv = eval(output)

    if fixups is None:
        fixups = FIXUPS
    for f in fixups:
        if f in env:
            nenv[f] = env[f]
        elif f in nenv:
            del nenv[f]

    if sys.version_info > (3, 6) and \
            env is not os.environ and \
            nenv.get('LC_CTYPE') == 'C.UTF-8':
        del nenv['LC_CTYPE']

    return nenv


def load_envbash(envbash, into=os.environ, override=False, remove=False, **kwargs):
    loaded = read_envbash(envbash, **kwargs)
    if loaded is not None:
        if remove:
            for k in set(into) - set(loaded):
                del into[k]
        if override:
            into.update(loaded)
        else:
            for k in set(loaded) - set(into):
                into[k] = loaded[k]
