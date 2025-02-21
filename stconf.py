#!/usr/bin/env python
import os, re, shutil

def check_component(source_root, target_root, component, owner=None):
    print(f'Processing component <{component}>')
    if re.match('.*@[0-9a-f]{32}$', component) and not component.endswith(f'@{machine_id}'):
        print('!! noop: the component is meant for other machine')
        return

    ## context
    # source and target path
    source_absolute_path = os.path.join(source_root, component)
    target_absolute_path = os.path.join(target_root, component)
    if source_absolute_path.endswith(f'@{machine_id}'):
        target_absolute_path = target_absolute_path[:-33]
        pass

    if verbose:
        print(f'++ source: {source_absolute_path}')
        print(f'++ target: {target_absolute_path}')
        pass

    # source and target content
    source_contents = set(os.listdir(source_absolute_path)) if os.path.isdir(source_absolute_path) else set()
    source_has_machine_specific = any(re.match('.*@[0-9a-f]{32}$', c) for c in source_contents)
    target_contents = set(
        path for path in os.listdir(target_absolute_path)
        if not path.startswith('.keep_')
    ) if os.path.isdir(target_absolute_path) else set()
    target_contents_has_no_directory = all(os.path.isfile(os.path.join(target_absolute_path, c)) for c in target_contents)

    if verbose:
        print(f'++ source contents: {source_contents}{"+" if source_has_machine_specific else ""}')
        print(f'++ target contents: {target_contents}')
        pass

    # default output state
    action = None
    copy_instead_of_symlink = False

    # determine if copy is required
    if any(component.startswith(pattern) for pattern in copy_includes):
        print('== target will be copied instead of symlink')
        copy_instead_of_symlink = True
        pass

    ## compare source & target to determine the final action
    # case 1: source is file - link or copy
    if os.path.isfile(source_absolute_path):
        print('== source is file')

        # always remove target if a directory
        if os.path.isdir(target_absolute_path):
            print('== target is directory, remove it if empty')
            os.rmdir(target_absolute_path)
            pass

        # case 1.1: source need to be copied
        if copy_instead_of_symlink:
            # copy nevertheless
            action = 'copy'
            print(f'!! {action}: copy file')
            pass
        # case 1.2: source could be symlinked
        else:
            # case 1.2.1: target is link
            if os.path.islink(target_absolute_path):
                # case 1.2.1.1: target links to right place
                if os.path.realpath(target_absolute_path) == os.path.realpath(source_absolute_path):
                    action = 'noop'
                    print(f'!! {action}: target already links to source')
                    pass
                # case 1.2.1.2: target links to wrong place
                else:
                    action = 'link'
                    print(f'!! {action}: target links to wrong source')
                    pass
                pass
            # case 1.2.2: target is not link
            else:
                action = 'link'
                print(f'!! {action}: target is nonexistent or file')
                pass
            pass

        # ensure target is nonexistent for link action
        if action == 'link' and os.path.exists(target_absolute_path):
            os.unlink(target_absolute_path)
            pass

        pass
    # case 2: source is dir - link or recur
    elif os.path.isdir(source_absolute_path):
        print(f'== source is directory')

        # always remove target if a directory
        if os.path.isfile(target_absolute_path):
            print('== target is file, remove it')
            os.unlink(target_absolute_path)
            pass

        # case 2.1: source need to be copied
        if copy_instead_of_symlink:
            action = 'recur'
            print(f'!! {action}: copy for directory')
            pass
        # case 2.2: source could be symlinked
        else:
            # case 2.2.1: source contains machine specific configurations
            if source_has_machine_specific:
                action = 'recur'
                print(f'!! {action}: machine specific configurations found')
                pass
            # case 2.2.2: source contains no machine specific configurations
            else:
                # case 2.2.2.1: target is empty
                # case 2.2.2.2: target has same content and no subdirectory
                if len(target_contents) == 0 or (target_contents_has_no_directory and target_contents == source_contents):
                    print('==== target is empty or same as source')
                    # case 2.2.2.2.1: target links to right place
                    if os.path.realpath(target_absolute_path) == os.path.realpath(source_absolute_path):
                        action = 'noop'
                        print(f'!! {action}: target already links to source')
                        pass
                    # case 2.2.2.2.2: target links to wrong place
                    else:
                        action = 'link'
                        print(f'!! {action}: target links to wrong source or a plain directory')
                        pass
                    pass
                # case 2.2.2.3: target has different contents
                else:
                    action = 'recur'
                    print(f'!! {action}: target has different contents')
                    pass
                pass
            pass

        # ensure the non-link dir existence for recur action
        if action == 'recur':
            if os.path.islink(target_absolute_path):
                os.unlink(target_absolute_path)
                pass

            if not os.path.exists(target_absolute_path):
                os.mkdir(target_absolute_path, 0o755)
                pass

            pass

        # ensure target is nonexistent for link action
        if action == 'link' and os.path.exists(target_absolute_path):
            if os.path.isfile(target_absolute_path):
                os.unlink(target_absolute_path)
                pass
            elif os.path.isdir(target_absolute_path):
                os.rmdir(target_absolute_path)
                pass
            pass

        pass
    else:
        print('== source is neither file nor directory')
        pass

    ## apply the actions
    if action == 'noop':
        pass
    elif action == 'copy':
        shutil.copy2(source_absolute_path, target_absolute_path, follow_symlinks = False)
        if owner is not None:
            shutil.chown(target_absolute_path, owner, owner)
            pass
        pass
    elif action == 'link':
        os.symlink(source_absolute_path, target_absolute_path)
        if owner is not None:
            shutil.chown(target_absolute_path, owner, owner)
            pass
        pass
    elif action == 'recur':
        for sub_component in source_contents:
            check_component(source_root, target_root, os.path.join(component, sub_component), owner)
            continue
        pass
    else:
        print(f'!! unknown action: <{action}>')
        pass

    return

verbose = True

source_base = '/data/repositories/conf'
target_base = '/'

source_root = os.path.join(source_base, 'etc')
target_root = os.path.join(target_base, 'etc')

copy_includes = [
    'binfmt.d',
    'env.d',
    'modules-load.d',
    'sysctl.d',
    'systemd/coredump.conf.d',
    'systemd/network',
    'tmpfiles.d',
    'udev',
] if source_root.endswith('etc') else []

with open('/etc/machine-id') as f:
    machine_id = f.read().strip()
    pass

if __name__ == '__main__':
    import sys

    owner = None

    if len(sys.argv) == 2:
        source_root = os.path.join(source_base, 'home')
        target_root = os.path.join(target_base, 'home', sys.argv[1])
        # owner = sys.argv[1]
        pass

    check_component(source_root, target_root, '', owner)
