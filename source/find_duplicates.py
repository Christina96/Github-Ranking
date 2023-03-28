import csv


def count_distinct(name, title):
    with open(name, newline='') as csvfile:
        lines = csv.reader(csvfile, delimiter=',')
        distinct_links = set()
        i = 0
        for row in lines:
            # if i == 0:
            if i == 0:
                i += 1
                continue
            link = row[5]  # github repository
            distinct_links.add(link)
    print(title, len(distinct_links))


count_distinct('../Data/github-fork-ranking-2023-03-28-Java.csv', "Java forks distinct_links")
count_distinct('../Data/github-star-ranking-2023-03-28-Java.csv', "Java stars distinct_links")
count_distinct('../Data/github-fork-ranking-2023-03-28-Python.csv', "Python forks distinct_links")
count_distinct('../Data/github-star-ranking-2023-03-28-Python.csv', "Python stars distinct_links")
count_distinct('../Data/github-fork-ranking-2023-03-28-C.csv', "C forks distinct_links")
count_distinct('../Data/github-star-ranking-2023-03-28-C.csv', "C stars distinct_links")
count_distinct('../Data/github-fork-ranking-2023-03-28-CPP.csv', "CPP forks distinct_links")
count_distinct('../Data/github-star-ranking-2023-03-28-CPP.csv', "CPP stars distinct_links")
count_distinct('../Data/github-fork-ranking-2023-03-28-CSharp.csv', "CSharp forks distinct_links")
count_distinct('../Data/github-star-ranking-2023-03-28-CSharp.csv', "CSharp stars distinct_links")
