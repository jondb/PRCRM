#types.py

import collections


Commit = collections.namedtuple("Commit", (
        'hexsha',
        'parents',
        'author',
        'email',
        'time',
        'ct_added',
        'ct_removed',
        'ct_files',
        'files',
        'pr_number',
        'pr_reviewer'
        ))

Pull = collections.namedtuple("Pull", (
        'gh_owner', 
        'gh_repo', 
        'pull_number', 
        'pull_requester',
        'base_sha', 
        'head_sha', 
        'pull_reviewer', 
        'merge_time', 
        'pull_title', 
        'pull_updated',
        'merge_sha',
        'work_tickets'
        ))

Repo = collections.namedtuple("Repo", (
        'user',
        'repo',
        'branch',
        'gitdir'
        ))

IssueComment = collections.namedtuple("IssueComment", (
        'gh_owner',
        'gh_repo',
        'gh_user',
        'gh_user_id',
        'update_time',
        'create_time',
        'comment_id',
        'issue_number',
        'body'
        ))