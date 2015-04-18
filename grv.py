#!/usr/bin/env python
import datetime
import argparse
import logging
import json
import sys

import lib.operations
import lib.grvgit
import lib.grvdb


blank_config = """{
    "credentials": {
        "github_personal_access_token": "xxx"
    },
    "paths": {
        "database": "data/dbgrv.db"
    },
    "repos": [
        {
            "label": "grvtest-master",
            "github_owner": "jondb",
            "github_repo": "grvtest",
            "git_repo_dir": "data/grvtest",
            "branch": "master"
        }
    ]
}          
"""


def parse_config(cf):
    config = json.load(open(cf))
    return config


def process_args(argv):
    parser = argparse.ArgumentParser(description='Audit git repository.')
    parser.add_argument('--cf', default="config.json",
                       help='The json config file. Defaults to config.json.')
    parser.add_argument('cmd', help='What shall I do?',
                        choices=('report-all', 'update-pulls', 'update-repo',
                                 'list-merge-commits', 'blank-config', 'list-direct-commits',
                                 'list-pulls', 'list-all-commits', 'init-pulls', 'list-repos',
                                 'list-violations'))
    parser.add_argument('--label', help='Which repo/branch should I work on?')
    parser.add_argument('--verbose', action="store_true")
    parser.add_argument('--since', help='return results from now until `since` hours ago.')

    args = parser.parse_args()
    return args 


def stop_time(time, hours):
    if (datetime.datetime.now() - datetime.datetime.fromtimestamp(float(time)) > datetime.timedelta(hours=int(hours))):
        return True
    return False


def main(argv):
    """Takes command line arguments and dispatch to operations."""
    args = process_args(argv)

    if args.verbose:
        logging.basicConfig(level=logging.INFO)
        logging.info("Verbose on")

    if args.cmd == 'blank-config':
        print blank_config
        sys.exit(0)

    config = parse_config(args.cf)
    if args.cmd == 'list-repos':
        pretty = json.dumps(config["repos"], sort_keys=True,
                            indent=4, separators=(',', ': '))
        print pretty
        exit(0)
    if not "label" in args:
        raise Exception("You must choose a repo from config.")
    repos = [r for r in config["repos"] if r["label"] == args.label]
    if not repos:
        raise Exception("You must specify a valid repo.")



    repo = repos[0]

    if args.cmd in ("update-pulls", "init-pulls"):
        # TODO: This validation belongs with process_args.
        gh_owner = repo["github_owner"]
        gh_repo = repo["github_repo"]
        gh_user = config["credentials"]["github_personal_access_token"]
        db_file = config["paths"]["database"]

        if args.cmd == "update-pulls":
            lib.operations.update_pulls(db_file, gh_user, gh_owner, gh_repo)
        else:
            lib.operations.init_pulls(db_file, gh_user, gh_owner, gh_repo)
    elif args.cmd == "list-merge-commits":
        commits = lib.grvgit.get_merge_commits(repo["git_repo_dir"], repo["branch"])
        for c in commits:
            print "%s, %s, %s" % (c.hexsha, c.parents, c.time)
    elif args.cmd == "list-direct-commits":
        commits = lib.grvgit.get_direct_commits(repo["git_repo_dir"], repo["branch"])
        for c in commits:
            date = datetime.datetime.fromtimestamp(float(c.time))
            print "%s, %s, %s, %s, %s" % (c.hexsha, c.parents, date, c.author, c.email)
    elif args.cmd == "list-all-commits":
        commits = lib.grvgit.get_all_commits(repo["git_repo_dir"], repo["branch"])
        for c in commits:
            date = datetime.datetime.fromtimestamp(float(c.time))
            print "%s, %s, %s, %s, %s" % (c.hexsha, c.parents, date, c.author, c.email)
    elif args.cmd == "update-repo":
        print lib.grvgit.update(repo["git_repo_dir"], repo["branch"])
    elif args.cmd == "list-pulls":
        pullsdb = lib.grvdb.Pulls(config["paths"]["database"])
        all_pulls = pullsdb.readall()
        for pull in all_pulls:
            print pull.base_sha, pull.head_sha, pull.pull_requester, pull.pull_reviewer
    elif args.cmd == "report-all":
        gh_owner = repo["github_owner"]
        gh_repo = repo["github_repo"]
        db_file = config["paths"]["database"]
        result = lib.operations.report_all(db_file, repo["git_repo_dir"], repo["branch"])
        print_commits(result, args.since)
    elif args.cmd == "list-violations":
        gh_owner = repo["github_owner"]
        gh_repo = repo["github_repo"]
        db_file = config["paths"]["database"]
        result = lib.operations.report_all(db_file, repo["git_repo_dir"], repo["branch"])
        result = [x for x in result if not x.pr_reviewer]
        print_commits(result, args.since)


def print_commits(result, since):
        print ','.join(("Commit", "Who", "When", "What", "Reviewed", "Reviewer"))
        for rec in result:
            if since and stop_time(rec.time, since):
                break
            t = 'direct'
            if len(rec.parents) > 1:
                t = 'merge'
            if rec.pr_number:
                t = 'pull'
            print ','.join([str(x) for x in (rec.hexsha, rec.email, str(datetime.datetime.fromtimestamp(float(rec.time))), t, rec.pr_number, rec.pr_reviewer)])


if __name__ == "__main__":
    main(sys.argv)
