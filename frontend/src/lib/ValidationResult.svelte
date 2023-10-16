<script>
  export let validationReport;
  export let validationReportVerbalized;
</script>

<div class="row justify-content-center">
  {#if validationReport}
    <div class="col-4">
      <p>Raw Explanation:</p>
      <textarea class="form-control" rows="15" readonly>
        {validationReport}
      </textarea>
    </div>
  {/if}
  {#if validationReportVerbalized}
    <div class="col-4">
      <p>Verbalized Explanation:</p>
      <textarea class="form-control" rows="15" readonly>
        {validationReportVerbalized}
      </textarea>
    </div>
  {/if}
</div>

<style>
  textarea {
    font-size: 8pt;
  }
</style>
