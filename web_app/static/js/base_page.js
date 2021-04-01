
// Search bar auto complete.
$('#allele').autocomplete({
    serviceUrl: '/suggest/allele',
    dataType: 'json',
    delimiter: ',',
});
$('#peptide').autocomplete({
    serviceUrl: '/suggest/peptide',
    dataType: 'json',
});

