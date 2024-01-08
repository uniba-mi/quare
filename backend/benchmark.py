#!/usr/bin/env python3

import glob
import logging
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

    benchmark_scenarios = [(github_access_token, repo_name, "FinishedResearchProject") for repo_name in
                           trending_github_repos] + [(github_access_token, repo_name, "InternalDocumentation")
                                                     for repo_name in trending_github_repos]

    for github_access_token, repo_name, repo_type in benchmark_scenarios:
        file_name = f"{repo_name.split('/')[1]}-{repo_type}"

        cmd = ["./shacl_validator.py", "--github_access_token", github_access_token, "--repo_name", repo_name,
               "--expected_type", repo_type]

        run(["python3", "-m", "cProfile", "-o",
             f"data/benchmarks/{file_name}", "-s", "cumulative"] + cmd)

        sleep(3)


def process_results():
    all_finished = []
    all_internal = []

    step_durations = [0, 0, 0]

    for result_file in glob.glob("./data/benchmarks/*"):
        stats = pstats.Stats(result_file)

        for k, v in stats.stats.items():
            _, _, function = k

            if function == "validate_repo_against_specs":
                if "FinishedResearchProject" in result_file:
                    all_finished.append(v[3])
                else:
                    all_internal.append(v[3])

            elif function == "create_project_type_representation":
                step_durations[0] += v[3]

            elif function == "create_repository_representation":
                step_durations[1] += v[3]

            elif function == "run_validation":
                step_durations[2] += v[3]

    _, ax = plt.subplots(figsize=(6, 3))

    ax.set(
        ylabel='Seconds',
    )

    ax.boxplot([all_finished, all_internal])

    ax.set_xticklabels(
        ["$T_{F}$", "$T_{I}$"])

    plt.tight_layout(pad=0)

    plt.savefig("./data/benchmarks/benchmark_results.pdf")

    total = sum(all_finished) + sum(all_internal)

    step_one_percent = '{:.2f}%'.format(
        step_durations[0] / total * 100)
    step_two_percent = '{:.2f}%'.format(
        step_durations[1] / total * 100)
    step_three_percent = '{:.2f}%'.format(
        step_durations[2] / total * 100)

    logging.info(
        f"Steps 1/2/3 account for {step_one_percent}/{step_two_percent}/{step_three_percent} of the total runtime.")


if __name__ == "__main__":
    run_benchmark()
    process_results()
