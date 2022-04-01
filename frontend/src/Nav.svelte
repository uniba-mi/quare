<script context="module">
  import ValidationPage from "./ValidationPage.svelte";
  import SpecificationPage from "./SpecificationPage.svelte";

  export const navOptions = [
    { page: "Validation", component: ValidationPage },
    { page: "Specification", component: SpecificationPage },
  ];
</script>
