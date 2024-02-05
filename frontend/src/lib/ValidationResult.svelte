<script>
    export let repositoryName;
    export let projectType;
    export let validationReport;
    export let validationReportVerbalized;
</script>

<div class="row justify-content-center">
    {#if validationReport}
        <div class="col-4">
            <p>Raw Explanation:</p>
            <textarea class="form-control" rows="15" readonly>{validationReport}</textarea>
        </div>
    {/if}
    {#if validationReportVerbalized}
        <div class="col-4">
            <p>Verbalized Explanation:</p>
            <div class="overflow-auto verbalized-explanation">
                {repositoryName} does not comply with the quality criteria of {projectType}:
                <ul>
                    {#each validationReportVerbalized as explanation}
                        <li>{explanation}</li>
                    {/each}
                </ul>
            </div>
        </div>
    {/if}
</div>

<style>
    textarea {
        font-size: 8pt;
    }

    ul {
        margin-top: 0.5em;
    }

    .verbalized-explanation {
        height: 254px;
        border: var(--bs-border-width) solid var(--bs-border-color);
        border-radius: var(--bs-border-radius);
        padding: 0.375rem 0.75rem;
    }

</style>
