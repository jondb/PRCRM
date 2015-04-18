import sqlite3
import logging

import lib.grvtypes


class Pulls(object):

    def __init__(self, db):
        self.conn = sqlite3.connect(db, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        self.conn.row_factory = sqlite3.Row
        c = self.conn.cursor()
        c.execute('''create table IF NOT EXISTS pulls 
            (id INTEGER PRIMARY KEY, gh_owner text, gh_repo text,
                pull_number text, pull_requester text, base_sha text, head_sha text,
            pull_reviewer text, merge_time timestamp, pull_title text, 
            pull_updated timestamp, merge_sha, work_tickets)''')
        self.conn.commit()
        c.close()
        pulls = self.readall()

    def _to_pull_type(self, pull):
        """Reads a hash, converts to pull type."""
        tpull = lib.grvtypes.Pull(
            gh_owner=pull['gh_owner'],
            gh_repo=pull['gh_repo'],
            pull_number=pull['pull_number'],
            pull_requester=pull['pull_requester'],
            base_sha=pull['base_sha'],
            head_sha=pull['head_sha'],
            pull_reviewer=pull['pull_reviewer'],
            merge_time=pull['merge_time'],
            pull_title=pull['pull_title'],
            pull_updated=pull['pull_updated'],
            merge_sha=pull['merge_sha'],
            work_tickets=pull['work_tickets']
            )
        return tpull

    def readall(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM pulls")
        return [self._to_pull_type(p) for p in c.fetchall()]

    def get_pulls_for_repo(self, repo):
        """Looks up all pulls for models.Repo object."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM pulls where gh_repo=? and gh_owner=?",
            (repo.repo, repo.user))
        return [self._to_pull_type(p) for p in c.fetchall()]

    def add_pull(self, pull):
        """Add or update a PR.
        Args:
          pull: A lib.types.pull object.
        Return:
          None
        """

        gh_owner = pull.gh_owner
        gh_repo = pull.gh_repo
        pull_number = pull.pull_number
        pull_requester = pull.pull_requester
        base_sha = pull.base_sha
        head_sha = pull.head_sha
        pull_reviewer = pull.pull_reviewer
        merge_time = pull.merge_time
        pull_title = pull.pull_title
        pull_updated = pull.pull_updated
        merge_sha = pull.merge_sha
        work_tickets = pull.work_tickets

        c = self.conn.cursor()
        # UPDATE?
        c.execute("SELECT 1 FROM pulls WHERE pull_number=? AND "
                  "gh_repo=? AND gh_owner=?", (pull_number, gh_repo, gh_owner))
        exists = c.fetchone()
        logging.info("updated: %s", pull_updated)

        if exists:
            logging.info("Updating")
            c.execute("UPDATE pulls SET pull_requester=?, base_sha=?, head_sha=?, pull_reviewer=?, "
                      "merge_time=?, pull_title=?, pull_updated=?, "
                      "merge_sha=?, work_tickets=? "
                      "WHERE pull_number=? AND gh_repo=? AND gh_owner=?",
                      (pull_requester, base_sha, head_sha, pull_reviewer, merge_time, pull_title, pull_updated,
                       merge_sha, work_tickets, pull_number, gh_repo, gh_owner))
        else:
            logging.info("Creating")
            c.execute("INSERT INTO pulls VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?,?)", (
                      gh_owner, gh_repo, pull_number, pull_requester, base_sha, head_sha, 
                      pull_reviewer, merge_time, pull_title, pull_updated,
                      merge_sha, work_tickets))
        self.conn.commit()
        c.close()

    def get_last_update(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM pulls ORDER BY pull_updated DESC LIMIT 1")
        last = c.fetchone()
        if last:
            return last['pull_updated']
        return None


if __name__ == "__main__":
    # All of these are unittests.
    # TODO(jondb): Move these to unittest.
    # run with python -m lib.grvdb.pulls
    import datetime
    logging.basicConfig(level=logging.DEBUG)

    logging.info("Testing pulls class.")
    pdb = Pulls("test.db")

    logging.info("Reading all pulls.")
    pulls = pdb.readall()
    assert len(pulls) == 0

    logging.info("Adding a pull.")
    now = datetime.datetime.utcnow()
    tpull = lib.grvtypes.Pull(
        gh_owner="owner1",
        gh_repo="gh_repo1",
        pull_number="10",
        pull_requester="test user",
        base_sha="xyz",
        head_sha="abc",
        pull_reviewer="jo tom",
        merge_time=datetime.datetime.utcnow(),
        pull_title="Some Pull Request Title",
        pull_updated=now,
        merge_sha=None,
        work_tickets=None,
        )
    pdb.add_pull(tpull)

    logging.info("Adding an old pull.")
    tpull = lib.grvtypes.Pull(
        gh_owner="owner",
        gh_repo="gh_repo",
        pull_number="11",
        pull_requester="test user",
        base_sha="xyz",
        head_sha="abc",
        pull_reviewer=None,
        merge_time=datetime.datetime.utcnow(),
        pull_title="Some Pull Request Title",
        pull_updated=datetime.datetime(2014, 11, 14, 6, 35, 46),
        merge_sha="fff",
        work_tickets="DSP-101",
        )
    pdb.add_pull(tpull)

    logging.info("Reading that it was added.")
    pdb = Pulls("test.db")
    pulls = pdb.readall()
    assert len(pulls) == 2

    logging.info("Trying to update")
    tpull = lib.grvtypes.Pull(
        gh_owner="owner",
        gh_repo="gh_repo",
        pull_number="11",
        pull_requester="test user",
        base_sha="xyz",
        head_sha="abc",
        pull_reviewer="jo bob",
        merge_time=datetime.datetime.utcnow(),
        pull_title="Some Pull Request Title",
        pull_updated=datetime.datetime(2014, 11, 14, 6, 35, 46),
        merge_sha="fff",
        work_tickets="DSP-101",
        )
    pdb.add_pull(tpull)

    pulls = pdb.readall()
    assert len(pulls) == 2
    pull = None
    for pull in pulls:
        if pull.pull_number == 11:
            break
    assert pull.pull_reviewer == "jo bob"

    logging.info("Testing get last updated")
    last_update = pdb.get_last_update()
    logging.info("now: %s, last: %s", now, last_update)
    assert (last_update == now)

    logging.info("Testing get_pulls_for_gh_repo")
    
    gh_repo = lib.grvtypes.Repo('owner1', 'gh_repo1', 'na', 'na')
    pulls = pdb.get_pulls_for_repo(gh_repo)
    assert len(pulls) == 1

    logging.info("Dropping the table.")
    c = pdb.conn.cursor()
    c.execute("Drop table pulls")
    pdb.conn.commit()
    c.close()
