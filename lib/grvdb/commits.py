'''
test with python -m lib.grvdb.commits
'''

import sqlite3
import logging

import lib.grvtypes


class Commits(object):

    def __init__(self, db):
        self.conn = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()
        c.execute('''create table IF NOT EXISTS commits 
            (id INTEGER PRIMARY KEY, gh_owner text, gh_repo, sha text, 
            parents text, author timestamp, ct_added int,
            ct_removed int, ct_files int, files text, pr_number text,
            pr_reviewer text, parent1 text, parent2 text, ct_parents)''')
        self.conn.commit()
        c.close()
        pulls = self.readall()

    def _to_type(self, pull):
        """Reads a hash, converts to pull type.

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
        """
        tpull = lib.grvtypes.IssueComment(
                gh_owner=pull['gh_owner'],
                gh_repo=pull['gh_repo'],
                gh_user=pull['gh_user'],
                gh_user_id=pull['gh_user_id'],
                update_time=pull['update_time'],
                create_time=pull['create_time'],
                comment_id=pull['comment_id'],
                issue_number=pull['issue_number'],
                body=pull['body']
            )
        return tpull

    def readall(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM issuecomments")
        return [self._to_type(p) for p in c.fetchall()]

    def get_for_repo(self, gh_owner, gh_repo):
        """Looks up all for repo object."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM issuecomments where gh_repo=? and gh_owner=?",
            (gh_repo, gh_owner))
        return [self._to_type(p) for p in c.fetchall()]

    def add(self, ci):
        """Add a CI.
        Args:
          pull: A lib.grvtypes.CommentIssue object.
        Return:
          None
        """
        gh_owner= ci.gh_owner
        gh_repo= ci.gh_repo
        gh_user= ci.gh_user
        gh_user_id= ci.gh_user_id
        update_time= ci.update_time
        create_time= ci.create_time
        comment_id= ci.comment_id
        issue_number= ci.issue_number
        body= ci.body

        c = self.conn.cursor()

        # Store updates as new issuecomment to retain old ones.
        logging.info("Creating")
        c.execute("INSERT INTO issuecomments VALUES (NULL,?,?,?,?,?,?,?,?,?)", (
                    gh_owner, gh_repo, gh_user, 
                    gh_user_id, update_time , create_time,
                    comment_id, issue_number, body))
        self.conn.commit()
        c.close()

    def get_last_update(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM issuecomments ORDER BY update_time DESC LIMIT 1")
        last = c.fetchone()
        if last:
            return last['update_time']
        return None


if __name__ == "__main__":
    # All of these are unittests.
    # TODO(jondb): Move these to unittest.
    # run with python -m lib.grvdb.pulls
    import datetime
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Testing IssueComment class.")
    icdb = IssueComments("test.db")

    logging.info("Reading all IssueComments.")
    ics = icdb.readall()
    assert len(ics) == 0

    logging.info("Adding an IC.")
    now = datetime.datetime.utcnow()
    tpull = lib.grvtypes.IssueComment(
        gh_owner="repoowner",
        gh_repo="reponame2",
        gh_user="CommentAuthor",
        gh_user_id="CommentAuthorID",
        update_time=now,
        create_time=now,
        comment_id="11",
        issue_number="2443",
        body="Hi There"
        )
    icdb.add(tpull)

    logging.info("Adding an old pull.")
    tpull = lib.grvtypes.IssueComment(
        gh_owner="repoowner",
        gh_repo="reponame",
        gh_user="CommentAuthor",
        gh_user_id="CommentAuthorID",
        update_time=datetime.datetime(2014, 11, 14, 6, 35, 46),
        create_time=datetime.datetime(2014, 11, 14, 6, 35, 46),
        comment_id="13",
        issue_number="2443",
        body="Hi There earlier."
        )
    icdb.add(tpull)

    logging.info("Reading that it was added.")
    icdb = IssueComments("test.db")
    pulls = icdb.readall()
    assert len(pulls) == 2

    latest_update = datetime.datetime.utcnow()
    logging.info("Trying to update")
    tpull = lib.grvtypes.IssueComment(
        gh_owner="repoowner",
        gh_repo="reponame",
        gh_user="CommentAuthor",
        gh_user_id="CommentAuthorID",
        update_time=latest_update,
        create_time=datetime.datetime(2014, 11, 14, 6, 35, 46),
        comment_id="13",
        issue_number="2443",
        body="Hi There earlier."
        )
    icdb.add(tpull)

    pulls = icdb.readall()
    assert len(pulls) == 3
    pull = None
    for pull in pulls:
        if pull.comment_id == 13:
            assert pull.gh_user == "jo bob"

    logging.info("Testing get last updated")
    last_update = icdb.get_last_update()
    logging.info("now: %s, last: %s", now, last_update)
    assert (last_update == latest_update)

    logging.info("Testing get_pulls_for_gh_repo")
    
    pulls = icdb.get_for_repo(gh_owner="repoowner", gh_repo="reponame2")
    assert len(pulls) == 1

    logging.info("Dropping the table.")
    c = icdb.conn.cursor()
    c.execute("Drop table issuecomments")
    icdb.conn.commit()
    c.close()
