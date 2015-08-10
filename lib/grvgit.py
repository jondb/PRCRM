#grvgit.py

"""Github commands."""
import logging
import json
import subprocess
import os
import re

import grvtypes


def get_merge_commits(gitdir, branch):
    """Get merges into branch."""
    commits = get_all_commits(gitdir, branch)
    return [c for c in commits if len(c.parents) > 1]


def get_direct_commits(gitdir, branch):
    """Get commits, not merges, direct to branch."""
    commits = get_all_commits(gitdir, branch)
    return [c for c in commits if len(c.parents) == 1]


def get_all_commits(gitdir, branch):
    """Gets all direct commits to the branch."""
    return rev_list(gitdir, branch, '--first-parent', 'HEAD')


def rev_list(gitdir, branch, *args):
    """Returns list of models.Commits.

    Args:
        gitdir: local dir with git.
        branch: branch to checkout.
        *args: additional args.
    """
    # Select dir
    logging.info("Changing to dir %s.", gitdir)
    cwd = os.getcwd()
    os.chdir(gitdir)
    abs_git_dir = os.getcwd()
    logging.info("CWD: %s", os.getcwd())
    # Switch branch
    subprocess.call(['git', 'checkout', branch, '--quiet'])

    # Setup command
    command = ['git', 'rev-list', '--full-history', '--pretty=format:%H,%P,%cn,%ce,%ct']
    command.extend(args)
    res = subprocess.check_output(command)

    command = ' '.join(command)
    logging.info(command)

    # Normalize Results
    commits = []
    lines = res.split("\n")
    logging.info("Lines: %s", len(lines))

    for l in lines:
        # Some reason rev-list ignores format and always prints
        # a commit <sha> preceding the formatted line.
        if l.strip() == "" or l.startswith("commit"):
            continue
        try:
            sha, parents_string, author, email, t = l.split(',')
            parents = tuple(parents_string.split(' '))
        except ValueError as e:
            print e
            print "'%s'" % l
            exit()
        ct_added, ct_removed, ct_files, files = stats(abs_git_dir, branch, sha, parents[0], False)
        commits.append(grvtypes.Commit(
            sha,
            parents,
            author,
            email,
            t,
            ct_added,
            ct_removed,
            ct_files,
            files,
            None,
            None
            ))

    # Return results
    os.chdir(cwd)
    return commits


def update(gitdir, branch):
    """Updates the branch and returns the last commit (HEAD)."""
    cwd = os.getcwd()
    os.chdir(gitdir)
    subprocess.call(['git', 'checkout', branch, '--quiet'])
    subprocess.call(['git', 'pull', '--quiet'])
    os.chdir(cwd)
    return rev_list(gitdir, branch, 'HEAD')[0].hexsha


class GCache(object):
    def __init__(self):
        self.loaded = 0
        self.c = None

    def cache_load(self):
        if not os.path.exists(".grvcache"):
            with open(".grvcache", 'w') as cf:
                json.dump({}, cf)
        with open(".grvcache", 'r') as cf:
            c = json.load(cf)
            self.c = c
        self.loaded = 1

    def cache_get(self, id_):
        if not self.loaded:
            self.cache_load()
        if id_ in self.c:
            return self.c[id_]
        else:
            return None

    def cache_put(self, id_, val):
        self.c[id_] = val
        self.cache_save()

    def cache_save(self):
        with open(".grvcache", 'w') as cf:
            json.dump(self.c, cf)


gcache = GCache()
re_change_count = re.compile(r'([\d]*)-?\s+(\d*)-?\s+(.*)')
def stats(gitdir, branch, parent, head, checkout=True):
    """Updates the branch and returns the last commit (HEAD)."""
    cwd = os.getcwd()
    try:
        os.chdir(gitdir)
    except OSError:
        print "CWD: %s" % cwd
        raise

    cache_key = head
    res = gcache.cache_get(cache_key)

    if not res:
        ct_added, ct_removed, files = 0, 0, []
        #git diff -w --numstat d860f200f73b248b59d33e7e4cd2d79a86b9f348..4d09275d4535d7c1f5657f6a0cfb9f121ed90485
        if checkout:
            subprocess.call(['git', 'checkout', branch, '--quiet'])
        res = subprocess.check_output(['git', 'diff', '-w', '--numstat', '%s..%s' % (parent, head)])
        if res:
            for line in res.split("\n"):
                if not line:
                    continue
                mres = re_change_count.match(line)
                if not mres:
                    print "Failed", line
                    exit(1)
                # Binary files +1.
                added, removed, file_ = mres.groups()
                ct_added += int(mres.group(1) if mres.group(1) else 1)
                ct_removed += int(mres.group(2) if mres.group(2) else 0)
                files.append(mres.group(3))
        res = (ct_added, ct_removed, len(files), files)
        gcache.cache_put(cache_key, res)

    os.chdir(cwd)
    return res

