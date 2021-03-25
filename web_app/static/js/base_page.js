
// Search bar auto complete.
$('#allele').autocomplete({
    serviceUrl: '/suggest/allele',
    dataType: 'json',
});
$('#peptide').autocomplete({
    serviceUrl: '/suggest/peptide',
    dataType: 'json',
});


