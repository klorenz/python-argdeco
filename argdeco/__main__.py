from .main import Main
from .arguments import arg

from textwrap import dedent

main = Main()
command = main.command

@command('install-bash-completions',
    arg('--dest', help="destination file.  Typically ~/.bashrc or ~/.profile", default="~/.bashrc"),
    arg('script_name'),
)
def install_bash_completions(dest, script_name):
    main.install_bash_completion(dest=dest, script_name=script_name)
    print(dedent("""
        To activate bash completions of script_name run:
            . %s
    """ % dest))

@command('uninstall-bash-completions',
    arg('--dest', help="destination file.  Typically ~/.bashrc or ~/.profile", default="~/.bashrc"),
    arg('script_name'),
)
def uninstall_bash_completions(dest, script_name):
    main.uninstall_bash_completion(dest=dest, script_name=script_name)

main()
