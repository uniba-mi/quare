#!/usr/bin/env python3

import json
import logging
import pstats
from subprocess import run
from time import sleep

import numpy as np
from github import UnknownObjectException, Github, Auth
from matplotlib import pyplot as plt
from brokenaxes import brokenaxes

import validation_interface, verbalization_interface

logging.basicConfig(level=logging.INFO)

def perform_evaluation() -> None:
    with open(".github_access_token") as file:
        github_access_token = file.readline().strip()

    repos_expected_to_be_fair = get_repos_expected_to_be_fair()
    trending_repos = get_trending_repo_set()

    results_per_criterion_fair = get_validation_result_per_criterion(repos_expected_to_be_fair, github_access_token)
    with open("./data/evaluation/repos_expected_to_be_fair.json", "w") as file:
        json.dump(results_per_criterion_fair, file)

    results_per_criterion_trending = get_validation_result_per_criterion(trending_repos, github_access_token)
    with open("./data/evaluation/trending_repos.json", "w") as file:
        json.dump(results_per_criterion_trending, file)

    runtime_benchmark_results = execute_runtime_benchmark(repos_expected_to_be_fair, trending_repos, github_access_token)
    with open("./data/evaluation/runtime_benchmark_results.json", "w") as file:
        json.dump(runtime_benchmark_results, file)


def get_repos_expected_to_be_fair() -> list[str]:
    return ["oeg-upm/oeg-software-graph", "zenodraft/zenodraft",
            "comses-education/wolf-sheep", "fair-software/howfairis",
            "GrainLearning/grainLearning", "online-behaviour/machine-learning"]


def get_trending_repo_set() -> list[str]:
    # First 20 repositories on the 15th of each month from https://github.com/trending?since=monthly (via Web Archive)
    trending_github_repos = {
        "march_2023": [
            "lllyasviel/ControlNet",
            "hpcaitech/ColossalAI",
            "AUTOMATIC1111/stable-diffusion-webui",
            "amazon-science/mm-cot",
            "usememos/memos",
            "civitai/civitai",
            "ggerganov/whisper.cpp",
            "zhayujie/chatgpt-on-wechat",
            "openai/openai-python",
            "f/awesome-chatgpt-prompts",
            "mrsked/mrsk",
            "yt-dlp/yt-dlp",
            "zloirock/core-js",
            "Asabeneh/30-Days-Of-Python",
            "jaymody/picoGPT",
            "bmaltais/kohya_ss",
            "ytdl-org/youtube-dl",
            "alibaba/lowcode-engine",
            "NAStool/nas-tools",
            "CompVis/stable-diffusion"
        ], "april_2023": [
            "tloen/alpaca-lora",
            "cocktailpeanut/dalai",
            "THUDM/ChatGLM-6B",
            "ggerganov/llama.cpp",
            "tatsu-lab/stanford_alpaca",
            "GaiZhenbiao/ChuanhuChatGPT",
            "hwchase17/langchain",
            "microsoft/DeepSpeed",
            "Chanzhaoyu/chatgpt-web",
            "oobabooga/text-generation-webui",
            "gencay/vscode-chatgpt",
            "PlexPt/awesome-chatgpt-prompts-zh",
            "shadcn/taxonomy",
            "apple/ml-stable-diffusion",
            "ConnectAI-E/Feishu-OpenAI",
            "ztjhz/BetterChatGPT",
            "kaixindelele/ChatPaper",
            "AUTOMATIC1111/stable-diffusion-webui",
            "comfyanonymous/ComfyUI",
            "chathub-dev/chathub"
        ], "may_2023": [
            "Significant-Gravitas/Auto-GPT",
            "voicepaw/so-vits-svc-fork",
            "reworkd/AgentGPT",
            "Ryujinx/Ryujinx",
            "LAION-AI/Open-Assistant",
            "imClumsyPanda/langchain-ChatGLM",
            "svc-develop-team/so-vits-svc",
            "pengzhile/pandora",
            "hwchase17/langchain",
            "lllyasviel/ControlNet-v1-1-nightly",
            "facebookresearch/AnimatedDrawings",
            "qdrant/qdrant",
            "gkamradt/langchain-tutorials",
            "RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
            "l15y/wenda",
            "TheRamU/Fay",
            "Yidadaa/ChatGPT-Next-Web",
            "bluesky-social/atproto",
            "shadcn/ui",
            "calcom/cal.com"
        ], "june_2023": [
            "microsoft/guidance",
            "smol-ai/developer",
            "sunner/ChatALL",
            "google/comprehensive-rust",
            "makeplane/plane",
            "facebookresearch/fairseq",
            "imartinez/privateGPT",
            "pengzhile/pandora",
            "xiangsx/gpt4free-ts",
            "csunny/DB-GPT",
            "FlowiseAI/Flowise",
            "geohot/tinygrad",
            "iperov/DeepFaceLive",
            "steven-tey/dub",
            "langgenius/dify",
            "alibaba/Chat2DB",
            "go-skynet/LocalAI",
            "JushBJJ/Mr.-Ranedeer-AI-Tutor",
            "iv-org/invidious",
            "RVC-Project/Retrieval-based-Voice-Conversion-WebUI"
        ], "july_2023": [
            "AntonOsika/gpt-engineer",
            "AI4Finance-Foundation/FinGPT",
            "alibaba/ali-dbhub",
            "baichuan-inc/Baichuan-7B",
            "tinygrad/tinygrad",
            "StanGirard/quivr",
            "h2oai/h2ogpt",
            "CodeEditApp/CodeEdit",
            "vercel/platforms",
            "toeverything/AFFiNE",
            "Uniswap/v4-core",
            "LemmyNet/lemmy",
            "sveltejs/svelte",
            "facebookresearch/ijepa",
            "hiyouga/ChatGLM-Efficient-Tuning",
            "mastodon/mastodon",
            "Mintplex-Labs/anything-llm",
            "996icu/996.ICU",
            "RVC-Project/Retrieval-based-Voice-Conversion-WebUI",
            "loft-sh/devpod"
        ], "august_2023": [
            "facebookresearch/llama",
            "geekan/MetaGPT",
            "bregman-arie/devops-exercises",
            "comfyanonymous/ComfyUI",
            "nextui-org/nextui",
            "OpenBMB/ToolBench",
            "Stability-AI/generative-models",
            "EbookFoundation/free-programming-books",
            "facebookresearch/audiocraft",
            "invoke-ai/InvokeAI",
            "Codium-ai/pr-agent",
            "kenjihiranabe/The-Art-of-Linear-Algebra",
            "Dao-AILab/flash-attention",
            "DioxusLabs/dioxus",
            "reflex-dev/reflex",
            "bazingagin/npc_gzip",
            "oobabooga/text-generation-webui",
            "vercel/commerce",
            "krahets/hello-algo",
            "songquanpeng/one-api"
        ], "september_2023": [
            "oven-sh/bun",
            "opentffoundation/manifesto",
            "krahets/hello-algo",
            "lllyasviel/Fooocus",
            "hehonghui/awesome-english-ebooks",
            "kuafuai/DevOpsGPT",
            "graphdeco-inria/gaussian-splatting",
            "modelscope/facechain",
            "zanfranceschi/rinha-de-backend-2023-q3",
            "Z4nzu/hackingtool",
            "a16z-infra/ai-town",
            "phoboslab/wipeout-rewrite",
            "organicmaps/organicmaps",
            "NVlabs/neuralangelo",
            "pedroslopez/whatsapp-web.js",
            "documenso/documenso",
            "prasanthrangan/hyprdots",
            "IceWhaleTech/CasaOS",
            "nlpxucan/WizardLM",
            "ymcui/Chinese-LLaMA-Alpaca-2"
        ], "october_2023": [
            "OpenBMB/ChatDev",
            "opentofu/opentofu",
            "Pythagora-io/gpt-pilot",
            "godotengine/godot",
            "appwrite/appwrite",
            "coqui-ai/TTS",
            "spacedriveapp/spacedrive",
            "novuhq/novu",
            "krahets/hello-algo",
            "jwasham/coding-interview-university",
            "massgravel/Microsoft-Activation-Scripts",
            "haotian-liu/LLaVA",
            "EbookFoundation/free-programming-books",
            "graphdeco-inria/gaussian-splatting",
            "bevyengine/bevy",
            "harness/gitness",
            "airbnb/javascript",
            "TabbyML/tabby",
            "fishaudio/Bert-VITS2",
            "TheAlgorithms/JavaScript"
        ], "november_2023": [
            "ByteByteGoHq/system-design-101",
            "zzzgydi/clash-verge",
            "cpacker/MemGPT",
            "localsend/localsend",
            "2dust/v2rayN",
            "yangshun/tech-interview-handbook",
            "SagerNet/sing-box",
            "XTLS/Xray-core",
            "public-apis/public-apis",
            "PWhiddy/PokemonRedExperiments",
            "chat2db/Chat2DB",
            "v2fly/v2ray-core",
            "2dust/v2rayNG",
            "lyswhut/lx-music-desktop",
            "OpenTalker/video-retalking",
            "MatsuriDayo/nekoray",
            "apache/incubator-answer",
            "apernet/hysteria",
            "danielgross/localpilot",
            "donnemartin/system-design-primer"
        ], "december_2023": [
            "abi/screenshot-to-code",
            "BuilderIO/gpt-crawler",
            "Stability-AI/generative-models",
            "lllyasviel/Fooocus",
            "microsoft/generative-ai-for-beginners",
            "facebookresearch/seamless_communication",
            "tldraw/tldraw",
            "microsoft/ML-For-Beginners",
            "lobehub/lobe-chat",
            "dotnet/eShop",
            "microsoft/AI-For-Beginners",
            "comfyanonymous/ComfyUI",
            "ollama-webui/ollama-webui",
            "cbh123/narrator",
            "Vaibhavs10/insanely-fast-whisper",
            "biomejs/biome",
            "google-deepmind/graphcast",
            "AppFlowy-IO/AppFlowy",
            "langgenius/dify",
            "danny-avila/LibreChat"
        ], "january_2024": [
            "Stirling-Tools/Stirling-PDF",
            "Pythagora-io/gpt-pilot",
            "mckaywrigley/chatbot-ui",
            "jzhang38/TinyLlama",
            "tachiyomiorg/tachiyomi",
            "Hillobar/Rope",
            "jianchang512/clone-voice",
            "shadcn-ui/ui",
            "anoma/namada",
            "DataTalksClub/data-engineering-zoomcamp",
            "jmorganca/ollama",
            "AmruthPillai/Reactive-Resume",
            "ruanyf/weekly",
            "danswer-ai/danswer",
            "karanpratapsingh/system-design",
            "tiann/KernelSU",
            "lobehub/lobe-chat",
            "practical-tutorials/project-based-learning",
            "apache/incubator-answer",
            "labring/FastGPT"
        ], "february_2024": [
            "maybe-finance/maybe",
            "netease-youdao/QAnything",
            "TencentARC/PhotoMaker",
            "KRTirtho/spotube",
            "stanfordnlp/dspy",
            "vanna-ai/vanna",
            "xiaolai/everyone-can-use-english",
            "usememos/memos",
            "DataTalksClub/data-engineering-zoomcamp",
            "joaomdmoura/crewAI",
            "SerenityOS/serenity",
            "EbookFoundation/free-programming-books",
            "MooreThreads/Moore-AnimateAnyone",
            "expo/expo",
            "backstage/backstage",
            "servo/servo",
            "Dooy/chatgpt-web-midjourney-proxy",
            "NvChad/NvChad",
            "rails/rails",
            "nushell/nushell"
        ]}

    repo_list: list = []

    for key in trending_github_repos:
        repo_list.extend(trending_github_repos[key])

    return list(set(repo_list))


def get_validation_result_per_criterion(repos: list, github_access_token: str) -> dict[str, dict[str, bool]]:
    results_per_criterion: dict[str, dict[str, bool]] = {}

    for repo_name in repos:
        try:
            _, _, report = validation_interface.run_validator(github_access_token, repo_name, "FAIRSoftware")
        except UnknownObjectException as e:
            logging.exception(f"Could not validate {repo_name} against the FAIRSoftware project type. {e}")
            continue
        verbalized_explanation = verbalization_interface.run_verbalizer(report)
        result_per_criterion = process_verbalized_explanation(verbalized_explanation)
        results_per_criterion[repo_name] = result_per_criterion

    return results_per_criterion


def process_verbalized_explanation(verbalized_explanation: list[str]) -> dict[str, bool]:
    possible_messages_with_mapping: dict[str, str] = {
        "The repository has no description and no README file.": "DescriptionOrReadme",
        "No persistent ID was found.": "PersistentId",
        "The repository is private.": "PublicRepository",
        "There are no releases or Semantic Versioning is violated.": "SemanticVersioning",
        "There is no README file or it does not contain usage instructions for the software.": "UsageNotesInReadme",
        "No license information was found.": "ExactlyOneLicense",
        "No citation information was found.": "ExplicitCitation",
        "The repository has no description and no topics assigned.": "DescriptionOrAtLeastOneTopic",
        "There is no README file or it does not contain installation instructions.": "InstallationInstructionsInReadme",
        "No information on the requirements of the software was found.": "SoftwareRequirements"
    }

    result_per_criterion: dict[str, bool] = {}
    for possible_message, mapping in possible_messages_with_mapping.items():
        if any(actual_message.startswith(possible_message) for actual_message in verbalized_explanation):
            result_per_criterion[mapping] = False
        else:
            result_per_criterion[mapping] = True

    return result_per_criterion


def execute_runtime_benchmark(repos_expected_to_be_fair: list, trending_repos: list, github_access_token: str) -> None:
    auth = Auth.Token(github_access_token)
    g = Github(auth=auth)

    runtime_benchmark_results = dict()

    runtime_per_repo = []
    step_durations = [0, 0, 0]

    for repo_name in trending_repos + repos_expected_to_be_fair:
        # skip repo for evaluation if relevant data cannot be fetched
        try:
            repo = g.get_repo(repo_name)
            # compute repo size as the sum of releases branches and issues
            repo_size = repo.get_releases().totalCount + repo.get_branches().totalCount + repo.get_issues().totalCount
        except:
            continue

        # perform fairness assessment with profiler
        file_name = f"{repo_name.split('/')[1]}"
        
        logging.info(f"{repo_name} has in total {repo_size} releases, branches, and issues.")

        cmd = ["./shacl_validator.py", "--github_access_token", github_access_token, "--repo_name", repo_name,
               "--expected_type", "FAIRSoftware"]

        run(["python3", "-m", "cProfile", "-o", f"data/benchmarks/{file_name}", "-s", "cumulative"] + cmd)
        
        # process stats of fairness assessment runtime
        stats = pstats.Stats(f"data/benchmarks/{file_name}")

        for k, v in stats.stats.items():
            _, _, function = k

            if function == "validate_repo_against_specs":
                runtime = v[3]

            elif function == "create_project_type_representation":
                step_durations[0] += v[3]

            elif function == "create_repository_representation":
                step_durations[1] += v[3]

            elif function == "run_validation":
                step_durations[2] += v[3]

        runtime_per_repo.append(runtime)
        origin = "trending" if repo_name in trending_repos else "expected"
        runtime_benchmark_results[file_name] = (repo_size, runtime, origin)

    total_runtime = sum(runtime_per_repo)
    step_durations = ["{:.2f}%".format(duration / total_runtime * 100) for duration in step_durations]

    logging.info(
        f"Shapes graph composition/repository representation generation/validation account for {'/'.join(step_durations)} of the total runtime.")

    return runtime_benchmark_results

def visualize_results() -> None:

    def get_results_in_percent(results_per_criterion: dict[str, dict[str, bool]]) -> dict[str, float]:
        first_inner_dict = list(results_per_criterion.values())[0]
        numeric_results: dict[str, int] = {key: 0 for key in first_inner_dict}

        for _, result_per_criterion in results_per_criterion.items():
            for criterion, value in result_per_criterion.items():
                if value:
                    numeric_results[criterion] += 1

        return {key: value / len(results_per_criterion) * 100 for key, value in numeric_results.items()}

    # plot FAIRness assessment
    with open("./data/evaluation/repos_expected_to_be_fair.json") as file_fair:
        results_per_criterion_fair: dict[str, dict[str, bool]] = json.load(file_fair)

    with open("./data/evaluation/trending_repos.json") as file_trending:
        results_per_criterion_trending: dict[str, dict[str, bool]] = json.load(file_trending)

    normalized_numeric_results_fair = get_results_in_percent(results_per_criterion_fair)
    normalized_numeric_results_trending = get_results_in_percent(results_per_criterion_trending)

    best_practices = ("BP1", "BP2", "BP3", "BP4", "BP5", "BP6", "BP7", "BP8", "BP9", "BP10")
    scores_fair = list(normalized_numeric_results_fair.values())
    scores_trending = list(normalized_numeric_results_trending.values())

    x = np.arange(len(best_practices))
    width = 0.35
    fig, ax = plt.subplots(figsize=(6, 4))

    ax.bar(x - width / 2, scores_fair, width, label="Repositories Expected to be FAIR (N=6)", color="#00407A")
    ax.bar(x + width / 2, scores_trending, width, label="Trending Repositories (N=217)", color="#8ed7d7")
    ax.legend(loc="lower left", ncol=1, bbox_to_anchor=(0, 1, 1, 0))

    ax.set_ylabel("Percentage of Conform Repositories")

    ax.set_yticks(np.arange(0, 101, 10))
    ax.set_yticks(np.arange(5, 100, 5), minor=True)
    ax.set_xticks(x)
    ax.set_xticklabels(best_practices)

    ax.set_axisbelow(True)
    ax.yaxis.grid(which="major", linestyle="dashed", linewidth=0.5, color="black")
    ax.yaxis.grid(which="minor", linestyle="dashed", linewidth=0.5)

    fig.tight_layout()

    plt.savefig("./data/evaluation/conformity_per_best_practice.pdf")

    # plot runtime benchmark
    x_trending = []
    y_trending = []

    x_expected = []
    y_expected = []

    with open("./data/evaluation/runtime_benchmark_results.json") as file_benchmark:
        runtime_benchmark_results: dict[str, dict[str, bool]] = json.load(file_benchmark)

    for size, runtime, origin in runtime_benchmark_results.values():
        if origin == "trending":
            x_trending.append(size)
            y_trending.append(runtime)

        else:
            x_expected.append(size)
            y_expected.append(runtime)

    fig = plt.figure(figsize=(6, 4))

    bax = brokenaxes(xlims=((0, 5000), (12000, 12500)), ylims=((0, 30), (50, 55)))

    bax.scatter(x_trending, y_trending, c="#8ed7d7", s=15, label="Trending Repositories\n(N=217)")
    bax.scatter(x_expected, y_expected, c="#00407A", s=15, label="Repositories Expected to\nbe FAIR (N=6)")

    bax.set_xlabel("Repository Size")
    bax.set_ylabel("Runtime Duration in Seconds")

    bax.legend(loc=1, ncol=1)

    bax.grid(axis='y', which='major', ls="dashed")
    bax.grid(axis='y', which='minor', ls="dashed", linewidth=0.5)

    plt.savefig("./data/evaluation/benchmark_results.pdf")


if __name__ == "__main__":
    perform_evaluation()
    visualize_results()
