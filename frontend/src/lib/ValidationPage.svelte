<script>
    import ValidationForm from "./ValidationForm.svelte";
    import ValidationResult from "./ValidationResult.svelte";

    let repositoryName = "";
    let projectType = "";
    let validationReport = "";
    let validationReportVerbalized = "";

    const revealValidationResult = (repoName, repoType, report, verbalized) => {
        console.log(report)
        repositoryName = repoName;
        projectType = repoType;
        validationReport = report;
        validationReportVerbalized = verbalized;
    };
</script>

<div class="container-fluid">
    <div class="row">
        <div class="col">
            <h1 class="mt-3 text-center">Validation</h1>
        </div>
    </div>
    <div class="row justify-content-center mb-3">
        <div class="col-6">
            <h5 class="text-center">
                On this page, GitHub repositories can be validated against a predefined
                project type which corresponds to a set of quality criteria.
            </h5>
        </div>
    </div>

    <ValidationForm {revealValidationResult}/>
    <ValidationResult {repositoryName} {projectType} {validationReport} {validationReportVerbalized}/>
</div>
