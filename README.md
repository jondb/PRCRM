README

# Overview

A tool to identify git commits that are merged into a branch bud did
not have a pull request reviewed by another user.

Output in csv looks like:

    Commit,Who,When,What,Reviewed,Reviewer
    abd46734a3ab82d5b74816005d3275a032623863,rob@example.com,2015-04-17 13:07:13,pull,1162,joan
    **119887d8458b15c14c007785b30c806d0964c883,paul@example.com,2015-04-17 12:14:02,pull,None,None**
    41378f6a41ceb5490a4ebdfc37ec3961afead383,paul@example.com,2015-04-17 12:12:58,pull,1319,joan
    ...

Main use in meeting compliance goals like "all changes are reviewed," policy, 
or developer best practices including strong security development lifecycle.

# Install

## 1. Setup your github token

            // Github Token: https://github.com/settings/tokens/new
            // Include:
            //    repo:status
            //    repo
            //    public_repo
            //    user:email
            //    read:org

## 2. Clone the Git Review repository

    git clone <this repository>

## 3. Install PyGithub from jondb's fork

Until the updates are merged into the PyGithub main repo.

    pip install git+https://github.com/jondb/PyGithub.git@master

## 4. Clone the grvtest repo to analyze

    cd gitreview
    mkdir data
    cd data
    git clone https://github.com/jondb/grvtest.git

## 5. Setup the config.json file

    cd gitreview
    ./grv.py blank_config > config.json

Edit `config.json` and add your github token.

## 6. Analyze the grvtest repo
 
    ./grv.py --label grvtest-master update_pulls 
    ./grv.py --label grvtest-master update_repo
    ./grv.py --label grvtest-master report_all


# To Do

TODO: Resolve the commit with the github user who pushed it.
TODO: Stats on the review percent
TODO: Stats on the number of lines not reviewed
TODO: Provide a list of authorized reviewers
TODO: Get list of authorized reviewers from github (owners/writers/contributers)
TODO: Get list of authorized reviewers from git (a file)
