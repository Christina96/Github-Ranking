# -*- coding: utf-8 -*-
from datetime import datetime
import os
import pandas as pd
from common import get_graphql_data, write_text, write_ranking_repo
import inspect

languages = ["Java", "Python", "C", "CPP", "CSharp"]
# languages = ["java"]
# Escape characters in markdown like # + - etc
languages_md = ["Java", "Python", "C", "C\+\+", "C\#", ]
# languages_md = ["Java"]
table_of_contents = """
* [Java](#java)
* [Python](#python)
* [C](#c)
* [C\+\+](#c-2)
* [C\#](#c-1)
"""


# table_of_contents = """
# * [Java](#java)
# """


class ProcessorGQL(object):
    """
    Github GraphQL API v4
    ref: https://docs.github.com/en/graphql
    use graphql to get data, limit 5000 points per hour
    check rate_limit with :
    curl -H "Authorization: bearer your-access-token" -X POST -d "{\"query\": \"{ rateLimit { limit cost remaining resetAt used }}\" }" https://api.github.com/graphql
    """

    def __init__(self):
        self.gql_format = """query{
    search(query: "%s", type: REPOSITORY, first:%d %s) {
      pageInfo { endCursor }
              edges {
                  node {
                    ... on Repository {
                      id,
                      name,
                      url,
                      forkCount,
                      stargazerCount,
                      description,
                      primaryLanguage {
                        name
                      }
                      pushedAt
                    }
                  }
                }
            }
        }
        """
        self.bulk_size = 100
        self.bulk_count = 10
        self.gql_stars_lang = self.gql_format % ("language:%s stars:>300 sort:stars", self.bulk_size, "%s")
        # get forks per language
        self.gql_forks_lang = self.gql_format % ("language:%s forks:>300 sort:forks", self.bulk_size, "%s")

        self.col = ['rank', 'repo_name', 'forks', 'stars', 'language', 'repo_url', 'description', 'id', 'last_commit']

    @staticmethod
    def parse_gql_result(result):
        res = []
        for repo in result["data"]["search"]["edges"]:
            repo_data = repo['node']
            res.append({
                'id': repo_data["id"],
                'name': repo_data['name'],
                'stargazers_count': repo_data['stargazerCount'],
                'forks_count': int(repo_data['forkCount']),
                'language': repo_data['primaryLanguage']['name'] if repo_data['primaryLanguage'] is not None else None,
                'html_url': repo_data['url'],
                'description': repo_data['description'],
                'last_commit': repo_data['pushedAt']
            })
        return res

    def get_repos(self, qql):
        cursor = ''
        repos = []
        for i in range(0, self.bulk_count):
            repos_gql = get_graphql_data(qql % cursor)
            cursor = ', after:"' + repos_gql["data"]["search"]["pageInfo"]["endCursor"] + '"'
            repos += self.parse_gql_result(repos_gql)
        return repos

    def get_all_repos(self):
        repos_languages = {}
        for lang in languages:
            print("Get most stars repos of {}...".format(lang))
            repos_languages[lang] = self.get_repos(self.gql_stars_lang % (lang, '%s'))
            print("Get most stars repos of {} success!".format(lang))

        repos_forks_languages = {}
        for lang in languages:
            print("Get most forks repos of {}...".format(lang))
            repos_forks_languages[lang] = self.get_repos(self.gql_forks_lang % (lang, '%s'))
            print("Get most forks repos of {} success!".format(lang))

        return repos_languages, repos_forks_languages


class WriteFile(object):
    def __init__(self, repos_languages, forks_languages):
        self.repos_languages = repos_languages
        self.forks_languages = forks_languages
        self.col = ['rank', 'repo_name', 'forks', 'stars', 'language', 'repo_url', 'description', 'id', 'last_commit']
        self.star_languages = []
        self.fork_languages = []
        if len(repos_languages) > 0:
            for i in range(len(languages)):
                lang = languages[i]
                lang_md = languages_md[i]
                self.star_languages.append({
                    "desc": "Forks",
                    "desc_md": "Forks",
                    "title_readme": lang_md,
                    "title_1000": f"Top 1000 Stars in {lang_md}",
                    "file_1000": f"{lang}-stars.md",
                    "data": repos_languages[lang],
                    "item": lang,
                })
        for i in range(len(languages)):
            lang = languages[i]
            lang_md = languages_md[i]
            self.fork_languages.append({
                "desc": "Forks",
                "desc_md": "Forks",
                "title_readme": lang_md,
                "title_1000": f"Top 1000 Forks in {lang_md}",
                "file_1000": f"{lang}-forks.md",
                "data": forks_languages[lang],
                "item": lang,
            })

    @staticmethod
    def write_head_contents():
        # write the head and contents of README.md
        write_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        head_contents = inspect.cleandoc("""[Github Ranking](./README.md)
                ==========
    
                **A list of the most github stars and forks repositories.**
    
                *Last Update Time: {write_time}*
    
                ## Table of Contents
    
                """.format(write_time=write_time)) + table_of_contents
        write_text("../README.md", 'w', head_contents)

    def write_readme_lang_md(self):
        os.makedirs('../Top1000', exist_ok=True)
        for repo in self.star_languages:
            WriteFile.write_file(repo)
        for repo in self.fork_languages:
            WriteFile.write_file(repo)

    @staticmethod
    def write_file(repo):
        # README.md
        title_readme, title_1000, file_1000, data = repo["title_readme"], repo["title_1000"], repo["file_1000"], \
            repo[
                "data"]
        write_text('../README.md', 'a',
                   f"\n## {title_readme}\n\nThis is top 10, for more click **[{title_1000}](Top1000/{file_1000})**\n\n")
        write_ranking_repo('../README.md', 'a', data[:10])
        print(f"Save {title_readme} in README.md!")

        # Top 1000 file forks
        write_text(f"../Top1000/{file_1000}", "w",
                   f"[Github Ranking](../README.md)\n==========\n\n## {title_1000}\n\n")
        write_ranking_repo(f"../Top1000/{file_1000}", 'a', data)
        print(f"Save {title_1000} in Top1000/{file_1000}!\n")

    def repo_to_df(self, repos):
        # prepare for saving data to csv file
        repos_list = []
        for idx, repo in enumerate(repos):
            repo_info = [idx + 1, repo['name'], repo['forks_count'], repo['stargazers_count'], repo['language'],
                         repo['html_url'], repo['description'], repo['id'], repo['last_commit']]
            repos_list.append(repo_info)
        return pd.DataFrame(repos_list, columns=self.col)

    def save_to_csv(self):
        # save top1000 repos info to csv file in Data/github-ranking-year-month-day.md

        for repo in self.star_languages:
            print(f"Star Languages CSV {repo['item']}")
            df_all = pd.DataFrame(columns=self.col)
            print(repo)
            df_repos = self.repo_to_df(repos=repo["data"])
            df_all = df_all.append(df_repos, ignore_index=True)
            df_all = df_all.sort_values(by=['stars'], ascending=False)
            save_date = datetime.utcnow().strftime("%Y-%m-%d")
            os.makedirs('../Data', exist_ok=True)
            df_all.to_csv('../Data/github-star-ranking-' + save_date + '-' + repo["item"] + '.csv', index=False,
                          encoding='utf-8')
            print('Save data to Data/github-star-ranking-' + save_date + '-' + repo["item"] + '.csv')

        for repo in self.fork_languages:
            print(f"Fork Languages CSV {repo['item']}")
            df_all = pd.DataFrame(columns=self.col)
            df_repos = self.repo_to_df(repos=repo["data"])
            df_all = df_all.append(df_repos, ignore_index=True)
            df_all = df_all.sort_values(by=['forks'], ascending=False)
            save_date = datetime.utcnow().strftime("%Y-%m-%d")
            os.makedirs('../Data', exist_ok=True)
            df_all.to_csv('../Data/github-fork-ranking-' + save_date + '-' + repo["item"] + '.csv', index=False,
                          encoding='utf-8')
            print('Save data to Data/github-fork-ranking-' + save_date + '-' + repo["item"] + '.csv')


def run_by_gql():
    ROOT_PATH = os.path.abspath(os.path.join(__file__, "../../"))
    os.chdir(os.path.join(ROOT_PATH, 'source'))

    processor = ProcessorGQL()  # use Github GraphQL API v4
    repos_languages, repos_forks_languages = processor.get_all_repos()
    print("Retrieve all repos. Start writing file")
    wt_obj = WriteFile(repos_languages, repos_forks_languages)
    wt_obj.write_head_contents()
    wt_obj.write_head_contents()
    wt_obj.write_readme_lang_md()
    wt_obj.save_to_csv()


if __name__ == "__main__":
    t1 = datetime.now()
    run_by_gql()
    print("Total time: {}s".format((datetime.now() - t1).total_seconds()))
