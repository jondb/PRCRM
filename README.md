PRCRM
=====

Pull Request / Code Review / before Merge

# Overview

A tool to identify git commits that are merged into a branch but did
not have a pull request reviewed by another user.

Output in csv looks like:

    Commit,Who,When,What,Reviewed,Reviewer
    abd46734a3ab82d5b74816005d3275a032623863,rob@example.com,2015-04-17 13:07:13,pull,1162,joan
    **119887d8458b15c14c007785b30c806d0964c883,paul@example.com,2015-04-17 12:14:02,pull,None,None**
    41378f6a41ceb5490a4ebdfc37ec3961afead383,paul@example.com,2015-04-17 12:12:58,pull,1319,joan
    ...

Can be used to meet compliance goals like "all changes are reviewed," engineering policy, 
 developer best practices or adherence to strong security development lifecycle.

# Install

## 1. Setup your github token...

at https://github.com/settings/tokens/new

and include the following permissions

* repo:status
* repo
* public_repo
* user:email
* read:org

## 2. Clone this repository

    git clone https://github.com/jondb/PRCRM.git

## 3. Install requirements

    cd PRCRM
    pip install -r requirements.txt

## 4. Test it on the test repo - clone the grvtest repo to analyze

    mkdir data
    cd data
    git clone https://github.com/jondb/grvtest.git
    cd ..
    # The default config contains instructions to scan the 
    # test repository
    python grv.py blank-config > config.json
    vi config.json
    
Edit config.json by adding your github token. Replace the "xxx" with your token.

Next, run the commands

    # Create the database (cache) of github pulls
    ./grv.py --label grvtest-master update-pulls 
    # Get latest changes to github repo
    ./grv.py --label grvtest-master update-repo
    # compare pulls and commits
    ./grv.py --label grvtest-master report-all

## 5. Edit `config.json` and add your github repos to test.

    Here is the config. Add as many repos/branches as you need to test.

    {
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


# To Do

* TODO: Resolve the commit with the github user who pushed it.
* TODO: Stats on the review percent
* TODO: Stats on the number of lines not reviewed
* TODO: Provide a list of authorized reviewers
* TODO: Get list of authorized reviewers from github (owners/writers/contributers)
* TODO: Get list of authorized reviewers from git (a file)
