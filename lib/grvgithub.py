'''grvgithub.py

Wraps PyGithub
'''
import logging
import re

from github import Github as pyGithub
import lib.grvtypes


re_review = re.compile(r'lgtm|sgtm|looks good to me|sounds good to me')

class GRVGithub(pyGithub):

    def get_pulls(self, gh_owner, gh_repo, last_update_time=None, skip_pulls=None, use_search=False):
        repo = self.get_user(gh_owner).get_repo(gh_repo)
        pulls = []
        logging.info("Getting the comments.")

        if use_search:
            reviewed = []
            issue_query = 'repo:%s/%s type:pr in:comment is:closed (LGTM OR SGTM OR "looks good to me" OR "sounds good to me")' % (gh_owner, gh_repo)
            logging.info("Query: %s", issue_query)
            for issue in self.search_issues(issue_query):
                reviewed.append(issue.number)

        logging.info("Getting the pulls.")
        for pull in repo.get_pulls(state="closed", sort="updated", direction="desc"):
            if not pull.merged:
                continue
            
            updated = pull.updated_at
            logging.info("Pull %s updated at %s", pull.number, pull.updated_at)
            
            if last_update_time and updated < last_update_time:
                logging.warning("We've found the last pull. %s, %s, %s",
                        pull.number, updated, last_update_time)
                break
            
            title = pull.title
            base = pull.base.sha
            head = pull.head.sha
            number = pull.number
            reviewer = None

            if skip_pulls and "%s/%s" % (number, updated) in skip_pulls:
                logging.info("we're skipping a pull")
                continue

            # Try to identify a reviewer
            if not use_search or number in reviewed:
                comments = repo.get_issue(number).get_comments()
                for comment in comments:
                    # Ignore if the commenter is the requester.
                    if comment.user.login == pull.user.login:
                        continue

                    # Search for magic review words.
                    comment_body = comment.body.lower()
                    if re_review.search(comment_body):
                        reviewer = comment.user.login
                        break

            tpull = lib.grvtypes.Pull(
                    gh_owner=gh_owner,
                    gh_repo=gh_repo,
                    pull_number=number,
                    pull_requester=pull.user.login,
                    base_sha=base,
                    head_sha=head,
                    pull_reviewer=reviewer,
                    merge_time=pull.merged_at,
                    pull_title=title,
                    pull_updated=updated,
                    merge_sha=None,
                    work_tickets=None
                    )
            yield tpull
