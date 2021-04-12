// Returns true if regex is valid
const checkRegex = (peptideQuery) => {
    var pairs = peptideQuery.split(",").map(x => x.trim());

    const checkLetter = (c) => (/[a-zA-Z]/).test(c);
    const checkNumber = (c) => (c <= "9" && c >= "1");

    const validate_pair = (p) => {
        return (p.length == 2) && (checkLetter(p.charAt(0))) && (checkNumber(p.charAt(1)));
    };

    pairs = pairs.filter(validate_pair);

    return pairs.length > 0;
};

// Search bar auto complete.
$(document).ready(function() {
    $('#allele').autocomplete({
        serviceUrl: '/suggest/allele',
        dataType: 'json',
        delimiter: ',',
    });
    $('#peptide').autocomplete({
        serviceUrl: '/suggest/peptide',
        dataType: 'json',
    });

    // Check if peptide query is regex or raw on change
    $('#peptide').on("input", function() {
        var currentValue = this.value;
        const result = checkRegex(currentValue);
        if (result) {
            $("#peptide-search-type").text("Regex Search");
            $("#peptide-regex").val("on");
        }
        else {
            $("#peptide-search-type").text("Plain Search");
            $("#peptide-regex").val("off");
        }
    });
});





