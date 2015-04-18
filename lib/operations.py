#operations.py

import collections
import logging

import grvdb
import grvgit
import grvgithub
import grvtypes


def update_pulls(db_file, gh_user, gh_owner, gh_repo):
    pdb = grvdb.Pulls(db_file)
    gh_conn = grvgithub.GRVGithub(gh_user)

    last_update_time = pdb.get_last_update()
    pulls = gh_conn.get_pulls(gh_owner, gh_repo, last_update_time=last_update_time)
 
    for pull in pulls:
        pdb.add_pull(pull)


def init_pulls(db_file, gh_user, gh_owner, gh_repo):
    """Similar to update pulls, except don't check last-update."""
    pdb = grvdb.Pulls(db_file)
    gh_conn = grvgithub.GRVGithub(gh_user)

    current_pulls = ("%s/%s" % (p.pull_number, p.pull_updated) for p in pdb.readall())

    for pull in gh_conn.get_pulls(gh_owner, gh_repo, skip_pulls=current_pulls):
        pdb.add_pull(pull)


def get_commits_with_pull(db_file, repo_dir, branch):
    """Scan pulls and repo mapping merges to pulls."""
    pullsdb = grvdb.Pulls(db_file)
    pulls = pullsdb.readall()

    commits = grvgit.get_all_commits(repo_dir, branch)
    logging.info("ct commits %s", len(commits))
    commit_index = {}
    for commit in commits:
        commit_index[commit.hexsha] = commit

    merges = [c for c in commits if len(c.parents) > 1]
    merge_heads = {}
    for merge in merges:
        merge_heads[merge.parents[1]] = merge

    # map merges to pulls
    for pull in pulls:
        if pull.head_sha in merge_heads:
            merge = merge_heads[pull.head_sha]
            c = commit_index[merge.hexsha]

            commit_index[c.hexsha] = grvtypes.Commit(
                    c.hexsha,
                    c.parents,
                    c.author,
                    c.email,
                    c.time,
                    c.ct_added,
                    c.ct_removed,
                    c.ct_files,
                    c.files,
                    pull.pull_number,
                    pull.pull_reviewer
                )

    res = [commit_index[c.hexsha] for c in commits]
    logging.info("ct res: %s", len(res))
    return res

def report_violations(db_file, repo_dir, branch):
    commits = get_commits_with_pull(db_file, repo_dir, branch)
    return [c for c in commits if not c.pr_reviewer]

def report_all(db_file, repo_dir, branch):
    commits = get_commits_with_pull(db_file, repo_dir, branch)
    return commits



