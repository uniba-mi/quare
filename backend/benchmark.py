#!/usr/bin/env python3

import glob
import json
from pprint import pprint
import pstats
from subprocess import run
from time import sleep

import matplotlib.pyplot as plt


def run_benchmark():

    # retrieved 2022/03/22 from https://github.com/trending?since=monthly
    trending_github_repos = [
        "Anduin2017/HowToCook",
        "MHProDev/MHDDoS",
        "alibaba/lowcode-engine",
        "lapce/lapce",
        "EbookFoundation/free-programming-books",
        "microsoft/Web-Dev-For-Beginners",
        "peng-zhihui/Dummy-Robot",
        "doocs/advanced-java",
        "hoppscotch/hoppscotch",
        "penpot/penpot",
        "OpenIMSDK/Open-IM-Server",
        "iamadamdev/bypass-paywalls-chrome",
        "facebook/react",
        "ant-design/ant-design-mobile",
        "mdn/content",
        "BishopFox/unredacter",
        "withfig/autocomplete",
        "vuejs/vue",
        "trailofbits/algo",
        "vulhub/vulhub"
    ]

    with open("./git_access_token") as file:
        github_access_token = file.readline().strip()

    benchmark_scenarios = [(github_access_token, repo_name, "FinishedResearchProject") for repo_name in trending_github_repos] + [
        (github_access_token, repo_name, "InternalDocumentation") for repo_name in trending_github_repos]

    for github_access_token, repo_name, repo_type in benchmark_scenarios:

        cmd_owl = ["./owl_validator.py", "--github_access_token", github_access_token,
                   "--repo_name", repo_name, "--expected_type", repo_type]

        file_name = f"-{repo_name.split('/')[1]}-{repo_type}"

        run(["python3", "-m", "cProfile", "-o",
             f"data/benchmarks/OWL{file_name}", "-s", "cumulative"] + cmd_owl)

        sleep(3)

        cmd_shacl = ["./shacl_validator.py", "--github_access_token", github_access_token,
                     "--repo_name", repo_name, "--expected_type", repo_type]

        run(["python3", "-m", "cProfile", "-o",
             f"data/benchmarks/SHACL{file_name}", "-s", "cumulative"] + cmd_shacl)

        sleep(3)


def process_results():

    all_owl_finished = []
    all_shacl_finished = []
    all_owl_internal = []
    all_shacl_internal = []

    shacl_step_durations = [0, 0, 0]
    owl_step_durations = [0, 0, 0]

    for result_file in glob.glob("./data/benchmarks/SHACL-*"):
        stats = pstats.Stats(result_file)

        for k, v in stats.stats.items():
            _, _, function = k

            if function == "test_repo_against_specs":
                if "FinishedResearchProject" in result_file:
                    all_shacl_finished.append(v[3])
                else:
                    all_shacl_internal.append(v[3])

            elif function == "create_project_type_representation":
                shacl_step_durations[0] += v[3]

            elif function == "create_repository_representation":
                shacl_step_durations[1] += v[3]

            elif function == "run_validation":
                shacl_step_durations[2] += v[3]

    for result_file in glob.glob("./data/benchmarks/OWL-*"):
        stats = pstats.Stats(result_file)

        for k, v in stats.stats.items():
            _, _, function = k

            if function == "test_repo_against_specs":
                if "FinishedResearchProject" in result_file:
                    all_owl_finished.append(v[3])
                else:
                    all_owl_internal.append(v[3])

            elif function == "create_project_type_representation":
                owl_step_durations[0] += v[3]

            elif function == "create_repository_representation":
                owl_step_durations[1] += v[3]

            elif function == "run_validation":
                owl_step_durations[2] += v[3]

    _, ax = plt.subplots(figsize=(6, 3))

    ax.set(
        ylabel='Seconds',
    )

    ax.boxplot([all_shacl_finished, all_owl_finished,
                all_shacl_internal, all_owl_internal])

    ax.set_xticklabels(
        ["$SHACL, T_{F}$", "$OWL, T_{F}$", "$SHACL, T_{I}$", "$OWL, T_{I}$"])

    plt.tight_layout(pad=0)

    plt.savefig("./data/benchmarks/benchmark_results.pdf")

    owl_total = sum(all_owl_finished) + sum(all_owl_internal)
    shacl_total = sum(all_shacl_finished) + sum(all_shacl_internal)

    owl_step_one_percent = '{:.2f}%'.format(
        owl_step_durations[0]/owl_total*100)
    owl_step_two_percent = '{:.2f}%'.format(
        owl_step_durations[1]/owl_total*100)
    owl_step_three_percent = '{:.2f}%'.format(
        owl_step_durations[2]/owl_total*100)

    shacl_step_one_percent = '{:.2f}%'.format(
        shacl_step_durations[0]/shacl_total*100)
    shacl_step_two_percent = '{:.2f}%'.format(
        shacl_step_durations[1]/shacl_total*100)
    shacl_step_three_percent = '{:.2f}%'.format(
        shacl_step_durations[2]/shacl_total*100)

    print(
        f"Using the OWL approach, steps 1/2/3 account for {owl_step_one_percent}/{owl_step_two_percent}/{owl_step_three_percent} of the total runtime.")
    print(
        f"Using the SHACL approach, steps 1/2/3 account for {shacl_step_one_percent}/{shacl_step_two_percent}/{shacl_step_three_percent} of the total runtime.")


if __name__ == "__main__":
    run_benchmark()
    process_results()
